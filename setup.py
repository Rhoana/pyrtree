#!/usr/bin/env python

from distutils.core import setup

setup(
    name = "pyrtree",
    packages = ["pyrtree"],
    version = "0.50",
    description = "2-Dimensional RTree spatial index",
    author = "Dan Shoutis",
    author_email = "dan@shoutis.org",
    url="http://code.google.com/p/pyrtree",
    long_description = """\
Two-dimensional RTree spatial index.

This is a simple pure python implemenation of a 2D RTree. For the
moment, it is insert-only, and aimed at creating indexes to speed
queries over mostly-static datasets.
"""
)
