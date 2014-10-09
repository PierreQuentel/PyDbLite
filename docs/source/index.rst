.. PyDbLite documentation master file, created by
   sphinx-quickstart on Mon Sep 15 14:19:46 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

:tocdepth: 3

 .. image:: ../../doc/img/banniere.jpg
    :align: center

.. role:: python(code)
    :language: py

.. highlight:: python
   :linenothreshold: 5

PyDbLite
------------------

PyDbLite is:

- a fast, :ref:`pure-Python <pure-python-engine>`, untyped, in-memory database engine, compatible with Python 2.3 and above, using Python syntax to manage data, instead of SQL
- a pythonic interface to SQLite (:ref:`sqlite-adapter`) and MySQL, using the same syntax as the pure-Python engine for most operations (except database connection and table creation because of each database specificities)

To install the package, just download it and install it by running

.. code-block:: bash

   python setup.py install

Supported Python versions: 2.6, 2.7, 3.3, 3.4

.. toctree::
   :maxdepth: 3

   pythonengine
   sqliteengine
   api
   examples


.. toctree::
   :hidden:

   unittests
   benchmarks
   changelog
   license
   doccoverage
   contact


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
