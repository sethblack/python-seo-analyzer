Python SEO and GEO Analyzer
===================

A modern SEO and GEO analysis tool that combines technical optimization and authentic human value. Beyond traditional site crawling and structure analysis, it uses AI to evaluate content's expertise signals, conversational engagement, and cross-platform presence. It helps you maintain strong technical foundations while ensuring your site demonstrates genuine authority and value to real users.

The AI features were heavily influenced by the clickbait-titled SEL article [A 13-point roadmap for thriving in the age of AI search](https://searchengineland.com/seo-roadmap-ai-search-449199).

Installation
------------

### PIP

```
pip install pyseoanalyzer
```

### Docker

The docker image is available on [Docker Hub](https://hub.docker.com/r/sethblack/python-seo-analyzer) and can be run with the same command-line arguments as the script.

```
docker run sethblack/python-seo-analyzer [ARGS ...]
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
from pyseoanalyzer import analyze

output = analyze(site, sitemap)

print(output)
```

In order to analyze heading tags (h1-h6) and other extra additional tags as well, the following options can be passed to the `analyze` function
```python
from pyseoanalyzer import analyze

output = analyze(site, sitemap, analyze_headings=True, analyze_extra_tags=True)

print(output)
```

By default, the `analyze` function analyzes all the existing inner links as well, which might be time consuming.
This default behaviour can be changed to analyze only the provided URL by passing the following option to the `analyze` function
```python
from pyseoanalyzer import analyze

output = analyze(site, sitemap, follow_links=False)

print(output)
```

Alternatively, you can run the analysis as a script from the seoanalyzer folder.

```sh
python -m seoanalyzer https://www.sethserver.com/ -f html > results.html
```

AI Optimization
---------------

The first pass of AI optimization features use Anthropic's `claude-3-sonnet-20240229` model to evaluate the content of the site. You will need to have an API key from [Anthropic](https://www.anthropic.com/) to use this feature. The API key needs to be set as the environment variable `ANTHROPIC_API_KEY`. I recommend using a `.env` file to set this variable. Once the API key is set, the AI optimization features can be enabled with the `--run-llm-analysis` flag.

Notes
-----

If you get `requests.exceptions.SSLError` at either the command-line or via the python-API, try using:
 - http://www.foo.bar
 
 **instead** of..
 
 -  https://www.foo.bar
