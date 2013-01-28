#!/usr/bin/env python
from bs4 import BeautifulSoup
from xml.dom import minidom
from urllib2 import urlopen

class Page(object):
    """
    Container for each page and the analyzer.
    """
    def __init__(self, url=''):
	"""
	Variables go here, *not* outside of __init__
	"""
	self.url = url
	self.title = ''
	self.description = ''
	self.keywords = ''
	self.warnings = []
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
	page = urlopen(self.url)
	raw_html = page.read()
	soup = BeautifulSoup(raw_html)

	self.populate(soup)

	self.analyze_title()
	self.analyze_description()
	self.analyze_keywords()

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

    def analyze_img_tags(self, bs):
	# TODO make sure img tags have alt and title tags
	pass

    def analyze_h_tags(self, bs):
	# TODO make sure each page has at least one h1 tag
	pass

    def analyze_a_tags(self, bs):
	# make sure all a tags have alt and title tags
	pass

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

def main():
    page = urlopen('http://monikerguitars.com/sitemap.xml')
    xml_raw = page.read()
    xmldoc = minidom.parseString(xml_raw)
    urls = xmldoc.getElementsByTagName('loc') 

    for url in urls:
	pg = Page(getText(url.childNodes))
	pg.analyze()
	pg.talk('warnings')

if __name__ == "__main__":
    main()


