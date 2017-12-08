# -*- coding: utf-8 -*-

import os
import sys
import unittest

from pydblite.pydblite import Base

from .common_tests import Generic

test_db_name = 'test_database'


class PyDbLiteTestCase(Generic, unittest.TestCase):

    def setUp(self):  # NOQA
        self.first_record_id = 0
        filter_db = Base(test_db_name, save_to_file=False)
        filter_db.create('unique_id', 'name', "active", mode="override")
        self.filter_db = filter_db

    def tearDown(self):  # NOQA
        if os.path.isfile(test_db_name):
            os.remove(test_db_name)
        elif os.path.isdir(test_db_name):
            os.rmdir(test_db_name)

    def setup_db_for_filter(self):
        self.reset_status_values_for_filter()
        for d in self.status:
            res = self.filter_db.insert(**d)
        self.assertEqual(res, 6)

    def test_open(self):
        db = Base('dummy', save_to_file=False)
        db.create('name', 'age', 'size')
        db.insert(name='homer', age=23, size=1.84)

    def test_open_file_with_existing_dir(self):
        os.mkdir(test_db_name)
        db = Base(test_db_name, save_to_file=True)
        # A dir with that name exists
        self.assertRaises(IOError, db.create, 'unique_id', 'name', "active",
            mode="open")

    def test_open_wrong_mode(self):
        db = Base(test_db_name, save_to_file=True)
        self.assertRaises(ValueError, db.create, 'name', mode="fancy")

    def test_open_existing(self):
        db = Base(test_db_name, save_to_file=True)
        db.create('unique_id', 'name', "active", mode="open")
        db.insert("123", "N", True)
        db.commit()

        # Just verify that it works to open an existing db.
        # The column names are ignored, therefore they should
        # equal the old column names
        db = Base(test_db_name, save_to_file=True)
        db.create('unique_id2', 'name2', "active2", mode="open")
        rec = db.insert("123", "N", True)
        db.commit()
        self.assertEqual(db.fields, ['unique_id', 'name', "active"])

        # mode="override" will overwrite existing db
        db = Base(test_db_name, save_to_file=True)
        db.create('unique_id', 'name', "active", mode="override")
        db.commit()
        self.assertEqual(len(self.filter_db), 0)

        # Equals passing mode=None
        self.assertRaises(IOError, db.create, 'unique_id', 'name', "active")
        self.assertRaises(ValueError, db.create, 'unique_id', 'name', "active", mode="invalidmode")

    def test_open_memory(self):
        db = Base(":memory:")
        self.assertFalse(db.save_to_file)

    def test_open_memory_with_existing_filename(self):
        self.filter_db = Base(test_db_name, save_to_file=True)
        self.filter_db.create('unique_id', 'name', "active", mode="override")
        self.filter_db.commit()

        db = Base(test_db_name, save_to_file=False)
        db.open()
        self.assertEqual(db.fields, ['unique_id', 'name', "active"])

        db = Base(test_db_name, save_to_file=False)
        db.create('unique_id2', 'name2', "active2", mode="override")
        self.assertEqual(db.fields, ['unique_id2', 'name2', "active2"])

    def test_insert_list(self):
        status = (8, "testname", 0)

        # Insert 7 entries
        rec = self.filter_db.insert(status)
        self.assertEqual(rec, 0)
        self.assertEqual(self.filter_db[rec]["unique_id"], status)

    def test_sqlite_compat_insert_list(self):
        self.filter_db = Base(test_db_name, save_to_file=False, sqlite_compat=True)
        self.filter_db.create('unique_id', 'name', "active", mode="override")
        status = [(8, "testname", 0)]

        # Insert 1 entries
        rec = self.filter_db.insert(status)
        self.assertEqual(rec, None)
        self.assertEqual(len(self.filter_db), 1)
        self.assertEqual(self.filter_db[0]["unique_id"], 8)
        self.assertEqual(self.filter_db[0]["name"], "testname")
        self.assertEqual(self.filter_db[0]["active"], 0)

    def test_sqlite_compat(self):
        db = Base(test_db_name, save_to_file=False, sqlite_compat=True)
        db.create('unique_id', 'name', "active", mode="open")
        self.reset_status_values_for_filter()

        # Insert 7 entries
        res = db.insert(self.status)
        self.assertEqual(res, None)
        self.assertEqual(len(db), 7)

        status = [(8, "testname", 0)]
        res = db.insert(status)
        self.assertEqual(res, None)
        self.assertEqual(len(db), 8)


if __name__ == "__main__":
    sys.path.insert(0, os.getcwd())
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PyDbLiteTestCase))
    unittest.TextTestRunner().run(suite)
