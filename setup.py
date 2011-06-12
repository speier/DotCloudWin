import os

from distutils.core import setup
import py2exe
   
requiredFiles = ['dotcloud.pem']

cygwinDir = os.path.join(os.path.abspath(os.curdir), 'cygwin')
for file in os.listdir(cygwinDir):
  path = os.path.join(cygwinDir, file)
  if os.path.isfile(path):
    requiredFiles.append(path)

setup(
  console = ['dotcloud.py'],
  options = {'py2exe': {
    'dist_dir': 'bin',
    'optimize': 2,
    'bundle_files': 1,
    'dll_excludes': ['w9xpopen.exe']
  }},
  data_files = requiredFiles,
  zipfile = None
)