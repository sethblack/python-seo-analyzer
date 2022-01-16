#!/usr/bin/env python3

from os import path
from setuptools import setup, find_packages

this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pyseoanalyzer',
    version='4.0.6',
    description='An SEO tool that analyzes the structure of a site, crawls the site, count words in the body of the site and warns of any technical SEO issues.',
    author='Seth Black',
    author_email='sblack@sethserver.com',
    url='https://github.com/sethblack/python-seo-analyzer',
    packages=find_packages(),
    keywords=['search engine optimization', 'seo', 'website parser', 'crawler', 'scraper',],
    package_data={'seoanalyzer': ['templates/index.html',]},
    include_package_data=True,
    install_requires=[
        'BeautifulSoup4', 'lxml', 'requests', 'jinja2', 'urllib3', 'certifi',
    ],
    entry_points={
        'console_scripts' : [
            'seoanalyze = seoanalyzer.__main__:main'
        ]
    },
    classifiers=[
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
    zip_safe=False,
    long_description=long_description,
    long_description_content_type='text/markdown'
)
