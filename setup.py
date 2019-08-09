#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='core-humanresources',
    version='0.0',
    description='',
    author='Ricardo Ribeiro',
    author_email='ricardojvr@gmail.com',
    packages=find_packages(),
    install_requires=[
        'django-localflavor',
        'weasyprint',
        'django-weasyprint',
        'django-model-utils',
        'django-money',
        'core-common',
        'core-finances',
        'core-people',
        'core-permissions',
    ]
)
