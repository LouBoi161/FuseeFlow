#!/bin/bash
set -e

# Define URLs for tools
LINUXDEPLOY_URL="https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage"
QT_PLUGIN_URL="https://github.com/linuxdeploy/linuxdeploy-plugin-qt/releases/download/continuous/linuxdeploy-plugin-qt-x86_64.AppImage"

# Setup directories
APP_DIR=AppDir
rm -rf $APP_DIR
mkdir -p $APP_DIR/usr/bin
mkdir -p $APP_DIR/usr/share/icons/hicolor/scalable/apps
mkdir -p $APP_DIR/usr/lib

# 1. Prepare AppDir structure
echo "Setting up AppDir..."

# Copy source
cp main.py $APP_DIR/usr/bin/main.py
cp config.json $APP_DIR/usr/bin/ 2>/dev/null || true
cp *.svg *.png $APP_DIR/usr/bin/

# Copy binary dependencies
cp fusee-nano $APP_DIR/usr/bin/
chmod +x $APP_DIR/usr/bin/fusee-nano

# Manually bundle libusb for pyusb (since fusee-nano might be static or pyusb loads it via ctypes)
echo "Bundling libusb..."
cp /usr/lib/libusb-1.0.so.0 $APP_DIR/usr/lib/

# Copy Desktop file and Icon
cp fuseeflow.desktop $APP_DIR/fuseeflow.desktop
cp app_icon.svg $APP_DIR/usr/share/icons/hicolor/scalable/apps/app_icon.svg
cp app_icon.svg $APP_DIR/app_icon.svg

# 2. Bundle Python Dependencies manually
echo "Bundling Python dependencies..."
python3 -m venv venv_build
source venv_build/bin/activate
pip install -r requirements.txt
# Find site-packages
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
PY_VER=$(python -c "import sys; print(f'python{sys.version_info.major}.{sys.version_info.minor}')")

# Copy site-packages to AppDir
# Move to /opt to avoid linuxdeploy scanning and trying to resolve dependencies for manylinux libs
mkdir -p $APP_DIR/opt/python
cp -r "$SITE_PACKAGES" $APP_DIR/opt/python/site-packages

# CLEANUP: Remove unused Qt modules to save space
# We still do this to reduce size
echo "Cleaning up unused PyQt6 modules..."
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/qml
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/plugins/qml*
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/plugins/assetimporters
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/plugins/geometryloaders
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/lib/libQt6Quick*
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/lib/libQt63D*
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/lib/libQt6Qml*
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/lib/libQt6Designer*
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/lib/libQt6Help*
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/lib/libQt6Labs*
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/lib/libQt6Sensors*
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/lib/libQt6SerialPort*
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/lib/libQt6Test*
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/lib/libQt6Web*
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/lib/libQt6Multimedia*
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/lib/libQt6Positioning*
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/lib/libQt6Nfc*
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/lib/libQt6Pdf*
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/lib/libQt6TextToSpeech*
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/lib/libQt6VirtualKeyboard*
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/lib/libQt6Wayland*
rm -rf $APP_DIR/opt/python/site-packages/PyQt6/Qt6/lib/libQt6WlShell*

deactivate

# 3. Download linuxdeploy tools
if [ ! -f linuxdeploy-x86_64.AppImage ]; then
    echo "Downloading linuxdeploy..."
    wget -q $LINUXDEPLOY_URL
    chmod +x linuxdeploy-x86_64.AppImage
fi

# 4. Create AppRun
cat > $APP_DIR/AppRun << EOF
#!/bin/bash
HERE="\$(dirname "\$(readlink -f "\${0}")")"
export PATH="\${HERE}/usr/bin:\${PATH}"
export LD_LIBRARY_PATH="\${HERE}/usr/lib:\${LD_LIBRARY_PATH}"

# Setup Python Path
export PYTHONPATH="\${HERE}/opt/python/site-packages:\${PYTHONPATH}"

# Launch
exec python3 "\${HERE}/usr/bin/main.py" "\$@"
EOF
chmod +x $APP_DIR/AppRun

# 5. Build AppImage
echo "Building AppImage..."

# We rely on the pip-installed PyQt6 being self-contained.
# We do NOT use the Qt plugin because it conflicts with the manylinux libs in the wheel.

./linuxdeploy-x86_64.AppImage \
    --appdir $APP_DIR \
    -d fuseeflow.desktop \
    -i app_icon.svg \
    --output appimage

echo "Done! FuseeFlow-x86_64.AppImage created."
rm -rf venv_build
