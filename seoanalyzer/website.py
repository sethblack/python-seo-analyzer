from collections import Counter
from collections import defaultdict
from urllib.parse import urlsplit
from xml.dom import minidom

import socket

from seoanalyzer.http import http
from seoanalyzer.page import Page

class Website():
    def __init__(self, base_url, sitemap):
        self.base_url = base_url
        self.sitemap = sitemap
        self.crawled_pages = []
        self.crawled_urls = set([])
        self.page_queue = []
        self.wordcount = Counter()
        self.bigrams = Counter()
        self.trigrams = Counter()
        self.content_hashes = defaultdict(set)

    def check_dns(self, url_to_check):
        try:
            o = urlsplit(url_to_check)
            socket.gethostbyname(o.hostname)
            return True
        except:
            pass

        return False

    def get_text_from_xml(self, nodelist):
        """
        Stolen from the minidom documentation
        """
        rc = []

        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc.append(node.data)

        return ''.join(rc)

    def crawl(self):
        if self.sitemap:
            page = http.get(self.sitemap)
            xmldoc = minidom.parseString(page.data.decode('utf-8'))
            sitemap_urls = xmldoc.getElementsByTagName('loc')

            for url in sitemap_urls:
                self.page_queue.append(self.get_text_from_xml(url.childNodes))

        self.page_queue.append(self.base_url)

        for url in self.page_queue:
            if url in self.crawled_urls:
                continue

            page = Page(url=url, base_domain=self.base_url)

            if page.parsed_url.netloc != page.base_domain.netloc:
                continue

            page.analyze()

            self.content_hashes[page.content_hash].add(page.url)

            for w in page.wordcount:
                self.wordcount[w] += page.wordcount[w]

            for b in page.bigrams:
                self.bigrams[b] += page.bigrams[b]

            for t in page.trigrams:
                self.trigrams[t] += page.trigrams[t]

            self.page_queue.extend(page.links)

            self.crawled_pages.append(page)
            self.crawled_urls.add(page.url)
