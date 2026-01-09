@echo off
echo ========================================
echo Creating Installer for DJs Timeline Machine v2.6.15
echo ========================================
echo.
echo DEBUG: Script started successfully
pause

REM Check if the application directory exists (PyInstaller creates in project root dist)
if not exist "..\dist\DJs_Timeline_Machine_v2.6.15" (
    echo ERROR: Application directory not found!
    echo Expected: ..\dist\DJs_Timeline_Machine_v2.6.15\
    echo Please run build_v2.6.15.bat first to create the application.
    echo.
    echo Checking what exists in dist folder:
    if exist "..\dist" (
        dir "..\dist"
    ) else (
        echo No dist folder found at project root.
    )
    pause
    exit /b 1
)

REM Check if the main executable exists in the directory
if not exist "..\dist\DJs_Timeline_Machine_v2.6.15\DJs_Timeline_Machine_v2.6.15.exe" (
    echo ERROR: Main executable not found in application directory!
    echo Checking what's in the application directory:
    dir "..\dist\DJs_Timeline_Machine_v2.6.15"
    echo.
    echo Please run build_v2.6.15.bat first to create the executable.
    pause
    exit /b 1
)

REM Check if Inno Setup is installed
set INNO_PATH=
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set INNO_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set INNO_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe
) else if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
) else (
    echo ERROR: Inno Setup 6 not found!
    echo Please install Inno Setup from: https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

echo Found Inno Setup at: %INNO_PATH%
echo.

REM Create output directory
if not exist "..\installer_output" mkdir "..\installer_output"

REM Build the installer
echo Building installer...
"%INNO_PATH%" installer_v2.6.15.iss

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Installer creation failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installer created successfully!
echo Location: ..\installer_output\DJs_Timeline_Machine_v2.6.15_Setup.exe
echo ========================================
echo.
pause