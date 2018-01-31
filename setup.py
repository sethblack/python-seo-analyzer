#!/usr/bin/env python3

from setuptools import setup
from distutils.command.install import install as _install

setup(
    name = 'pyseoanalyzer',
    version = '3.1.0',
    description = 'An SEO tool that gives you general Search Engine Optimization directions.',
    author = 'Seth Black',
    author_email = 'sblack@sethserver.com',
    url = 'https://github.com/sethblack/python-seo-analyzer',
    packages = ['seoanalyzer'],
    keywords = ['search engine optimization', 'seo', 'website parser', 'crawler', 'scraper',],
    package_data={'seoanalyzer': ['templates/index.html']},
    include_package_data = True,
    install_requires = [
        'BeautifulSoup4', 'requests','jinja2',
    ],
    # no idea why this needed fixing, the diff says it didn't change...
    entry_points = {
        'console_scripts' : [
            'seoanalyze = seoanalyzer.__main__:main'
        ]
    },
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing",
        "Topic :: Internet :: WWW/HTTP",
    ],
    long_description = """\
SEOAnalyzer
-----------

An SEO tool that analyzes the structure of a site, crawls the site, count words in the body of the site and warns of any general SEO related issues.

This version requires Python 3.4 or later. C'mon everyone, get with the times, Python 3 is great!
"""
)
