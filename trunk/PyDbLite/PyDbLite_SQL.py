import datetime

def make_date(d):
    if d is None:
        return None
    d = str(d)
    y,m,d = int(d[:4]),int(d[4:6]),int(d[6:])
    return datetime.date(y,m,d)

def make_datetime(d):
    if d is None:
        return None
    d = str(d)
    y,m,d,h,mn,s = int(d[:4]),int(d[4:6]),int(d[6:8]),\
        int(d[8:10]),int(d[10:12]),int(d[12:14])
    return datetime.datetime(y,m,d,h,mn,s)

class Base:

    conv_func = {"DATE":make_date,"TIMESTAMP":make_datetime,
        "DATETIME":make_datetime}
    auto_increment = "AUTO_INCREMENT" # this is for MySQL
                                      # SQLite uses AUTOINCREMENT...

    def __init__(self,basename,connection,db_module):
        """basename = name of the PyDbLite database = a MySQL table
        connection = a connection to a MySQL database"""
        self.name = basename
        self.conn = connection
        self.cursor = connection.cursor()
        self.db_module = db_module

    def create(self,*fields,**kw):
        """Create a new base with specified field names
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
        self.fields = [ f[0] for f in fields ]
        self.all_fields = ["__id__","__version__"]+self.fields
        _types = ["INTEGER PRIMARY KEY %s" %self.auto_increment,"INTEGER"] + \
            [f[1] for f in fields]
        f_string = [ "%s %s" %(f,t) for (f,t) in zip(self.all_fields,_types)]
        self.types = dict([ (f[0],self.conv_func[f[1].upper()]) 
            for f in fields if f[1].upper() in self.conv_func ])
        sql = "CREATE TABLE %s (%s)" %(self.name,",".join(f_string))
        self.cursor.execute(sql)
        return self

    def open(self):
        """Open an existing database"""
        if self._table_exists():
            self.mode = "open"
            # get table info
            self._get_table_info()
            self.types = dict([ (f[0],self.conv_func[f[1].upper()]) 
                for f in self.fields if f[1].upper() in self.conv_func ])
            return self
        else:
            # table not found
            raise IOError,"Table %s doesn't exist" %self.name

    def _table_exists(self):
        """Test if table exists in the database - Override"""
        raise NotImplementedError

    def _get_table_info(self):
        """Inspect the base to get field names - Override"""
        raise NotImplementedError

    def commit(self):
        """No use here ???"""
        pass

    def insert(self,*args,**kw):
        """Insert a record in the database
        Parameters can be positional or keyword arguments. If positional
        they must be in the same order as in the create() method
        If some of the fields are missing the value is set to None
        Return the record identifier
        Override
        """
        raise NotImplementedError

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
        """Convert Python values to MySQL values"""
        if isinstance(v,str):
            return '"%s"' %v.replace("'","''")
        elif isinstance(v,datetime.datetime):
            if v.tzinfo is not None:
                raise ValueError,\
                    "datetime instances with tzinfo not supported"
            return '"%s"' %self.db_module.Timestamp(v.year,v.month,v.day,
                v.hour,v.minute,v.second)
        elif isinstance(v,datetime.date):
            return '"%s"' %self.db_module.Date(v.year,v.month,v.day)
        else:
            return v

    def _make_record(self,row):
        """Make a record dictionary from the result of a fetch_"""
        res = dict(zip(self.all_fields,row))
        for k in self.types:
            res[k] = self.types[k](res[k])
        return res
        
    def add_field(self,field,default=None):
        fname,ftype = field
        if fname in self.all_fields:
            raise ValueError,'Field "%s" already defined' %fname
        self.all_fields.append(fname)
        if ftype.upper() in self.conv_func:
            self.types[fname] = self.conv_func[ftype.upper()]
        sql = "ALTER TABLE %s ADD %s %s" %(self.name,fname,ftype)
        if default is not None:
            sql += " DEFAULT %s" %self._conv(default)
        self.cursor.execute(sql)
        self.commit()
    
    def drop_field(self,field):
        """Drop a field - Override"""
        raise NotImplementedError

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
