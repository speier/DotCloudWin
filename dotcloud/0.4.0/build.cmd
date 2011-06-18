@echo off

rmdir bin /s /q
python setup.py py2exe
rmdir build /s /q