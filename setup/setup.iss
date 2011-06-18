#define AppVersion "0.3.1"

[Setup]
AppName=DotCloud for Windows
AppVersion={#AppVersion}
OutputBaseFilename=dotcloud-{#AppVersion}
DefaultDirName={pf}\DotCloud
DefaultGroupName=DotCloud
UninstallDisplayIcon={app}\dotcloud.exe
SetupIconFile=..\dotcloud\dotcloud.ico
DisableProgramGroupPage=yes
ChangesEnvironment=yes

[Tasks]
Name: modifypath; Description: "Add DotCloud's folder to your system path (recommended)";

[Files]
Source: "..\dotcloud\{#AppVersion}\bin\*"; DestDir: "{app}"; Flags: recursesubdirs;
Source: "..\redist\vcredist_x86.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall;

[Icons]
Name: "{group}\DotCloud"; Filename: "cmd"; Parameters: "/K dotcloud.exe"; WorkingDir: "{app}"; IconFilename: "{app}\dotcloud.exe"
Name: "{group}\Uninstall DotCloud"; Filename: "{uninstallexe}"; WorkingDir: "{app}";

[Dirs]
Name: "{code:UserDir}\.dotcloud"

[Run]
Filename: {tmp}\vcredist_x86.exe; Parameters: "/q:a /c:""msiexec /i vcredist.msi /qn"""; StatusMsg: "Installing Microsoft Visual C++ Redistributable Package";

[UninstallDelete]
Type: filesandordirs; Name: "{code:UserDir}\.dotcloud"

[Registry]
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: expandsz; ValueName: "HOME"; ValueData: "{code:UserDir}"

[Registry]
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: expandsz; ValueName: "CYGWIN"; ValueData: "nodosfilewarning"

[Code]
function UserDir(Param: String): String;
begin
  Result := GetEnv('USERPROFILE');
end;

var
  apiKeyPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  apiKeyPage := CreateInputQueryPage(wpSelectTasks,
    'DotCloud API Key',
    'You can find it at http://www.dotcloud.com/account/settings',
    'Optionally you can specify your DotCloud API Key (not required)');
  apiKeyPage.Add('API Key:', False);
end;

function NextButtonClick(CurrentPageID: Integer) : Boolean;
var
  StrApiKey: String;
  DotCloudConfPath: String;
begin
  Result := True;
  if CurrentPageID = apiKeyPage.ID then
  begin
    StrApiKey := Trim(apiKeyPage.Values[0]);
    if StrApiKey <> '' then
    begin
      if (Pos(':', StrApiKey) <> 21) and (Length(StrApiKey) <> 61) then
      begin
        Result := False;
        MsgBox('Not a valid api key.', mbError, MB_OK);
      end
    end
  end
  else if CurrentPageID = wpFinished then
  begin
    StrApiKey := Trim(apiKeyPage.Values[0]);
    if StrApiKey <> '' then
    begin
      DotCloudConfPath := UserDir('') + '\.dotcloud\' + 'dotcloud.conf';
      SaveStringToFile(DotCloudConfPath, '{' + #13#10, false);
      SaveStringToFile(DotCloudConfPath, '    "url": "https://api.dotcloud.com/", ' + #13#10, true);
      SaveStringToFile(DotCloudConfPath, '    "apikey": "'+ StrApiKey +'"' + #13#10, true);
      SaveStringToFile(DotCloudConfPath, '}', true);
    end
  end
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
