#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

from setuptools import setup
from setuptools.command.register import register
from setuptools.command.test import test as command_test

import pydblite

package_data = {
    'tests': ["test_pydblite.py", "*.py"],
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

info = {}


def load_files(files):
    if type(files) is not list:
        files = list(files)
    for fn in files:
        try:
            with open("docs/%s.rst" % fn) as f:
                info[os.path.basename(fn)] = f.read()
        except IOError as err:  # NOQA
            print("Error when reading file '%s'" % fn)
            info[os.path.basename(fn)] = ""


class RegisterCommand(register):

    def run(self):
        if not os.path.isfile("docs/%s.rst" % pypi_description):
            print("ERROR: build/rst/pypi_description.rst is missing. "
                  "Regenerate with 'make -C docs pypi' before running register.")
            return
        register.run(self)


pypi_description = "build/rst/pypi_description"
files = ["source/description", "source/long_description"]
files.append(pypi_description)
load_files(files)

setup(name='PyDbLite',
      version=pydblite.__version__,
      description=info["description"],
      long_description=info["pypi_description"],
      author='Pierre Quentel, Bendik Rønning Opstad',
      author_email='pierre.quentel@gmail.com',
      url='http://www.pydblite.net/',
      license="BSD",
      platforms=["Platform-independent, runs with Python2.6+"],
      keywords="Python database engine SQLite",
      packages=['pydblite'],
      cmdclass={'test': PyTest, 'register': RegisterCommand},
      tests_require=['pytest'],
      # tests_require=['tox'],
      # cmdclass={'test': Tox},
      )
