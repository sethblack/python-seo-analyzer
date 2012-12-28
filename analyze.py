from bs4 import BeautifulSoup
import urllib2
from xml.dom import minidom

class Page:

    def __init__(self):
	self.title = ''
	self.url = ''
	self.description = ''
	self.keywords = ''
	self.warnings = []

    def talk(self, output='all'):
	if output == 'all':
	    print "%s\t%s\t%s\t%s\t%s" % (self.url, self.title, self.description, self.keywords, self.warnings)
	elif output == 'warnings':
	    if len(self.warnings) > 0:
		print "%s\t%s" % (self.url, self.warnings)
	else:
	    print "I don't know what %s is." % output

    def analyze(self, url):
	self.url = url
	page = urllib2.urlopen(url)
	html_doc = page.read()
	soup = BeautifulSoup(html_doc)

	self.title = soup.title.text

	descr = soup.findAll('meta', attrs={'name':'description'})

	if len(descr) > 0:
	    self.description = descr[0].get('content')
	else:
	    self.description = ''
	    self.warnings.append('No description')

	keywords = soup.findAll('meta', attrs={'name':'keywords'})

	if len(keywords) > 0:
	    self.keywords = keywords[0].get('content')
	else:
	    self.keywords = ''
	    self.warnings.append('No keywords')

	if len(self.title) > 70:
	    self.warnings.append('Title is too long')

	if len(self.description) < 140:
	    self.warnings.append('Description is too short')

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

page = urllib2.urlopen('http://monikerguitars.com/sitemap.xml')
xml_raw = page.read()
xmldoc = minidom.parseString(xml_raw)
urls = xmldoc.getElementsByTagName('loc') 

for url in urls:
    pg = Page()
    pg.analyze(getText(url.childNodes))
    pg.talk('warnings')


