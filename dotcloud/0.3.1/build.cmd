@echo off

echo Building DotCloud for Windows 0.3.1

python setup.py py2exe
rmdir build /s /q