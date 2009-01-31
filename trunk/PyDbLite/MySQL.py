"""PyDbLite.py adapted for MySQL backend

Differences with PyDbLite:
- pass the connection to the MySQL db as argument to Base()
- in create(), field definitions must specify a type
- no index
- the Base() instance has a cursor attribute, so that SQL requests
  can be executed :
    db.cursor.execute(an_sql_request)
    result = db.cursor.fetchall()

Fields must be declared 
Syntax :
    from PyDbLite.MySQL import Base
    import MySQLdb
    # connect to a MySQL server and use database "test"
    connection = MySQLdb.connect("localhost","root","admin")
    connection.cursor().execute("USE test")
    # pass the connection as argument to Base creation
    db = Base('dummy',connection)
    # create new base with field names
    db.create(('name','INTEGER'),('age',"INTEGER'),('size','REAL'))
    # existing base
    db.open()
    # insert new record
    db.insert(name='homer',age=23,size=1.84)
    # records are dictionaries with a unique integer key __id__
    # selection by list comprehension
    res = [ r for r in db if 30 > r['age'] >= 18 and r['size'] < 2 ]
    # or generator expression
    for r in (r for r in db if r['name'] in ('homer','marge') ):
    # simple selection (equality test)
    res = db(age=30)
    # delete a record or a list of records
    db.delete(one_record)
    db.delete(list_of_records)
    # delete a record by its id
    del db[rec_id]
    # direct access by id
    record = db[rec_id] # the record such that record['__id__'] == rec_id
    # update
    db.update(record,age=24)
    # add and drop fields
    db.add_field('new_field')
    db.drop_field('name')
    # save changes on disk
    db.commit()
"""

import os
import cPickle
import bisect

import MySQLdb

# compatibility with Python 2.3
try:
    set([])
except NameError:
    from sets import Set as set
    
class Base:

    def __init__(self,basename,connection):
        """basename = name of the PyDbLite database = a MySQL table
        connection = a connection to a MySQL database"""
        self.name = basename
        self.conn = connection
        self.cursor = connection.cursor()
        self._iterating = False

    def create(self,*fields,**kw):
        """Create a new base with specified field names
        A keyword argument mode can be specified ; it is used if a file
        with the base name already exists
        - if mode = 'open' : open the existing base, ignore the fields
        - if mode = 'override' : erase the existing base and create a
        new one with the specified fields"""
        self.mode = mode = kw.get("mode",None)
        if self._table_exists():
            if mode == "override":
                self.cursor.execute("DROP TABLE %s" %self.name)
            elif mode == "open":
                return self.open()
            else:
                raise IOError,"Base %s already exists" %self.name
        self.fields = [ f[0] for f in fields ]
        self.all_fields = ["__id__","__version__"]+self.fields
        _types = ["INTEGER PRIMARY KEY AUTO_INCREMENT","INTEGER"] + \
            [f[1] for f in fields]
        f_string = [ "%s %s" %(f,t) for (f,t) in zip(self.all_fields,_types)]
        sql = "CREATE TABLE %s (%s)" %(self.name,
            ",".join(f_string))
        self.cursor.execute(sql)
        return self

    def open(self):
        """Open an existing database"""
        if self._table_exists():
            self.mode = "open"
            self._get_table_info()
            return self
        # table not found
        raise IOError,"Table %s doesn't exist" %self.name

    def _table_exists(self):
        """Database-specific method to see if the table exists"""
        self.cursor.execute("SHOW TABLES")
        for table in self.cursor.fetchall():
            if table[0].lower() == self.name.lower():
                return True
        return False

    def _get_table_info(self):
        """Database-specific method to get field names"""
        self.cursor.execute('DESCRIBE %s' %self.name)
        self.all_fields = [ f[0] for f in self.cursor.fetchall() ]
        self.fields = self.all_fields[2:]

    def commit(self):
        """No use here ???"""
        pass

    def insert(self,*args,**kw):
        """Insert a record in the database
        Parameters can be positional or keyword arguments. If positional
        they must be in the same order as in the create() method
        If some of the fields are missing the value is set to None
        Returns the record identifier
        """
        if args:
            kw = dict([(f,arg) for f,arg in zip(self.all_fields[2:],args)])
        kw["__version__"] = 0

        vals = self._make_sql_params(kw)
        sql = "INSERT INTO %s SET %s" %(self.name,",".join(vals))
        res = self.cursor.execute(sql)
        self.cursor.execute("SELECT LAST_INSERT_ID()")
        __id__ = self.cursor.fetchone()[0]
        return __id__

    def delete(self,removed):
        """Remove a single record, or the records in an iterable
        Before starting deletion, test if all records are in the base
        and don't have twice the same __id__
        Return the number of deleted items
        """
        if isinstance(removed,dict):
            # remove a single record
            removed = [removed]
        else:
            # convert iterable into a list (to be able to sort it)
            removed = [ r for r in removed ]
        if not removed:
            return 0
        _ids = [ r['__id__'] for r in removed ]
        _ids.sort()
        sql = "DELETE FROM %s WHERE __id__ IN (%s)" %(self.name,
            ",".join([str(_id) for _id in _ids]))
        self.cursor.execute(sql)
        return len(removed)

    def update(self,record,**kw):
        """Update the record with new keys and values"""
        # increment version number
        kw["__version__"] = record["__version__"] + 1
        vals = self._make_sql_params(kw)
        sql = "UPDATE %s SET %s WHERE __id__=%s" %(self.name,
            ",".join(vals),record["__id__"])
        self.cursor.execute(sql)

    def _make_sql_params(self,kw):
        """Make a list of strings to pass to an SQL statement
        from the dictionary kw with Python types"""
        vals = []
        for k,v in kw.iteritems():
            vals.append('%s=%s' %(k,self._conv(v)))
        return vals

    def _conv(self,v):
        if isinstance(v,str):
            return '"%s"' %v.replace("'","''")
        elif isinstance(v,datetime.date):
            return v.strftime("%Y%m%d")
        else:
            return v

    def _make_record(self,row):
        """Make a record dictionary from the result of a fetch_"""
        return dict(zip(self.all_fields,row))
        
    def add_field(self,field,default=None):
        fname,ftype = field
        if fname in self.all_fields:
            raise ValueError,'Field "%s" already defined' %fname
        sql = "ALTER TABLE %s ADD %s %s" %(self.name,fname,ftype)
        if default is not None:
            sql += " DEFAULT %s" %self._conv(default)
        self.cursor.execute(sql)
        self.commit()
        self._get_table_info()
    
    def drop_field(self,field):
        if field in ["__id__","__version__"]:
            raise ValueError,"Can't delete field %s" %field
        if not field in self.fields:
            raise ValueError,"Field %s not found in base" %field
        sql = "ALTER TABLE %s DROP %s" %(self.name,field)
        self.cursor.execute(sql)
        self._get_table_info()

    def __call__(self,**kw):
        """Selection by field values
        db(key=value) returns the list of records where r[key] = value"""
        for key in kw:
            if not key in self.all_fields:
                raise ValueError,"Field %s not in the database" %key
        vals = self._make_sql_params(kw)
        sql = "SELECT * FROM %s WHERE %s" %(self.name,",".join(vals))
        self.cursor.execute(sql)
        return [self._make_record(row) for row in self.cursor.fetchall() ]
    
    def __getitem__(self,record_id):
        """Direct access by record id"""
        sql = "SELECT * FROM %s WHERE __id__=%s" %(self.name,record_id)
        self.cursor.execute(sql)
        res = self.cursor.fetchone()
        if res is None:
            raise IndexError,"No record at index %s" %record_id
        else:
            return self._make_record(res)
    
    def __len__(self):
        return len(self.records)

    def __delitem__(self,record_id):
        """Delete by record id"""
        self.delete(self[record_id])
        
    def __iter__(self):
        """Iteration on the records"""
        self.cursor.execute("SELECT * FROM %s" %self.name)
        results = [ self._make_record(r) for r in self.cursor.fetchall() ]
        return iter(results)

if __name__ == '__main__':

    connection = MySQLdb.connect("localhost","root","admin")
    cursor = connection.cursor()
    cursor.execute("USE test")

    db = Base("pydbtest",connection).create(("name","TEXT"),("age","INTEGER"),
        ("size","REAL"),("birth","DATE"),
        mode="override")

    try:
        db.add_field(("name","TEXT"))
    except:
        pass

    import random
    import datetime

    names = ['pierre','claire','simon','camille','jean',
                 'florence','marie-anne']
    #db = Base('PyDbLite_test')
    #db.create('name','age','size','birth',mode="override")
    for i in range(1000):
        db.insert(name=random.choice(names),
             age=random.randint(7,47),size=random.uniform(1.10,1.95),
             birth=datetime.date(1990,10,10))
    db.commit()

    print 'Record #20 :',db[20]
    print '\nRecords with age=30 :'
    for rec in [ r for r in db if r["age"]==30 ]:
        print '%-10s | %2s | %s' %(rec['name'],rec['age'],round(rec['size'],2))

    print "\nSame with __call__"
    # same with select
    for rec in db(age=30):
        print '%-10s | %2s | %s' %(rec['name'],rec['age'],round(rec['size'],2))
    print [ r for r in db if r["age"]==30 ] == db(age=30)
    raw_input()

    db.insert(name=random.choice(names)) # missing fields
    print '\nNumber of records with 30 <= age < 33 :',
    print sum([1 for r in db if 33 > r['age'] >= 30])
    
    print db.delete([])

    d = db.delete([r for r in db if 32> r['age'] >= 30 and r['name']==u'pierre'])
    print "\nDeleting %s records with name == 'pierre' and 30 <= age < 32" %d
    print '\nAfter deleting records '
    for rec in db(age=30):
        print '%-10s | %2s | %s' %(rec['name'],rec['age'],round(rec['size'],2))
    print '\n',sum([1 for r in db]),'records in the database'
    print '\nMake pierre uppercase for age > 27'
    for record in ([r for r in db if r['name']=='pierre' and r['age'] >27]) :
        db.update(record,name="Pierre")
    print len([r for r in db if r['name']=='Pierre']),'Pierre'
    print len([r for r in db if r['name']=='pierre']),'pierre'
    print len([r for r in db if r['name'] in ['pierre','Pierre']]),'p/Pierre'
    print 'is unicode :',isinstance(db[20]['name'],unicode)
    db.commit()
    db.open()
    print '\nSame operation after commit + open'
    print len([r for r in db if r['name']=='Pierre']),'Pierre'
    print len([r for r in db if r['name']=='pierre']),'pierre'
    print len([r for r in db if r['name'] in ['pierre','Pierre']]),'p/Pierre'
    print 'is unicode :',isinstance(db[20]['name'],unicode)
    
    print "\nDeleting record #21"
    del db[21]
    if not 21 in db:
        print "record 21 removed"

    print db[22]
    db.drop_field('name')
    print db[22]
    db.add_field(('adate',"DATE"),datetime.date.today())
    print db[22]
    
    
    