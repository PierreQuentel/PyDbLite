"""PyDbLite.py

BSD licence

Author : Pierre Quentel (pierre.quentel@gmail.com)

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

version 2.2 : add __contains__

version 2.3 : introduce syntax (db('name')>'f') & (db('age') == 30)

version 2.4 :'
- add BSD Licence
- raise exception if unknown fields in insert

version 2.5 :
- test is now in folder test

version 2.6
- if db exists, read field names on instance creation
- allow add_field on an instance even if it was not open()
- attribute path is the path of the database in the file system
  (was called "name" in previous versions)
- attribute name is the base name of the database, without the extension
- adapt code to run on Python 2 and Python 3
"""

version = "2.6"

import os
import bisect
import sys

try:
    import cPickle as pickle
except:
    import pickle

# compatibility with Python 2.3
try:
    set([])
except NameError:
    from sets import Set as set

from . import common
from .common import Expression, ExpressionGroup, Filter

from itertools import groupby
import operator


class PyDbExpression(Expression):

    def __init__(self, **kwargs):
        super(PyDbExpression, self).__init__(**kwargs)
        self.operations = {'AND': 'AND', 'OR': 'OR',
                           'LIKE': operator.contains,
                           'GLOB': operator.contains,
                           "IN": operator.contains,
                           '=': operator.eq, '!=': operator.ne, '<': operator.lt,
                           '<=': operator.le, '>': operator.gt, '>=': operator.ge}

    def apply(self, records):
        operation = self.operations[self.operator]
        if self.operator == Filter.operations.LIKE:
            records = [r for r in records if operation(r[self.key].lower(), self.value.lower())]
        else:
            records = [r for r in records if operation(r[self.key], self.value)]
        return records


class PyDbExpressionGroup(ExpressionGroup):

    def apply_filter(self, records):
        if self.is_dummy():
            return ""
        if self.expression:
            return self.expression.apply(records.values())
        else:
            # Parent of two expressions
            records1 = self.exp_group1.apply_filter(records)
            records2 = self.exp_group2.apply_filter(records)
            if self.exp_operator == Filter.operations.AND:
                ids1 = dict([(id(r), r) for r in records1])
                ids2 = dict([(id(r), r) for r in records2])
                ids = set(ids1.keys()) & set(ids2.keys())
                records = [ids1[_id] for _id in ids]
            else:
                ids = dict([(id(r), r) for r in records1])
                ids.update(dict([(id(r), r) for r in records2]))
                records = ids.values()
            return records


common.ExpressionGroup = PyDbExpressionGroup
common.Expression = PyDbExpression


class Index(object):
    """Class used for indexing a base on a field
    The instance of Index is an attribute the Base instance"""

    def __init__(self, db, field):
        self.db = db  # database object (instance of Base)
        self.field = field  # field name

    def __iter__(self):
        return iter(self.db.indices[self.field])

    def keys(self):
        return self.db.indices[self.field].keys()

    def __getitem__(self, key):
        """Lookup by key : return the list of records where
        field value is equal to this key, or an empty list"""
        ids = self.db.indices[self.field].get(key, [])
        return [self.db.records[_id] for _id in ids]


class _Base(object):

    def __init__(self, path, protocol=pickle.HIGHEST_PROTOCOL, save_to_file=True):
        """protocol as defined in pickle / pickle
        Defaults to the highest protocol available
        For maximum compatibility use protocol = 0"""
        self.path = path
        self.name = os.path.splitext(os.path.basename(path))[0]
        self.protocol = protocol
        self.save_to_file = save_to_file
        # if base exists, get field names
        if save_to_file and self.exists():
            if protocol == 0:
                _in = open(self.path)  # don't specify binary mode !
            else:
                _in = open(self.path, 'rb')
            self.fields = pickle.load(_in)

    def exists(self):
        return os.path.exists(self.path)

    def create(self, *fields, **kw):
        """
        Create a new base with specified field names
        A keyword argument mode can be specified ; it is used if a file
        with the base name already exists
        - if mode = 'open' : open the existing base, ignore the fields
        - if mode = 'override' : erase the existing base and create a
        new one with the specified fields

        Args:
            fields (str): The fields names to create.
            mode (str): the mode used when creating the database.

        Returns:
            Returns the database (self).
        """
        self.mode = mode = kw.get("mode", None)
        if os.path.exists(self.path):
            if not os.path.isfile(self.path):
                raise IOError("%s exists and is not a file" % self.path)
            elif mode is None:
                raise IOError("Base %s already exists" % self.path)
            elif mode == "open":
                return self.open()
            elif mode == "override":
                os.remove(self.path)

        self.fields = []
        self.field_values = {}
        for field in fields:
            if type(field) is dict:
                self.fields.append(field["name"])
                self.field_values[field["name"]] = field.get("default", None)
            else:
                self.fields.append(field)
                self.field_values[field] = None

        self.records = {}
        self.next_id = 0
        self.indices = {}
        self.commit()
        return self

    def create_index(self, *fields):
        """
        Create an index on the specified field names

        An index on a field is a mapping between the values taken by the field
        and the sorted list of the ids of the records whose field is equal to
        this value

        For each indexed field, an attribute of self is created, an instance
        of the class Index (see above). Its name it the field name, with the
        prefix _ to avoid name conflicts

        Args:
            *fields (str): the field(s) to index
        """
        reset = False
        for f in fields:
            if not f in self.fields:
                raise NameError("%s is not a field name %s" % (f, self.fields))
            # initialize the indices
            if self.mode == "open" and f in self.indices:
                continue
            reset = True
            self.indices[f] = {}
            for _id, record in self.records.items():
                # use bisect to quickly insert the id in the list
                bisect.insort(self.indices[f].setdefault(record[f], []), _id)
            # create a new attribute of self, used to find the records
            # by this index
            setattr(self, '_' + f, Index(self, f))
        if reset:
            self.commit()

    def delete_index(self, *fields):
        """Delete the index on the specified fields"""
        for f in fields:
            if not f in self.indices:
                raise ValueError("No index on field %s" % f)
        for f in fields:
            del self.indices[f]
        self.commit()

    def open(self):
        """Open an existing database and load its content into memory"""
        # guess protocol
        if self.protocol == 0:
            _in = open(self.path)  # don't specify binary mode !
        else:
            _in = open(self.path, 'rb')
        self.fields = pickle.load(_in)
        self.next_id = pickle.load(_in)
        self.records = pickle.load(_in)
        self.indices = pickle.load(_in)
        for f in self.indices.keys():
            setattr(self, '_' + f, Index(self, f))
        _in.close()
        self.mode = "open"
        return self

    def commit(self):
        """Write the database to a file"""
        if not self.save_to_file:
            return
        out = open(self.path, 'wb')
        pickle.dump(self.fields, out, self.protocol)
        pickle.dump(self.next_id, out, self.protocol)
        pickle.dump(self.records, out, self.protocol)
        pickle.dump(self.indices, out, self.protocol)
        out.close()

    def insert(self, *args, **kw):
        """
        Insert one or more records in the database.

        Parameters can be positional or keyword arguments. If positional
        they must be in the same order as in the create() method
        If some of the fields are missing the value is set to None

        Args:
            args (the values to insert, or a list of values): The record(s) to delete.
            kw (dict): The field/values to insert

        Returns:
            Returns the record identifier if inserting one item, else None.
        """
        if args:
            if isinstance(args[0], (list, tuple)):
                inserted = []
                for e in args[0]:
                    if type(e) is dict:
                        inserted.append(self.insert(**e))
                    else:
                        inserted.append(self.insert(*e))
                return None
            kw = dict([(f, arg) for f, arg in zip(self.fields, args)])
        # initialize all fields to None
        import copy
        record = copy.deepcopy(self.field_values)
        # raise exception if unknown field
        for key in kw:
            if not key in self.fields:
                raise NameError("Invalid field name : %s" % key)
        # set keys and values
        for (k, v) in kw.items():
            record[k] = v
        # add the key __id__ : record identifier
        record['__id__'] = self.next_id
        # add the key __version__ : version number
        record['__version__'] = 0
        # create an entry in the dictionary self.records, indexed by __id__
        self.records[self.next_id] = record
        # update index
        for ix in self.indices.keys():
            bisect.insort(self.indices[ix].setdefault(record[ix], []), self.next_id)
        # increment the next __id__
        self.next_id += 1
        return record['__id__']

    def delete(self, remove):
        """
        Remove a single record, or the records in an iterable

        Before starting deletion, test if all records are in the base
        and don't have twice the same __id__

        Args:
            remove (record or list of records): The record(s) to delete.

        Returns:
            Return the number of deleted items
        """
        if isinstance(remove, dict):
            remove = [remove]
        else:
            # convert iterable into a list (to be able to sort it)
            remove = [r for r in remove]
        if not remove:
            return 0
        _ids = [r['__id__'] for r in remove]
        _ids.sort()
        keys = set(self.records.keys())
        # check if the records are in the base
        if not set(_ids).issubset(keys):
            missing = list(set(_ids).difference(keys))
            raise IndexError('Delete aborted. Records with these ids'
                             ' not found in the base : %s' % str(missing))
        # raise exception if duplicate ids
        for i in range(len(_ids)-1):
            if _ids[i] == _ids[i+1]:
                raise IndexError("Delete aborted. Duplicate id : %s" % _ids[i])
        deleted = len(remove)
        while remove:
            r = remove.pop()
            _id = r['__id__']
            # remove id from indices
            for indx in self.indices.keys():
                pos = bisect.bisect(self.indices[indx][r[indx]], _id)-1
                del self.indices[indx][r[indx]][pos]
                if not self.indices[indx][r[indx]]:
                    del self.indices[indx][r[indx]]
            # remove record from self.records
            del self.records[_id]
        return deleted

    def update(self, records, **kw):
        """
        Update one record or a list of records
        with new keys and values and update indices

        Args:
            records (record or list of records): The record(s) to update.
        """
        # ignore unknown fields
        kw = dict([(k, v) for (k, v) in kw.items() if k in self.fields])
        if isinstance(records, dict):
            records = [records]
        # update indices
        for indx in set(self.indices.keys()) & set(kw.keys()):
            for record in records:
                if record[indx] == kw[indx]:
                    continue
                _id = record["__id__"]
                # remove id for the old value
                old_pos = bisect.bisect(self.indices[indx][record[indx]], _id)-1
                del self.indices[indx][record[indx]][old_pos]
                if not self.indices[indx][record[indx]]:
                    del self.indices[indx][record[indx]]
                # insert new value
                bisect.insort(self.indices[indx].setdefault(kw[indx], []), _id)
        for record in records:
            # update record values
            record.update(kw)
            # increment version number
            record["__version__"] += 1

    def add_field(self, field, column_type="ignored", default=None):
        if field in self.fields + ["__id__", "__version__"]:
            raise ValueError("Field %s already defined" % field)
        if not hasattr(self, 'records'):  # base not open yet
            self.open()
        for r in self:
            r[field] = default
        self.fields.append(field)
        self.field_values[field] = default
        self.commit()

    def drop_field(self, field):
        if field in ["__id__", "__version__"]:
            raise ValueError("Can't delete field %s" % field)
        self.fields.remove(field)
        for r in self:
            del r[field]
        if field in self.indices:
            del self.indices[field]
        self.commit()

    def __call__(self, *args, **kw):
        """Selection by field values

        db(key=value) returns the list of records where r[key] = value

        Args:
            args (list): A field to filter on.
            kw (dict): pairs of field and value to filter on.

        Returns:
            When args supplied, return a Filter object that filters on the specified field.
            When kw supplied, return all the records where field values matches the
            key/values in kw.
        """
        if args and kw:
            raise SyntaxError("Can't specify positional AND keyword arguments")

        if args:
            if len(args) > 1:
                raise SyntaxError("Only one field can be specified")
            elif (type(args[0]) is PyDbExpressionGroup or type(args[0]) is Filter):
                return args[0].apply_filter(self.records)
            elif args[0] not in self.fields:
                raise ValueError("%s is not a field" % args[0])
            else:
                return Filter(self, args[0])
        if not kw:
            return self.records.values()  # db() returns all the values

        # indices and non-indices
        keys = kw.keys()
        ixs = set(keys) & set(self.indices.keys())
        no_ix = set(keys) - ixs
        if ixs:
            # fast selection on indices
            ix = ixs.pop()
            res = set(self.indices[ix].get(kw[ix], []))
            if not res:
                return []
            while ixs:
                ix = ixs.pop()
                res = res & set(self.indices[ix].get(kw[ix], []))
        else:
            # if no index, initialize result with test on first field
            field = no_ix.pop()
            res = set([r["__id__"] for r in self if r[field] == kw[field]])
        # selection on non-index fields
        for field in no_ix:
            res = res & set([_id for _id in res if self.records[_id][field] == kw[field]])
        return [self[_id] for _id in res]

    def __getitem__(self, key):
        # direct access by record id
        return self.records[key]

    def _len(self, db_filter=None):
        if db_filter is not None:
            if not type(db_filter) is PyDbExpressionGroup:
                raise ValueError("Filter argument is not of type 'PyDbExpressionGroup': %s" % type(db_filter))
            return len(db_filter.apply_filter(self.records))
        return len(self.records)

    def __len__(self):
        return self._len()

    def __delitem__(self, record_id):
        """Delete by record id"""
        self.delete(self[record_id])

    def __contains__(self, record_id):
        return record_id in self.records

    def group_by(self, column, torrents_filter):
        gropus = [(k, len(list(g))) for k, g in groupby(torrents_filter, key=lambda x: x[column])]
        result = {}
        for column, count in gropus:
            result[column] = result.get(column, 0) + count
        return [(c, result[c]) for c in result]

    def filter(self, key=None):
        return Filter(self, key)

    def get_group_count(self, group_by_field, db_filter=None):
        if db_filter is None:
            db_filter = self.filter()

        gropus = [(k, len(list(g))) for k, g in groupby(db_filter, key=lambda x: x[group_by_field])]
        groups_dict = {}
        for group, count in gropus:
            groups_dict[group] = groups_dict.get(group, 0) + count
        return [(k, groups_dict[k]) for k in groups_dict]

    def get_unique_ids(self, unique_id, db_filter=None):
        if not db_filter is None:
            records = self(db_filter)
        else:
            records = self()
        return set([row[unique_id] for row in records])

    def get_indices(self):
        return list(self.indices)


class _Base_Py2(_Base):

    def __iter__(self):
        """Iteration on the records"""
        return iter(self.records.itervalues())


class _Base_Py3(_Base):

    def __iter__(self):
        """Iteration on the records"""
        return iter(self.records.values())

import sys
if sys.version_info[0] == 2:
    Base = _Base_Py2
else:
    Base = _Base_Py3


if __name__ == '__main__':
    from PyDbLite import Base
    db = Base('dummy', save_to_file=False)
    # create new base with field names
    db.create('name', 'age', 'size')
    # insert new record
    db.insert(name='homer', age=23, size=1.84)
    # records are dictionaries with a unique integer key __id__
    # simple selection by field value
    records = db(name="homer")
    # complex selection by list comprehension
    res = [ r for r in db if 30 > r['age'] >= 18 and r['size'] < 2 ]
    # delete a record or a list of records
    r = records[0]
    db.delete(r)

    list_of_records = []
    r = db.insert(name='homer', age=23, size=1.84)
    list_of_records.append(db[r])
    r = db.insert(name='marge', age=36, size=1.94)
    list_of_records.append(db[r])

    # or generator expression
    for r in (r for r in db if r['name'] in ('homer','marge') ):
        #print "record:", r
        pass

    db.delete(list_of_records)

    rec_id = db.insert(name='Bart', age=15, size=1.34)
    record = db[rec_id] # the record such that record['__id__'] == rec_id

    # delete a record by its id
    del db[rec_id]

    # create an index on a field
    db.create_index('age')
    # update
    rec_id = db.insert(name='Lisa', age=13, size=1.24)

    # direct access by id
    record = db[rec_id]

    db.update(record, age=24)
    # add and drop fields
    db.add_field('new_field',default=0)
    db.drop_field('name')
    # save changes on disk
    db.commit()
