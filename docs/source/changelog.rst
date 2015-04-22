Changelog
---------------

3.0.2 (2015-04-18)
~~~~~~~~~~~~~~~~~~~~~~~~

- Fixed bug (#1) in :class:`Base <pydblite.pydblite._Base>` where calling
  :func:`db.create() <pydblite.pydblite._Base.create>` without supplying
  a value for the "mode" parameter with give an error.

3.0.1 (2015-02-23)
~~~~~~~~~~~~~~~~~~~~~~~~

- Fixed bug in :class:`Base <pydblite.pydblite._Base>` where opening
  existing database would fail.

3.0 (2014-09-18)
~~~~~~~~~~~~~~~~~~~~~~~~

Note: Some changes in this release are not backwards compatible with 2.X versions.

- pydblite and sqlite are rewritten to use a common :class:`Filter <pydblite.common.Filter>` object.
- Tests have been improved and standardised in :ref:`unittests-label`.
- Updated :ref:`examples-label`.
- Renamed module and package names to lower case according to :PEP:`8`
- Converted to UNIX line endings and follow :PEP:`8` code style.
- MySQL adapter has been dropped until it can be tested with unit tests.

2.6
~~~~~~~~~~~~~~~~~~~~~~~~

- if db exists, read field names on instance creation
- allow add_field on an instance even if it was not open()
- attribute path is the path of the database in the file system
  (was called "name" in previous versions)
- attribute name is the base name of the database, without the extension
- adapt code to run on Python 2 and Python 3

2.5
~~~~~~~~~~~~~~~~~~~~~~~~

- test is now in folder "test"
- SQLite changes:

  - many changes to support "legacy" SQLite databases

    - no control on types declared in CREATE TABLE or ALTER TABLE
    - no control on value types in INSERT or UPDATE
    - no version number in records

  - add methods to specify a conversion function for fields after a SELECT
  - change names to be closer to SQLite names

    - a class Database to modelise the database
    - a class Table (not Base) for each table in the database

2.4
~~~~~~~~~~~~~~~~~~~~~~~~

- add BSD Licence
- raise exception if unknown fields in insert

2.3
~~~~~~~~~~~~~~~~~~~~~~~~

- introduce syntax (db('name')>'f') & (db('age') == 30)

2.2
~~~~~~~~~~~~~~~~~~~~~~~~

- add __contains__
