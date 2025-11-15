#!/usr/bin/env bash
set -e

# --- Configuration ---
APP_NAME="Kid3 Tag Copier"
APP_EXEC="kid3-tag-copy.py"
APP_VERSION=${1:-"1.0"}  # Get version from command line argument or default to 1.0
APPDIR="./AppDir"
DIST_DIR="./dist"
ICON_FILE="$APPDIR/kid3.png"
DESKTOP_FILE="$APPDIR/kid3-tag-copy.desktop"
APPIMAGETOOL="./appimagetool-x86_64.AppImage"
VENV_DIR="./venv_appimage"
PYTHON_BIN="$(which python3 || true)"

# --- Choose build method ---
BUILD_METHOD="appimagetool"  # default: appimagetool
for arg in "$@"; do
    case $arg in
        --method=briefcase) BUILD_METHOD="briefcase" ;;
        --method=appimagetool) BUILD_METHOD="appimagetool" ;;
        --method=pyappimage) BUILD_METHOD="pyappimage" ;;
    esac
done

echo "⚙️ Build method: $BUILD_METHOD"

# --- Checks ---
if [ -z "$PYTHON_BIN" ]; then
    echo "❌ Python3 not found. Please install Python3."
    exit 1
fi

mkdir -p "$APPDIR" "$DIST_DIR"

# --- Step 1: Detect ImageMagick (v6 or v7) ---
echo "🔍 Detecting ImageMagick..."

if command -v magick >/dev/null; then
    IM_CMD="magick"
    echo "✨ Using ImageMagick 7 (magick)"
elif command -v convert >/dev/null; then
    IM_CMD="convert"
    echo "✨ Using ImageMagick 6 (convert)"
else
    echo "⚠️ No ImageMagick installation found. Skipping icon generation."
    IM_CMD=""
fi

# --- Step 2: Generate icon ---
if [ -n "$IM_CMD" ]; then
    echo "🎨 Generating icon using $IM_CMD..."
    "$IM_CMD" -size 256x256 \
    gradient:lightblue-darkblue \
    -fill white -stroke black -strokewidth 2 \
    -draw "translate 128,128 text -50,0 '♪'" \
    -gravity south -pointsize 36 -annotate +0+20 "Kid3" \
    "$ICON_FILE"
fi

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

if [ "$BUILD_METHOD" == "briefcase" ]; then
    pip install briefcase
elif [ "$BUILD_METHOD" == "pyappimage" ]; then
    pip install pyappimage
fi

deactivate

# Copy application files into AppDir
echo "📂 Copying files into AppDir..."
cp "$APP_EXEC" "$APPDIR/"
[ -f setup.py ] && cp setup.py "$APPDIR/"

# Copy venv into AppDir for portable execution
cp -r "$VENV_DIR" "$APPDIR/venv"

# --- Step 5: Build AppImage ---
case "$BUILD_METHOD" in

    appimagetool)
        if [ ! -f "$APPIMAGETOOL" ]; then
            echo "⬇️ Downloading AppImageTool..."
            wget -O "$APPIMAGETOOL" https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
            chmod +x "$APPIMAGETOOL"
        fi

        echo "🛠️ Building AppImage with appimagetool..."
        "$APPIMAGETOOL" "$APPDIR" "$DIST_DIR/kid3-tag-copy-$APP_VERSION.AppImage"
        ;;

    briefcase)
        echo "🛠️ Building with Briefcase..."
        source "$VENV_DIR/bin/activate"
        briefcase create linux --name "kid3-tag-copy" --version "$APP_VERSION" --app "$APP_EXEC" --output "$DIST_DIR"
        briefcase build linux
        briefcase package linux
        deactivate
        ;;

    pyappimage)
        echo "🛠️ Building with PyAppImage..."
        source "$VENV_DIR/bin/activate"
        pyappimage -v "$APP_VERSION" -d "$APPDIR" -o "$DIST_DIR/kid3-tag-copy-$APP_VERSION.AppImage"
        deactivate
        ;;

esac

echo "✅ Done! AppImage created in $DIST_DIR"
