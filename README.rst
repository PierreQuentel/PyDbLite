PyDbLite
=============

PyDbLite is an in-memory database management library, with selection
by list comprehension or generator expression

One can choose between native python or SQLite backend.

Authors:
     - Pierre Quentel (pierre.quentel@gmail.com)
     - Bendik Rønning Opstad (bro.devlopment@gmail.com)

Read the documentation: |docs|

Build status: |build-status|


Changelog: `docs/source/changelog.rst <docs/source/changelog.rst>`_

Tests
---------------

Run tests with

.. code-block:: bash

    python -m unittest -v tests

Run individual tests like this:

.. code-block:: bash

    python -m unittest -v tests.test_pydblite.PyDbLiteTestCase
    python -m unittest -v tests.test_pydblite_sqlite.SQLiteTestCase
    python -m unittest -v tests.test_pydblite_sqlite.SQLiteTestCase.test_filter_or

The tests will not pass for Python 3.0-3.2 due to the unicode literal being invalid syntax

Run tests for python 2.7 and 3.4, pep8 verification and documentation with

.. code-block:: bash

    tox

.. |build-status| image:: https://api.travis-ci.org/bendikro/PyDbLite.svg
    :target: https://travis-ci.org/bendikro/PyDbLite

.. |docs| image:: https://readthedocs.org/projects/pydblite/badge/?version=latest
    :target: https://readthedocs.org/projects/pydblite/?badge=latest
    :alt: Documentation Status
