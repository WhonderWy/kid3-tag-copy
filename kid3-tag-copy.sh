#!/bin/bash

LOGFILE=$(mktemp /tmp/kid3_tagcopy_log.XXXXXX)

# --- Helper Functions ---

check_kid3_cli() {
    if ! command -v kid3-cli >/dev/null 2>&1; then
        kdialog --error "kid3-cli not found in PATH. Please install kid3-cli."
        exit 1
    fi
}

log_line() {
    local msg="$1"
    local success="$2"
    if [ "$success" = true ]; then
        echo "[OK] $msg" >> "$LOGFILE"
    else
        echo "[ERROR] $msg" >> "$LOGFILE"
    fi
}

copy_and_paste_tags_bulk() {
    local src_files=("$@")
    local dst_files=("${DEST_FILES[@]}")

    if [ "${#src_files[@]}" -ne "${#dst_files[@]}" ]; then
        log_line "Source and destination counts do not match!" false
        kdialog --error "Source and destination counts do not match!"
        return 1
    fi

    for i in "${!src_files[@]}"; do
        local src="${src_files[$i]}"
        local dst="${dst_files[$i]}"

        log_line "Copying tags from: $src → $dst" true

        kid3-cli \
            -c "cd \"$(dirname "$src")\"" \
            -c "select \"$(basename "$src")\"" \
            -c "copy" \
            -c "cd \"$(dirname "$dst")\"" \
            -c "select \"$(basename "$dst")\"" \
            -c "paste" \
            -c "save"

        if [ $? -eq 0 ]; then
            log_line "Tags successfully copied from $src to $dst" true
        else
            log_line "ERROR copying tags from $src to $dst" false
        fi
    done
}

# --- Main ---

check_kid3_cli

# Launch persistent log window in background
kdialog --textbox "$LOGFILE" 600 400 &
LOG_PID=$!

# Ask user for source files
SRC_FILES=$(kdialog --getopenfilename . "*.mp3 *.flac *.m4a *.mp4 *.ogg *.wav *aiff *.wma *.dsf *.opus *.m4b *.mpc *.mpp *.mp+ *.ape *.wv *.wvc" --multiple --separate-output)
if [ -z "$SRC_FILES" ]; then
    log_line "No source files selected." false
    kill $LOG_PID
    exit 1
fi
SRC_FILES_ARRAY=($SRC_FILES)

# Ask user for destination files
DEST_FILES=$(kdialog --getopenfilename . "*.mp3 *.flac *.m4a *.mp4 *.ogg *.wav *aiff *.wma *.dsf *.opus *.m4b *.mpc *.mpp *.mp+ *.ape *.wv *.wvc" --multiple --separate-output)
if [ -z "$DEST_FILES" ]; then
    log_line "No destination files selected." false
    kill $LOG_PID
    exit 1
fi
DEST_FILES_ARRAY=($DEST_FILES)

# Run copy
copy_and_paste_tags_bulk "${SRC_FILES_ARRAY[@]}"

# Completion message
log_line "Tag copying completed." true
kdialog --msgbox "Tag copying completed."

# Cleanup
kill $LOG_PID
rm -f "$LOGFILE"
