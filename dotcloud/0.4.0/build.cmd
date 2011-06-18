@echo off

echo Building DotCloud for Windows 0.4.0

python setup.py py2exe
rmdir build /s /q