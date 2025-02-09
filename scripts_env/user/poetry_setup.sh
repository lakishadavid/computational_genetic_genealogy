#!/bin/bash

source "$(dirname "$0")/../utils/common.sh"

if [ "$(id -u)" == "0" ]; then
    error_msg "Poetry setup should not be run as root"
    exit 1
fi

separator
highlight "Installing Poetry..."
separator

# Check if Poetry is already installed
if command -v poetry &>/dev/null; then
    echo "Poetry is already installed at $(which poetry)"
else
    # Remove conflicting symlink if it exists
    if [ -L "/usr/local/bin/poetry" ]; then
        echo "Removing conflicting Poetry symlink..."
        sudo_cmd rm /usr/local/bin/poetry
    fi

    # Install Poetry in user space
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# Verify installation
if ! command -v poetry &>/dev/null; then
    error_msg "Poetry installation failed or is not in PATH."
    exit 1
fi

# Configure Poetry
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true

# Fix Poetry cache permissions
if [ -d "$HOME/.cache/poetry" ] && [ "$(stat -c '%U' "$HOME/.cache/poetry")" != "$USER" ]; then
    echo "Fixing Poetry cache ownership..."
    sudo_cmd chown -R "$USER:$USER" "$HOME/.cache/poetry"
fi

# Install project dependencies
if [ -f "pyproject.toml" ] && [ -f "poetry.lock" ]; then
    poetry install --no-root
else
    echo "Warning: pyproject.toml or poetry.lock not found in $(pwd)"
fi