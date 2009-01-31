def stringToDate(fmt="%Y-%m-%d"):
    """returns a function to convert a string to a datetime.date instance
    using the formatting string fmt as in time.strftime"""
    import time
    import datetime
    def conv_func(s):
        return datetime.date(*time.strptime(s,fmt)[:3])
    return conv_func

def toCsv(src,dest,dialect='excel'):
    """Convert a PyDbLite base to a CSV file
    src is the PyDbLite.Base instance
    dest is the file-like object for the CSV output
    dialect is the same as in csv module"""
    import csv
    fieldnames = ["__id__","__version__"]+src.fields
    w = csv.DictWriter(dest,fieldnames,dialect)
    first = dict([(f,f) for f in fieldnames])
    w.writerow(first) # first row has the field names
    for r in src:
        if not "__version__" in r:
            r["__version__"] = 0
        w.writerow(r)
    dest.close()

def fromCsv(src,dest,fieldnames=None,fieldtypes=None,dialect='excel'):
    """Convert a CSV file to a PyDbLite base
    src is the file object from which csv values are read
    dest is the name of the PyDbLite base
    If fieldnames is not set, the CSV file *must* have row names 
    in the first line
    fieldtypes is a dictionary mapping field names to a function
    used to convert the string read from the CSV file to the value
    that will be stored in the PyDbLite base. For instance, if the
    field is an integer, the function is the built-in int() function"""
    import csv
    import PyDbLite
    _in = csv.DictReader(src,fieldnames=fieldnames)
    # read the first line to get field names if not specified
    if fieldnames is None:
        _in.next()
        fieldnames = _in.fieldnames[:]
    print fieldnames
    out = PyDbLite.Base(dest)
    for fieldname in ["__id__","__version__"]:
        try:
            fieldnames.remove(fieldname)
        except ValueError:
            pass
    kw = {"mode":"override"}
    out.create(*fieldnames,**kw)
    print "base created",out.fields
    default_fieldtypes = {"__id__":int,"__version__":int}
    if fieldtypes is None:
        fieldtypes = default_fieldtypes
    else:
        fieldtypes.update(default_fieldtypes)
    for row in _in:
        for k in fieldtypes:
            try:
                row[k] = fieldtypes[k](row[k])
            except:
                print k,row[k],fieldtypes[k]
                raise
        out.insert(**row)
    out.commit()