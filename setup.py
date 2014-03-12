#!/usr/bin/env python
import os
#from distutils.core import setup
from setuptools import setup, find_packages

import sys

package_dir = {
    'PyDbLite.test':'PyDbLite/tests'
    }

package_data = {
    'doc':['*.html','*.css','img/*.jpg','fr/*.html','fr/*.css',
        'en/*.html','en/*.css','en/*.jpg']
    }

description = 'PyDbLite, a fast, pure-Python in-memory database'


setup(name='PyDbLite',
      version='2.6',
      description=description,
      long_description=description,
      author='Pierre Quentel',
      author_email='pierre.quentel@gmail.com',
      url='http://www.pydblite.net/',
      license="BSD",
      platforms=["Any"],
      packages=['PyDbLite','PyDbLite.tests'],
      package_dir=package_dir,
      package_data=package_data,
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python',
          'Topic :: Database :: Database Engines/Servers'
          ]
     )

