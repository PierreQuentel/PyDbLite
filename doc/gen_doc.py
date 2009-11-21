import os
import shutil
import string

# find destination folder
dest = os.path.dirname(os.getcwd())
dest_dir = ''
for _dir in os.listdir(dest):
    path = os.path.join(dest,_dir)
    if os.path.isdir(path) and _dir.startswith('20'):
        if _dir > dest_dir:
            dest_dir = _dir

print dest_dir

shutil.rmtree('gendoc',ignore_errors=True)
os.mkdir('gendoc')

out = open(os.path.join('gendoc','index.html'),'w')
out.write(open('index.html').read())
out.close()

for lang in ('en','fr'):
    os.mkdir(os.path.join('gendoc',lang))

    _in = open('pydblite.css').read()
    out = open(os.path.join('gendoc',lang,'pydblite.css'),'w')
    out.write(_in)
    out.close()

    template = string.Template(open(os.path.join(lang,'template.html')).read())

    for fname in ['index.html','PyDbLite.html','SQLite.html','MySQL.html','bench.html',
        'licence.html','contact.html']:
        out = open(os.path.join('gendoc',lang,fname),'w')
        content = open(os.path.join(lang,fname)).read()
        out.write(template.substitute({'content':content,'filename':fname}))
        out.close()
    
