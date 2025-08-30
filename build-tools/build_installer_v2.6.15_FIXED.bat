@echo off
echo ========================================
echo Creating Installer for DJs Timeline Machine v2.6.15
echo ========================================
echo.

REM First, let's see what we have
echo Current directory: %CD%
echo.
echo Checking for application files...

if exist "..\dist\DJs_Timeline_Machine_v2.6.15" (
    echo ✓ Found application directory: ..\dist\DJs_Timeline_Machine_v2.6.15
) else (
    echo ✗ Application directory NOT found: ..\dist\DJs_Timeline_Machine_v2.6.15
    echo.
    echo What's in the dist folder:
    if exist "..\dist" (
        dir "..\dist"
    ) else (
        echo No dist folder found!
    )
    pause
    exit /b 1
)

if exist "..\dist\DJs_Timeline_Machine_v2.6.15\DJs_Timeline_Machine_v2.6.15.exe" (
    echo ✓ Found main executable
) else (
    echo ✗ Main executable NOT found
    echo.
    echo What's in the application directory:
    dir "..\dist\DJs_Timeline_Machine_v2.6.15"
    pause
    exit /b 1
)

REM Check for Inno Setup
echo.
echo Checking for Inno Setup...
set INNO_PATH=
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set INNO_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
    echo ✓ Found Inno Setup at: %INNO_PATH%
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set INNO_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe
    echo ✓ Found Inno Setup at: %INNO_PATH%
) else (
    echo ✗ Inno Setup 6 not found!
    echo Please install Inno Setup from: https://jrsoftware.org/isdl.php
    echo.
    echo Checked locations:
    echo - %ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
    echo - %ProgramFiles%\Inno Setup 6\ISCC.exe
    pause
    exit /b 1
)

REM Create output directory
echo.
echo Creating output directory...
if not exist "..\installer_output" (
    mkdir "..\installer_output"
    echo ✓ Created: ..\installer_output
) else (
    echo ✓ Output directory already exists: ..\installer_output
)

REM Check if Inno Setup script exists
if exist "installer_v2.6.15.iss" (
    echo ✓ Found Inno Setup script: installer_v2.6.15.iss
) else (
    echo ✗ Inno Setup script NOT found: installer_v2.6.15.iss
    echo Current files in build-tools:
    dir
    pause
    exit /b 1
)

REM Build the installer
echo.
echo Building installer...
echo Running: "%INNO_PATH%" installer_v2.6.15.iss
"%INNO_PATH%" installer_v2.6.15.iss

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ✗ ERROR: Installer creation failed with error code: %ERRORLEVEL%
    echo.
    echo Troubleshooting tips:
    echo 1. Check that all source files exist
    echo 2. Check Inno Setup script for syntax errors
    echo 3. Make sure no files are locked/in use
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo ✓ Installer created successfully!
    echo Location: ..\installer_output\DJs_Timeline_Machine_v2.6.15_Setup.exe
    echo ========================================
    echo.
    
    REM Verify the installer file was actually created
    if exist "..\installer_output\DJs_Timeline_Machine_v2.6.15_Setup.exe" (
        echo ✓ Installer file verified: 
        dir "..\installer_output\DJs_Timeline_Machine_v2.6.15_Setup.exe"
    ) else (
        echo ✗ WARNING: Installer file not found despite successful build
        echo Checking installer_output folder:
        if exist "..\installer_output" (
            dir "..\installer_output"
        ) else (
            echo installer_output folder doesn't exist!
        )
    )
)

echo.
pause