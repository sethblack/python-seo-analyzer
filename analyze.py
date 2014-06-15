#!/usr/bin/env python
from bs4 import BeautifulSoup
from xml.dom import minidom
from urllib2 import urlopen
from string import maketrans, punctuation
from operator import itemgetter
from re import sub, match
import re
import sys

# nice, a global variable >:{
wordcount = {}

# and, now some more
pages_crawled = []
pages_to_crawl = []

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

        page = urlopen(self.url)
        raw_html = page.read()

        # remove comments, they screw with BeautifulSoup
        clean_html = sub(r'<!--.*?-->', r'', raw_html.encode('utf-8'), flags=re.DOTALL)

        soup = BeautifulSoup(clean_html)

        texts = soup.findAll(text=True)
        visible_text = filter(self.visible_tags, texts)

        for element in visible_text:
            self.incr_global_word_count(element.encode('utf-8'))

        self.populate(soup)

        self.analyze_title()
        self.analyze_description()
        self.analyze_keywords()
        self.analyze_a_tags(soup)
        self.analyze_img_tags(soup)

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

        ignore = ('com','net','org','co','edu')

        if word in ignore:
            return False

        return True

    def incr_global_word_count(self, data):
        """
        Increment the global word count
        """
        clean = data.translate(self.translation).lower()

        for word in clean.split():
            if not self.is_valid_word(word):
                continue

            if word in wordcount:
                wordcount[word] += 1
            else:
                wordcount[word] = 1

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

        pass

    def analyze_h_tags(self, bs):
        # TODO make sure each page has at least one h1 tag
        pass

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
        print "%s\t%d" % (word[0], word[1])

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


