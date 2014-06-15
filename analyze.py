#!/usr/bin/env python
from bs4 import BeautifulSoup
from xml.dom import minidom
from urllib2 import urlopen
import urllib2
from string import maketrans, punctuation
from operator import itemgetter
from re import sub, match
from nltk.stem.wordnet import WordNetLemmatizer
from nltk import stem
from json import loads
import re
import sys
import nltk

# nice, a global variable >:{
wordcount = {}

# and, now some more
pages_crawled = []
pages_to_crawl = []
stem_to_word = {}
stemmer = stem.porter.PorterStemmer()
#stemmer = stem.lancaster.LancasterStemmer()

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
        self.title = ''
        self.description = ''
        self.keywords = ''
        self.warnings = []
        self.translation = maketrans(punctuation, " " * len(punctuation))
        super(Page, self).__init__()

    def talk(self, output='all'):
        """
        Print the results to stdout, tab delimited
        """
        if output == 'all':
            print "%s\t%s\t%s\t%s\t%s" % (self.url, self.title, self.description, self.keywords, self.warnings)
        elif output == 'warnings':
            if len(self.warnings) > 0:
                print "%s\t%s" % (self.url, self.warnings)
        else:
            print "I don't know what %s is." % output

    def populate(self, bs):
        """
        Populates the instance variables from BeautifulSoup
        """
        self.title = bs.title.text

        descr = bs.findAll('meta', attrs={'name':'description'})

        if len(descr) > 0:
            self.description = descr[0].get('content')

        keywords = bs.findAll('meta', attrs={'name':'keywords'})

        if len(keywords) > 0:
            self.keywords = keywords[0].get('content')

    def analyze(self):
        """
        Analyze the page and populate the warnings list
        """
        if self.url in pages_crawled:
            return

        pages_crawled.append(self.url)

        try:
            page = urlopen(self.url)
        except urllib2.HTTPError:
            self.warn('Returned 404')
            return

        encoding = page.headers['content-type'].split('charset=')[-1]

        if encoding not in('text/html', 'text/plain'):
            raw_html = unicode(page.read(), encoding)
        else:
            raw_html = page.read()

        # remove comments, they screw with BeautifulSoup
        clean_html = sub(r'<!--.*?-->', r'', raw_html.encode('utf-8'), flags=re.DOTALL)

        soup = BeautifulSoup(clean_html)

        texts = soup.findAll(text=True)
        visible_text = filter(self.visible_tags, texts)

        self.process_text(visible_text)

        self.populate(soup)

        self.analyze_title()
        self.analyze_description()
        self.analyze_keywords()
        self.analyze_a_tags(soup)
        self.analyze_img_tags(soup)
        self.analyze_h1_tags(soup)
        self.social_shares()

    def social_shares(self):
        page = urlopen('http://api.ak.facebook.com/restserver.php?v=1.0&method=links.getStats&urls=%s&format=json' % self.url)
        fb_data = loads(page.read())

        print 'facebook\t%s\t%s\t%s\t%s\t%s' % (self.url, fb_data[0]['share_count'], fb_data[0]['comment_count'], fb_data[0]['like_count'], fb_data[0]['click_count'])

        page = urlopen('http://urls.api.twitter.com/1/urls/count.json?url=%s&callback=twttr.receiveCount' % self.url)
        twitter_data = loads(page.read()[19:-2])

        print 'twitter\t%s\t%s' % (self.url, twitter_data['count'])

        page = urlopen('http://www.stumbleupon.com/services/1.01/badge.getinfo?url=%s' % self.url)
        su_data = loads(page.read())

        print 'stumbleupon\t%s\t%s' % (self.url, su_data['views'])


    def process_text(self, vt):
        page_text = ''

        for element in vt:
            page_text += element.encode('utf-8').lower() + ' '

        tokens = nltk.word_tokenize(page_text)

        freq_dist = nltk.FreqDist(tokens)

        for word in freq_dist:
            # strip out punctuation
            word = word.translate(self.translation)

            # strip suffixes
            root = stemmer.stem(word)

            # add one more layer of stripping
            if not self.is_valid_word(root):
                continue

            if root in stem_to_word and freq_dist[word] > stem_to_word[root]['count']:
                stem_to_word[root] = {'word': word, 'count': freq_dist[word]}
            else:
                stem_to_word[root] = {'word': word, 'count': freq_dist[word]}

            if root in wordcount:
                wordcount[root] += freq_dist[word]
            else:
                wordcount[root] = freq_dist[word]

    def is_valid_word(self, word):
        """
        Test a word to make sure it's "real" enough
        """

        # needs to be greater than two characters
        if len(word) <= 2:
            return False

        # dump all number strings
        if word.isdigit():
            return False

        ignore = ('a', 'at', 'the', 'of', 'and', 'that', 'for', 'are', 'is',)

        if word in ignore:
            return False

        return True

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
            self.warn('Missing title tag')
        elif length < 10:
            self.warn('Title tag is too short')
        elif length > 70:
            self.warn('Title tag is too long')

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
            self.warn('Missing description')
        elif length < 140:
            self.warn('Description is too short')
        elif length > 255:
            self.warn('Description is too long')

    def analyze_keywords(self):
        """
        Validate keywords
        """

        # getting lazy, create a local variable so save having to
        # type self.x a billion times
        k = self.keywords

        # calculate the length of keywords once
        length = len(k)

        if length == 0:
            self.warn('Missing keywords')

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
            if 'alt' not in image:
                self.warn('Image missing alt')

            if 'title' not in image:
                self.warn('Image missing title')

    def analyze_h1_tags(self, bs):
        """
        Make sure each page has at least one H1 tag
        """
        htags = bs.find_all('h1')

        if len(htags) == 0:
            warn('Each page should have at least one h1 tag')

    def analyze_a_tags(self, bs):
        """
        Add any new links (that we didn't find in the sitemap)
        """
        anchors = bs.find_all('a', href=True)

        for tag in anchors:
            if 'title' not in tag:
                self.warn('Anchor missing title tag')

            if self.site not in tag['href']:
                continue

            if tag['href'] in pages_crawled:
                continue

            pages_to_crawl.append(tag['href'])

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

def main(site, sitemap):
    page = urlopen(sitemap)
    xml_raw = page.read()
    xmldoc = minidom.parseString(xml_raw)
    urls = xmldoc.getElementsByTagName('loc') 

    for url in urls:
        pages_to_crawl.append(getText(url.childNodes))

    for page in pages_to_crawl:
        pg = Page(page, site)
        pg.analyze()
        pg.talk('warnings')

    sorted_words = sorted(wordcount.iteritems(), key=itemgetter(1), reverse=True)

    for word in sorted_words:
        print "%s\t%d" % (stem_to_word[word[0]]['word'], word[1])

if __name__ == "__main__":
    site = ''
    sitemap = ''

    if len(sys.argv) == 2:
        site = sys.argv[1]
        sitemap = site + 'sitemap.xml'
    elif len(sys.argv) == 3:
        site = sys.argv[1]
        sitemap = site + sys.argv[2]
    else:
        print "Usage: python analyze.py http://www.site.tld [sitemap]"
        exit()

    main(site, sitemap)


