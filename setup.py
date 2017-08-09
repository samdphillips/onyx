#!/usr/bin/env python

from setuptools import find_packages, setup

setup(name='Onyx',
      version='0.1',
      description='Onyx Programming Language',
      author='Sam Phillips',
      author_email='samdphillips@gmail.com',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      setup_requires=['pytest-runner'],
      tests_require=['pytest', 'pytest-cov']
)
