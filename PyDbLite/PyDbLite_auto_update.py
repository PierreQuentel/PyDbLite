# this version :
# - db[i][key] = new_value automatically updates the index on key
# - remove bisect to insert or remove items from indices
# - arguments to create can be a string : the field name, or a
# two-item tuple, (field_name,default_value)

"""PyDbLite.py

In-memory database management, with selection by list comprehension 
or generator expression

Fields are untyped : they can store anything that can be pickled.
Selected records are returned as dictionaries. Each record is 
identified by a unique id and has a version number incremented
at every record update, to detect concurrent access

Syntax :
    from PyDbLite import Base
    db = Base('dummy')
    # create new base with field names
    db.create('name','age','size')
    # existing base
    db.open()
    # insert new record
    db.insert(name='homer',age=23,size=1.84)
    # records are dictionaries with a unique integer key __id__
    # simple selection by field value
    records = db(name="homer")
    # complex selection by list comprehension
    res = [ r for r in db if 30 > r['age'] >= 18 and r['size'] < 2 ]
    # or generator expression
    for r in (r for r in db if r['name'] in ('homer','marge') ):
    # delete a record or a list of records
    db.delete(one_record)
    db.delete(list_of_records)
    # delete a record by its id
    del db[rec_id]
    # direct access by id
    record = db[rec_id] # the record such that record['__id__'] == rec_id
    # create an index on a field
    db.create_index('age')
    # update
    db.update(record,age=24)
    # add and drop fields
    db.add_field('new_field',default=0)
    db.drop_field('name')
    # save changes on disk
    db.commit()
"""

__version__ = "2.2"

import os
import cPickle

# compatibility with Python 2.3
try:
    set([])
except NameError:
    from sets import Set as set
    
class Index:
    """Class used for indexing a base on a field
    The instance of Index is an attribute the Base instance"""

    def __init__(self,db,field):
        self.db = db # database object (instance of Base)
        self.field = field # field name

    def __iter__(self):
        return iter(self.db.indices[self.field])

    def keys(self):
        return self.db.indices[self.field].keys()

    def __getitem__(self,key):
        """Lookup by key : return the list of records where
        field value is equal to this key, or an empty list"""
        ids = self.db.indices[self.field].get(key,[])
        return [ self.db.records[_id] for _id in ids ]

class Record(dict):

    def __init__(self,db,*args):
        self.db = db
        dict.__init__(self,*args)

    def __setitem__(self,key,value):
        self.db.update_indices([self],{key:value})
        dict.__setitem__(self,key,value)

    def to_dict(self):
        return dict([(k,v) for (k,v) in self.iteritems()])

class Base:

    def __init__(self,basename,protocol=cPickle.HIGHEST_PROTOCOL):
        """protocol as defined in pickle / cPickle
        Defaults to the highest protocol available
        For maximum compatibility use protocol = 0"""
        self.name = basename
        self.protocol = protocol

    def create(self,*fields,**kw):
        """Create a new base with specified field names
        A field can be a string (the field name) or a 2-item tuple
        (field_name, default_value)
        A keyword argument mode can be specified ; it is used if a file
        with the base name already exists
        - if mode = 'open' : open the existing base, ignore the fields
        - if mode = 'override' : erase the existing base and create a
        new one with the specified fields"""
        self.mode = mode = kw.get("mode",None)
        if os.path.exists(self.name):
            if not os.path.isfile(self.name):
                raise IOError,"%s exists and is not a file" %self.name
            elif mode is None:
                raise IOError,"Base %s already exists" %self.name
            elif mode == "open":
                return self.open()
            elif mode == "override":
                os.remove(self.name)
        self._make_fields(fields)
        self.records = {}
        self.next_id = 0
        self.indices = {}
        self.commit()
        return self

    def _make_fields(self,fields):
        self.default = {}
        self.fields = []
        for field in fields:
            if isinstance(field,(list,tuple)):
                self.fields.append(field[0])
                self.default[field[0]] = field[1]
            else:
                self.fields.append(field)

    def create_index(self,*fields):
        """Create an index on the specified field names
        
        An index on a field is a mapping between the values taken by the field
        and the sorted list of the ids of the records whose field is equal to 
        this value
        
        For each indexed field, an attribute of self is created, an instance 
        of the class Index (see above). Its name it the field name, with the
        prefix _ to avoid name conflicts
        """
        reset = False
        for f in fields:
            if not f in self.fields:
                raise NameError,"%s is not a field name" %f
            # initialize the indices
            if self.mode == "open" and f in self.indices:
                continue
            reset = True
            self.indices[f] = {}
            for _id,record in self.records.iteritems():
                self.indices[f].setdefault(record[f],[]).append(_id)
            # create a new attribute of self, used to find the records
            # by this index
            setattr(self,'_'+f,Index(self,f))
        if reset:
            self.commit()

    def delete_index(self,*fields):
        """Delete the index on the specified fields"""
        for f in fields:
            if not f in self.indices:
                raise ValueError,"No index on field %s" %f
        for f in fields:
            del self.indices[f]
        self.commit()

    def open(self):
        """Open an existing database and load its content into memory"""
        # guess protocol
        if self.protocol==0:
            _in = open(self.name) # don't specify binary mode !
        else:
            _in = open(self.name,'rb')
        fields = cPickle.load(_in)
        self._make_fields(fields)
        self.next_id = cPickle.load(_in)
        records = cPickle.load(_in)
        self.records = dict([(_id,Record(self,record))
            for (_id,record) in records.iteritems()])
        self.indices = cPickle.load(_in)
        for f in self.indices.keys():
            setattr(self,'_'+f,Index(self,f))
        _in.close()
        self.mode = "open"
        return self

    def commit(self):
        """Write the database to a file"""
        for record in self.records.values():
            if not hasattr(record,"db"):
                raise TypeError,record.__class__
        out = open(self.name,'wb')
        fields = []
        for field in self.fields:
            if field in self.default:
                fields.append((field,self.default[field]))
            else:
                fields.append(field)
        cPickle.dump(fields,out,self.protocol)
        cPickle.dump(self.next_id,out,self.protocol)
        records = dict([(_id,rec.to_dict()) 
            for (_id,rec) in self.records.iteritems()])
        cPickle.dump(records,out,self.protocol)
        cPickle.dump(self.indices,out,self.protocol)
        out.close()

    def insert(self,*args,**kw):
        """Insert a record in the database
        Parameters can be positional or keyword arguments. If positional
        they must be in the same order as in the create() method
        If some of the fields are missing the value is set to None
        Returns the record identifier
        """
        if args:
            kw = dict([(f,arg) for f,arg in zip(self.fields,args)])
        # initialize all fields to default values
        record = Record(self,[(f,self.default.get(f,None)) 
            for f in self.fields])
        # ignore unknown fields
        kw = dict([(k,v) for (k,v) in kw.iteritems() if k in self.fields])        
        # set keys and values
        for (k,v) in kw.iteritems():
            record[k]=v
        # add the key __id__ : record identifier
        record['__id__'] = self.next_id
        # add the key __version__ : version number
        record['__version__'] = 0
        # create an entry in the dictionary self.records, indexed by __id__
        self.records[self.next_id] = record
        # update index
        for ix in self.indices.keys():
            self.indices[ix].setdefault(record[ix],[]).append(self.next_id)
        # increment the next __id__
        self.next_id += 1
        return record['__id__']

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
        keys = set(self.records.keys())
        # check if the records are in the base
        if not set(_ids).issubset(keys):
            missing = list(set(_ids).difference(keys))
            raise IndexError,'Delete aborted. Records with these ids' \
                ' not found in the base : %s' %str(missing)
        # raise exception if duplicate ids
        for i in range(len(_ids)-1):
            if _ids[i] == _ids[i+1]:
                raise IndexError,"Delete aborted. Duplicate id : %s" %_ids[i]
        deleted = len(removed)
        while removed:
            r = removed.pop()
            _id = r['__id__']
            # remove id from indices
            for indx in self.indices.keys():
                self.indices[indx][r[indx]].remove(_id)
                if not self.indices[indx][r[indx]]:
                    del self.indices[indx][r[indx]]
            # remove record from self.records
            del self.records[_id]
        return deleted

    def update(self,records,**kw):
        """Update one record of a list of records 
        with new keys and values and update indices"""
        # ignore unknown fields
        kw = dict([(k,v) for (k,v) in kw.iteritems() if k in self.fields])
        if isinstance(records,Record):
            records = [ records ]
        # update indices
        self.update_indices(records,kw)
        for record in records:
            # update record values
            record.update(kw)
            # increment version number
            record["__version__"] += 1

    def update_indices(self,records,kw):
        # update indices
        for indx in set(self.indices.keys()) & set (kw.keys()):
            for record in records:
                if record[indx] == kw[indx]:
                    continue
                _id = record["__id__"]
                # remove id for the old value
                self.indices[indx][record[indx]].remove(_id)
                if not self.indices[indx][record[indx]]:
                    del self.indices[indx][record[indx]]
                # insert new value
                self.indices[indx].setdefault(kw[indx],[]).append(_id)

    def add_field(self,field,default=None):
        if field in self.fields + ["__id__","__version__"]:
            raise ValueError,"Field %s already defined" %field
        for r in self:
            r[field] = default
        self.fields.append(field)
        if default is not None:
            self.default[field] = default
        self.commit()
    
    def drop_field(self,field):
        if field in ["__id__","__version__"]:
            raise ValueError,"Can't delete field %s" %field
        self.fields.remove(field)
        for r in self:
            del r[field]
        if field in self.indices:
            del self.indices[field]
        self.commit()

    def __call__(self,**kw):
        """Selection by field values
        db(key=value) returns the list of records where r[key] = value"""
        if not kw:
            return self.records.values() # db() returns all the values
        # indices and non-indices
        keys = kw.keys()
        ixs = set(keys) & set(self.indices.keys())
        no_ix = set(keys) - ixs
        if ixs:
            # fast selection on indices
            ix = ixs.pop()
            res = set(self.indices[ix].get(kw[ix],[]))
            if not res:
                return []
            while ixs:
                ix = ixs.pop()
                res = res & set(self.indices[ix].get(kw[ix],[]))
        else:
            # if no index, initialize result with test on first field
            field = no_ix.pop()
            res = set([r["__id__"] for r in self if r[field] == kw[field] ])
        # selection on non-index fields
        for field in no_ix:
            res = res & set([ _id for _id in res 
                if self.records[_id][field] == kw[field] ])
        return [ self[_id] for _id in res ]
    
    def __getitem__(self,record_id):
        """Direct access by record id"""
        return self.records[record_id]
    
    def __len__(self):
        return len(self.records)

    def __delitem__(self,record_id):
        """Delete by record id"""
        self.delete(self[record_id])
        
    def __iter__(self):
        """Iteration on the records"""
        return self.records.itervalues()

if __name__ == '__main__':
    # test on a 1000 record base
    import random
    import datetime
    names = ['pierre','claire','simon','camille','jean',
                 'florence','marie-anne']
    db = Base('PyDbLite_test',protocol=2)
    db.create(('name',''),('age',10),'size','birth',mode="override")
    for i in range(1000):
        db.insert(name=unicode(random.choice(names)),
             age=random.randint(7,47),size=random.uniform(1.10,1.95),
             birth=datetime.date(1990,10,10))
    db.create_index('age')
    db.commit()
    db.open()

    print 'Record #20 :',db[20]
    print '\nRecords with age=30 :'
    for rec in db._age[30]:
        print '%-10s | %2s | %s' %(rec['name'],rec['age'],round(rec['size'],2))

    print "\nSame with __call__"
    # same with select
    for rec in db(age=30):
        print '%-10s | %2s | %s' %(rec['name'],rec['age'],round(rec['size'],2))
    assert len(db._age[30]) == len(db(age=30))

    # update index when value is changed    
    rec30 = db(age=30)
    if rec30:
        rec = rec30[0]
        rec["age"] = 31
        assert rec in db(age=31)
        assert not rec in db(age=30)

    raw_input()

    recid = db.insert(name=unicode(random.choice(names))) # missing fields
    print db[recid]
    print db.default
    
    print '\nNumber of records with 30 <= age < 33 :',
    print sum([1 for r in db if 33 > r['age'] >= 30])
    
    print db.delete([])

    d = db.delete([r for r in db if 32> r['age'] >= 30 and r['name']==u'pierre'])
    print "\nDeleting %s records with name == 'pierre' and 30 <= age < 32" %d
    print '\nAfter deleting records '
    for rec in db._age[30]:
        print '%-10s | %2s | %s' %(rec['name'],rec['age'],round(rec['size'],2))
    print '\n',sum([1 for r in db]),'records in the database'
    print '\nMake pierre uppercase for age > 27'
    for record in ([r for r in db if r['name']=='pierre' and r['age'] >27]) :
        db.update(record,name=u"Pierre")
    print len([r for r in db if r['name']==u'Pierre']),'Pierre'
    print len([r for r in db if r['name']==u'pierre']),'pierre'
    print len([r for r in db if r['name'] in [u'pierre',u'Pierre']]),'p/Pierre'
    print 'is unicode :',isinstance(db[20]['name'],unicode)
    db.commit()
    db.open()
    print '\nSame operation after commit + open'
    print len([r for r in db if r['name']==u'Pierre']),'Pierre'
    print len([r for r in db if r['name']==u'pierre']),'pierre'
    print len([r for r in db if r['name'] in [u'pierre',u'Pierre']]),'p/Pierre'
    print 'is unicode :',isinstance(db[20]['name'],unicode)
    
    print "\nDeleting record #20"
    del db[20]
    if not 20 in db:
        print "record 20 removed"

    print db[21]
    db.drop_field('name')
    print db[21]
    db.add_field('now',datetime.datetime.now())
    print db[21]
    
    k = db._age.keys()[0]
    print "key",k
    print k in db._age
    db.delete(db._age[k])
    print db._age[k]
    print k in db._age

    db.delete_index("age")
    