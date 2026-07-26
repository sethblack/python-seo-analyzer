from collections import Counter, defaultdict
from urllib.parse import urlsplit
from xml.dom import minidom
import socket

from .http import http
from .page import Page


# User-agent tokens for AI crawlers/agents that read a site's robots.txt to
# decide whether they may fetch it. Not exhaustive, but covers the major
# training and retrieval crawlers as of 2026.
AI_CRAWLER_USER_AGENTS = [
    "GPTBot",
    "ChatGPT-User",
    "OAI-SearchBot",
    "ClaudeBot",
    "Claude-User",
    "anthropic-ai",
    "PerplexityBot",
    "Google-Extended",
]


class Website:
    def __init__(
        self,
        base_url,
        sitemap,
        analyze_headings=True,
        analyze_extra_tags=False,
        follow_links=False,
        run_llm_analysis=False,
        max_pages=None,
    ):
        self.base_url = base_url
        self.sitemap = sitemap
        self.analyze_headings = analyze_headings
        self.analyze_extra_tags = analyze_extra_tags
        self.follow_links = follow_links
        self.run_llm_analysis = run_llm_analysis
        self.max_pages = max_pages
        self.crawled_pages = []
        self.crawled_urls = set()
        self.page_queue = []
        self.wordcount = Counter()
        self.bigrams = Counter()
        self.trigrams = Counter()
        self.content_hashes = defaultdict(set)
        self.ai_crawler_access = {
            "llms_txt": False,
            "robots_txt_found": False,
            "blocked_ai_bots": [],
        }

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
        return "".join(
            node.data for node in nodelist if node.nodeType == node.TEXT_NODE
        )

    def check_ai_crawler_access(self):
        """
        Checks whether the site publishes an llms.txt file and whether its
        robots.txt explicitly disallows any of the well-known AI crawler
        user-agents (GPTBot, ClaudeBot, PerplexityBot, Google-Extended, etc).

        Returns a dict:
            {
                "llms_txt": bool,
                "robots_txt_found": bool,
                "blocked_ai_bots": [str, ...],
            }
        """
        result = {
            "llms_txt": False,
            "robots_txt_found": False,
            "blocked_ai_bots": [],
        }

        base = self.base_url.rstrip("/")

        try:
            llms_response = http.get(f"{base}/llms.txt")
            result["llms_txt"] = llms_response.status == 200
        except Exception:
            pass

        try:
            robots_response = http.get(f"{base}/robots.txt")
            if robots_response.status == 200:
                result["robots_txt_found"] = True
                robots_txt = robots_response.data.decode("utf-8", errors="ignore")

                current_agents = []
                for line in robots_txt.splitlines():
                    line = line.split("#", 1)[0].strip()
                    if not line or ":" not in line:
                        continue

                    field, _, value = line.partition(":")
                    field = field.strip().lower()
                    value = value.strip()

                    if field == "user-agent":
                        current_agents = [value]
                    elif field == "disallow" and value == "/" and current_agents:
                        for agent in current_agents:
                            for bot in AI_CRAWLER_USER_AGENTS:
                                if (
                                    agent.lower() == bot.lower()
                                    and bot not in result["blocked_ai_bots"]
                                ):
                                    result["blocked_ai_bots"].append(bot)
        except Exception:
            pass

        return result

    def crawl(self):
        self.ai_crawler_access = self.check_ai_crawler_access()

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
                    run_llm_analysis=self.run_llm_analysis,
                )

                if page.parsed_url.netloc != page.base_domain.netloc:
                    continue

                # Analyze the page and check if successful
                analysis_successful = page.analyze()

                # Only process and add the page if analysis completed
                if analysis_successful:
                    self.content_hashes[page.content_hash].add(page.url)
                    self.wordcount.update(page.wordcount)
                    self.bigrams.update(page.bigrams)
                    self.trigrams.update(page.trigrams)

                    # Only add links if following is enabled and analysis was successful
                    if self.follow_links:
                        self.page_queue.extend(page.links)

                    self.crawled_pages.append(page)
                    self.crawled_urls.add(page.url)

                    # Stop if we've reached the maximum number of pages
                    if self.max_pages is not None and len(self.crawled_pages) >= self.max_pages:
                        break

                # Stop after the first page if not following links, regardless of analysis success
                if not self.follow_links:
                    break
        except Exception as e:
            print(f"Error occurred during crawling: {e}")
