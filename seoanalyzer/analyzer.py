#!/usr/bin/env python3

from bs4 import BeautifulSoup
from collections import Counter
from operator import itemgetter
from string import punctuation
from urllib.parse import urlsplit
from xml.dom import minidom

from seoanalyzer.stemmer import stem

import argparse
import json
import nltk
import re
import requests
import socket
import time

##
# python 3.6+ support.
import sys

if list(sys.version_info)[:2] >= [3, 6]:
    unicode = str
##


# This list of English stop words is taken from the "Glasgow Information
# Retrieval Group". The original list can be found at
# http://ir.dcs.gla.ac.uk/resources/linguistic_utils/stop_words
ENGLISH_STOP_WORDS = frozenset([
    "a", "about", "above", "across", "after", "afterwards", "again", "against",
    "all", "almost", "alone", "along", "already", "also", "although", "always",
    "am", "among", "amongst", "amoungst", "amount", "an", "and", "another",
    "any", "anyhow", "anyone", "anything", "anyway", "anywhere", "are",
    "around", "as", "at", "back", "be", "became", "because", "become",
    "becomes", "becoming", "been", "before", "beforehand", "behind", "being",
    "below", "beside", "besides", "between", "beyond", "bill", "both",
    "bottom", "but", "by", "call", "can", "cannot", "cant", "co", "con",
    "could", "couldnt", "cry", "de", "describe", "detail", "do", "done",
    "down", "due", "during", "each", "eg", "eight", "either", "eleven", "else",
    "elsewhere", "empty", "enough", "etc", "even", "ever", "every", "everyone",
    "everything", "everywhere", "except", "few", "fifteen", "fify", "fill",
    "find", "fire", "first", "five", "for", "former", "formerly", "forty",
    "found", "four", "from", "front", "full", "further", "get", "give", "go",
    "had", "has", "hasnt", "have", "he", "hence", "her", "here", "hereafter",
    "hereby", "herein", "hereupon", "hers", "herself", "him", "himself", "his",
    "how", "however", "hundred", "i", "ie", "if", "in", "inc", "indeed",
    "interest", "into", "is", "it", "its", "itself", "keep", "last", "latter",
    "latterly", "least", "less", "ltd", "made", "many", "may", "me",
    "meanwhile", "might", "mill", "mine", "more", "moreover", "most", "mostly",
    "move", "much", "must", "my", "myself", "name", "namely", "neither",
    "never", "nevertheless", "next", "nine", "no", "nobody", "none", "noone",
    "nor", "not", "nothing", "now", "nowhere", "of", "off", "often", "on",
    "once", "one", "only", "onto", "or", "other", "others", "otherwise", "our",
    "ours", "ourselves", "out", "over", "own", "part", "per", "perhaps",
    "please", "put", "rather", "re", "same", "see", "seem", "seemed",
    "seeming", "seems", "serious", "several", "she", "should", "show", "side",
    "since", "sincere", "six", "sixty", "so", "some", "somehow", "someone",
    "something", "sometime", "sometimes", "somewhere", "still", "such",
    "system", "take", "ten", "than", "that", "the", "their", "them",
    "themselves", "then", "thence", "there", "thereafter", "thereby",
    "therefore", "therein", "thereupon", "these", "they",
    "third", "this", "those", "though", "three", "through", "throughout",
    "thru", "thus", "to", "together", "too", "top", "toward", "towards",
    "twelve", "twenty", "two", "un", "under", "until", "up", "upon", "us",
    "very", "via", "was", "we", "well", "were", "what", "whatever", "when",
    "whence", "whenever", "where", "whereafter", "whereas", "whereby",
    "wherein", "whereupon", "wherever", "whether", "which", "while", "whither",
    "who", "whoever", "whole", "whom", "whose", "why", "will", "with",
    "within", "without", "would", "yet", "you", "your", "yours", "yourself",
    "yourselves"])

TOKEN_REGEX = re.compile(r'(?u)\b\w\w+\b')


class Manifest(object):
    """
    Pretty much what it sounds like...
    This is a singleton class which *should*:
    - allow for easy namespace-separation
    &
    - reinitialization of what were previously global vars.
    """
    # class vars
    wordcount = Counter()
    bigrams = Counter()
    trigrams = Counter()
    pages_crawled = []
    pages_to_crawl = []
    stem_to_word = {}
    page_titles = []
    page_descriptions = []

    # b/c this is necessary for persistence...I think...it is in python2...
    def __init__(self):
        super(Manifest, self).__init__()

    @classmethod
    def clear_cache(cls):
        # called at the end of the global `analyze()` function to make a fresh manifest.
        cls.wordcount = Counter()
        cls.bigrams = Counter()
        cls.trigrams = Counter()
        cls.pages_crawled = []
        cls.pages_to_crawl = []
        cls.stem_to_word = {}
        cls.page_titles = []
        cls.page_descriptions = []


class Page(object):
    """
    Container for each page and the analyzer.
    """

    def __init__(self, url='', site=''):
        """
        Variables go here, *not* outside of __init__
        """
        self.site = site
        self.url = url
        self.title = u''
        self.description = u''
        self.keywords = {}
        self.warnings = []
        self.translation = bytes.maketrans(punctuation.encode('utf-8'), str(u' ' * len(punctuation)).encode('utf-8'))
        self.social = {'facebook': {
                            'shares': 0,
                            'comments': 0,
                            'likes': 0,
                            'clicks': 0},
                       'stumbleupon' : {
                           'stumbles' : 0,
                       }}
        super(Page, self).__init__()

    def talk(self):
        """
        Returns a dictionary that can be printed
        """

        return {
            'url': self.url,
            'title': self.title,
            'description': self.description,
            'keywords': self.sort_freq_dist(self.keywords, limit=5),
            'warnings': self.warnings,
        }

    def populate(self, bs):
        """
        Populates the instance variables from BeautifulSoup
        """
        try:
            self.title = bs.title.text
        except AttributeError:
            self.title = 'No Title'

        descr = bs.findAll('meta', attrs={'name': 'description'})

        if len(descr) > 0:
            self.description = descr[0].get('content')

        keywords = bs.findAll('meta', attrs={'name': 'keywords'})

        if len(keywords) > 0:
            self.warn(
                u'Keywords should be avoided as they are a spam indicator and no longer used by Search Engines: {0}'.format(
                    k))

    def analyze(self):
        """
        Analyze the page and populate the warnings list
        """
        if self.url.startswith('mailto:'):
            return

        if self.url in Manifest.pages_crawled:
            return

        Manifest.pages_crawled.append(self.url)

        if self.url.startswith('//'):
            self.url = 'http:{0}'.format(self.url)

        try:
            page = requests.get(self.url)
        except requests.exceptions.HTTPError as e:
            self.warn(u'Returned {0}'.format(page.status_code))
            return

        encoding = 'ascii'
        if 'content-type' in page.headers:
            encoding = page.headers['content-type'].split('charset=')[-1]

        if encoding.lower() not in ('text/html', 'text/plain', 'utf-8'):
            try:
                raw_html = unicode(page.read(), encoding)
            except:
                self.warn(u'Can not read {0}'.format(encoding))
                return
        else:
            raw_html = u'{}'.format(page.text)

        # remove comments, they screw with BeautifulSoup
        clean_html = re.sub(r'<!--.*?-->', r'', raw_html, flags=re.DOTALL)

        soup_lower = BeautifulSoup(clean_html.lower(), 'html.parser')
        soup_unmodified = BeautifulSoup(clean_html, 'html.parser')

        texts = soup_lower.findAll(text=True)
        visible_text = filter(self.visible_tags, texts)

        self.process_text(visible_text)

        self.populate(soup_lower)

        self.analyze_title()
        self.analyze_description()
        self.analyze_og(soup_lower)
        self.analyze_a_tags(soup_unmodified)
        self.analyze_img_tags(soup_lower)
        self.analyze_h1_tags(soup_lower)
        self.social_shares()

    def word_list_freq_dist(self, wordlist):
        freq = [wordlist.count(w) for w in wordlist]
        return dict(zip(wordlist, freq))

    def sort_freq_dist(self, freqdist, limit=1):
        aux = [(freqdist[key], Manifest.stem_to_word[key]) for key in freqdist if freqdist[key] >= limit]
        aux.sort()
        aux.reverse()
        return aux

    def social_shares(self):
        fb_share_count = 0
        fb_comment_count = 0
        fb_like_count = 0
        fb_click_count = 0

        try:
            page = requests.get(
                'https://graph.facebook.com/?fields=og_object{{likes.limit(0).summary(true)}},share&id={}'.format(
                    self.url))
            fb_data = json.loads(page.text)
            fb_share_count = fb_data['share']['share_count']
            fb_comment_count = fb_data['share']['comment_count']
            fb_like_count = fb_data['og_object']['likes']['summary']['total_count']
            # fb_reaction_count = fb_data['engagement']['reaction_count']
        except:
            pass

        self.social['facebook'] = {
            'shares': fb_share_count,
            'comments': fb_comment_count,
            'likes': fb_like_count,
            'clicks': fb_click_count,
        }

        su_views = 0

        try:
            page = requests.get('http://www.stumbleupon.com/services/1.01/badge.getinfo?url={0}'.format(self.url))
            su_data = page.json()
            if 'result' in su_data and 'views' in su_data['result']:
                su_views = su_data['result']['views']
        except:
            pass

        self.social['stumbleupon'] = {
            'stumbles': su_views,
        }

    def raw_tokenize(self, rawtext):
        return TOKEN_REGEX.findall(rawtext.lower())

    def tokenize(self, rawtext):
        return [word for word in TOKEN_REGEX.findall(rawtext.lower()) if word not in ENGLISH_STOP_WORDS]

    def getngrams(self, D, n=2):
        return zip(*[D[i:] for i in range(n)])

    def process_text(self, vt):
        page_text = ''

        for element in vt:
            page_text += element.lower() + u' '

        tokens = self.tokenize(page_text)
        raw_tokens = self.raw_tokenize(page_text)

        bigrams = self.getngrams(raw_tokens, 2)

        for ng in bigrams:
            vt = ' '.join(ng)
            Manifest.bigrams[vt] += 1

        trigrams = self.getngrams(raw_tokens, 3)

        for ng in trigrams:
            vt = ' '.join(ng)
            Manifest.trigrams[vt] += 1

        freq_dist = self.word_list_freq_dist(tokens)

        for word in freq_dist:
            root = stem(word)
            cnt = freq_dist[word]

            if root not in Manifest.stem_to_word:
                Manifest.stem_to_word[root] = word

            if root in Manifest.wordcount:
                Manifest.wordcount[root] += cnt
            else:
                Manifest.wordcount[root] = cnt

            if root in self.keywords:
                self.keywords[root] += cnt
            else:
                self.keywords[root] = cnt

    def analyze_og(self, bs):
        """
        Validate open graph tags
        """
        og_title = bs.findAll('meta', attrs={'property': 'og:title'})
        og_description = bs.findAll('meta', attrs={'property': 'og:description'})
        og_image = bs.findAll('meta', attrs={'property': 'og:image'})

        if len(og_title) == 0:
            self.warn(u'Missing og:title')

        if len(og_description) == 0:
            self.warn(u'Missing og:descriptoin')

        if len(og_image) == 0:
            self.warn(u'Missing og:image')

    def analyze_title(self):
        """
        Validate the title
        """

        # getting lazy, create a local variable so save having to
        # type self.x a billion times
        t = self.title

        # calculate the length of the title once
        length = len(t)

        if length == 0:
            self.warn(u'Missing title tag')
            return
        elif length < 10:
            self.warn(u'Title tag is too short (less than 10 characters): {0}'.format(t))
        elif length > 70:
            self.warn(u'Title tag is too long (more than 70 characters): {0}'.format(t))

        if t in Manifest.page_titles:
            self.warn(u'Duplicate page title: {0}'.format(t))
            return

        Manifest.page_titles.append(t)

    def analyze_description(self):
        """
        Validate the description
        """

        # getting lazy, create a local variable so save having to
        # type self.x a billion times
        d = self.description

        # calculate the length of the description once
        length = len(d)

        if length == 0:
            self.warn(u'Missing description')
            return
        elif length < 140:
            self.warn(u'Description is too short (less than 140 characters): {0}'.format(d))
        elif length > 255:
            self.warn(u'Description is too long (more than 255 characters): {0}'.format(d))

        if d in Manifest.page_descriptions:
            self.warn(u'Duplicate description: {0}'.format(d))
            return

        Manifest.page_descriptions.append(d)

    def visible_tags(self, element):
        if element.parent.name in ['style', 'script', '[document]']:
            return False

        return True

    def analyze_img_tags(self, bs):
        """
        Verifies that each img has an alt and title
        """
        images = bs.find_all('img')

        for image in images:
            src = ''
            if 'src' in image:
                src = image['src']
            elif 'data-src' in image:
                src = image['data-src']
            else:
                src = image

            if len(image.get('alt', '')) == 0:
                self.warn('Image missing alt tag: {0}'.format(src))

    def analyze_h1_tags(self, bs):
        """
        Make sure each page has at least one H1 tag
        """
        htags = bs.find_all('h1')

        if len(htags) == 0:
            self.warn('Each page should have at least one h1 tag')

    def analyze_a_tags(self, bs):
        """
        Add any new links (that we didn't find in the sitemap)
        """
        anchors = bs.find_all('a', href=True)

        for tag in anchors:
            tag_href = tag['href']
            tag_text = tag.text.lower().strip()

            if len(tag.get('title', '')) == 0:
                self.warn('Anchor missing title tag: {0}'.format(tag_href))

            if tag_text in ['click here', 'page', 'article']:
                self.warn('Anchor text contains generic text: {0}'.format(tag_text))

            if self.site not in tag_href and ':' in tag_href:
                continue

            modified_url = self.rel_to_abs_url(tag_href)

            if modified_url in Manifest.pages_crawled:
                continue

            Manifest.pages_to_crawl.append(modified_url)

    def rel_to_abs_url(self, link):
        if ':' in link:
            return link

        relative_path = link
        domain = self.site

        if domain[-1] == '/':
            domain = domain[:-1]

        if len(relative_path) > 0 and relative_path[0] == '?':
            if '?' in self.url:
                return '{0}{1}'.format(self.url[:self.url.index('?')], relative_path)

            return '{0}{1}'.format(self.url, relative_path)

        if len(relative_path) > 0 and relative_path[0] != '/':
            relative_path = '/{0}'.format(relative_path)

        return '{0}{1}'.format(domain, relative_path)

    def warn(self, warning):
        self.warnings.append(warning)


def getText(nodelist):
    """
    Stolen from the minidom documentation
    """
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)


def do_ignore(url_to_check):
    # todo: add blacklist of url types
    return False


def check_dns(url_to_check):
    try:
        o = urlsplit(url_to_check)
        socket.gethostbyname(o.hostname)
        return True
    except:
        pass

    return False


def analyze(site, sitemap=None):
    start_time = time.time()

    def calc_total_time():
        return time.time() - start_time

    crawled = []
    output = {'pages': [], 'keywords': [], 'errors': [], 'total_time': calc_total_time()}

    if check_dns(site) == False:
        output['errors'].append('DNS Lookup Failed')
        output['total_time'] = calc_total_time()
        return output

    if sitemap is not None:
        page = requests.get(sitemap)
        xml_raw = page.text
        xmldoc = minidom.parseString(xml_raw)
        urls = xmldoc.getElementsByTagName('loc')

        for url in urls:
            Manifest.pages_to_crawl.append(getText(url.childNodes))

    Manifest.pages_to_crawl.append(site)

    for page in Manifest.pages_to_crawl:
        if page.strip().lower() in crawled:
            continue

        if '#' in page:
            if page[:page.index('#')].strip().lower() in crawled:
                continue

        if do_ignore(page) == True:
            continue

        crawled.append(page.strip().lower())

        pg = Page(page, site)

        pg.analyze()

        output['pages'].append(pg.talk())

    sorted_words = sorted(Manifest.wordcount.items(), key=itemgetter(1), reverse=True)
    sorted_bigrams = sorted(Manifest.bigrams.items(), key=itemgetter(1), reverse=True)
    sorted_trigrams = sorted(Manifest.trigrams.items(), key=itemgetter(1), reverse=True)

    output['keywords'] = []

    for w in sorted_words:
        if w[1] > 4:
            output['keywords'].append({
                'word': Manifest.stem_to_word[w[0]],
                'count': w[1],
            })

    for w, v in sorted_bigrams:
        if v > 4:
            output['keywords'].append({
                'word': w,
                'count': v,
            })

    for w, v in sorted_trigrams:
        if v > 4:
            output['keywords'].append({
                'word': w,
                'count': v,
            })

    # Sort one last time...
    output['keywords'] = sorted(output['keywords'], key=itemgetter('count'), reverse=True)

    output['total_time'] = calc_total_time()

    # Clear our "global" variables for the next run.
    Manifest.clear_cache()

    return output


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument('site', help='URL of the site you are wanting to analyze.')
    arg_parser.add_argument('-s', '--sitemap', help='URL of the sitemap to seed the crawler with.')
    arg_parser.add_argument('-f', '--output-format', help='Output format.', choices=['json', 'html', ], default='json')

    args = arg_parser.parse_args()

    output = analyze(args.site, args.sitemap)

    if args.output_format == 'html':
        from jinja2 import Environment
        from jinja2 import FileSystemLoader

        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('index.html')
        output_from_parsed_template = template.render(result=output)
        print(output_from_parsed_template)
    elif args.output_format == 'json':
        print(json.dumps(output, indent=4, separators=(',', ': ')))
