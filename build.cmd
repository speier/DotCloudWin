@echo off

echo Building DotCloud for Windows

cd dotcloud\0.3.1
call build.cmd

echo Building DotCloud for Windows Setup

cd .

PATH=%PATH%;C:\Program Files (x86)\Inno Setup 5
iscc.exe setup.iss

pause