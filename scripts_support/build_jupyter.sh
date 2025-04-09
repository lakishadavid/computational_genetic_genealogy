#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
STAGING_DIR="jupyterlite_staging"       # Temporary area for preparing content
DEPLOY_DIR="docs/jupyterlite_app"       # Final location AND build target
LAB_SRC_DIR="labs"
DATA_SRC_DIR="data/class_data"
ROOT_CONFIG_FILE="jupyter_lite_config.json" # Explicit root config file

# --- Script Start ---
echo "Starting enhanced JupyterLite build process..."

# 1. Clean up previous build artifacts
echo "Cleaning up previous directories ($STAGING_DIR and $DEPLOY_DIR)..."
rm -rf "$STAGING_DIR"
rm -rf "$DEPLOY_DIR" # Remove the old deployment target dir first

# 1b. Ensure the root config file exists (create if not)
if [ ! -f "$ROOT_CONFIG_FILE" ]; then
    echo "Creating empty root config file: $ROOT_CONFIG_FILE"
    echo "{}" > "$ROOT_CONFIG_FILE"
fi

# 2. Create staging directories
echo "Creating staging directory structure in $STAGING_DIR..."
mkdir -p "$STAGING_DIR/class_data"
mkdir -p "$STAGING_DIR/results"  # Add results directory for student work
mkdir -p "$STAGING_DIR/images"   # Add images directory

# 3. Process and copy lab notebooks to staging area
echo "Processing and copying Lab notebooks ($LAB_SRC_DIR/Lab*.ipynb) to $STAGING_DIR..."

# Run the enhanced preprocessing script
echo "Preprocessing notebooks with enhanced compatibility..."
poetry run python -m scripts_support.preprocess_notebooks "$LAB_SRC_DIR" "$STAGING_DIR"

# 4. Copy the cross-compatibility module
echo "Copying lab_cross_compatibility module..."
mkdir -p "$STAGING_DIR/scripts_support"
cp scripts_support/lab_cross_compatibility.py "$STAGING_DIR/scripts_support/"
# Create an __init__.py file to make it a proper package
touch "$STAGING_DIR/scripts_support/__init__.py"

# 5. Run the JupyterLite build command directly into DEPLOY_DIR
echo "Running JupyterLite build directly into $DEPLOY_DIR using $ROOT_CONFIG_FILE..."
poetry run jupyter lite build \
    --config "$ROOT_CONFIG_FILE" \
    --contents "$STAGING_DIR" \
    --output-dir "$DEPLOY_DIR"

# 6. Copy class data files instead of symlinks
echo "Copying class data files to $DEPLOY_DIR/files/class_data..."
mkdir -p "$DEPLOY_DIR/files/class_data"

# Remove any existing class_data content to avoid conflicts
rm -rf "$DEPLOY_DIR/files/class_data"/*

# Copy all content in the class_data directory
for file in "$DATA_SRC_DIR"/*; do
    if [ -d "$file" ]; then
        # For directories, copy the entire directory
        cp -r "$file" "$DEPLOY_DIR/files/class_data/"
    else
        # For regular files, copy the file
        cp "$file" "$DEPLOY_DIR/files/class_data/"
    fi
done

# 7. Create results directory for student work
echo "Creating results directory for student work..."
mkdir -p "$DEPLOY_DIR/files/results"

# 8. Copy images if they exist
if [ -d "$LAB_SRC_DIR/images" ]; then
    echo "Copying images..."
    mkdir -p "$DEPLOY_DIR/files/images"
    cp "$LAB_SRC_DIR/images"/* "$DEPLOY_DIR/files/images/"
fi

# 9. Clean up temporary staging directory ONLY
echo "Cleaning up temporary staging directory ($STAGING_DIR)..."
rm -rf "$STAGING_DIR"

# --- Script End ---
echo "Enhanced build successful!"
echo "JupyterLite site generated directly in: $DEPLOY_DIR"
echo "The site includes:"
echo "- Processed notebooks with cross-compatibility"
echo "- A results directory for student work"
echo "- The lab_cross_compatibility.py helper module"
echo "- Class data files"
echo "- Images (if available)"
echo "Remember to check/update .gitignore if needed and add $DEPLOY_DIR to Git."

exit 0