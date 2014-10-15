.. _sqlite-adapter:

SQLite adapter
====================================

.. role:: python(code)
    :language: py

The main difference with the pure-Python module is the syntax to identify a database and a table, and the need to specify field types on base creation

For compliance with SQLite vocabulary, the module defines two classes, :class:`Database <pydblite.sqlite.Database>` and :class:`Table <pydblite.sqlite.Table>`

Database
-----------------------------------

:python:`Database(db_path[,**kw])` : db_path is the database path in the file system. The keyword arguments are the same as for the method :python:`connect()` of the Python built-in module sqlite3

Instances of Database are dictionary-like objects, where keys are the table names and values are instances of the :class:`Table <pydblite.sqlite.Table>` class

- :python:`db["foo"]` returns the instance of the Table class for table "foo"
- :python:`db.keys()` returns the table names
- :python:`if "foo" in db` tests if table "foo" exists in the database
- :python:`del db["foo"]` drops the table "foo"

To create a new table

.. code-block:: python

    table = db.create(table_name, *fields[,mode])

The fields must be 2-element tuples :python:`(field_name, field_type)` where field_type is an SQLite field type

- INTEGER
- REAL
- TEXT
- BLOB

.. code-block:: python

    db.create('test', ('name', 'TEXT'), ('age', 'INTEGER'), ('size', 'REAL'))

If other information needs to be provided, put it in the second argument, using the SQL syntax for SQLite

.. code-block:: python

    db.create('test', ('date', 'BLOB DEFAULT CURRENT_DATE'))

The optional keyword argument :python:`mode` specifies what you want to do if a table of the same name already exists in the database

- :python:`mode="open"` opens the table and ignores the field definition
- :python:`mode="override"` erases the existing table and creates a new one with the field definition
- if :python:`mode` is not specified and the table already exists, an :python:`IOError` is raised

Table
-----------------------------------

For record insertion, updating, deletion and selection the syntax is the same as for the :ref:`pure-Python module <pure-python-engine>`. The SQLite primary key rowid is used like the key :python:`__id__` to identify records

To insert many records at a time,

.. code-block:: python

    table.insert(list_of_values)

will be much faster than

.. code-block:: python

    for values in list_of_values:
        table.insert(values)

Note that you can't use the :python:`drop_field()` method, since dropping fields is not supported by SQLite

Type conversion
~~~~~~~~~~~~~~~~~~~

Conversions between Python types and SQLite field types use the behaviour of the Python SQLite module. :python:`datetime.date`, :python:`datetime.time` and :python:`datetime.datetime` instances are stored as ISO dates/datetimes

Selection methods return dictionaries, with SQLite types converted to Python types like this

+--------------+--------------+
| SQLite type  | Python type  |
+==============+==============+
| NULL         | None         |
+--------------+--------------+
| TEXT         | unicode      |
+--------------+--------------+
| BLOB         | str          |
+--------------+--------------+
| INTEGER      | int          |
+--------------+--------------+
| REAL         | float        |
+--------------+--------------+

If you want fields to be returned as instances of datetime.date, datetime.time or datetime.datetime instances, you can specify it when creating or opening the table, using methods :func:`is_date(field_name) <pydblite.sqlite.Table.is_date>`, :func:`is_time(field_name) <pydblite.sqlite.Table.is_time>` or :func:`is_datetime(field_name) <pydblite.sqlite.Table.is_datetime>`.

.. code-block:: python

    db = Database('test.sqlite')
    table = db['dummy']
    table.is_date('birthday')

cursor and commit
~~~~~~~~~~~~~~~~~~~~~~~

Instances of :class:`Database <pydblite.sqlite.Database>` and :class:`Table <pydblite.sqlite.Table>` have the attribute :attr:`cursor <pydblite.sqlite.Database.cursor>`, the SQLite connections cursor, so you can also execute SQL expressions by

.. code-block:: python

    db.cursor.execute(some_sql)

and get the result by

.. code-block:: python

    results = db.cursor.fetchall()

the method :func:`commit() <pydblite.sqlite.Database.commit>` saves the changes to a database after a transaction

.. code-block:: python

    db.commit()
