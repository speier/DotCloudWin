import os

from distutils.core import setup
import py2exe
   
requiredFiles = ['dotcloud.pem']

cygwinFiles = os.path.join(os.path.abspath(os.curdir), 'cygwin')
for file in os.listdir(cygwinFiles):
  path = os.path.join(cygwinFiles, file)
  if os.path.isfile(path):
    requiredFiles.append(path)

setup(
  console = [
    {
      'script': 'dotcloud.py',
      'icon_resources': [(1, 'dotcloud.ico')]
    }
  ],
  options = {'py2exe': {
    'dist_dir': 'bin',
    'optimize': 2,
    'bundle_files': 1,
    'dll_excludes': ['w9xpopen.exe']
  }},
  data_files = requiredFiles,
  zipfile = None
)