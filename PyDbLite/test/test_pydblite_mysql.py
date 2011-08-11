# -*- coding: iso-8859-1 -*-

import datetime
import unittest
import random

import os
import sys
sys.path.insert(0,os.path.dirname(os.getcwd()))
import MySQL
print MySQL.__file__

try:
    host,user,password = open('mysql.txt').read().strip().split(',')
except IOError:
    print "Store host,user,password in mysql.txt"

class TestOperators(unittest.TestCase):

    def testIterateOnConnection(self):
        for i,db in enumerate(conn): pass
        assert len(conn.keys())==i+1

    def testIteritemsOnConnection(self):
        for db_name,db in conn.iteritems(): 
            assert isinstance(db_name,unicode)
            assert isinstance(db,MySQL.Database)
            assert db == conn[db_name]

    def testTableList(self):
        for _db in conn:
            for table in conn[_db]:
                pass

class TestMySQLFunctions(unittest.TestCase):
    
    def test_01_insert_one(self):
        for i,val in enumerate(vals1):
            assert t1.insert(*val)==i+1

    def test_02_insert_many(self):
        t1.insert(vals2)
        assert len(t1) == 5

    def test_03_insert_unicode(self):
        t1.insert(vals3)

    def test_10_select(self):
        for i,v in enumerate(vals1+vals2+vals3):
            rec = db['table1'][i+1]
            for j,field in enumerate(db['table1'].fields[1:]):
                assert rec[field]==v[j]

if __name__=="__main__":
    conn = MySQL.Connection(host,user,password,charset="utf8")
        
    db_name = ''.join([ random.choice('abcdefghij') for i in range(10)])
    db = conn.create(db_name)
    assert db_name in conn

    t1 = db['table1'].create(('rowid','INTEGER PRIMARY KEY AUTO_INCREMENT'),
        ('name','TEXT'),('birth','DATE'),('age','INTEGER'),mode="override")
    vals1 = [('simon',datetime.date(1984,8,17),26)]
    vals2 = [('camille',datetime.date(1986,12,12),24),
        ('jean',datetime.date(1989,6,12),21),('florence',datetime.date(1994,1,14),17),
        ('marie-anne',datetime.date(1999,1,28),12)]
    vals3 = [(unicode('éçùï','iso-8859-1'),datetime.date(2000,10,10),55)]
    
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestOperators))
    suite.addTest(unittest.makeSuite(TestMySQLFunctions))
    unittest.TextTestRunner().run(suite)

    print 'test finished'
    del db['table1']
    del conn[db_name]
    assert db_name not in conn

