"""PyDbLite.py adapted for SQLite backend

Differences with PyDbLite:
- pass the connection to the SQLite db as argument to Table()
- in create(), field definitions must specify a type
- no index
- no drop_field (not supported by SQLite)
- the Table() instance has a cursor attribute, so that SQL requests
  can be executed :
    db.cursor.execute(an_sql_request)
    result = db.cursor.fetchall()

Syntax :
    from PyDbLite.SQLite import Table
    # connect to SQLite database "test"
    connection = sqlite.connect("test")
    # pass the table name and database path as arguments to Table creation
    db = Table('dummy','test')
    # create new base with field names
    db.create(('name','TEXT'),('age','INTEGER'),('size','REAL'))
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

Changes in version 2.5 :
- many changes to support "legacy" SQLite databases :
    . no control on types declared in CREATE TABLE or ALTER TABLE
    . no control on value types in INSERT or UPDATE
    . no version number in records
- add methods to specify a conversion function for fields after a SELECT
- change names to be closer to SQLite names : 
    . a class Database to modelise the database
    . a class Table (not Base) for each table in the database
- test is now in folder "test"
"""

import os
import cPickle
import bisect
import re
import time
import datetime

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

# classes for CURRENT_DATE, CURRENT_TIME, CURRENT_TIMESTAMP
class CURRENT_DATE:
    def __call__(self):
        return datetime.date.today().strftime('%Y-%M-%D')

class CURRENT_TIME:
    def __call__(self):
        return datetime.datetime.now().strftime('%h:%m:%s')

class CURRENT_TIMESTAMP:
    def __call__(self):
        return datetime.datetime.now().strftime('%Y-%M-%D %h:%m:%s')

DEFAULT_CLASSES = [CURRENT_DATE,CURRENT_TIME,CURRENT_TIMESTAMP]

# Return the value formatted for inclusion in a
# INSERT or UPDATE SQL expression
def to_SQLite(value):
    if value is None:
        return 'NULL'
    elif value in DEFAULT_CLASSES:
        return value.__class__
    elif isinstance(value,str):
        return '"%s"' %value.replace('"','""')
    elif isinstance(value,unicode):
        return '"%s"' %value.encode('utf-8').replace('"','""')
    elif isinstance(value,(int,float)):
        return str(value)
    elif isinstance(value,datetime.date):
        return '"%s"' %value.strftime('%Y-%m-%d')
    elif isinstance(value,datetime.datetime):
        return '"%s"' %value.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(value,datetime.time):
        return '"%s"' %value.strftime('%H:%M:%S')
    else:
        raise ValueError,'Wrong value %s : type %s not supported' \
            %(value,value.__class__)


# functions to convert a value returned by a SQLite SELECT

# DATE : convert YYYY-MM-DD to datetime.date instance
def to_date(date):
    if date is None:
        return None
    mo = c_date_fmt.match(date)
    if not mo:
        raise ValueError,"Bad value %s for DATE format" %date
    year,month,day = [int(x) for x in mo.groups()]
    return datetime.date(year,month,day)

# TIME : convert HH-MM-SS to datetime.time instance
def to_time(_time):
    if _time is None:
        return None
    mo = c_time_fmt.match(_time)
    if not mo:
        raise ValueError,"Bad value %s for TIME format" %_time
    hour,minute,second = [int(x) for x in mo.groups()]
    return datetime.time(hour,minute,second)

# DATETIME or TIMESTAMP : convert %YYYY-MM-DD HH:MM:SS
# to datetime.datetime instance
def to_datetime(timestamp):
    if timestamp is None:
        return None
    if not isinstance(timestamp,unicode):
        raise ValueError,"Bad value %s for TIMESTAMP format" %timestamp
    mo = c_tmsp_fmt.match(timestamp)
    if not mo:
        raise ValueError,"Bad value %s for TIMESTAMP format" %timestamp
    return datetime.datetime(*[int(x) for x in mo.groups()])

# if default value is CURRENT_DATE etc. SQLite doesn't
# give the information, default is the value of the
# variable as a string. We have to guess...
#
# CURRENT_TIME format is HH:MM:SS
# CURRENT_DATE : YYYY-MM-DD
# CURRENT_TIMESTAMP : YYYY-MM-DD HH:MM:SS

c_time_fmt = re.compile('^(\d{2}):(\d{2}):(\d{2})$')
c_date_fmt = re.compile('^(\d{4})-(\d{2})-(\d{2})$')
c_tmsp_fmt = re.compile('^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})$')

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
            datetime.date(y,m,d)
            return CURRENT_DATE
        except:
            pass
    mo = c_tmsp_fmt.match(value)
    if mo:
        y,mth,d,h,mn,s = [int(x) for x in mo.groups()]
        try:
            datetime.datetime(y,mth,d,h,mn,s)
            return CURRENT_TIMESTAMP
        except:
            pass
    return value

class SQLiteError(Exception):

    pass

class Database:

    def __init__(self,db):
        self.conn = sqlite.connect(db)
        self.cursor = self.conn.cursor()

    def tables(self):
        """Return the list of table names in the database"""
        tables = []
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for table_info in self.cursor.fetchall():
            if table_info[0] != 'sqlite_sequence':
                tables.append(table_info[0])
        return tables

    def has_table(self,table):
        return table in self.tables()
    
class Table:

    def __init__(self,basename,db):
        """basename = name of the PyDbLite database = a MySQL table
        db = a connection to a SQLite database, a Database instance
        or the database path"""
        self.name = basename
        if isinstance(db,sqlite.Connection):
            self.conn = db
            self.cursor = db.cursor()
        elif isinstance(db,Database):
            self.conn = db.conn
            self.cursor = db.cursor
        else:
            self.conn = sqlite.connect(db)
            self.cursor = self.conn.cursor()
        self.conv_func = {}

    def create(self,*fields,**kw):
        """Create a new table
        For each field, a 2-element tuple is provided :
        - the field name
        - a string with additional information : field type +
          other information using the SQLite syntax
          eg : ('name','TEXT NOT NULL')
               ('date','BLOB DEFAULT CURRENT_DATE')
        A keyword argument mode can be specified ; it is used if a file
        with the base name already exists
        - if mode = 'open' : open the existing base, ignore the fields
        - if mode = 'override' : erase the existing base and create a
        new one with the specified fields"""
        mode = kw.get("mode",None)
        if self._table_exists():
            if mode == "override":
                self.cursor.execute("DROP TABLE %s" %self.name)
            elif mode == "open":
                return self.open()
            else:
                raise IOError,"Base %s already exists" %self.name
        sql = "CREATE TABLE %s (" %self.name
        for field in fields:
            sql += self._validate_field(field)
            sql += ','
        sql = sql[:-1]+')'
        self.cursor.execute(sql)
        self._get_table_info()
        return self

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
            info = {'type':ftype}
            # can be null ?
            info['NOT NULL'] = field_info[3] != 0
            # default value
            default = field_info[4]
            if isinstance(default,unicode):
               default = guess_default_fmt(default)
            info['DEFAULT'] = default
            self.field_info[fname] = info

    def info(self):
        # returns information about the table
        return [(field,self.field_info[field]) for field in self.fields]

    def commit(self):
        """Commit changes on disk"""
        self.conn.commit()

    def _validate_field(self,field):
        if len(field)!= 2:
            msg = "Error in field definition %s" %field
            msg += ": should be a 2- tuple (field_name,field_info)"
            raise SQLiteError,msg
        return '%s %s' %(field[0],field[1])

    def conv(self,field_name,conv_func):
        """When a record is returned by a SELECT, ask conversion of
        specified field value with the specified function"""
        if field_name not in self.fields:
            raise NameError,"Unknown field %s" %field_name
        self.conv_func[field_name] = conv_func

    def conv_date(self,field_name):
        """Ask conversion of field to an instance of datetime.date"""
        self.conv(field_name,to_date)

    def conv_time(self,field_name):
        """Ask conversion of field to an instance of datetime.date"""
        self.conv(field_name,to_time)

    def conv_datetime(self,field_name):
        """Ask conversion of field to an instance of datetime.date"""
        self.conv(field_name,to_datetime)

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
        vals = [ to_SQLite(kw[k]) for k in kw.keys() ]
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
            vals.append('%s=%s' %(k,to_SQLite(v)))
        return vals

    def _make_record(self,row):
        """Make a record dictionary from the result of a fetch_"""
        res = dict(zip(['__id__']+[f for f in self.fields],row))
        for field_name in self.conv_func:
            res[field_name] = self.conv_func[field_name](res[field_name])
        return res
        
    def add_field(self,field):
        sql = "ALTER TABLE %s ADD " %self.name
        sql += self._validate_field(field)
        self.cursor.execute(sql)
        self.commit()
        self._get_table_info()
    
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

Base = Table # compatibility with previous versions

if __name__ == '__main__':
    os.chdir(os.path.join(os.getcwd(),'test'))
    execfile('SQLite_test.py')