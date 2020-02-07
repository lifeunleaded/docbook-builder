#!/usr/bin/python
import sys,os,subprocess,shutil,re,datetime
from git import Repo
from lxml import etree

thisrepo = Repo('./')
thisbranch = sys.argv[1]
sys.stderr.write("Builder.py for branch {}\n".format(thisbranch))
hc = thisrepo.head.commit
print "Last commit:"
print hc.hexsha
print hc.message
print "================="

setup=False
if not os.path.exists('buildcache/{}'.format(thisbranch)):
    os.makedirs('buildcache/{}'.format(thisbranch))
try:
    lastbuildfile = open('buildcache/{}/lastbuild'.format(thisbranch),'r')
    lastbuild = lastbuildfile.readlines()[0]
    lastbuildfile.close()
    sys.stderr.write("Last build was "+lastbuild+'\n')
    allchangedfiles = thisrepo.git.diff_tree(hc.hexsha+'..'+lastbuild, no_commit_id=True, name_only=True, r=True).split('\n')
except IOError:
    sys.stderr.write("Did not find buildcache/{}/lastbuild. Assuming initial setup. Writing lastbuild.\n".format(thisbranch))
    allchangedfiles = thisrepo.git.diff_tree(hc.hexsha, no_commit_id=True, name_only=True, r=True).split('\n')
    lastbuild=hc.hexsha
    lastbuildfile = open('buildcache/{}/lastbuild'.format(thisbranch),'w')
    lastbuildfile.write(lastbuild)
    lastbuildfile.close()
    
changedfiles=[f for f in allchangedfiles if f.split('/')[0] not in ['auto_generated_content','build','buildcache','buildtmp','public','runner','output','templates']]
sys.stderr.write("Changed files since last build:\n")
sys.stderr.write('\n'.join(changedfiles)+'\n')

books = {}
allfiles = {}

def collect_includes(path, book):
    try:
        adoc = open(path,'r')
        try:
            docxml = etree.parse(adoc)
            docroot = docxml.getroot()
            for include in docroot.findall('.//{http://www.w3.org/2001/XInclude}include'):
                inpath = os.path.relpath(os.path.realpath(os.path.normpath(os.path.join(os.path.dirname(path),include.attrib['href']))))
                if inpath not in allfiles.keys():
                    allfiles[inpath] = [book]
                elif book not in allfiles[inpath]:
                    allfiles[inpath].append(book)
                if inpath not in books[book]:
                    books[book].append(inpath)
                    collect_includes(inpath, book)
        except etree.XMLSyntaxError as e:
            sys.stderr.write("Invalid XML in "+path+':\n')
            sys.stderr.write(str(e)+'\n')
        adoc.close()
    except IOError:
        sys.stderr.write("Trying to open "+path+" but failed"+'\n')

docids = {}
docchanged = False
cwd = os.getcwd()
sys.stderr.write('=================\n'+sys.argv[0]+": Traversing from "+cwd+" to find book files\n-------------\n")
for root,dirs,files in os.walk("."):
    for fil in files:
        if os.path.splitext(fil)[1] == '.xml':
            npath = os.path.relpath(os.path.realpath(os.path.normpath(os.path.join(root,fil))))
            if npath.split('/')[0] not in ['auto_generated_content','build','buildtmp','buildcache','public','templates','runner', 'output']:
                try:
                    doc = open(npath,'r')
                    docxml = etree.parse(doc)
                    doc.close()
                    docroot = docxml.getroot()
                    if docroot.tag == "{http://docbook.org/ns/docbook}book":
                        books[npath] = []
                        if '{http://www.w3.org/XML/1998/namespace}id' in docroot.attrib.keys():
                            docids[npath] = docroot.attrib['{http://www.w3.org/XML/1998/namespace}id']
                        else:
                            docname = npath.split('/')[-1].rstrip('.xml')
                            sys.stderr.write("Did not find root xml:id in {}, setting {}\n".format(npath, docname))
                            docids[npath] = docname
                            docroot.attrib['{http://www.w3.org/XML/1998/namespace}id'] = docname
                            docxml.write(npath)
                        if npath not in allfiles.keys():
                            allfiles[npath] = [npath]
                        elif npath not in allfiles[npath]:
                            allfiles[npath].append(npath)
                        if npath not in books[npath]:
                            books[npath].append(npath)
                        collect_includes(npath, npath)
                except etree.XMLSyntaxError as e:
                    sys.stderr.write("Invalid XML in "+npath+':\n')
                    sys.stderr.write(str(e)+'\n')
buildlist = []
buildlistfile = open('buildcache/{}/buildlist'.format(thisbranch),'w')
for a in changedfiles:
    if a in allfiles.keys():
        for b in allfiles[a]:
            sys.stderr.write("Build "+b+" due to the following change to "+a+'\n')
            thislog = thisrepo.git.log(lastbuild+'..'+hc.hexsha, '--', a, pretty="format:%s")
            try:
                sys.stderr.write('{}\n'.format(thislog).encode('utf8'))
            except UnicodeEncodeError:
                sys.stderr.write('Commit {} has utf8, cannot list here\n'.format(hc.hexsha))
            if b not in buildlist:
                buildlist.append(b)
                buildlistfile.write(b+'\n')

autogenerated = []

built=[]
autogens_done=[]

for book in buildlist:
    sys.stderr.write("Starting build for {}\n".format(book))
    subprocess.check_output(['build/builder.sh',book])
    justbuilt=open('buildtmp/docname','r').readlines()[0].rstrip('\n')
    if justbuilt not in built:
        built.append(justbuilt)
if not os.path.exists('public/{}/index.html'.format(thisbranch)):
    if not os.path.exists('public/{}'.format(thisbranch)):
        os.mkdir('public/{}'.format(thisbranch))
    published = open('public/{}/index.html'.format(thisbranch),'w')
    published.write("<html><head/><body><ul>")
else:
    oldpublished = open('public/{}/index.html'.format(thisbranch),'r')
    text = oldpublished.readlines()[-1].replace('</ul></body></html>','')
    oldpublished.close()
    published = open('public/{}/index.html'.format(thisbranch),'w')
    published.write(text)
sys.stderr.write('Built:\n')
sys.stderr.write('{}\n'.format(','.join(built)))
for builtbook in built:
    sys.stderr.write("writing for {} in branch index\n".format(builtbook))
    published.write('<li>')
    published.write('<p>{}</p>'.format(builtbook))
    published.write('<p><a href="{}/public/html/bk01-FSet.html">Public version</a>'.format(builtbook))
    published.write('(<a href="{}/public/{}.zip">ZIP archive</a>)</p>'.format(builtbook,builtbook))
    published.write('<p><a href="{}/internal/html/bk01-FSet.html">Internal version</a></p>'.format(builtbook))
    published.write('<p>Last build {} due to <a href="https://gitlab.com/lifeunleaded/docbook-builder/commit/{}">{}</a></p></li>'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), hc.hexsha, hc.hexsha))
                    
published.write("</ul></body></html>")
published.close()
    
lastbuildfile = open('buildcache/{}/lastbuild'.format(thisbranch),'w')
lastbuildfile.write(hc.hexsha)
lastbuildfile.close()
buildlistfile.close()
