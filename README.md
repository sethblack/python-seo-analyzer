Python SEO Analyzer
===========

An SEO tool that analyzes the structure of a site, crawls the site, counts words in the body of the site and warns of any general SEO related issues.

Requires Python 3.4+, BeautifulSoup4, flask, minidom, nltk, numpy and urllib2.

Installation
------------

### PIP

```
pip3 install pyseoanalyzer
```

Command-line Usage
------------------

If you run without a sitemap it will start crawling at the homepage.

```
#> seoanalyze http://www.domain.com/
```

Or you can specify the path to a sitmap to seed the urls to scan list.

```
#> seoanalyze http://www.domain.com/ --sitemap path/to/sitemap.xml
```

HTML output can be generated from the analysis instead of json.

```
#> seoanalyze http://www.domain.com/ --output-format html
```

API
---

The `analyze` function returns a dictionary with the results of the crawl.

```python
from seoanalyzer import analyze

output = analyze(site, sitemap)

print(output)
```
