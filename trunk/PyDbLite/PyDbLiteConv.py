import os

def stringToDate(fmt="%Y-%m-%d"):
    """returns a function to convert a string to a datetime.date instance
    using the formatting string fmt as in time.strftime"""
    import time
    import datetime
    def conv_func(s):
        return datetime.date(*time.strptime(s,fmt)[:3])
    return conv_func

def PyDbLite_to_csv(src,dest=None,dialect='excel'):
    """Convert a PyDbLite base to a CSV file
    src is the PyDbLite.Base instance
    dest is the file-like object for the CSV output
    dialect is the same as in csv module"""
    import csv
    fieldnames = ["__id__","__version__"]+src.fields
    if dest is None:
        dest = open(os.path.splitext(src.name)[0]+'.csv','w')
    w = csv.DictWriter(dest,fieldnames,dialect)
    first = dict([(f,f) for f in fieldnames])
    w.writerow(first) # first row has the field names
    for r in src:
        if not "__version__" in r:
            r["__version__"] = 0
        w.writerow(r)
    dest.close()

def csv_to_PyDbLite(src,dest,fieldnames=None,fieldtypes=None,dialect='excel'):
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
    if not fieldnames:
        _in = csv.DictReader(open(src),fieldnames=fieldnames)
        _in.next()
        fieldnames = _in.fieldnames
    out = PyDbLite.Base(dest)
    kw = {"mode":"override"}
    out.create(*_in.fieldnames,**kw)
    default_fieldtypes = {"__id__":int,"__version__":int}

    if fieldtypes is None:
        fieldtypes = default_fieldtypes
    else:
        fieldtypes.update(default_fieldtypes)
    _in = csv.DictReader(open(src),fieldnames=fieldnames)
    _in.next()
    for row in _in:
        for k in fieldtypes:
            try:
                row[k] = fieldtypes[k](row[k])
            except:
                print k,row[k],fieldtypes[k]
                raise
        out.insert(**row)
    out.commit()

if __name__ == "__main__":
    import os
    import PyDbLite
    os.chdir(os.path.join(os.getcwd(),'test'))
    pdl = PyDbLite.Base("test.pdl").open()
    PyDbLite_to_csv(pdl)
    import datetime
    csv_to_PyDbLite('test.csv',dest="test_copy.pdl")
    
    ok = nok = 0
    for r1 in PyDbLite.Base('test_copy.pdl').open():
        r2 = pdl[r1["__id__"]]
        ok += 1
        nok += 1
    print ok,nok
