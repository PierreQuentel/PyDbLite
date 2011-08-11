# -*- coding: iso-8859-1 -*-

import datetime
import unittest
import random

import os
import sys
sys.path.insert(0,os.path.dirname(os.getcwd()))
import SQLite
print SQLite.__file__
if os.path.exists("test.sqlite"):
    os.remove("test.sqlite")

class TestSQLiteFunctions(unittest.TestCase):

    def setUp(self):    
        self.db = SQLite.Database("test.sqlite")

    def test_00_create(self):
        t1 = self.db.create('table1',
            ('name','TEXT'),('birth','DATE DEFAULT CURRENT_DATE'),mode="override")
        t1.is_date('birth')

    def test_01_add_field(self):
        t1 = self.db['table1']
        t1.add_field(('age','INTEGER'))

    def test_02_IterateOnDatabase(self):
        for i,table in enumerate(self.db): pass
        assert len(self.db.keys())==i+1

    def test_10_insert_one(self):
        t1 = self.db['table1']
        for i,val in enumerate(vals1):
            assert t1.insert(*val)==i+1
            self.db.commit()

    def test_11_insert_many(self):
        t1 = self.db['table1']
        t1.insert(vals2)
        self.db.commit()
        assert len(t1) == 5

    def test_12_insert_kw_unicode_missing(self):
        t1 = self.db['table1']
        t1.insert(**rec3)
        self.db.commit()

    def test_20_select(self):
        table = self.db['table1']
        table.is_date('birth')
        for i,v in enumerate(vals1+vals2):
            rec = table[i+1]
            for j,field in enumerate(table.fields):
                self.assertEqual(rec[field],v[j])

    def test_30_update(self):
        table = self.db['table1']
        table.is_date('birth')
        vals = vals1+vals2
        for rec in table:
            if rec['__id__']==len(table):
                assert rec['birth']==datetime.date.today()
                continue
            table.update(rec,name=rec['name'].capitalize())
            self.assertEqual(table[rec['__id__']]['name'],
                vals[rec['__id__']-1][0].capitalize())
            self.db.commit()

    def test_40_delete(self):
        table = self.db['table1']
        del table[1]
        self.assertRaises(IndexError,table.__getitem__,1)

if __name__=="__main__":
    vals1 = [('simon',datetime.date(1984,8,17),26)]
    vals2 = [('camille',datetime.date(1986,12,12),24),
        ('jean',datetime.date(1989,6,12),21),('florence',datetime.date(1994,1,14),17),
        ('marie-anne',datetime.date(1999,1,28),12)]
    rec3 = {'name':unicode('éçùï','iso-8859-1'),'age':55}
    
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSQLiteFunctions))
    unittest.TextTestRunner().run(suite)

