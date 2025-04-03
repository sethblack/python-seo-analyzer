Python SEO and GEO Analyzer
===========================

[![PyPI version](https://badge.fury.io/py/pyseoanalyzer.svg)](https://badge.fury.io/py/pyseoanalyzer)
[![Docker Pulls](https://img.shields.io/docker/pulls/sethblack/python-seo-analyzer.svg)](https://hub.docker.com/r/sethblack/python-seo-analyzer)

A modern SEO and GEO (Generative AI Engine Optimization or better AI Search Optimization) analysis tool that combines technical optimization and authentic human value. Beyond traditional site crawling and structure analysis, it uses AI to evaluate content's expertise signals, conversational engagement, and cross-platform presence. It helps you maintain strong technical foundations while ensuring your site demonstrates genuine authority and value to real users.

The AI features were heavily influenced by the clickbait-titled SEL article [A 13-point roadmap for thriving in the age of AI search](https://searchengineland.com/seo-roadmap-ai-search-449199).

Note About Python
-----------------

I've written quite a bit about the speed of Python and how there are very specific use cases where it isn't the best choice. I feel like crawling websites is definitely one of those cases. I wrote this tool in Python around 2010 to solve the very specific need of crawling some small HTML-only websites for startups I was working at. I'm excited to see how much it has grown and how many people are using it. I feel like Python SEO Analyzer is acceptable for most smaller use cases, but if you are looking for something better, I've built a much faster and more comprehensive tool [Black SEO Analyzer](https://github.com/sethblack/black-seo-analyzer).

-Seth

Installation
------------

### PIP

```
pip install pyseoanalyzer
```

### Docker

#### Using the Pre-built Image from Docker Hub

The easiest way to use the Docker image is to pull it directly from [Docker Hub](https://hub.docker.com/r/sethblack/python-seo-analyzer).

```bash
# Pull the latest image
docker pull sethblack/python-seo-analyzer:latest

# Run the analyzer (replace example.com with the target URL)
# The --rm flag automatically removes the container when it exits
docker run --rm sethblack/python-seo-analyzer http://example.com/

# Run with specific arguments (e.g., sitemap and HTML output)
# Note: If the sitemap is local, you'll need to mount it (see mounting example below)
docker run --rm sethblack/python-seo-analyzer http://example.com/ --sitemap /path/inside/container/sitemap.xml --output-format html

# Run with AI analysis (requires ANTHROPIC_API_KEY)
# Replace "your_api_key_here" with your actual Anthropic API key
docker run --rm -e ANTHROPIC_API_KEY="your_api_key_here" sethblack/python-seo-analyzer http://example.com/ --run-llm-analysis

# Save HTML output to your local machine
# This mounts the current directory (.) into /app/output inside the container.
# The output file 'results.html' will be saved in your current directory.
# The tool outputs JSON by default to stdout, so we redirect it for HTML.
# Since the ENTRYPOINT handles the command, we redirect the container's stdout.
# We need a shell inside the container to handle the redirection.
docker run --rm -v "$(pwd):/app/output" sethblack/python-seo-analyzer /bin/sh -c "seoanalyze http://example.com/ --output-format html > /app/output/results.html"
# Note for Windows CMD users: Use %cd% instead of $(pwd)
# docker run --rm -v "%cd%:/app/output" sethblack/python-seo-analyzer /bin/sh -c "seoanalyze http://example.com/ --output-format html > /app/output/results.html"
# Note for Windows PowerShell users: Use ${pwd} instead of $(pwd)
# docker run --rm -v "${pwd}:/app/output" sethblack/python-seo-analyzer /bin/sh -c "seoanalyze http://example.com/ --output-format html > /app/output/results.html"


# Mount a local sitemap file
# This mounts 'local-sitemap.xml' from the current directory to '/app/sitemap.xml' inside the container
docker run --rm -v "$(pwd)/local-sitemap.xml:/app/sitemap.xml" sethblack/python-seo-analyzer http://example.com/ --sitemap /app/sitemap.xml
# Adjust paths and Windows commands as needed (see volume mounting example above)

```

#### Building the Image Locally

You can also build the Docker image yourself from the source code. Make sure you have Docker installed and running.

```bash
# Clone the repository (if you haven't already)
# git clone https://github.com/sethblack/python-seo-analyzer.git
# cd python-seo-analyzer

# Build the Docker image (tag it as 'my-seo-analyzer' for easy reference)
docker build -t my-seo-analyzer .

# Run the locally built image
docker run --rm my-seo-analyzer http://example.com/

# Run with AI analysis using the locally built image
docker run --rm -e ANTHROPIC_API_KEY="your_api_key_here" my-seo-analyzer http://example.com/ --run-llm-analysis

# Run with HTML output saved locally using the built image
docker run --rm -v "$(pwd):/app/output" my-seo-analyzer /bin/sh -c "seoanalyze http://example.com/ --output-format html > /app/output/results.html"
# Adjust Windows commands as needed (see volume mounting example above)
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
