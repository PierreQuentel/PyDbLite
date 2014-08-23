PyDbLite is an in-memory database management library, with selection
by list comprehension or generator expression

One can choose between native python or SQLite backend.

Authors : Pierre Quentel (pierre.quentel@gmail.com)
        : bendikro (bro.devlopment@gmail.com)

Fields are untyped : they can store anything that can be pickled.
Selected records are returned as dictionaries. Each record is
identified by a unique id and has a version number incremented
at every record update, to detect concurrent access

version 2.2 : add __contains__

version 2.3 : introduce syntax (db('name')>'f') & (db('age') == 30)

version 2.4 :'
- add BSD Licence
- raise exception if unknown fields in insert

version 2.5 :
- test is now in folder test
- SQLite changes:
  - many changes to support "legacy" SQLite databases :
      . no control on types declared in CREATE TABLE or ALTER TABLE
      . no control on value types in INSERT or UPDATE
      . no version number in records
  - add methods to specify a conversion function for fields after a SELECT
  - change names to be closer to SQLite names :
      . a class Database to modelise the database
      . a class Table (not Base) for each table in the database
  - test is now in folder "test"

version 2.6
- if db exists, read field names on instance creation
- allow add_field on an instance even if it was not open()
- attribute path is the path of the database in the file system
  (was called "name" in previous versions)
- attribute name is the base name of the database, without the extension
- adapt code to run on Python 2 and Python 3

version 3.0
 - PyDbLite and SQLite are rewritten to use a common Filter object.
 - Tests have been improved
 - Updated examples
 - Uses UNIX line endings and follow pep8 code style


Installation : python setup.py install

Run tests with
python -m unittest -v PyDbLite.tests

Run individual tests like this:
python -m unittest -v PyDbLite.tests.test_pydblite.PyDbLiteTestCase
python -m unittest -v PyDbLite.tests.test_pydblite_sqlite.SQLiteTestCase
python -m unittest -v PyDbLite.tests.test_pydblite_sqlite.SQLiteTestCase.test_filter_or

The tests will not pass for Python 3.0-3.2 due to the unicode literal being invalid syntax
