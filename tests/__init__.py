__all__ = ["test_pydblite", "test_pydblite_sqlite"]

import unittest

from .test_pydblite import PyDbLiteTestCase
from .test_pydblite_sqlite import TestSQLiteFunctions, SQLiteTestCase

suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(PyDbLiteTestCase))
suite.addTest(unittest.makeSuite(TestSQLiteFunctions))
suite.addTest(unittest.makeSuite(SQLiteTestCase))

unittest.TextTestRunner().run(suite)