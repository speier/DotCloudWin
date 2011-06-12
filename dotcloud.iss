[Setup]
AppName=DotCloud for Windows
AppVersion=0.3.1
OutputBaseFilename=dotcloud-0.3.1
OutputDir=setup
DefaultDirName={pf}\DotCloud
ChangesEnvironment=yes

[Tasks]
Name: modifypath; Description: "Add DotCloud's path to path environment variable (recommended)";

[Files]
Source: "bin\*"; DestDir: "{app}"; Flags: recursesubdirs;

[UninstallDelete]
Type: filesandordirs; Name: "{code:UserDir}\.dotcloud"

[Code]
function UserDir(Param: String): String;
begin
  Result := GetEnv('USERPROFILE');
end;

function ModPathDir(): TArrayOfString;
var
  Dir:	TArrayOfString;
begin
  setArrayLength(Dir, 1)
  Dir[0] := ExpandConstant('{app}');
  Result := Dir;
end;

#include "modpath.iss"
