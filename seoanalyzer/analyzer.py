import json

from seoanalyzer.website import Website

def analyze(url, sitemap_url=None):
    site = Website(url, sitemap_url)

    site.crawl()

    print('[', flush=True)

    for p in site.crawled_pages:
        print(json.dumps(p.talk()), flush=True)
        print(',', flush=True)

    print(']', flush=True)
