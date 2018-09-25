#!/usr/bin/env python

from os.path import exists
from setuptools import setup

packages = ['zstreamz', 'zstreamz.dataframe']

tests = [p + '.tests' for p in packages]


setup(name='zstreamz',
      version='0.4.0',
      description='Streams',
      url='http://github.com/mrocklin/zstreamz/',
      maintainer='CJ Wright',
      maintainer_email='cjwright4242@gmail.com',
      license='BSD',
      keywords='streams',
      packages=packages + tests,
      long_description=(open('README.rst').read() if exists('README.rst')
                        else ''),
      install_requires=list(open('requirements.txt').read().strip().split('\n')),
      zip_safe=False)
