@echo off

CALL build.cmd

PATH=%PATH%;C:\Program Files (x86)\Inno Setup 5
iscc.exe dotcloud.iss