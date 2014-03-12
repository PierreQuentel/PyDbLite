#!/usr/bin/env python
import warnings
import unittest

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.resetwarnings()

if __name__=="__main__":
    from PyDbLite.tests.test_pydblite import PyDbLiteTestCase
    from PyDbLite.tests.test_pydblite_sqlite import SQLiteTestCase, TestSQLiteFunctions

    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PyDbLiteTestCase))
    suite.addTest(unittest.makeSuite(SQLiteTestCase))
    suite.addTest(unittest.makeSuite(TestSQLiteFunctions))
    unittest.TextTestRunner().run(suite)
