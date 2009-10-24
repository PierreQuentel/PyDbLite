"""PyDbLite.py adapted for SQLite backend

Differences with PyDbLite:
- pass the connection to the SQLite db as argument to Base()
- in create(), field definitions must specify a type
- no index
- no drop_field (not supported by SQLite)
- the Base() instance has a cursor attribute, so that SQL requests
  can be executed :
    db.cursor.execute(an_sql_request)
    result = db.cursor.fetchall()

Syntax :
    from PyDbLite.SQLite import Table
    # create instance of Table with table name and path to the database file
    table = Table('dummy','test.sqlite')
    # create new base with field names and types
    db.create(('name','TEXT'),('age',"INTEGER'),('size','REAL'))
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
    # add a field
    db.add_field('new_field')
    # save changes on disk
    db.commit()

Version 2.3 : 
. change name Base to Table (compliant with SQLite vocabulary)
. in Table(table_name,db), db can either be the connection to the db, or the
  path of the db in the file system

Version 2.5 :
. add class Database, rename Base to Table
. changes to accept all legacy SQLite dbs (eg remove __version__, only accept
  SQLite types TEXT, BLOB, REAL, INTEGER, more inspection in _get_table_info())
"""

import os
import cPickle
import bisect
import re

# test if sqlite is installed or raise exception
try:
    from sqlite3 import dbapi2 as sqlite
except ImportError:
    try:
        from pysqlite2 import dbapi2 as sqlite
    except ImportError:
        print "SQLite is not installed"
        raise

# compatibility with Python 2.3
try:
    set([])
except NameError:
    from sets import Set as set

class SQLiteError(Exception):
    pass

# conversion functions
conv_func = {'INTEGER':int,'REAL':float,'BLOB':str,'TIMESTAMP':float}
def conv(txt):
    if isinstance(txt,str):
        return str
    elif isinstance(txt,unicode):
        return txt.encode('utf-8')
conv_func['TEXT'] = conv

# if default value is CURRENT_DATE etc. SQLite doesn't
# give the information, default is the value of the
# variable as a string. We have to guess...
# CURRENT_TIME format is HH:MM:SS
# CURRENT_DATE : YYYY-MM-DD
# CURRENT_TIMESTAMP : YYYY-MM-DD HH:MM:SS
c_time_fmt = re.compile('(\d\d):(\d\d):(\d\d)')
c_date_fmt = re.compile('(\d\d\d\d)-(\d\d)-(\d\d)')
c_tmsp_fmt = re.compile('(\d\d\d\d)-(\d\d)-(\d\d) (\d\d):(\d\d):(\d\d)')

def guess_default_fmt(value):
    mo = c_time_fmt.match(value)
    if mo:
        h,m,s = [int(x) for x in mo.groups()]
        if (0<=h<=23) and (0<=m<=59) and (0<=s<=59):
            return CURRENT_TIME
    mo = c_date_fmt.match(value)
    if mo:
        y,m,d = [int(x) for x in mo.groups()]
        try:
            date(y,m,d)
            return CURRENT_DATE
        except:
            pass
    mo = c_tmsp_fmt.match(value)
    if mo:
        y,mth,d,h,mn,s = [int(x) for x in mo.groups()]
        try:
            datetime(y,mth,d,h,mn,s)
            return CURRENT_TIMESTAMP
        except:
            pass
    return value

# classes for default CURRENT_TIME, CURRENT_DATE or CURRENT_TIMESTAMP
import datetime

class CURRENT_DATE:

    def __call__(self):
        return datetime.date.today().strftime('%Y-%M-%D')

class CURRENT_TIME:

    def __call__(self):
        return datetime.datetime.now().strftime('%h:%m:%s')

class CURRENT_TIMESTAMP:

    def __call__(self):
        return datetime.datetime.now().strftime('%Y-%M-%D %h:%m:%s')

class Database:

    def __init__(self,db):
        self.conn = sqlite.connect(db)
        self.cursor = self.conn.cursor()

    def tables(self):
        tables = []
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for table_info in self.cursor.fetchall():
            if table_info[0] != 'sqlite_sequence':
                tables.append(Table(table_info[0],self.conn))
        return tables

class Table:

    def __init__(self,table_name,db):
        """basename = name of the PyDbLite database = a MySQL table
        db = a connection to a SQLite database, or its path"""
        self.name = table_name
        if isinstance(db,str):
            self.conn = sqlite.connect(db)
        elif isinstance(db,sqlite.Connection):
            self.conn = db
        self.cursor = self.conn.cursor()
        self._iterating = False

    def create(self,*fields,**kw):
        """Create a new base with specified fields
        Each field is a tuple with 2 or 3 elements
        - 1st : field name
        - 2nd : field type
        - optional 3rd : a dictionary with keys = 'allow_empty' and/or 'default'
        A keyword argument mode can be specified ; it is used if a file
        with the base name already exists
        - if mode = 'open' : open the existing base, ignore the fields
        - if mode = 'override' : erase the existing base and create a
        new one with the specified fields
        """
        mode = kw.get("mode",None)
        if self._table_exists():
            if mode == "override":
                self.cursor.execute("DROP TABLE %s" %self.name)
            elif mode == "open":
                return self.open()
            else:
                raise IOError,"Base %s already exists" %self.name
        self.fields = []
        self.field_info = {}
        sql = 'CREATE TABLE %s (' %self.name
        for field in fields:
            name = field[0]
            self.fields.append(name)
            if len(field) <2 or len(field)>3:
                msg = "Error in field definition %s" %field
                msg += ": should be a 2- or 3-element tuple"
                msg += "(field_name,field_type[,info_dict])"
                raise SQLiteError,msg
            _type = field[1]
            self.field_info[name] = {'type':_type}
            if not _type in ['NULL','INTEGER','REAL','TEXT','BLOB']:
                raise SQLiteError,"Unknow type %s" %_type
            self.field_info['conv'] = conv_func[_type]
            sql += '%s %s' %(name,_type)
            if len(field)==3: # default value
                info = field[2]
                if info.get('NOT NULL',False) is True:
                    sql += ' NOT NULL'
                default = field[2].get('DEFAULT',None)
                sql += self._validate_default(name,_type,default)
            sql += ','
        sql = sql[:-1]+')'
        self.cursor.execute(sql)
        return self

    def _validate_default(self,name,_type,default):
        if default is None:
            return ''
        if _type=='INTEGER':
            if isinstance(default,int):
                self.field_info[name]['default'] = default
                sql = " DEFAULT %s" %default
            else:
                raise SQLiteError,'Default value for %s is not %s' \
                %(name,_type)
        elif _type=='REAL':
            if isinstance(default,float):
                self.field_info[name]['default'] = default
                sql = " DEFAULT %s" %default
            else:
                raise SQLiteError,'Default value for %s is not %s' \
                %(name,_type)
        elif _type=='TEXT':
            if isinstance(default,(str,unicode)):
                default = default.replace('"','""')
                self.field_info[name]['default'] = default
                sql = ' DEFAULT "%s"' %default
            else:
                raise SQLiteError,'Default value for %s is not %s' \
                %(name,_type)
        elif _type=='BLOB':
            if isinstance(default,str):
                self.field_info[name]['default'] = default
                sql = ' DEFAULT "%s"' %default
            elif default in [CURRENT_TIME,CURRENT_DATE,
                CURRENT_TIMESTAMP]:
                self.field_info[name]['default'] = default
                sql = ' DEFAULT %s' %default.__name__
            else:
                raise SQLiteError,'Default value for %s is not %s' \
                    %(name,_type)
        return sql

    def open(self):
        """Open an existing database"""
        if self._table_exists():
            self.mode = "open"
            # get table info
            self._get_table_info()
            return self
        else:
            # table not found
            raise IOError,"Table %s doesn't exist" %self.name

    def drop(self):
        """Drop the table from the database"""
        sql = "DROP TABLE %s" %self.name
        self.cursor.execute(sql)
        self.commit()

    def _table_exists(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for table_info in self.cursor.fetchall():
            if table_info[0] == self.name:
                return True
        return False

    def _get_table_info(self):
        """Inspect the base to get field names"""
        self.fields = []
        self.field_info = {}
        self.cursor.execute('PRAGMA table_info (%s)' %self.name)
        for field_info in self.cursor.fetchall():
            fname = field_info[1].encode('utf-8')
            self.fields.append(fname)
            ftype = field_info[2].encode('utf-8')
            info = {'type':ftype,'conv':conv_func[ftype]}
            # can be null ?
            info['NOT NULL'] = field_info[3] != 0
            # default value
            default = field_info[4]
            if isinstance(default,unicode):
               default = guess_default_fmt(default)
            info['DEFAULT'] = default
            self.field_info[fname] = info

    def commit(self):
        """Commit changes on disk"""
        self.conn.commit()

    def insert(self,*args,**kw):
        """Insert a record in the database
        Parameters can be positional or keyword arguments. If positional
        they must be in the same order as in the create() method
        If some of the fields are missing the value is set to None
        Returns the record identifier
        """
        if args:
            kw = dict([(f,arg) for f,arg in zip(self.fields,args)])

        ks = kw.keys()
        vals = [ str(self._conv(kw[k])) for k in kw.keys() ]
        s1 = ",".join(ks)
        s2 = ",".join(vals)
        sql = "INSERT INTO %s (%s) VALUES (%s)" %(self.name,s1,s2)
        self.cursor.execute(sql)
        # return last row id
        return self.cursor.lastrowid

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
        sql = "DELETE FROM %s WHERE rowid IN (%s)" %(self.name,
            ",".join([str(_id) for _id in _ids]))
        self.cursor.execute(sql)
        return len(removed)

    def update(self,record,**kw):
        """Update the record with new keys and values"""
        vals = self._make_sql_params(kw)
        sql = "UPDATE %s SET %s WHERE rowid=%s" %(self.name,
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
            v = v.replace('"','""')
            return '"%s"' %v
        elif isinstance(v,unicode):
            return self._conv(v.encode('utf-8'))
        else:
            return v

    def _make_record(self,row):
        """Make a record dictionary from the result of a fetch_"""
        res = dict(zip(['__id__']+[f for f in self.fields],row))
        for f in self.fields:
            if res[f] is not None:
                res[f] = conv_func[self.field_info[f]['type']](res[f])
        return res
        
    def add_field(self,*fields):
        for field in fields:
            if len(field)==2:
                fname,ftype = field
                default = None
            elif len(field)==3:
                fname,ftype,info = field
                default = info.get('DEFAULT',None)
            if fname in self.fields:
                raise ValueError,'Field "%s" already defined' %fname
            self.fields.append(fname)
            if ftype.upper() in conv_func:
                self.field_info[fname] = {'type':ftype.upper(),
                    'conv':conv_func[ftype.upper()]}
            else:
                raise SQLiteError,'Unknown type %s' %ftype
            sql = "ALTER TABLE %s ADD %s %s" %(self.name,fname,ftype)
            if default is not None:
                sql += self._validate_default(fname,ftype,default)
            self.cursor.execute(sql)
        self.commit()
    
    def drop_field(self,field):
        raise SQLiteError,"Dropping fields is not supported by SQLite"

    def __call__(self,**kw):
        """Selection by field values
        db(key=value) returns the list of records where r[key] = value"""
        if kw:
            for key in kw:
                if not key in self.fields:
                    raise ValueError,"Field %s not in the database" %key
            vals = self._make_sql_params(kw)
            sql = "SELECT rowid,* FROM %s WHERE %s" %(self.name," AND ".join(vals))
        else:
            sql = "SELECT rowid,* FROM %s" %self.name
        self.cursor.execute(sql)
        return [self._make_record(row) for row in self.cursor.fetchall() ]
    
    def __getitem__(self,record_id):
        """Direct access by record id"""
        sql = "SELECT rowid,* FROM %s WHERE rowid=%s" %(self.name,record_id)
        self.cursor.execute(sql)
        res = self.cursor.fetchone()
        if res is None:
            raise IndexError,"No record at index %s" %record_id
        else:
            return self._make_record(res)
    
    def __len__(self):
        self.cursor.execute("SELECT rowid FROM %s" %self.name)
        return len(self.cursor.fetchall())

    def __delitem__(self,record_id):
        """Delete by record id"""
        self.delete(self[record_id])
        
    def __iter__(self):
        """Iteration on the records"""
        self.cursor.execute("SELECT rowid,* FROM %s" %self.name)
        results = [ self._make_record(r) for r in self.cursor.fetchall() ]
        return iter(results)

# compatibility with previous versions
Base = Table

if __name__ == '__main__':

    db = Table("pydbsqlite_test","test_sqlite")
    db.create(("name","TEXT",{'NOT NULL':True}),
        ("age","INTEGER"),
        ("size","REAL"),("birth","BLOB"),("date","BLOB",{'DEFAULT':CURRENT_DATE}),
        mode="override")

    try:
        db.add_field(("name","TEXT"))
    except:
        pass

    print len(db)
    
    import random
    import datetime

    names = ['pierre','claire','simon','camille','jean',
                 'florence','marie-anne']
    #db = Base('PyDbLite_test')
    #db.create('name','age','size','birth',mode="override")
    for i in range(1000):
        db.insert(name=random.choice(names),
             age=random.randint(7,47),size=random.uniform(1.10,1.95),
             birth=datetime.datetime(1990,10,10,20,10,20,2345).strftime('%Y-%m-%d %H:%M:%S'))
    db.commit()

    print 'Record #20 :',db[20]
    raw_input()
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

    for field in db.fields:
        print field,db.field_info[field]

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
    print "add field adate"
    db.add_field(('adate',"BLOB",
        {'DEFAULT':datetime.date.today().strftime('%Y-%m-%d')}))
    
    print db[22]
    
    
    