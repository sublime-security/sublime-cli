#!/usr/bin/env python
"""Sublime API client package."""
import os

from setuptools import find_packages, setup


def read(fname):
    """Read file and return its contents."""
    with open(os.path.join(os.path.dirname(__file__), fname)) as input_file:
        return input_file.read()


INSTALL_REQUIRES = [
    "Click>=7.0",
    "ansimarkup",
    "cachetools",
    "click-default-group",
    "click-repl",
    "dicttoxml",
    "jinja2",
    "more-itertools",
    "requests",
    "six",
    "structlog",
]

setup(
    name="sublime",
    version="0.3.0",
    description="Abstraction to interact with Sublime API.",
    url="https://sublimesecurity.com/",
    author="Sublime Security",
    author_email="hello@sublimesecurity.com",
    license="MIT",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={"sublime.cli": ["templates/*.j2"]},
    install_requires=INSTALL_REQUIRES,
    long_description=read("README.rst") + "\n\n" + read("CHANGELOG.rst"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Libraries",
    ],
    entry_points={"console_scripts": ["sublime = sublime.cli:main"]},
    zip_safe=False,
    keywords=["internet", "scanning", "threat intelligence", "security"],
    download_url="https://github.com/sublime-security/sublime-cli",
)
