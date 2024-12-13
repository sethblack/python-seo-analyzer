from collections import Counter, defaultdict
from urllib.parse import urlsplit
from xml.dom import minidom
import socket

from .http import http
from .page import Page


class Website:
    def __init__(
        self, base_url, sitemap, analyze_headings, analyze_extra_tags, follow_links
    ):
        self.base_url = base_url
        self.sitemap = sitemap
        self.analyze_headings = analyze_headings
        self.analyze_extra_tags = analyze_extra_tags
        self.follow_links = follow_links
        self.crawled_pages = []
        self.crawled_urls = set()
        self.page_queue = []
        self.wordcount = Counter()
        self.bigrams = Counter()
        self.trigrams = Counter()
        self.content_hashes = defaultdict(set)

    def check_dns(self, url_to_check):
        try:
            o = urlsplit(url_to_check)
            socket.gethostbyname_ex(o.hostname)
            return True
        except (socket.herror, socket.gaierror):
            return False

    def get_text_from_xml(self, nodelist):
        """
        Stolen from the minidom documentation
        """
        return "".join(node.data for node in nodelist if node.nodeType == node.TEXT_NODE)

    def crawl(self):
        try:
            if self.sitemap:
                page = http.get(self.sitemap)
                if self.sitemap.endswith("xml"):
                    xmldoc = minidom.parseString(page.data.decode("utf-8"))
                    sitemap_urls = xmldoc.getElementsByTagName("loc")
                    for url in sitemap_urls:
                        self.page_queue.append(self.get_text_from_xml(url.childNodes))
                elif self.sitemap.endswith("txt"):
                    sitemap_urls = page.data.decode("utf-8").split("\n")
                    for url in sitemap_urls:
                        self.page_queue.append(url)

            self.page_queue.append(self.base_url)

            for url in self.page_queue:
                if url in self.crawled_urls:
                    continue

                page = Page(
                    url=url,
                    base_domain=self.base_url,
                    analyze_headings=self.analyze_headings,
                    analyze_extra_tags=self.analyze_extra_tags,
                )

                if page.parsed_url.netloc != page.base_domain.netloc:
                    continue

                page.analyze()

                self.content_hashes[page.content_hash].add(page.url)
                self.wordcount.update(page.wordcount)
                self.bigrams.update(page.bigrams)
                self.trigrams.update(page.trigrams)

                self.page_queue.extend(page.links)

                self.crawled_pages.append(page)
                self.crawled_urls.add(page.url)

                if not self.follow_links:
                    break
        except Exception as e:
            print(f"Error occurred during crawling: {e}")
