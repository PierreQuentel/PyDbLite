Benchmarks
~~~~~~~~~~~~~~~

PyDbLite has been measured by the time taken by various operations for 3 pure-Python database modules (PyDbLite, buzhug and Gadfly) and compared them with SQLite.

The tests are those described on the SQLite comparisons pages, which compares performance of SQLite to that of MySQL and PostGreSQL


insert
=============================
create the base and insert n elements (n= 1000, 25,000 or 100,000) in it

The database has 3 fields:

- a (integer, from 1 to n)
- b (random integer between 1 and 100000)
- c (a string, value = 'fifty nine' if b=59)

For PyDbLite, gadfly and SQLite two options are possible : with an index on field a, or without index

The values of a, b, c are stored in a list recs

SQL statements
----------------------

.. code-block:: python

    cursor.execute("CREATE TABLE t1(a INTEGER, b INTEGER, c VARCHAR(100))")
    if make_index:
        cursor.execute("CREATE INDEX i3 ON t1(a)")
    for a, b, c in recs:
        cursor.execute("INSERT INTO t1 VALUES(%s,%s,'%s')" %(a, b, c))
    conn.commit()

PyDbLite code
----------------------

.. code-block:: python

    db = PyDbLite.Base(name).create('a','b','c')
    if index:
        db.create_index('a')
    for a,b,c in recs:
       db.insert(a=a,b=b,c=c)
    db.commit()

buzhug code
----------------------

.. code-block:: python

    db=Base('t1').create(('a', int), ('b', int), ('c', str))
    for rec in recs:
        db.insert(*rec)
    db.commit()

gadfly code
----------------------

.. code-block:: python

    conn = gadfly.gadfly()
    conn.startup(folder_name,folder_name)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE t1(a INTEGER, b INTEGER, c VARCHAR(100))")
    if make_index:
        cursor.execute("CREATE INDEX i3 ON t1(a)")
    insertstat = "INSERT INTO t1 VALUES(?,?,?)"
    for a, b, c in recs:
        cursor.execute(insertstat,(a, b, c))
    conn.commit()



select1
=============================
100 selections to count the number of records and the average of field b for values of b between 10*n and 10*n + 1000 for n = 1 to 100

SQL statements
----------------------

.. code-block:: python

    for i in range(100):
        sql = 'SELECT count(*), avg(b) FROM t1 WHERE b>=%s AND b<%s' % (100 * i, 1000 + 100 * i)
        cursor.execute(sql)
        nb,avg = cursor.fetchall()[0]

buzhug code
----------------------

.. code-block:: python

    for i in range(100):
        recs = db.select(['b'], b=[100 * i, 999 + 100 * i])
        nb = len(recs)
        if nb:
            avg = sum([r.b for r in recs]) / nb


select2
=============================
100 selections to count the number of records and the average of field b for values of c with the string 'one', 'two', ...,'ninety nine' inside. It uses the keyword LIKE for SQL database (I couldn't do the test for Gadfly which doesn't support LIKE) ; for buzhug I use regular expressions. The strings for each number between 0 and 99 are stored in the list num_strings

SQL statements
----------------------

.. code-block:: python

    for num_string in num_strings:
        sql = "SELECT count(*), avg(b) FROM t1 WHERE c LIKE '%%%s%%'" %num_string
        cursor.execute(sql)
        nb,avg = cursor.fetchall()[0]

buzhug code
----------------------

.. code-block:: python

    for num_string in num_strings:
        pattern = re.compile(".*"+num_string+".*")
        recs = db.select(['b'], 'p.match(c)', p=pattern)
        nb = len(recs)
        if nb:
            avg = sum([r.b for r in recs]) / nb


delete1
=============================
delete all the records where the field c contains the string 'fifty'. There again I couldn't do the test for gadfly


SQL statements
----------------------

.. code-block:: python

    sql = "DELETE FROM t1 WHERE c LIKE '%fifty%';"
    cursor.execute(sql)
    conn.commit()

buzhug code
----------------------

.. code-block:: python

    db.delete(db.select(['__id__'], 'p.match(c)', p=re.compile('.*fifty.*')))


delete2
=============================
delete all the records for which the field a is > 10 and < 20000

SQL statements
----------------------

.. code-block:: python

    sql="DELETE FROM t1 WHERE a > 10 AND a < 20000;"
    cursor.execute(sql)
    conn.commit()

buzhug code
----------------------

.. code-block:: python

    db.delete(db.select(['__id__'], 'x < a < y', x=10, y=20000))

update1
=============================
1000 updates, multiply b by 2 for records where 10*n <= a < 10 * (n + 1) for n = 0 to 999

SQL statements
----------------------

.. code-block:: python

    for i in range(100):
        sql="UPDATE t1 SET b = b * 2 WHERE a>=%s AND a<%s;" % (10 * i, 10 * (i + 1))
        cursor.execute(sql)
    conn.commit()

buzhug code
----------------------

.. code-block:: python

    for i in range(100):
        for r in db.select(a=[10 * i, 10 * i + 9]):
            db.update(r, b=r.b * 2)

update2
=============================
1000 updates to set c to a random value where a = 1 to 1000 New values of field c are stored in a list new_c

SQL statements
----------------------

.. code-block:: python

    for i in range(0, 1000):
        sql="UPDATE t1 SET c='%s' WHERE a=%s" % (new_c[i], i)
        cursor.execute(sql)
    conn.commit()

buzhug code
----------------------

.. code-block:: python

    recs = db.select_for_update(['a','c'], a=[1,999])
    for r in recs:
        db.update(r, c=new_c[r.a])

The tests were made on a Windows XP machine, with Python 2.5 (except gadfly : using the compile kjbuckets.pyd requires Python 2.2)

Versions : PyDbLite 2.5, buzhug 1.6, gadfly 1.0.0, SQLite 3.0 embedded in Python 2.5
Results

Here are the results

::

    1000 records

                     PyDbLite              sqlite           gadfly         buzhug
               no index   index      no index   index   no index  index

    size (kO)    79       91            57        69      60                154

    create     0.04       0.03        1.02      0.77    0.71      2.15     0.29
    select1    0.06       0.07        0.09      0.09    1.50      1.49     0.21
    select2    0.04       0.04        0.16      0.16    -         -        0.51
    delete1    0.01       0.02        0.49      0.50    -         -        0.04
    delete2    0.08       0.01        0.56      0.26    0.04      0.05     0.17
    update1    0.07       0.07        0.52      0.37    1.91      1.91     0.49
    update2    0.20       0.03        0.99      0.45    7.72      0.54     0.72

    25,000 records

                     PyDbLite              sqlite           gadfly         buzhug
               no index     index    no index   index   no index  index

    size         2021       2339        1385    1668      2948             2272

    create       0.73       1.28        2.25    2.20    117.04             7.04
    select1      2.31       2.72        2.69    2.67    153.05             3.68
    select2      1.79       1.71        4.53    4.48    -                 12.33
    delete1      0.40       0.89        1.88    0.98    -          (1)     0.84
    delete2      0.22       0.35        0.82    0.69      1.78             2.88
    update1      2.85       3.55        2.65    0.45    183.06             1.23
    update2     18.90       0.96       10.93    0.47    218.30             0.81

    100,000 records

                     PyDbLite              sqlite       buzhug
               no index     index    no index   index

    size       8290       9694        5656      6938     8881

    create     4.07       7.94        5.54      7.06    28.23
    select1    9.27      13.73        9.86      9.99    14.72
    select2    7.49       8.00       16.86     16.64    51.46
    delete1    2.97       4.10        2.58      3.58     3.48
    delete2    3.00       4.23        0.98      1.41     3.31
    update1   13.72      15.80        9.22      0.99     1.87
    update2   24.83       5.95       69.61      1.21     0.93


    (1) not tested with index, creation time is +INF

Conclusions
PyDblite is as fast, and even faster than SQLite for small databases. It is faster than gadfly in all cases. buzhug is faster on most operations when size grows
