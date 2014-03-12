Installation : python setup.py install

Run tests with
python -m unittest -v PyDbLite.tests

Run individual tests like this:
python -m unittest -v PyDbLite.tests.common_tests.SQLiteTestCase
python -m unittest -v PyDbLite.tests.common_tests.SQLiteTestCase.test_filter_or
