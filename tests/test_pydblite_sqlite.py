# -*- coding: utf-8 -*-

import datetime
import os
import sys
import unittest

from pydblite import sqlite

from .common_tests import Generic

if sys.version_info[0] == 3:
    def unicode(s, en):
        return s


vals1 = [('simon', datetime.date(1984, 8, 17), 26)]
vals2 = [('camille', datetime.date(1986, 12, 12), 24),
         ('jean', datetime.date(1989, 6, 12), 21),
         ('florence', datetime.date(1994, 1, 14), 17),
         ('marie-anne', datetime.date(1999, 1, 28), 12)]

rec3 = {'name': unicode('éçùï', 'iso-8859-1'), 'age': 55}


class TestSQLiteFunctions(unittest.TestCase):

    def setUp(self):  # NOQA
        self.db = sqlite.Database(":memory:")
        self.db.create('table1',
                       ('name', 'TEXT'),
                       ('birth', 'DATE DEFAULT CURRENT_DATE'),
                       ('age', 'INT'),
                       mode="override")

    def insert_test_data(self):
        t1 = self.db['table1']
        t1.insert(vals1)

    def test_00_create(self):
        db = sqlite.Database(":memory:")
        t1 = db.create('table1',
                       ('name', 'TEXT'),
                       ('birth', 'DATE DEFAULT CURRENT_DATE'),
                       ('age', 'INT'),
                       mode="override")

        t1.is_date('birth')

    def test_02_iterate_on_database(self):
        for i, table in enumerate(self.db):
            pass
        assert len(self.db.keys()) == i + 1

    def test_10_insert_one(self):
        t1 = self.db['table1']
        for i, val in enumerate(vals1):
            assert t1.insert(*val) == i + 1
            self.db.commit()

    def test_11_insert_many(self):
        self.insert_test_data()
        t1 = self.db['table1']
        self.assertEqual(len(t1), 1)
        t1.insert(vals2)
        self.assertEqual(len(t1), 5)
        self.db.commit()

    def test_12_insert_kw_unicode_missing(self):
        t1 = self.db['table1']
        t1.insert(**rec3)
        self.db.commit()

    def test_20_select(self):
        table = self.db['table1']
        self.insert_test_data()
        table.insert(vals2)
        table.is_date('birth')
        for i, v in enumerate(vals1 + vals2):
            rec = table[i + 1]
            for j, field in enumerate(table.fields):
                self.assertEqual(rec[field], v[j])

    def test_40_delete(self):
        table = self.db['table1']
        table.insert(vals2)
        del table[1]
        self.assertRaises(IndexError, table.__getitem__, 1)


class SQLiteTestCase(Generic, unittest.TestCase):

    def setUp(self):  # NOQA
        self.first_record_id = 1
        from pydblite.sqlite import Table, Database
        db = Database(":memory:")
        filter_db = Table('test_database', db)
        filter_db.create(('unique_id', 'INTEGER'), ('name', 'TEXT'), ('active', 'INTEGER'))
        self.filter_db = filter_db

    def tearDown(self):  # NOQA
        pass


if __name__ == "__main__":
    sys.path.insert(0, os.getcwd())
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSQLiteFunctions))
    suite.addTest(unittest.makeSuite(SQLiteTestCase))
    unittest.TextTestRunner().run(suite)
