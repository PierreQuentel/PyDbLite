#!/usr/bin/env python
import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

import pydblite

package_dir = {
    'test': 'tests'
    }

package_data = {
    'docs': ['Makefile', 'sources', 'themes']
    }


class PyTest(TestCommand):

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


class Tox(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import tox
        errcode = tox.cmdline(self.test_args)
        sys.exit(errcode)


description = 'PyDbLite, a fast, pure-Python in-memory database'

setup(name='PyDbLite',
      version=pydblite.__version__,
      description=description,
      long_description=description,
      author='Pierre Quentel',
      author_email='pierre.quentel@gmail.com',
      url='http://www.pydblite.net/',
      license="BSD",
      platforms=["Any"],
      packages=['pydblite', 'tests'],
      # package_dir=package_dir,
      # package_data=package_data,
      cmdclass={'test': PyTest},
      tests_require=['pytest'],
      # tests_require=['tox'],
      # cmdclass={'test': Tox},
      )
