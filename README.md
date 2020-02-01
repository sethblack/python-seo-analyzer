Python SEO Analyzer
===================

[![Googling Google by taleas.com](https://www.taleas.com/static/images/comics/NeverDoThis.png "Googling Google by taleas.com")](https://www.taleas.com/comics/googling-google.html)

An SEO tool that analyzes the structure of a site, crawls the site, counts words in the body of the site and warns of any technical SEO issues.

Requires Python 3.6+, BeautifulSoup4 and urllib3.

Installation
------------

### PIP

```
pip3 install pyseoanalyzer
```

Command-line Usage
------------------

If you run without a sitemap it will start crawling at the homepage.

```sh
seoanalyze http://www.domain.com/
```

Or you can specify the path to a sitmap to seed the urls to scan list.

```sh
seoanalyze http://www.domain.com/ --sitemap path/to/sitemap.xml
```

HTML output can be generated from the analysis instead of json.

```sh
seoanalyze http://www.domain.com/ --output-format html
```

API
---

The `analyze` function returns a dictionary with the results of the crawl.

```python
from seoanalyzer import analyze

output = analyze(site, sitemap)

print(output)
```

Alternatively, you can run the analysis as a script from the seoanalyzer folder.

```sh
python analyzer.py https://www.sethserver.com/ -f html > results.html
```

Notes
-----

If you get `requests.exceptions.SSLError` at either the command-line or via the python-API, try using:
 - http://www.foo.bar
 
 **instead** of..
 
 -  https://www.foo.bar
