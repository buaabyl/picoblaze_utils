from distutils.core import setup
import py2exe
import os
import re

#find mcpp and astyle
def find_dependent():
    path_env = os.environ['PATH']
    lst_path = re.split(';[ ]*', path_env)
    lst_path.append('.')

    fn_mcpp = None
    fn_astyle = None

    for e in lst_path:
        tofind = os.path.join(e, 'astyle.exe')
        if os.path.isfile(tofind):
            fn_astyle = tofind
        tofind = os.path.join(e, 'mcpp.exe')
        if os.path.isfile(tofind):
            fn_mcpp = tofind

    return (fn_mcpp, fn_astyle)

(fn_mcpp, fn_astyle) = find_dependent()
if fn_mcpp == None or fn_astyle == None:
    print 'Could not find mcpp.exe and astyle.exe'
    raise BaseException()

#bundle_files   1:everythings
#               2:everythings except PythonXX.dll
#               3:Don't bundle, just library
opt = {'py2exe':
        {'bundle_files': 1,
        "includes" : ["mako.template", "mako.cache", "pygments.styles.default"]
        }}

class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # for the versioninfo resources
        self.description    = "picoblaze utils"
        self.version        = "0.0.3"
        self.company_name   = "No Company"
        self.copyright      = "GPLv3"
        self.name           = "pblaze"

#using setup.py py2exe to compile.
#use zipfile=None to let all thing in exe!
#or just special zipfile='filename'
setup(
        console =[
            Target(script = 'pblaze-cc.py'),
            Target(script = 'pblaze-as.py'),
            Target(script = 'pblaze-ld.py')],
        data_files = [
            ('.', ['kcpsm3.h', fn_mcpp, fn_astyle])],
        #data_files=[(".", ["test.xml", "test.ini"])],
        zipfile ='pblaze.pkg',
        #zipfile=None,
        options =opt
)

