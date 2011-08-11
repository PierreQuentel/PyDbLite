# -*- coding: iso-8859-1 -*-

import datetime
import unittest
import random

import os
import sys
#sys.path.insert(0,os.path.dirname(os.getcwd()))
import PyDbLite

db = None
vals1 = [('simon',datetime.date(1984,8,17),26)]
vals2 = [('camille',datetime.date(1986,12,12),24),
    ('jean',datetime.date(1989,6,12),21),('florence',datetime.date(1994,1,14),17),
    ('marie-anne',datetime.date(1999,1,28),12)]
vals3 = [('éçùï',datetime.date(2000,10,10),55)]

class TestFunctions(unittest.TestCase):

    def test_00_init(self):
        global db
        db = PyDbLite.Base('test.pdl')
        db.create('name','birth','age',mode="override")

    def test_01_insert(self):
        for i,val in enumerate(vals1+vals2+vals3):
            assert db.insert(*val)==i
        assert len(db)==len(vals1+vals2+vals3)

    def test_10_select(self):
        for i,v in enumerate(vals1):
            rec = db[i]
            for j,field in enumerate(db.fields):
                assert rec[field]==v[j]

    def test_11_select(self):
        assert db(name='foo')==[]
        assert db(name='éçùï')[0]['birth']==datetime.date(2000,10,10)

    def test_12_iter(self):
        self.assertEqual(len([x for x in db]),len(db))
        for val in vals1+vals2+vals3:
            self.assertEqual([ x for x in db if x['name']==val ],db(name=val))
            self.assertEqual([ x for x in db if x['birth']==val ],db(birth=val))
            self.assertEqual([ x for x in db if x['age']==val ],db(age=val))

    def test_30_update(self):
        for record in db:
            db.update(record,name=record['name'].capitalize())
        self.assertEqual(db[0]['name'],"Simon")
        #self.assertEqual(db[5]['name'][0],"É")

    def test_40_delete(self):
        del db[0]
        self.assertEqual(db(name='Simon'),[])
        self.assertEqual(len(db),len(vals1+vals2+vals3)-1)

if __name__=="__main__":
    
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestFunctions))
    unittest.TextTestRunner().run(suite)
