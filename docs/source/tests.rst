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
