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
    from PyDbLite.MySQL import Connection,Database,Table
    conn = Connection("localhost","root","admin")
    db = Database("test",conn)
    # pass the connection as argument to Base creation
    table = Table('dummy',db)
    # create new table with field names
    table.create(('name','INTEGER PRIMARY KEY AUTO_INCREMENT'),
        ('age','INTEGER'),('size','REAL'))
    # open existing base
    table.open()
    # insert new record
    table.insert(name='homer',age=23,size=1.84)
    # selection by list comprehension
    res = [ r for r in table if 30 > r['age'] >= 18 and r['size'] < 2 ]
    # or generator expression
    for r in (r for r in table if r['name'] in ('homer','marge') ):
    # simple selection (equality test)
    res = table(age=30)

    # the following methods only work if the table has an
    # AUTO_INCREMENT
    # delete a record or a list of records
    table.delete(one_record)
    table.delete(list_of_records)
    # delete a record by its id
    del table[rec_id]
    # direct access by id
    record = table[rec_id] # the record such that record['__id__'] == rec_id
    # update
    table.update(record,age=24)
    # add and drop fields
    table.add_field('new_field')
    table.drop_field('name')
    # save changes on disk
    table.commit()
"""

import os
import cPickle
import bisect

import datetime

import MySQLdb

# compatibility with Python 2.3
try:
    set([])
except NameError:
    from sets import Set as set

class MySQLError(Exception):

    pass

class Connection:

    def __init__(self,host,login,password):
        self.conn = MySQLdb.connect(host,login,password)
        self.cursor = self.conn.cursor()

    def databases(self):
        self.cursor.execute('SHOW DATABASES')
        return [db[0] for db in self.cursor.fetchall()]

    def create(self,db_name,mode=None):
        if mode=="open":
            if not db_name in self.databases():
                self.cursor.execute('CREATE DATABASE %s' %db_name)
            else:
                self.cursor.execute('USE %s' %db_name)
        else:
            self.cursor.execute('CREATE DATABASE %s' %db_name)
        return Database(db_name,self)

class Database:

    def __init__(self,db_name,connection):
        self.conn = connection
        self.cursor = connection.cursor
        self.cursor.execute('USE %s' %db_name)

    def tables(self):
        self.cursor.execute("SHOW TABLES")
        return [ t[0] for t in self.cursor.fetchall() ]

    def drop(self):
        # drop database
        self.cursor.execute('USE %s' %db)
        self.cursor.execute('SHOW TABLES')
        if len(self.cursor.fetchall()):
            raise MySQLError,\
              "Can't drop database %s ; all tables must be dropped first" %db
    
class Table:

    def __init__(self,table_name,db):
        """db = an instance of Database"""
        self.name = table_name
        self.db = db
        self.conn = self.db.conn.conn
        self.cursor = db.cursor

    def create(self,*fields,**kw):
        """Create a new table
        For each field, a 2-element tuple is provided :
        - the field name
        - a string with additional information : field type +
          other information using the MySQL syntax
          eg : ('name','TEXT NOT NULL')
               ('date','TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
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
        self.fields = []
        self.field_info = {}
        sql = "CREATE TABLE %s (" %self.name
        for field in fields:
            sql += self._validate_field(field)
            sql += ','
        sql = sql[:-1]+')'
        self.cursor.execute(sql)
        self._get_table_info()
        return self

    def _validate_field(self,field):
        if len(field)!= 2:
            msg = "Error in field definition %s" %field
            msg += ": should be a 2- tuple (field_name,field_info)"
            raise SQLiteError,msg
        return '%s %s' %(field[0],field[1])

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
        self.rowid = None
        self.fields = []
        self.field_info = {}
        self.cursor.execute('DESCRIBE %s' %self.name)
        for row in self.cursor.fetchall():
            field,typ,null,key,default,extra = row
            self.fields.append(field)
            self.field_info[field] = {'type':typ,'NOT NULL':null,'key':key,
                'DEFAULT':default,'extra':extra}
            if extra == 'auto_increment':
                self.rowid = field

    def commit(self):
        self.conn.commit()

    def insert(self,*args,**kw):
        """Insert a record in the database
        Parameters can be positional or keyword arguments. If positional
        they must be in the same order as in the create() method
        If some of the fields are missing the value is set to None
        Returns the record identifier
        """
        fields = [ f for f in self.fields
            if not self.field_info[f]['extra']=="auto_increment"]
        if args:
            kw = dict([(f,arg) for f,arg in zip(fields,args)])

        vals = self._make_sql_params(kw)
        sql = "INSERT INTO %s SET %s" %(self.name,",".join(vals))
        res = self.cursor.execute(sql,kw.values())
        self.cursor.execute("SELECT LAST_INSERT_ID()")
        __id__ = self.cursor.fetchone()[0]
        return __id__

    def delete(self,removed):
        """Remove a single record, or the records in an iterable
        Before starting deletion, test if all records are in the base
        and don't have twice the same __id__
        Return the number of deleted items
        """
        if self.rowid is None:
            raise MySQLError,"Can't use delete() : missing row id"
        if isinstance(removed,dict):
            # remove a single record
            removed = [removed]
        else:
            # convert iterable into a list (to be able to sort it)
            removed = [ r for r in removed ]
        if not removed:
            return 0
        _ids = [ r[self.rowid] for r in removed ]
        _ids.sort()
        sql = "DELETE FROM %s WHERE %s IN (%s)" %(self.name,self.rowid,
            ",".join([str(_id) for _id in _ids]))
        self.cursor.execute(sql)
        return len(removed)

    def update(self,record,**kw):
        """Update the record with new keys and values"""
        # increment version number
        if self.rowid is None:
            raise MySQLError,"Can't use update() : missing row id"
        vals = self._make_sql_params(kw)
        sql = "UPDATE %s SET %s WHERE %s=%s" %(self.name,
            ",".join(vals),self.rowid,record[self.rowid])
        self.cursor.execute(sql,kw.values())

    def _make_sql_params(self,kw):
        """Make a list of strings to pass to an SQL statement
        from the dictionary kw with Python types"""
        return ['%s=%%s' %k for k in kw.keys() ]

    def _conv(self,v):
        if isinstance(v,str):
            v = v.replace('"','""')
            return '"%s"' %v
        elif isinstance(v,datetime.datetime):
            return '"%s"' %v.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(v,datetime.date):
            return v.strftime("%Y-%m-%d")
        else:
            return v

    def _make_record(self,row):
        """Make a record dictionary from the result of a fetch_"""
        return dict(zip(self.fields,row))
        
    def add_field(self,field,default=None):
        fname,ftype = field
        if fname in self.fields:
            raise ValueError,'Field "%s" already defined' %fname
        sql = "ALTER TABLE %s ADD %s %s" %(self.name,fname,ftype)
        if default is not None:
            sql += " DEFAULT %s" %self._conv(default)
        self.cursor.execute(sql)
        self.commit()
        self._get_table_info()
    
    def drop_field(self,field):
        if not field in self.fields:
            raise ValueError,"Field %s not found in base" %field
        sql = "ALTER TABLE %s DROP %s" %(self.name,field)
        self.cursor.execute(sql)
        self._get_table_info()

    def __call__(self,**kw):
        """Selection by field values
        db(key=value) returns the list of records where r[key] = value"""
        for key in kw:
            if not key in self.fields:
                raise ValueError,"Field %s not in the database" %key
        vals = self._make_sql_params(kw)
        if vals:
            sql = "SELECT * FROM %s WHERE %s" %(self.name," AND ".join(vals))
        else: # all records
            sql = "SELECT * FROM %s" %self.name
        self.cursor.execute(sql,kw.values())            
        return [self._make_record(row) for row in self.cursor.fetchall() ]
    
    def __getitem__(self,record_id):
        """Direct access by record id"""
        if self.rowid is None:
            raise MySQLError,"Can't use __getitem__() : missing row id"
        sql = "SELECT * FROM %s WHERE %s=%s" %(self.name,self.rowid,record_id)
        self.cursor.execute(sql)
        res = self.cursor.fetchone()
        if res is None:
            raise IndexError,"No record at index %s" %record_id
        else:
            return self._make_record(res)
    
    def __len__(self):
        self.cursor.execute("SELECT COUNT(*) FROM %s" %self.name)
        return int(self.cursor.fetchone()[0])

    def __delitem__(self,record_id):
        """Delete by record id"""
        self.delete(self[record_id])
        
    def __iter__(self):
        """Iteration on the records"""
        self.cursor.execute("SELECT * FROM %s" %self.name)
        results = [ self._make_record(r) for r in self.cursor.fetchall() ]
        return iter(results)

Base = Table # compatibility with older versions

if __name__ == '__main__':
    os.chdir(os.path.join(os.getcwd(),'test'))
    execfile('MySQL_test.py')
    
