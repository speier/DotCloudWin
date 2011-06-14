@echo off

python setup.py py2exe
rmdir build /s /q
pause
PATH=%PATH%;C:\Program Files (x86)\Inno Setup 5
REM iscc.exe dotcloud.iss