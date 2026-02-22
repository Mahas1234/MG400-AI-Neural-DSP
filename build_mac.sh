#!/bin/bash
set -e

echo "Building MG400 AI Generator for macOS Production..."

# Install packaging tools and dependencies
pip install -r requirements.txt
pip install pyinstaller dmgbuild

# 1. Clean previous builds
rm -rf build/ dist/ *.spec

# 2. Generate Spec and Build the standalone execution binary using PyInstaller
echo "Compiling execution binaries using PyInstaller..."
pyinstaller --name "MG400_AI_Generator" \
            --windowed \
            --noconfirm \
            --clean \
            app.py

echo "Build complete! Initiating DMG compression workflow..."
APP_NAME="MG400_AI_Generator.app"
DMG_NAME="MG400_AI_Generator_v1.0.dmg"

# 3. Create intuitive macOS DMG container targeting the newly built PyInstaller app
echo "Injecting binaries into Drag-and-Drop Volume container..."
dmgbuild -s build_dmg_settings.py "MG400 AI Generator" "dist/$DMG_NAME"

echo "Production bundle successfully built! Location: dist/$DMG_NAME"
