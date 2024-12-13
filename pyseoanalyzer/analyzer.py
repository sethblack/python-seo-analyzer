import time
from operator import itemgetter
from .website import Website


def calc_total_time(start_time):
    return time.time() - start_time


def analyze(
    url,
    sitemap_url=None,
    analyze_headings=False,
    analyze_extra_tags=False,
    follow_links=True,
):
    start_time = time.time()

    output = {
        "pages": [],
        "keywords": [],
        "errors": [],
        "total_time": 0,  # Initialize to 0 before calculation
    }

    site = Website(
        url,
        sitemap_url,
        analyze_headings,
        analyze_extra_tags,
        follow_links,
    )

    site.crawl()

    for p in site.crawled_pages:
        output["pages"].append(p.as_dict())

    output["duplicate_pages"] = [
        list(site.content_hashes[p])
        for p in site.content_hashes
        if len(site.content_hashes[p]) > 1
    ]

    sorted_words = sorted(site.wordcount.items(), key=itemgetter(1), reverse=True)
    sorted_bigrams = sorted(site.bigrams.items(), key=itemgetter(1), reverse=True)
    sorted_trigrams = sorted(site.trigrams.items(), key=itemgetter(1), reverse=True)

    output["keywords"] = []

    for w in sorted_words:
        if w[1] > 4:
            output["keywords"].append(
                {
                    "word": w[0],
                    "count": w[1],
                }
            )

    for w, v in sorted_bigrams:
        if v > 4:
            output["keywords"].append(
                {
                    "word": w,
                    "count": v,
                }
            )

    for w, v in sorted_trigrams:
        if v > 4:
            output["keywords"].append(
                {
                    "word": w,
                    "count": v,
                }
            )

    # Sort one last time...
    output["keywords"] = sorted(
        output["keywords"], key=itemgetter("count"), reverse=True
    )

    output["total_time"] = calc_total_time(start_time)

    return output
