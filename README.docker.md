# Docker Usage for Python SEO Analyzer

This document provides instructions on how to build and run the `python-seo-analyzer` tool using Docker.

## Overview

The Docker image provides a self-contained environment to run the `python-seo-analyzer` command-line tool without needing to install Python or dependencies directly on your host system.

The image is based on `python:3.13.2-bookworm` and includes all necessary dependencies specified in `requirements.txt`.

## Building the Image (Optional)

While pre-built images might be available (e.g., via GitHub Packages), you can build the image locally using the provided `Dockerfile`:

```bash
docker build -t python-seo-analyzer .
```

## Running the Container

The container is configured to run the `python-seo-analyzer` command directly. You pass the command-line arguments for the tool after the image name. The official image is available at `sethblack/python-seo-analyzer:latest`.

**Default Command (Show Version):**

If you run the container without any arguments, it executes the default command (`--version`):

```bash
docker run --rm sethblack/python-seo-analyzer:latest
```
*(Note: The examples below use `sethblack/python-seo-analyzer:latest`. If you built the image locally with a different tag, replace the image name accordingly.)*

**Analyzing a Website:**

To analyze a website, provide the site URL as the main argument:

```bash
# Analyze a site and output JSON (default)
docker run --rm sethblack/python-seo-analyzer:latest https://example.com

# Analyze a site and output HTML
docker run --rm sethblack/python-seo-analyzer:latest https://example.com -f html > analysis_report.html

# Analyze a site using a sitemap
docker run --rm sethblack/python-seo-analyzer:latest https://example.com -s https://example.com/sitemap.xml

# Analyze with heading analysis enabled
docker run --rm sethblack/python-seo-analyzer:latest https://example.com --analyze-headings

# Analyze without following internal links
docker run --rm sethblack/python-seo-analyzer:latest https://example.com --no-follow-links

# Analyze with LLM analysis (requires appropriate environment variables for the LLM provider, e.g., ANTHROPIC_API_KEY)
# You'll need to pass environment variables using the -e flag
docker run --rm -e ANTHROPIC_API_KEY=your_api_key sethblack/python-seo-analyzer:latest https://example.com --run-llm-analysis
```

## Command-Line Arguments

The `python-seo-analyzer` tool accepts the following arguments when run via Docker:

*   `site`: (Required) The URL of the website you want to analyze.
*   `-s`, `--sitemap`: URL of the sitemap to seed the crawler with.
*   `-f`, `--output-format`: Output format. Choices: `json` (default), `html`.
*   `--analyze-headings`: Enable analysis of heading tags (h1-h6). Default: `False`.
*   `--analyze-extra-tags`: Enable analysis of other additional tags. Default: `False`.
*   `--no-follow-links`: Disable following internal links during the crawl. By default, the crawler *does* follow internal links. Use this flag to prevent that behavior.
*   `--run-llm-analysis`: Run Large Language Model (LLM) analysis on the content. Requires API keys to be configured via environment variables (e.g., `ANTHROPIC_API_KEY`). Default: `False`.
*   `--version`: Display the tool's version and exit. (This is the default command if no other arguments are provided).

## Examples

**Analyze `sethserver.com` and save the output as HTML:**

```bash
docker run --rm sethblack/python-seo-analyzer:latest https://sethserver.com -f html > sethserver_report.html
```

**Analyze `github.com` using its sitemap and output JSON:**

```bash
docker run --rm sethblack/python-seo-analyzer:latest https://github.com -s https://github.com/sitemap.xml
```

**Analyze `example.com` with heading analysis but without following internal links:**

```bash
docker run --rm sethblack/python-seo-analyzer:latest https://example.com --analyze-headings --no-follow-links
