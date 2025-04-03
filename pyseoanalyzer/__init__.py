#!/usr/bin/env python3

import sys

# Use importlib.metadata (available in Python 3.8+) to get the version
# defined in pyproject.toml. This avoids duplicating the version string.
if sys.version_info >= (3, 8):
    from importlib import metadata
else:
    # Fallback for Python < 3.8 (requires importlib-metadata backport)
    # Consider adding 'importlib-metadata; python_version < "3.8"' to dependencies
    # if you need to support older Python versions.
    import importlib_metadata as metadata

try:
    # __package__ refers to the package name ('pyseoanalyzer')
    __version__ = metadata.version(__package__)
except metadata.PackageNotFoundError:
    # Fallback if the package is not installed (e.g., when running from source)
    # You might want to handle this differently, e.g., raise an error
    # or read from a VERSION file. For now, setting it to unknown.
    __version__ = "0.0.0-unknown"


from .analyzer import analyze
