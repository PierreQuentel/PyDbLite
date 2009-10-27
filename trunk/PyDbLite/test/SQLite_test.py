import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import SQLite

db = SQLite.Base("test",'test.sqlite')
db.create(("name","TEXT",{'NOT NULL':True}),
    ("age","INTEGER"),
    ("size","REAL"),("birth","BLOB"),
    ("ctime","BLOB",{'DEFAULT':SQLite.CURRENT_TIME}),
    ("ctimestamp","BLOB",{'DEFAULT':SQLite.CURRENT_TIMESTAMP}),
    mode="override")

try:
    db.add_field(("name","TEXT"))
except:
    pass

import random
import datetime

names = ['pierre','claire','simon','camille','jean',
             'florence','marie-anne']
#db = Base('PyDbLite_test')
#db.create('name','age','size','birth',mode="override")
for i in range(1000):
    db.insert(name=random.choice(names),
         age=random.randint(7,47),size=random.uniform(1.10,1.95),
         birth=datetime.datetime(1990,10,10,20,10,20,2345))
db.commit()

print 'Record #20 :',db[20]
raw_input()
print '\nRecords with age=30 :'
for rec in [ r for r in db if r["age"]==30 ]:
    print '%-10s | %2s | %s' %(rec['name'],rec['age'],round(rec['size'],2))

print "\nSame with __call__"
# same with select
for rec in db(age=30):
    print '%-10s | %2s | %s' %(rec['name'],rec['age'],round(rec['size'],2))
print [ r for r in db if r["age"]==30 ] == db(age=30)
raw_input()

db.insert(name=random.choice(names)) # missing fields
print '\nNumber of records with 30 <= age < 33 :',
print sum([1 for r in db if 33 > r['age'] >= 30])

print db.delete([])

d = db.delete([r for r in db if 32> r['age'] >= 30 and r['name']==u'pierre'])
print "\nDeleting %s records with name == 'pierre' and 30 <= age < 32" %d
print '\nAfter deleting records '
for rec in db(age=30):
    print '%-10s | %2s | %s' %(rec['name'],rec['age'],round(rec['size'],2))
print '\n',sum([1 for r in db]),'records in the database'
print '\nMake pierre uppercase for age > 27'
for record in ([r for r in db if r['name']=='pierre' and r['age'] >27]) :
    db.update(record,name="Pierre")
print len([r for r in db if r['name']=='Pierre']),'Pierre'
print len([r for r in db if r['name']=='pierre']),'pierre'
print len([r for r in db if r['name'] in ['pierre','Pierre']]),'p/Pierre'
print 'is unicode :',isinstance(db[20]['name'],unicode)
db.commit()

db.open()
for field in db.fields:
    info = db.field_info[field]
    if info.get('DEFAULT',None) in [SQLite.CURRENT_TIME,SQLite.CURRENT_DATE,
        SQLite.CURRENT_TIMESTAMP]:
            info['DEFAULT'] = info['DEFAULT'].__name__
    print field,info['type'],info.get('NOT NULL',''),info.get('DEFAULT','')

print '\nSame operation after commit + open'
print len([r for r in db if r['name']=='Pierre']),'Pierre'
print len([r for r in db if r['name']=='pierre']),'pierre'
print len([r for r in db if r['name'] in ['pierre','Pierre']]),'p/Pierre'
print 'is unicode :',isinstance(db[20]['name'],unicode)

print "\nDeleting record #21"
del db[21]
if not 21 in db:
    print "record 21 removed"

print db[22]
print "add field adate"
db.add_field(('adate',"BLOB",{'DEFAULT':datetime.date.today()}))

print db[22]


