# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for DJs Timeline Machine v2.6.17
# Updated for CustomTkinter compatibility (requires --onedir mode)
# Added requests library for GitHub version checking feature

import os
import sys
from pathlib import Path

# Get the project root directory
project_root = Path(SPECPATH).parent

# Find CustomTkinter installation path
customtkinter_location = None
for path in sys.path:
    potential_path = Path(path) / 'customtkinter'
    if potential_path.exists():
        customtkinter_location = str(potential_path)
        break

if not customtkinter_location:
    # Fallback - try common locations
    import customtkinter
    try:
        customtkinter_location = str(Path(customtkinter.__file__).parent)
    except:
        customtkinter_location = r'C:\Users\dan\AppData\Local\Programs\Python\Python313\Lib\site-packages\customtkinter'

print(f"CustomTkinter location: {customtkinter_location}")

a = Analysis(
    [str(project_root / 'app.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # CRITICAL: Include CustomTkinter assets (required for CustomTkinter to work)
        (customtkinter_location, 'customtkinter'),
        # Include the icon file
        (str(project_root / 'Agg-med-smor-v4-transperent.ico'), '.'),
        # Include documentation files
        (str(project_root / 'docs' / 'Manual.rtf'), 'docs'),
        (str(project_root / 'docs' / 'DJs_Timeline-maskin_User_Manual.rtf'), 'docs'),
    ],
    hiddenimports=[
        'customtkinter',
        'darkdetect',  # Required by CustomTkinter
        'ttkbootstrap',
        'openpyxl',
        'xlsxwriter', 
        'PyPDF2',
        'tkinter',
        'PIL',
        'PIL._tkinter_finder',
        'packaging',  # Required by CustomTkinter
        'requests',  # Added for GitHub version checking
        'urllib3',  # Dependency of requests
        'certifi',  # SSL certificates for requests
        'charset_normalizer',  # Dependency of requests
        'idna',  # Dependency of requests
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
    ],
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # CRITICAL: Must be True for --onedir mode
    name='DJs_Timeline_Machine_v2.6.17',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'Agg-med-smor-v4-transperent.ico'),
)

# CRITICAL: COLLECT section required for CustomTkinter (--onedir mode)
# Running from project root, so dist will be created in correct location
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DJs_Timeline_Machine_v2.6.17',
)