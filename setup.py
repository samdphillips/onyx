#!/usr/bin/env python

from glob import glob
from setuptools import find_packages, setup

setup(name='Onyx',
      version='0.1',
      description='Onyx Programming Language',
      author='Sam Phillips',
      author_email='samdphillips@gmail.com',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      data_files=[('onyx/ost/boot', glob('src/ost/boot/*.ost'))],
      zip_safe=False
)
