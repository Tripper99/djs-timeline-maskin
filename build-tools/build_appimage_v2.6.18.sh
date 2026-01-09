#!/bin/bash
# Build script for DJs Timeline Machine v2.6.18 AppImage
# This script builds a Linux AppImage from the Python application

set -e  # Exit on error

VERSION="2.6.18"
APP_NAME="DJs_Timeline_Machine"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="${PROJECT_ROOT}/build"
DIST_DIR="${PROJECT_ROOT}/dist"
APPDIR="${BUILD_DIR}/${APP_NAME}_v${VERSION}.AppDir"

echo "========================================="
echo "Building ${APP_NAME} v${VERSION} AppImage"
echo "========================================="

# Step 1: Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "ERROR: Virtual environment is not activated!"
    echo "Please run: source ../venv/bin/activate"
    exit 1
fi

echo "✓ Virtual environment active: $VIRTUAL_ENV"

# Step 2: Install PyInstaller if not already installed
echo ""
echo "Checking for PyInstaller..."
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
else
    echo "✓ PyInstaller is installed"
fi

# Step 3: Clean previous build
echo ""
echo "Cleaning previous build..."
rm -rf "${DIST_DIR}/${APP_NAME}_v${VERSION}"
rm -rf "${BUILD_DIR}/${APP_NAME}_v${VERSION}"
echo "✓ Cleaned previous build files"

# Step 4: Run PyInstaller
echo ""
echo "Running PyInstaller..."
cd "${PROJECT_ROOT}"
pyinstaller --clean --noconfirm "build-tools/${APP_NAME}_v${VERSION}.spec"
echo "✓ PyInstaller build complete"

# Step 5: Create AppDir structure
echo ""
echo "Creating AppDir structure..."
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/lib"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

# Step 6: Copy PyInstaller output to AppDir
echo "Copying application files..."
if [ ! -d "${DIST_DIR}/${APP_NAME}_v${VERSION}" ]; then
    echo "ERROR: PyInstaller output not found at ${DIST_DIR}/${APP_NAME}_v${VERSION}"
    exit 1
fi
cp -r "${DIST_DIR}/${APP_NAME}_v${VERSION}/"* "${APPDIR}/usr/bin/" 2>/dev/null || cp -r "${DIST_DIR}/${APP_NAME}_v${VERSION}"/* "${APPDIR}/usr/bin/"
echo "✓ Application files copied"

# Step 7: Create AppRun script
echo "Creating AppRun script..."
cat > "${APPDIR}/AppRun" << 'APPRUN_EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
cd "${HERE}/usr/bin"
exec "./DJs_Timeline_Machine_v2.6.18" "$@"
APPRUN_EOF
chmod +x "${APPDIR}/AppRun"
echo "✓ AppRun script created"

# Step 8: Create .desktop file
echo "Creating .desktop file..."
cat > "${APPDIR}/usr/share/applications/${APP_NAME}_v${VERSION}.desktop" << DESKTOP_EOF
[Desktop Entry]
Type=Application
Name=DJs Timeline Machine
Comment=Timeline management tool for journalists and researchers
Exec=DJs_Timeline_Machine_v${VERSION}
Icon=DJs_Timeline_Machine_v${VERSION}
Categories=Office;Utility;
Terminal=false
DESKTOP_EOF
echo "✓ .desktop file created"

# Step 9: Create icon (convert .ico to .png if needed)
echo "Checking for icon..."
ICON_FILE="${PROJECT_ROOT}/Agg-med-smor-v4-transperent.ico"
if [ -f "${ICON_FILE}" ]; then
    # Try to convert ico to png using ImageMagick if available
    if command -v convert &> /dev/null; then
        echo "Converting icon..."
        convert "${ICON_FILE}" -resize 256x256 "${APPDIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}_v${VERSION}.png"
        echo "✓ Icon converted"
    else
        echo "WARNING: ImageMagick not found, cannot convert icon. Copying as-is..."
        cp "${ICON_FILE}" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}_v${VERSION}.png"
    fi
else
    echo "WARNING: Icon file not found, creating placeholder"
    # Create a simple placeholder icon
    echo "P3 256 256 255" > "${APPDIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}_v${VERSION}.ppm"
fi

# Step 10: Create symlinks for AppImage
cd "${APPDIR}"
ln -sf "usr/share/applications/${APP_NAME}_v${VERSION}.desktop" "${APP_NAME}_v${VERSION}.desktop"
ln -sf "usr/share/icons/hicolor/256x256/apps/${APP_NAME}_v${VERSION}.png" "${APP_NAME}_v${VERSION}.png"
ln -sf "${APP_NAME}_v${VERSION}.png" .DirIcon
cd "${PROJECT_ROOT}"

echo "✓ AppDir structure complete"

# Step 11: Download appimagetool if not present
APPIMAGETOOL="appimagetool-x86_64.AppImage"
APPIMAGETOOL_PATH="${SCRIPT_DIR}/${APPIMAGETOOL}"
if [ ! -f "${APPIMAGETOOL_PATH}" ]; then
    echo ""
    echo "Downloading appimagetool..."
    wget -O "${APPIMAGETOOL_PATH}" "https://github.com/AppImage/AppImageKit/releases/download/continuous/${APPIMAGETOOL}"
    chmod +x "${APPIMAGETOOL_PATH}"
    echo "✓ appimagetool downloaded"
else
    echo "✓ appimagetool already present"
fi

# Step 12: Build AppImage
echo ""
echo "Building AppImage..."
OUTPUT_FILE="${PROJECT_ROOT}/${APP_NAME}_v${VERSION}-x86_64.AppImage"
rm -f "${OUTPUT_FILE}"

cd "${PROJECT_ROOT}"
ARCH=x86_64 "${APPIMAGETOOL_PATH}" "${APPDIR}" "${OUTPUT_FILE}"

# Step 13: Make AppImage executable
chmod +x "${OUTPUT_FILE}"

# Step 14: Success message
echo ""
echo "========================================="
echo "✓ BUILD SUCCESSFUL!"
echo "========================================="
echo "AppImage created: ${OUTPUT_FILE}"
echo "Size: $(du -h "${OUTPUT_FILE}" | cut -f1)"
echo ""
echo "To test the AppImage:"
echo "  \"${OUTPUT_FILE}\""
echo ""
echo "The AppImage can be distributed and run on any Linux system."
echo "Settings will be saved to: ~/.djs_timeline_machine/"
echo "========================================="
