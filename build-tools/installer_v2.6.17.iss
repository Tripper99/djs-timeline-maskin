; Inno Setup Script for DJs Timeline Machine v2.6.17
; This script creates a professional Windows installer
; Updated to include GitHub version checking feature

#define MyAppName "DJs Timeline Machine"
#define MyAppVersion "2.6.17"
#define MyAppPublisher "DJs Development"
#define MyAppExeName "DJs_Timeline_Machine_v2.6.17.exe"
#define MyAppIconName "Agg-med-smor-v4-transperent.ico"

[Setup]
; NOTE: The value of AppId uniquely identifies this application
AppId={{A7B3C5D8-9E2F-4A6B-8C7D-1E3F5A8B9C2D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://github.com/Tripper99/djs-timeline-maskin
AppSupportURL=https://github.com/Tripper99/djs-timeline-maskin/issues
AppUpdatesURL=https://github.com/Tripper99/djs-timeline-maskin/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Output installer file  
OutputDir=..\installer_output
OutputBaseFilename=DJs_Timeline_Machine_v{#MyAppVersion}_Setup
; Use the same icon for the installer
SetupIconFile=..\{#MyAppIconName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; Require Windows 7 or later
MinVersion=6.1
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes
LicenseFile=
InfoBeforeFile=
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} v{#MyAppVersion}

[Languages]
Name: "swedish"; MessagesFile: "compiler:Languages\Swedish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsWindows64

[Files]
; CRITICAL: Include entire application directory (CustomTkinter requires all files)
; NOTE: Paths are relative to build-tools directory where this script runs
; PyInstaller now creates dist in project root, so we look in ..\dist
Source: "..\dist\DJs_Timeline_Machine_v2.6.17\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Explicitly include the icon file to ensure it's available for shortcuts
Source: "..\Agg-med-smor-v4-transperent.ico"; DestDir: "{app}"; Flags: ignoreversion
; Documentation files 
Source: "..\docs\Manual.rtf"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\docs\DJs_Timeline-maskin_User_Manual.rtf"; DestDir: "{app}\docs"; Flags: ignoreversion
; Include template directory if it exists
Source: "..\Saved_excel_name_templates\*"; DestDir: "{app}\Saved_excel_name_templates"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: DirExists(ExpandConstant('{#SourcePath}..\Saved_excel_name_templates'))

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\Agg-med-smor-v4-transperent.ico"
Name: "{group}\Manual (Svenska)"; Filename: "{app}\docs\Manual.rtf"
Name: "{group}\User Manual (English)"; Filename: "{app}\docs\DJs_Timeline-maskin_User_Manual.rtf"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\Agg-med-smor-v4-transperent.ico"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\Agg-med-smor-v4-transperent.ico"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function DirExists(const Name: String): Boolean;
var
  FindRec: TFindRec;
begin
  Result := FindFirst(Name, FindRec);
  if Result then
    FindClose(FindRec);
end;

function IsWindows64: Boolean;
begin
  Result := IsWin64;
end;

[CustomMessages]
swedish.CreateDesktopIcon=Skapa skrivbordsgenväg
swedish.CreateQuickLaunchIcon=Skapa genväg i Snabbstart
swedish.LaunchProgram=Starta %1 efter installation
swedish.UninstallProgram=Avinstallera %1