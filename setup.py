#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md', 'r') as fd:
    long_description = fd.read()

setup(
    name='core-humanresources',
    version='0.0',
    description='Research CORE ERM - human resources module',
    author='Ricardo Ribeiro, Hugo Cachitas',
    author_email='ricardojvr@gmail.com, hugo.cachitas@research.fchampalimaud.org',
    url='https://github.com/research-core/core-humanresources',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    license='CC BY-NC 2.0',
    install_requires=[
        'django-localflavor',
        'weasyprint',
        'django-weasyprint',
        'django-model-utils',
        'django-money',
        'core-common',
        'core-people',
        'core-finance',
        'core-permissions',
    ]
)
