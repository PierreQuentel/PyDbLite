__all__ = ["test_pydblite", "test_pydblite_sqlite", "test_pydblite_mysql"]

import os
dirname = os.path.dirname

from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)
basedir = dirname(dirname(dirname(__file__))) # To get PyDbLite as a module
__path__ = extend_path(__path__, basedir)

def load_tests(loader, tests, pattern):
    ''' Discover and load all unit tests in all files named ``*_test.py`` in ``./src/``
    '''
    import unittest
    suite = unittest.TestSuite()
    from unittest import loader
    import unittest.loader
    for all_test_suite in unittest.defaultTestLoader.discover(
            ".",
            pattern='test*.py'
    ):
        if "ModuleImportFailure" in str(all_test_suite):
            print("Found ModuleImportFailure:", all_test_suite)
            pass
        else:
            suite.addTests(all_test_suite)
    return suite

