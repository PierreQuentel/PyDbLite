import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import PyDbLite
Base = PyDbLite.Base

# test on a 1000 record base
import random
import datetime
names = ['pierre','claire','simon','camille','jean',
             'florence','marie-anne']
db = Base('PyDbLite_test',protocol=1)
db.create('name','age','size','birth',mode="override")
for i in range(1000):
    db.insert(name=random.choice(names),
         age=random.randint(7,47),size=random.uniform(1.10,1.95),
         birth=datetime.date(1990,10,10))
db.create_index('age')
db.commit()

print ('Record #20 :',db[20])
print ('\nRecords with age=30 :')
for rec in db._age[30]:
    print ('%-10s | %2s | %s' %(rec['name'],rec['age'],round(rec['size'],2)))

print ("\nSame with __call__")
# same with select
for rec in db(age=30):
    print ('%-10s | %2s | %s' %(rec['name'],rec['age'],round(rec['size'],2)))
print (len(db._age[30]) == len(db(age=30)))

db.insert(name=random.choice(names)) # missing fields
print ('\nNumber of records with 30 <= age < 33 :',end=" ")
print (sum([1 for r in db if r['age'] is not None and 33 > r['age'] >= 30]))
print (len(33 > db('age') >= 30))

print (sum([1 for r in db if r['age'] is not None and r['age'] > 30 \
    and r['name'] is not None and r['name']>'f']))
print (len((db('age')>30) & (db('name')>'f')))

print (len(db('age')==30),len(db(age=30)))
input()

print (db.delete([]))

d = db.delete([r for r in db if r['age'] is not None
    and (32> r['age'] >= 30) 
    and r['name'] is not None and (r['name']=='pierre')])
print ("\nDeleting %s records with name == 'pierre' and 30 <= age < 32" %d)
print ('\nAfter deleting records ')
for rec in db._age[30]:
    print ('%-10s | %2s | %s' %(rec['name'],rec['age'],round(rec['size'],2)))
print ('\n',sum([1 for r in db]),'records in the database')
print ('\nMake pierre uppercase for age > 27')
for record in ([r for r in db if r['age'] is not None and r['age'] is not None 
    and r['name']=='pierre' and r['age'] >27]) :
    db.update(record,name="Pierre")
print (len([r for r in db if r['name']=='Pierre']),'Pierre')
print (len([r for r in db if r['name']=='pierre']),'pierre')
print (len([r for r in db if r['name'] in ['pierre','Pierre']]),'p/Pierre')
print ('is unicode :',isinstance(db[20]['name'],str))
db.commit()
db.open()
print ('\nSame operation after commit + open')
print (len([r for r in db if r['name']=='Pierre']),'Pierre')
print (len([r for r in db if r['name']=='pierre']),'pierre')
print (len([r for r in db if r['name'] in ['pierre','Pierre']]),'p/Pierre')
print ('is unicode :',isinstance(db[20]['name'],str))

print ("\nDeleting record #20")
del db[20]
if not 20 in db:
    print ("record 20 removed")

print (db[21])
db.drop_field('name')
print (db[21])
db.add_field('now',datetime.datetime.now())
print (db[21])

k = next(db._age) # first item
assert (k in db._age)
db.delete(db._age[k])
assert (not db._age[k])
assert (not k in db._age)
db.delete_index("age")
print('test finished')
