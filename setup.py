#!/usr/bin/env python
# coding: utf-8

"""setuptools based setup module for ccad

View model.py for a full description of ccad.

"""

from setuptools import setup
# To use a consistent encoding
import codecs
from os import path

import ccad
import numpy

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with codecs.open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name=ccad.__name__,
    version=ccad.__version__,
    description=ccad.__description__,
    long_description=long_description,
    url=ccad.__url__,
    download_url=ccad.__download_url__,
    author=ccad.__author__,
    author_email=ccad.__author_email__,
    license=ccad.__license__,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6'],
    keywords='OpenCASCADE pythonocc CAD',
    packages=['ccad'],
    install_requires=[],
    include_dirs=[numpy.get_include()],
    extras_require={
        'dev': [],
        'test': ['pytest', 'coverage'],
    },
    package_data={},
    data_files=[],
    entry_points={})
