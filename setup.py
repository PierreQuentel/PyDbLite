#!/usr/bin/env python
import sys

from setuptools import setup
from setuptools.command.test import test as command_test

import pydblite

package_dir = {
    'test': 'tests'
}

package_data = {
    'docs': ['Makefile', 'sources', 'themes']
}


class PyTest(command_test):

    def initialize_options(self):
        command_test.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        command_test.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


class Tox(command_test):

    def finalize_options(self):
        command_test.finalize_options(self)
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
