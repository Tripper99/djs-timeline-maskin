#!/bin/bash
# Build script for DJs Timeline Machine v2.6.20 macOS .app bundle
# Produces a native .app and optionally a .dmg disk image for distribution

set -e  # Exit on error

VERSION="2.6.20"
APP_NAME="DJs_Timeline_Machine"
APP_DISPLAY_NAME="DJs Timeline Machine"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="${PROJECT_ROOT}/build"
DIST_DIR="${PROJECT_ROOT}/dist"
APP_BUNDLE="${DIST_DIR}/${APP_DISPLAY_NAME}.app"

echo "========================================="
echo "Building ${APP_DISPLAY_NAME} v${VERSION} for macOS"
echo "========================================="

# Step 1: Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "ERROR: Virtual environment is not activated!"
    echo "Please run: source venv/bin/activate"
    exit 1
fi

echo "Virtual environment active: $VIRTUAL_ENV"

# Step 2: Check macOS
if [ "$(uname)" != "Darwin" ]; then
    echo "ERROR: This build script is for macOS only!"
    exit 1
fi

ARCH=$(uname -m)
echo "Architecture: $ARCH"

# Step 3: Install PyInstaller if not already installed
echo ""
echo "Checking for PyInstaller..."
if ! python -m PyInstaller --version &> /dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
else
    echo "PyInstaller is installed: $(python -m PyInstaller --version 2>&1)"
fi

# Step 4: Check that .icns icon exists
ICNS_ICON="${PROJECT_ROOT}/Agg-med-smor-v4-transperent.icns"
if [ ! -f "$ICNS_ICON" ]; then
    echo "ERROR: macOS icon file not found: $ICNS_ICON"
    echo "Please convert the .ico to .icns first."
    exit 1
fi
echo "Icon file found: $ICNS_ICON"

# Step 5: Clean previous build
echo ""
echo "Cleaning previous build..."
rm -rf "${DIST_DIR}/${APP_NAME}_v${VERSION}"
rm -rf "${DIST_DIR}/${APP_DISPLAY_NAME}.app"
rm -rf "${BUILD_DIR}/${APP_NAME}_v${VERSION}"
echo "Cleaned previous build files"

# Step 6: Run PyInstaller with macOS spec
echo ""
echo "Running PyInstaller..."
cd "${PROJECT_ROOT}"
pyinstaller --clean --noconfirm "build-tools/${APP_NAME}_v${VERSION}_macOS.spec"
echo "PyInstaller build complete"

# Step 7: Verify .app bundle was created
if [ ! -d "$APP_BUNDLE" ]; then
    echo "ERROR: .app bundle was not created at: $APP_BUNDLE"
    echo "Check PyInstaller output above for errors."
    exit 1
fi

echo ""
echo ".app bundle created: $APP_BUNDLE"
APP_SIZE=$(du -sh "$APP_BUNDLE" | cut -f1)
echo "Size: $APP_SIZE"

# Step 8: Create DMG for distribution (optional)
echo ""
echo "Creating DMG disk image for distribution..."
DMG_NAME="${APP_NAME}_v${VERSION}_macOS_${ARCH}.dmg"
DMG_PATH="${DIST_DIR}/${DMG_NAME}"
DMG_TEMP="${BUILD_DIR}/dmg_temp"

# Clean up any previous DMG
rm -f "$DMG_PATH"
rm -rf "$DMG_TEMP"

# Create temporary directory for DMG contents
mkdir -p "$DMG_TEMP"
cp -R "$APP_BUNDLE" "$DMG_TEMP/"

# Create a symlink to /Applications for drag-and-drop install
ln -s /Applications "$DMG_TEMP/Applications"

# Create DMG using hdiutil
hdiutil create -volname "${APP_DISPLAY_NAME} v${VERSION}" \
    -srcfolder "$DMG_TEMP" \
    -ov -format UDZO \
    "$DMG_PATH"

# Clean up temp
rm -rf "$DMG_TEMP"

if [ -f "$DMG_PATH" ]; then
    DMG_SIZE=$(du -sh "$DMG_PATH" | cut -f1)
    echo "DMG created: $DMG_PATH"
    echo "DMG size: $DMG_SIZE"
fi

# Step 9: Success message
echo ""
echo "========================================="
echo "BUILD SUCCESSFUL!"
echo "========================================="
echo ""
echo ".app bundle: $APP_BUNDLE ($APP_SIZE)"
if [ -f "$DMG_PATH" ]; then
    echo "DMG file:    $DMG_PATH ($DMG_SIZE)"
fi
echo ""
echo "To test the app:"
echo "  open \"$APP_BUNDLE\""
echo ""
echo "NOTE: Since the app is unsigned, on first launch:"
echo "  1. Right-click the .app and select 'Open'"
echo "  2. Click 'Open' in the Gatekeeper dialog"
echo "  3. Or: System Settings > Privacy & Security > Open Anyway"
echo ""
echo "Settings will be saved to: ~/.djs_timeline_machine/"
echo "========================================="
