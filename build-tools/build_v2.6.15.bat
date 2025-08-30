@echo off
echo ========================================
echo Building DJs Timeline Machine v2.6.15
echo ========================================
echo.
echo NOTE: Building for CustomTkinter compatibility
echo Output: Directory with executable and assets
echo ========================================
echo.

REM Clean previous builds (both local and project root)
echo Cleaning previous builds...
if exist "dist" (
    echo Cleaning local build-tools/dist...
    rmdir /s /q dist
)
if exist "build" (
    echo Cleaning local build-tools/build...
    rmdir /s /q build
)
if exist "..\dist\DJs_Timeline_Machine_v2.6.15" (
    echo Cleaning previous app in project root...
    rmdir /s /q "..\dist\DJs_Timeline_Machine_v2.6.15"
)

REM Build the executable with PyInstaller (--onedir mode for CustomTkinter)
echo Building executable with PyInstaller...
echo Using --onedir mode for CustomTkinter compatibility...
echo Changing to project root to ensure correct output location...
cd ..
pyinstaller --clean "build-tools\DJs_Timeline_Machine_v2.6.15.spec"
cd build-tools

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: PyInstaller build failed!
    echo.
    echo Troubleshooting tips:
    echo - Make sure CustomTkinter is installed: pip install customtkinter
    echo - Check if darkdetect is installed: pip install darkdetect
    echo - Verify all dependencies: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Verify the build was created in the right place
if exist "..\dist\DJs_Timeline_Machine_v2.6.15\DJs_Timeline_Machine_v2.6.15.exe" (
    echo.
    echo ========================================
    echo Build completed successfully!
    echo Application directory: ..\dist\DJs_Timeline_Machine_v2.6.15\
    echo Main executable: ..\dist\DJs_Timeline_Machine_v2.6.15\DJs_Timeline_Machine_v2.6.15.exe
    echo ========================================
    echo.
    echo CustomTkinter assets included: ..\dist\DJs_Timeline_Machine_v2.6.15\customtkinter\
    echo.
    echo Next step: Run build_installer_v2.6.15.bat to create the installer
    echo.
) else (
    echo.
    echo ERROR: Build completed but executable not found in expected location!
    echo Expected: ..\dist\DJs_Timeline_Machine_v2.6.15\DJs_Timeline_Machine_v2.6.15.exe
    echo.
    echo Checking where the build ended up:
    if exist "dist" (
        echo Found local dist folder:
        dir dist
    )
    if exist "..\dist" (
        echo Found project root dist folder:
        dir "..\dist"
    )
    echo.
)
pause