#!/usr/bin/env bash
set -e

# --- Configuration ---
APP_NAME="Kid3 Tag Copier"
APP_EXEC="kid3-tag-copy.py"
APP_VERSION="1.0"
APPDIR="./AppDir"
DIST_DIR="./dist"
ICON_FILE="$APPDIR/kid3.png"
DESKTOP_FILE="$APPDIR/kid3-tag-copy.desktop"
APPIMAGETOOL="./appimagetool-x86_64.AppImage"
PYTHON_BIN="$(which python3 || true)"

# --- Checks ---
if [ -z "$PYTHON_BIN" ]; then
    echo "❌ Python3 not found. Please install Python3."
    exit 1
fi

mkdir -p "$APPDIR" "$DIST_DIR"

# --- Step 1: Generate Kid3-like icon ---
echo "🎨 Generating icon..."
magick -size 256x256 \
    gradient:lightblue-darkblue \
    -fill white -stroke black -strokewidth 2 \
    -draw "translate 128,128 text -50,0 '♪'" \
    -gravity south -pointsize 36 -annotate +0+20 "Kid3" \
    "$ICON_FILE"

# --- Step 2: Create desktop file ---
echo "📝 Creating desktop file..."
cat > "$DESKTOP_FILE" <<EOL
[Desktop Entry]
Name=$APP_NAME
Comment=Copy tags between audio files using Kid3
Exec=./$APP_EXEC
Icon=kid3
Terminal=false
Type=Application
Categories=Audio;AudioVideo;Utility;
StartupNotify=true
EOL

# --- Step 3: Set up Python virtual environment ---
VENV_DIR="./venv_appimage"
echo "🐍 Setting up virtual environment..."
$PYTHON_BIN -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

echo "⬇️ Installing dependencies..."
pip install --upgrade pip
pip install PySide6

deactivate

# Copy application files into AppDir
echo "📂 Copying files into AppDir..."
cp "$APP_EXEC" "$APPDIR/"
cp setup.py "$APPDIR/"

# Copy venv into AppDir for portable execution
cp -r "$VENV_DIR" "$APPDIR/venv"

# --- Step 4: Download appimagetool if missing ---
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "⬇️ Downloading AppImageTool..."
    wget -O "$APPIMAGETOOL" https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x "$APPIMAGETOOL"
fi

# --- Step 5: Make AppImage ---
echo "🛠️ Building AppImage..."
"$APPIMAGETOOL" "$APPDIR" "$DIST_DIR/kid3-tag-copy-$APP_VERSION.AppImage"

echo "✅ Done! AppImage created in $DIST_DIR/kid3-tag-copy-$APP_VERSION.AppImage"
