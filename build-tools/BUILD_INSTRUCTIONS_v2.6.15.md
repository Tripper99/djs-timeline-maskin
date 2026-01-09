# Build Instructions for DJs Timeline Machine v2.6.15

## ⚠️ CRITICAL: CustomTkinter Requirements

This application uses **CustomTkinter** which requires **special PyInstaller settings**. The standard single-file (`--onefile`) approach **WILL NOT WORK**. 

### CustomTkinter Compatibility Requirements:
- ✅ Must use `--onedir` mode (directory distribution)
- ✅ Must include CustomTkinter assets using `--add-data`
- ✅ Must include dependencies: `darkdetect`, `packaging`
- ❌ **Cannot use `--onefile`** - CustomTkinter will fail to start

## Prerequisites

### 1. Install Python Dependencies
```bash
pip install pyinstaller customtkinter darkdetect packaging
```

**All Required Dependencies:**
```bash
pip install customtkinter ttkbootstrap openpyxl xlsxwriter PyPDF2 pillow darkdetect packaging
```

### 2. Install Inno Setup 6
Download from: https://jrsoftware.org/isdl.php
- Choose the stable version (6.2.2 or later)
- Install with default settings

## Build Process

### Step 1: Build the Executable
1. Open Command Prompt or PowerShell
2. Navigate to the `build-tools` folder:
   ```
   cd "C:\Dropbox\Dokument\Python\APP DJs Timeline-maskin\DJs Timeline-maskin (projekt)\build-tools"
   ```
3. Run the build script:
   ```
   build_v2.6.15.bat
   ```
   This will create: `dist\DJs_Timeline_Machine_v2.6.15\` (directory with all files)

### Step 2: Create the Installer
1. After the executable is built successfully, run:
   ```
   build_installer_v2.6.15.bat
   ```
2. The installer will be created in: `installer_output\DJs_Timeline_Machine_v2.6.15_Setup.exe`

## What's Included

The installer will include:
- ✅ Complete application directory with all CustomTkinter assets
- ✅ Main executable with your custom icon (Agg-med-smor-v4-transperent.ico)
- ✅ CustomTkinter theme files and assets (required for GUI)
- ✅ All Python runtime libraries
- ✅ Swedish manual (Manual.rtf)
- ✅ English manual (DJs_Timeline-maskin_User_Manual.rtf)
- ✅ Desktop shortcut (optional during installation)
- ✅ Start menu shortcuts
- ✅ Uninstaller

## Features of the Installer

- **Multi-language**: Swedish and English installation
- **Professional appearance**: Modern wizard style
- **Compression**: LZMA2 maximum compression for smaller file size
- **Architecture**: Supports both 32-bit and 64-bit Windows
- **Clean uninstall**: Removes all files and shortcuts
- **Custom icon**: Uses your Agg-med-smor-v4-transperent.ico throughout

## Troubleshooting

### PyInstaller Issues
- If you get import errors, make sure all packages are installed:
  ```bash
  pip install customtkinter ttkbootstrap openpyxl xlsxwriter PyPDF2 pillow darkdetect packaging
  ```
- **CustomTkinter path errors**: The spec file automatically detects CustomTkinter location
- If detection fails, check the CustomTkinter location in the build output

### Inno Setup Not Found
- Make sure Inno Setup 6 is installed
- The script checks common installation paths
- If installed elsewhere, modify the path in `build_installer_v2.6.15.bat`

### Executable Won't Run
- **Most Common**: CustomTkinter assets missing - ensure `--onedir` mode was used
- Check Windows Defender/Antivirus - may need to add exception
- Verify CustomTkinter folder exists in the dist directory
- For debugging: temporarily set `console=True` in spec file to see error messages
- **Critical**: Never use `--onefile` with CustomTkinter applications

## Distribution

The final installer file (`DJs_Timeline_Machine_v2.6.15_Setup.exe`) can be distributed to users. They can simply run it to install the application with all necessary files.

## File Sizes (Approximate)
- Application Directory: ~60-80 MB (includes Python runtime, CustomTkinter assets, and all libraries)
- Installer: ~20-30 MB (compressed)

## Version Information
- Application Version: 2.6.15
- Build Date: 2025-08-21
- Icon: Agg-med-smor-v4-transperent.ico