__all__ = ["test_pydblite", "test_pydblite_sqlite"]


def load_tests(loader, tests, pattern):
    ''' Discover and load all unit tests in all files named ``*_test.py`` in ``./src/``
    '''
    import unittest
    suite = unittest.TestSuite()
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
