# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for DJs Timeline Machine v2.6.20 - macOS
# Produces a native .app bundle for macOS (Apple Silicon arm64)
# Requires --onedir mode for CustomTkinter compatibility

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
    # Fallback - try import
    import customtkinter
    try:
        customtkinter_location = str(Path(customtkinter.__file__).parent)
    except:
        print("WARNING: Could not automatically detect CustomTkinter location")

print(f"CustomTkinter location: {customtkinter_location}")

a = Analysis(
    [str(project_root / 'app.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # CRITICAL: Include CustomTkinter assets (required for CustomTkinter to work)
        (customtkinter_location, 'customtkinter'),
        # Include the icon files
        (str(project_root / 'Agg-med-smor-v4-transperent.ico'), '.'),
        (str(project_root / 'Agg-med-smor-v4-transperent.icns'), '.'),
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
        'requests',  # For GitHub version checking
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
    name='DJs_Timeline_Machine_v2.6.20',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX not commonly available on macOS
    console=False,  # GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'Agg-med-smor-v4-transperent.icns'),
)

# CRITICAL: COLLECT section required for CustomTkinter (--onedir mode)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='DJs_Timeline_Machine_v2.6.20',
)

# macOS .app bundle
app = BUNDLE(
    coll,
    name='DJs Timeline Machine.app',
    icon=str(project_root / 'Agg-med-smor-v4-transperent.icns'),
    bundle_identifier='com.tripper99.djs-timeline-machine',
    info_plist={
        'CFBundleName': 'DJs Timeline Machine',
        'CFBundleDisplayName': 'DJs Timeline Machine',
        'CFBundleShortVersionString': '2.6.20',
        'CFBundleVersion': '2.6.20',
        'CFBundlePackageType': 'APPL',
        'NSHighResolutionCapable': True,
        'NSAppleEventsUsageDescription': 'DJs Timeline Machine needs access to send Apple Events.',
        'LSMinimumSystemVersion': '11.0',
    },
)
