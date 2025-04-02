#!/bin/bash
# Build script for JupyterLite with Poetry

# Setup error handling
set -e

# Get absolute path to script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Script directory: $SCRIPT_DIR"

# Change to the script directory
cd "$SCRIPT_DIR"

echo "===== Building JupyterLite environment with Poetry ====="

# Install dependencies
echo "Installing dependencies with Poetry..."
poetry install --no-root

# Clean any previous builds in both script directory and root
echo "Cleaning previous builds..."
rm -rf "$SCRIPT_DIR/_output"
rm -rf "$SCRIPT_DIR/app"
rm -rf "$SCRIPT_DIR/.jupyter_lite_build.log"
rm -rf "$SCRIPT_DIR/.jupyterlite.doit.db"

# Also clean up any stray builds at the project root
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
echo "Project root: $ROOT_DIR"
rm -rf "$ROOT_DIR/_output"
rm -rf "$ROOT_DIR/lab1" "$ROOT_DIR/lab2" "$ROOT_DIR/lab3"

# Create directory structure
mkdir -p "$SCRIPT_DIR/notebooks"
mkdir -p "$SCRIPT_DIR/notebooks/lab1"
mkdir -p "$SCRIPT_DIR/notebooks/lab2"
mkdir -p "$SCRIPT_DIR/notebooks/lab3"
mkdir -p "$SCRIPT_DIR/_output"
mkdir -p "$SCRIPT_DIR/app"

# Ensure permissions are correct
chmod -R 755 "$SCRIPT_DIR"

# Build JupyterLite
echo "Building JupyterLite..."
# Use absolute paths in the command
cd "$SCRIPT_DIR"
poetry run jupyter lite build --output-dir="$SCRIPT_DIR/_output"

# Copy notebooks to the build
echo "Copying notebooks to the build..."
if [ -d "$SCRIPT_DIR/_output" ]; then
    mkdir -p "$SCRIPT_DIR/_output/files/notebooks"
    if [ -d "$SCRIPT_DIR/notebooks" ] && [ "$(ls -A "$SCRIPT_DIR/notebooks")" ]; then
        cp -r "$SCRIPT_DIR/notebooks"/* "$SCRIPT_DIR/_output/files/notebooks/"
    else
        echo "Warning: notebooks directory is empty or does not exist"
    fi
else
    echo "Warning: _output directory was not created during build"
fi

# Move build to the final location
echo "Moving build to the final location..."
if [ -d "$SCRIPT_DIR/_output" ]; then
    rm -rf "$SCRIPT_DIR/app"
    mv "$SCRIPT_DIR/_output" "$SCRIPT_DIR/app"
    echo "Build moved to app directory"
else
    echo "Error: _output directory does not exist, build may have failed"
    exit 1
fi

echo "===== JupyterLite build complete ====="
echo "The JupyterLite environment is now available in the 'app' directory at:"
echo "$SCRIPT_DIR/app"
echo "Access it via: https://lakishadavid.github.io/computational_genetic_genealogy/jupyterlite/app/"