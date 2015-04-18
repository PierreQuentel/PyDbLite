.. _pure-python-engine:

Pure-Python engine
====================================

.. role:: python(code)
    :language: py

The pure-Python engine consists of one module, pydblite.py. To use it, import the class :class:`Base <pydblite.pydblite._Base>` from this module:

.. code-block:: python

    from pydblite import Base

Create or open a database
----------------------------------------

Create a database instance, passing it a path in the file system

.. code-block:: python

    db = Base('test.pdl')

For a new database, define the field names

.. code-block:: python

    db.create('name', 'age', 'size')

You don't have to define the field types. Any value will be accepted as long as it can be serialized by the cPickle module:

- strings
- Unicode strings
- integers
- floats
- dates and datetimes (instances of the date and datetime classes in the datetime module)
- user-defined classes


:func:`db.exists() <pydblite.pydblite._Base.exists>` indicates if the base exists.

if the base exists, open it

.. code-block:: python

    if db.exists():
        db.open()

You can pass a parameter "mode" to the :func:`create() <pydblite.pydblite._Base.create>` method, to specify what you want to do if the base already exists in the file system

-  mode = "open" : :python:`db.create('name', 'age', 'size', mode="open")` opens the database and ignores the field definition
-  mode = "override" : :python:`db.create('name', 'age', 'size', mode="override")` erases the existing base and creates a new one with the field definition
-  if :python:`mode` is not specified and the base already exists, an :python:`IOError` is raised

Insert, update, delete a record
----------------------------------------

insert a new record
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

by keywords
################

.. code-block:: python

    db.insert(name='homer', age=23, size=1.84)

If some fields are missing, they are initialized with the value None

by positional arguments
##############################

.. code-block:: python

    db.insert('homer', 23, 1.84)

The arguments must be provided in the same order as in the :python:`create()` method

save the changes on disk
##############################

.. code-block:: python

    db.commit()

If you don't commit the changes, the insertion, deletion and update operations will not be saved on disk. As long as changes are not commited, use :python:`open()` to restore the values as they are currently on disk (this is equivalent to rollback in transactional databases)

delete a record
##############################

.. code-block:: python

    db.delete(record)

or, if you know the record identifier

.. code-block:: python

    del db[rec_id]

to delete a list of records
##############################

.. code-block:: python

    db.delete(list_of_records)

where list_of_records can be any iterable (list, tuple, set, etc) yielding records

to update a record
##############################

.. code-block:: python

    db.update(record, age=24)


- besides the fields passed to the :python:`create()` method, an internal field called :python:`__id__` is added. It is an integer which is guaranteed to be unique and unchanged for each record in the base, so that it can be used as the record identifier
- another internal field called :python:`__version__` is also managed by the database engine. It is an integer which is set to 0 when the record is created, then incremented by 1 each time the record is updated. This is used to detect concurrency control, for instance in a web application where 2 users select the same record and want to update it at the same time


Selection
----------------------------------------

The instance of Base is a Python iterator

to iterate on all the records
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    for r in db:
        do_something_with(r)

Direct access
~~~~~~~~~~~~~~~~~~~~~~~

A record can be accessed by its identifier

.. code-block:: python

    record = db[rec_id]

returns the record such that :python:`record['__id__'] == rec_id`

Simple selections
~~~~~~~~~~~~~~~~~~~~~~~

- :python:`db(key1=val1, key2=val2)` returns the list of records where the keys take the given values
- :python:`db(key) >= val` returns an iterator on all records where the value of the field key is greater than or equal to val.

Example

.. code-block:: python

    for rec in (db("age") > 30):
         print rec["name"]

such "rich comparison" operations can be combined with & (AND) and | (OR)

.. code-block:: python

    for rec in (db("age") > 30) & (db("country") == "France"):
        print rec["name"]

List comprehension
----------------------------------------

The selection of records can use Python list comprehension syntax

.. code-block:: python

    recs = [r for r in db if 30 > r['age'] >= 18 and r['size'] < 2]

Returns the records in the base where the age is between 18 and 30, and size is below 2 meters. The record is a dictionary, where the key is the field name and value is the field value

Python generator expression syntax can also be used

.. code-block:: python

    for r in (r for r in db if r['name'] in ('homer', 'marge')):
        do_something_with(r)

iterates on the records where the name is one of 'homer' or 'marge'

Index
----------------------------------------

To speed up selections, an index can be created on a field using :func:`create_index('field') <pydblite.pydblite._Base.create_index>`

.. code-block:: python

    db.create_index('age')

When an index is created, the database instance has an attribute (here :python:`_age` : note the heading underscore, to avoid name conflicts with internal names). This attribute is a dictionary-like object, where keys are the values taken by the field, and values are the records whose field values are egal to the key :

:python:`records = db._age[23]` returns the list of records with :python:`age == 23`

If no record has this value, lookup by this value returns an empty list

The index supports iteration on the field values, and the :python:`keys()` method returns all existing values for the field

Other attributes and methods
----------------------------------------

- :func:`add_field('new_field'[,default=v]) <pydblite.pydblite._Base.add_field>`: adds a new field to an existing base. :python:`default` is an optional default value ; set to :python:`None` if not specified
- :func:`drop_field('field') <pydblite.pydblite._Base.drop_field>`: drops an existing field
- :attr:`db.path <pydblite.pydblite._Base.path>`: the path of the database in the file system
- :attr:`db.name <pydblite.pydblite._Base.name>`: the database name : the basename of the path, stripped of its extension
- :attr:`db.fields <pydblite.pydblite._Base.fields>`: the list of the fields (does not include the internal fields :python:`__id__` and :python:`__version__`)
- :python:`len(db)` : number of records in the base


