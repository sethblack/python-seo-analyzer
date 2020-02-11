import hashlib
import json
import re

from bs4 import BeautifulSoup
from collections import Counter
from string import punctuation
from urllib.parse import urlsplit
from urllib3.exceptions import HTTPError

from seoanalyzer.http import http
from seoanalyzer.stemmer import stem

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


class Page():
    """
    Container for each page and the core analyzer.
    """

    def __init__(self, url='', base_domain=''):
        """
        Variables go here, *not* outside of __init__
        """

        self.base_domain = urlsplit(base_domain)
        self.parsed_url = urlsplit(url)
        self.url = url
        self.title = ''
        self.description = ''
        self.keywords = {}
        self.warnings = []
        self.translation = bytes.maketrans(punctuation.encode('utf-8'), str(' ' * len(punctuation)).encode('utf-8'))
        self.social = {
            'facebook': {'shares': 0, 'comments': 0, 'likes': 0, 'clicks': 0},
        }
        self.links = []
        self.total_word_count = 0
        self.wordcount = Counter()
        self.bigrams = Counter()
        self.trigrams = Counter()
        self.stem_to_word = {}
        self.content_hash = None

    def talk(self):
        """
        Returns a dictionary that can be printed
        """

        return {
            'url': self.url,
            'title': self.title,
            'description': self.description,
            'word_count': self.total_word_count,
            'keywords': self.sort_freq_dist(self.keywords, limit=5),
            'bigrams': self.bigrams,
            'trigrams': self.trigrams,
            'warnings': self.warnings,
            'social': self.social,
            'content_hash': self.content_hash
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
            self.warn(f'Keywords should be avoided as they are a spam indicator and no longer used by Search Engines: {keywords}')

    def analyze(self, raw_html=None):
        """
        Analyze the page and populate the warnings list
        """

        if not raw_html:
            valid_prefixes = []

            # only allow http:// https:// and //
            for s in ['http://', 'https://', '//',]:
                valid_prefixes.append(self.url.startswith(s))

            if True not in valid_prefixes:
                self.warn(f'{self.url} does not appear to have a valid protocol.')
                return

            if self.url.startswith('//'):
                self.url = f'{self.base_domain.scheme}:{self.url}'

            if self.parsed_url.netloc != self.base_domain.netloc:
                self.warn(f'{self.url} is not part of {self.base_domain.netloc}.')
                return

            try:
                page = http.get(self.url)
            except HTTPError as e:
                self.warn(f'Returned {e}')
                return

            encoding = 'ascii'

            if 'content-type' in page.headers:
                encoding = page.headers['content-type'].split('charset=')[-1]

            if encoding.lower() not in ('text/html', 'text/plain', 'utf-8'):
                # there is no unicode function in Python3
                # try:
                #     raw_html = unicode(page.read(), encoding)
                # except:
                self.warn(f'Can not read {encoding}')
                return
            else:
                raw_html = page.data.decode('utf-8')

        self.content_hash = hashlib.sha1(raw_html.encode('utf-8')).hexdigest()

        # remove comments, they screw with BeautifulSoup
        clean_html = re.sub(r'<!--.*?-->', r'', raw_html, flags=re.DOTALL)

        soup_lower = BeautifulSoup(clean_html.lower(), 'html.parser') #.encode('utf-8')
        soup_unmodified = BeautifulSoup(clean_html, 'html.parser') #.encode('utf-8')

        texts = soup_lower.findAll(text=True)
        visible_text = [w for w in filter(self.visible_tags, texts)]

        self.process_text(visible_text)

        self.populate(soup_lower)

        self.analyze_title()
        self.analyze_description()
        self.analyze_og(soup_lower)
        self.analyze_a_tags(soup_unmodified)
        self.analyze_img_tags(soup_lower)
        self.analyze_h1_tags(soup_lower)
        self.social_shares()

        return True

    def word_list_freq_dist(self, wordlist):
        freq = [wordlist.count(w) for w in wordlist]
        return dict(zip(wordlist, freq))

    def sort_freq_dist(self, freqdist, limit=1):
        aux = [(freqdist[key], self.stem_to_word[key]) for key in freqdist if freqdist[key] >= limit]
        aux.sort()
        aux.reverse()
        return aux

    def social_shares(self):
        fb_share_count = 0
        fb_comment_count = 0
        fb_like_count = 0
        fb_click_count = 0

        try:
            page = self.session.get(
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

    def raw_tokenize(self, rawtext):
        return TOKEN_REGEX.findall(rawtext.lower())

    def tokenize(self, rawtext):
        return [word for word in TOKEN_REGEX.findall(rawtext.lower()) if word not in ENGLISH_STOP_WORDS]

    def getngrams(self, D, n=2):
        return zip(*[D[i:] for i in range(n)])

    def process_text(self, vt):
        page_text = ''

        for element in vt:
            if element.strip():
                page_text += element.strip().lower() + u' '

        tokens = self.tokenize(page_text)
        raw_tokens = self.raw_tokenize(page_text)
        self.total_word_count = len(raw_tokens)

        bigrams = self.getngrams(raw_tokens, 2)

        for ng in bigrams:
            vt = ' '.join(ng)
            self.bigrams[vt] += 1

        trigrams = self.getngrams(raw_tokens, 3)

        for ng in trigrams:
            vt = ' '.join(ng)
            self.trigrams[vt] += 1

        freq_dist = self.word_list_freq_dist(tokens)

        for word in freq_dist:
            root = stem(word)
            cnt = freq_dist[word]

            if root not in self.stem_to_word:
                self.stem_to_word[root] = word

            if root in self.wordcount:
                self.wordcount[root] += cnt
            else:
                self.wordcount[root] = cnt

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

            if self.base_domain.netloc not in tag_href and ':' in tag_href:
                continue

            modified_url = self.rel_to_abs_url(tag_href)

            self.links.append(modified_url)

    def rel_to_abs_url(self, link):
        if ':' in link:
            return link

        relative_path = link
        domain = self.base_domain.netloc

        if domain[-1] == '/':
            domain = domain[:-1]

        if len(relative_path) > 0 and relative_path[0] == '?':
            if '?' in self.url:
                return f'{self.url[:self.url.index("?")]}{relative_path}'

            return f'{self.url}{relative_path}'

        if len(relative_path) > 0 and relative_path[0] != '/':
            relative_path = f'/{relative_path}'

        return f'{self.base_domain.scheme}://{domain}{relative_path}'

    def warn(self, warning):
        self.warnings.append(warning)
