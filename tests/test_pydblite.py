# -*- coding: utf-8 -*-

import os
import sys
import unittest

from .common_tests import Generic


class PyDbLiteTestCase(Generic, unittest.TestCase):

    def setUp(self):  # NOQA
        from pydblite.pydblite import Base
        self.first_record_id = 0
        filter_db = Base('test_database', save_to_file=False)
        filter_db.create('unique_id', 'name', "active", mode="override")
        self.filter_db = filter_db

    def tearDown(self):  # NOQA
        pass


if __name__ == "__main__":
    sys.path.insert(0, os.getcwd())
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PyDbLiteTestCase))
    unittest.TextTestRunner().run(suite)
