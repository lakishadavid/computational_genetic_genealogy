#!/bin/bash
# JupyterLite build script with proper configuration injection

# Setup error handling
set -e

# Get absolute path to script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
LABS_DIR="$ROOT_DIR/labs"
DATA_DIR="$ROOT_DIR/data/class_data"

echo "===== Building JupyterLite environment ====="

# Clean previous builds
rm -rf "$SCRIPT_DIR/app"

# Build JupyterLite with proper configuration
echo "Running JupyterLite build with configuration..."
# Use the local jupyter_lite_config.json
poetry run jupyter lite build --config="$SCRIPT_DIR/jupyter_lite_config.json" --output-dir="$SCRIPT_DIR/app"

# Verify build success
if [ ! -d "$SCRIPT_DIR/app" ]; then
  echo "Error: Build failed - app directory not created"
  exit 1
fi

# Now manually copy lab notebooks
echo "Copying lab notebooks..."
if [ ! -d "$SCRIPT_DIR/app/files" ]; then
  mkdir -p "$SCRIPT_DIR/app/files"
fi

# Copy lab notebooks (excluding instructor notebooks)
for NOTEBOOK in "$LABS_DIR"/Lab*.ipynb; do
  if [ -f "$NOTEBOOK" ]; then
    BASENAME=$(basename "$NOTEBOOK")
    if [[ ! "$BASENAME" == *"For_Instructor"* ]]; then
      cp "$NOTEBOOK" "$SCRIPT_DIR/app/files/"
      echo "  Copied $BASENAME"
    fi
  fi
done

# Create class_data directory
echo "Setting up class_data directory..."
mkdir -p "$SCRIPT_DIR/app/files/class_data"
echo "# Class Data Directory" > "$SCRIPT_DIR/app/files/class_data/README.md"

# Copy class data if it exists
if [ -d "$DATA_DIR" ] && [ "$(ls -A "$DATA_DIR" 2>/dev/null)" ]; then
  cp -r "$DATA_DIR"/* "$SCRIPT_DIR/app/files/class_data/"
  echo "  Copied class_data from $DATA_DIR"
fi

# Fix app name in HTML files if needed
echo "Checking HTML files for title updates..."
for HTML_FILE in $(find "$SCRIPT_DIR/app" -name "*.html"); do
  if grep -q 'title>JupyterLite' "$HTML_FILE"; then
    sed -i 's|<title>JupyterLite</title>|<title>Computational Genetic Genealogy</title>|g' "$HTML_FILE"
    echo "  Updated title in $(basename "$HTML_FILE")"
  fi
done

# Make sure labs with numbers work correctly
echo "Creating lab file symlinks for direct access..."
cd "$SCRIPT_DIR/app/files"
for FILE in Lab*.ipynb; do
  if [[ $FILE =~ Lab([0-9]+)_ ]]; then
    LAB_NUM="${BASH_REMATCH[1]}"
    ln -sf "$FILE" "lab${LAB_NUM}.ipynb"
    echo "  Created symlink lab${LAB_NUM}.ipynb -> $FILE"
  fi
done

echo "Build complete!"