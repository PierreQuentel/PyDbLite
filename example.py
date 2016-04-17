# -*- coding: utf-8 -*-
#
# BSD licence
#
# Copyright (c) <2008-2011> Pierre Quentel (pierre.quentel@gmail.com)
# Copyright (c) <2014-2015> Bendik Rønning Opstad <bro.devel@gmail.com>.
#


def sqlite():
    from pydblite.sqlite import Database, Table
    # connect to SQLite database "test"
    db = Database(":memory:")
    # pass the table name and database path as arguments to Table creation
    table = Table('dummy', db)
    # create new base with field names
    table.create(('name', 'TEXT'), ('age', 'INTEGER'), ('size', 'REAL'))
    # existing base
    table.open()
    # insert new record
    table.insert(name='homer', age=23, size=1.84)
    table.insert(name='marge', age=36, size=1.94)
    rec_id = table.insert(name='Lisa', age=13, size=1.24)

    # records are dictionaries with a unique integer key __id__
    # selection by list comprehension
    res = [r for r in table if 30 > r['age'] >= 18 and r['size'] < 2]
    print("res:", res)
    # or generator expression
    for r in (r for r in table if r['name'] in ('homer', 'marge')):
        pass
    # simple selection (equality test)
    records = table(age=23)

    # delete a record by its id
    del table[rec_id]

    rec_id = records[0]['__id__']

    # direct access by id
    record = table[rec_id]  # the record such that record['__id__'] == rec_id
    # update
    table.update(record, age=24)
    # add a field
    table.add_field('new_field')  # Defaults to type 'TEXT'
    # save changes on disk
    table.commit()


def pydblite():
    from pydblite.pydblite import Base
    db = Base('dummy', save_to_file=False)
    # create new base with field names
    db.create('name', 'age', 'size')
    # insert new record
    db.insert(name='homer', age=23, size=1.84)
    # records are dictionaries with a unique integer key __id__
    # simple selection by field value
    records = db(name="homer")
    # complex selection by list comprehension
    res = [r for r in db if 30 > r['age'] >= 18 and r['size'] < 2]
    print("res:", res)
    # delete a record or a list of records
    r = records[0]
    db.delete(r)

    list_of_records = []
    r = db.insert(name='homer', age=23, size=1.84)
    list_of_records.append(db[r])
    r = db.insert(name='marge', age=36, size=1.94)
    list_of_records.append(db[r])

    # or generator expression
    for r in (r for r in db if r['name'] in ('homer', 'marge')):
        # print "record:", r
        pass

    db.delete(list_of_records)

    rec_id = db.insert(name='Bart', age=15, size=1.34)
    record = db[rec_id]  # the record such that record['__id__'] == rec_id

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
    db.add_field('new_field', default=0)
    db.drop_field('name')
    # save changes on disk
    db.commit()

if __name__ == "__main__":
    sqlite()
    pydblite()
