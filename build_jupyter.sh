#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
STAGING_DIR="jupyterlite_staging"
OUTPUT_DIR="jupyterlite_content"
LAB_SRC_DIR="labs"
DATA_SRC_DIR="data/class_data"

# --- Script Start ---
echo "Starting JupyterLite build process..."

# 1. Clean up previous build artifacts
echo "Cleaning up previous build directories ($STAGING_DIR and $OUTPUT_DIR)..."
rm -rf "$STAGING_DIR"
rm -rf "$OUTPUT_DIR"

# 2. Create staging directories
echo "Creating staging directory structure in $STAGING_DIR..."
mkdir -p "$STAGING_DIR/class_data"

# 3. Copy content to staging area
echo "Copying Lab notebooks ($LAB_SRC_DIR/Lab*.ipynb) to $STAGING_DIR..."
cp "$LAB_SRC_DIR"/Lab*.ipynb "$STAGING_DIR/"

echo "Copying class data ($DATA_SRC_DIR) to $STAGING_DIR/class_data..."
# Use trailing slash on source to copy contents
cp -r "$DATA_SRC_DIR"/. "$STAGING_DIR/class_data/"

# 4. Run the JupyterLite build command using Poetry
echo "Running JupyterLite build..."
poetry run jupyter lite build --contents "$STAGING_DIR" --output-dir "$OUTPUT_DIR"

# 5. Clean up staging directory (optional)
echo "Cleaning up staging directory ($STAGING_DIR)..."
rm -rf "$STAGING_DIR"

# --- Script End ---
echo "Build successful!"
echo "JupyterLite site generated in: $OUTPUT_DIR"
echo "To test locally, run:"
echo "cd $OUTPUT_DIR && poetry run python -m http.server 8000"
echo "Then open http://localhost:8000 in your browser."

exit 0