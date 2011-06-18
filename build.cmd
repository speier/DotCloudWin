@echo off

set currentdir=%CD%
set dotcloudver=0.3.1

cd dotcloud\%dotcloudver%
call build.cmd

cd %currentdir%
PATH=%PATH%;C:\Program Files (x86)\Inno Setup 5
iscc.exe setup\setup.iss /dVERSION=%dotcloudver%

cd dotcloud\%dotcloudver%
rmdir bin /s /q