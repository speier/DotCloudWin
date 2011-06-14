@echo off

python setup.py py2exe
rmdir build /s /q

PATH=%PATH%;C:\Program Files (x86)\Inno Setup 5
iscc.exe dotcloud.iss