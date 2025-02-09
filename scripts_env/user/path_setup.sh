#!/bin/bash

source "$(dirname "$0")/../utils/common.sh"

if [ "$(id -u)" == "0" ]; then
    error_msg "User setup should not be run as root"
    exit 1
fi

separator
highlight "Setting up user paths and directories..."
separator

if [ ! -d "$HOME/.local" ]; then
    mkdir -p "$HOME/.local"
fi

# Add ~/.local/bin to PATH
if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' ~/.bashrc; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo "Added ~/.local/bin to PATH in ~/.bashrc"
else
    echo "~/.local/bin is already in PATH in ~/.bashrc"
fi

# Apply path updates immediately
export PATH="$HOME/.local/bin:$PATH"

# Ensure correct ownership
CURRENT_USER=$(whoami)
if [ "$(stat -c '%U' "$HOME/.local")" != "$CURRENT_USER" ]; then
    echo "Fixing ownership of $HOME/.local..."
    sudo_cmd chown -R "$CURRENT_USER:$CURRENT_USER" "$HOME/.local"
fi