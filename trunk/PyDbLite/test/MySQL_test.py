import os
import sys
sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))

import MySQL

conn = MySQL.Connection("localhost",'root','admin')
db = MySQL.Database(conn,'test')
print db.tables()

table = MySQL.Table(db,'essai')
table.create(("rowid",'INTEGER PRIMARY KEY AUTO_INCREMENT'),
    ("name",'TEXT NOT NULL'),
    ("age","INTEGER"),
    ("size","REAL"),("birth","BLOB"),
    ("ctime","BLOB"),
    ("ctimestamp","BLOB"),
    mode="override")

table.insert(name="a",age=10)
try:
    table.insert(name="b",age='erty')
    raise ValueError,'this record should not be accepted - age is not an int'
except:
    pass

print [r for r in table]

try:
    table.add_field(("name","TEXT"))
except:
    pass

import random
import datetime

names = ['pierre','claire','simon','camille','jean',
             'florence','marie-anne']
#table = Base('PyDbLite_test')
#table.create('name','age','size','birth',mode="override")
for i in range(1000):
    table.insert(name=random.choice(names),
         age=random.randint(7,47),size=random.uniform(1.10,1.95),
         birth=datetime.datetime(1990,10,10,20,10,20,2345))
table.commit()

print 'Record #20 :',table[20]
print len(table),'records'
print len(table())
raw_input()
print '\nRecords with age=30 :'
for rec in [ r for r in table if r["age"]==30 ]:
    print '%-10s | %2s | %s' %(rec['name'],rec['age'],round(rec['size'],2))

print "\nSame with __call__"
# same with select
for rec in table(age=30):
    print '%-10s | %2s | %s' %(rec['name'],rec['age'],round(rec['size'],2))
print [ r for r in table if r["age"]==30 ] == table(age=30)
raw_input()

table.insert(name=random.choice(names)) # missing fields
print '\nNumber of records with 30 <= age < 33 :',
print sum([1 for r in table if 33 > r['age'] >= 30])

print table.delete([])

d = table.delete([r for r in table if 32> r['age'] >= 30 and r['name']==u'pierre'])
print "\nDeleting %s records with name == 'pierre' and 30 <= age < 32" %d
print '\nAfter deleting records '
for rec in table(age=30):
    print '%-10s | %2s | %s' %(rec['name'],rec['age'],round(rec['size'],2))
print '\n',sum([1 for r in table]),'records in the database'
print '\nMake pierre uppercase for age > 27'
for record in ([r for r in table if r['name']=='pierre' and r['age'] >27]) :
    table.update(record,name="Pierre")
print len([r for r in table if r['name']=='Pierre']),'Pierre'
print len([r for r in table if r['name']=='pierre']),'pierre'
print len([r for r in table if r['name'] in ['pierre','Pierre']]),'p/Pierre'
print 'is unicode :',isinstance(table[20]['name'],unicode)
table.commit()

table.open()
for field in table.fields:
    info = table.field_info[field]
    print field,info['type'],info.get('NOT NULL',''),info.get('DEFAULT','')

print '\nSame operation after commit + open'
print len([r for r in table if r['name']=='Pierre']),'Pierre'
print len([r for r in table if r['name']=='pierre']),'pierre'
print len([r for r in table if r['name'] in ['pierre','Pierre']]),'p/Pierre'
print 'is unicode :',isinstance(table[20]['name'],unicode)

print "\nDeleting record #21"
del table[21]
if not 21 in table:
    print "record 21 removed"

print table[22]
print "add field adate"
table.add_field(('adate','TIMESTAMP DEFAULT CURRENT_TIMESTAMP'))

print table[22]


