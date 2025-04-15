#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
STAGING_DIR="jupyterlite_staging"       # Temporary area for preparing content
DEPLOY_DIR="docs/jupyterlite_app"       # Final location AND build target
LAB_SRC_DIR="labs"                      # Original labs directory
LABV2_SRC_DIR="labs_v2"                 # New labs_v2 directory
DATA_SRC_DIR="data/class_data"
ROOT_CONFIG_FILE="jupyter_lite_config.json" # Explicit root config file

# =======================================================================================
# TRANSITION GUIDE: From dual "labs" and "labs_v2" to just "labs_v2"
# =======================================================================================
# This script is currently configured to build both the original "labs" content 
# and the new "labs_v2" content. This allows for a transition period where both 
# versions are available to students.
#
# When you're ready to fully transition to just using labs_v2 (e.g., after one month),
# follow these steps:
#
# 1. Comment out or remove the original labs processing steps:
#    - Comment out line: mkdir -p "$STAGING_DIR/images"
#    - Comment out lines 35-40 (Process original labs)
#    - Comment out lines 85-90 (Copy original labs images)
#
# 2. Rename "labs_v2" to "labs" in the JupyterLite output to make it the default:
#    - Change: poetry run python -m scripts_support.preprocess_notebooks "$LABV2_SRC_DIR" "$STAGING_DIR/labs_v2"
#      To: poetry run python -m scripts_support.preprocess_notebooks "$LABV2_SRC_DIR" "$STAGING_DIR"
#    - Remove or comment out line: mkdir -p "$STAGING_DIR/labs_v2"
#    - Change: mkdir -p "$DEPLOY_DIR/files/labs_v2/images"
#      To: mkdir -p "$DEPLOY_DIR/files/images"
#    - Remove line: mkdir -p "$DEPLOY_DIR/files/labs_v2"
#
# 3. Optionally update configuration variables for clarity:
#    - Change: LAB_SRC_DIR="labs" to LAB_SRC_DIR="labs_v2"
#    - Remove or comment out: LABV2_SRC_DIR="labs_v2"
#
# 4. Update index2.html to be index.html and ensure all links point to the right locations
#
# After these changes, the build script will only process labs_v2 notebooks, and they 
# will appear at the root level in JupyterLite, just as the original labs did.
# =======================================================================================

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
mkdir -p "$STAGING_DIR/labs_v2"  # Add directory for labs_v2 notebooks

# 3. Process and copy original lab notebooks to staging area
echo "Processing and copying original Lab notebooks ($LAB_SRC_DIR/Lab*.ipynb) to $STAGING_DIR..."

# Run the enhanced preprocessing script for original labs
echo "Preprocessing original notebooks with enhanced compatibility..."
poetry run python -m scripts_support.preprocess_notebooks "$LAB_SRC_DIR" "$STAGING_DIR"

# 3b. Process and copy labs_v2 notebooks to staging area
echo "Processing and copying labs_v2 notebooks ($LABV2_SRC_DIR/Lab*.ipynb) to $STAGING_DIR/labs_v2..."

# Run the enhanced preprocessing script for labs_v2
echo "Preprocessing labs_v2 notebooks with enhanced compatibility..."
poetry run python -m scripts_support.preprocess_notebooks "$LABV2_SRC_DIR" "$STAGING_DIR/labs_v2"

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

# 8b. Copy images from labs_v2 if they exist
if [ -d "$LABV2_SRC_DIR/images" ]; then
    echo "Copying labs_v2 images..."
    mkdir -p "$DEPLOY_DIR/files/labs_v2/images"
    cp "$LABV2_SRC_DIR/images"/* "$DEPLOY_DIR/files/labs_v2/images/"
fi

# 9. Ensure the labs_v2 directory exists in the final output
echo "Ensuring labs_v2 directory exists in final output..."
mkdir -p "$DEPLOY_DIR/files/labs_v2"

# 10. Clean up temporary staging directory ONLY
echo "Cleaning up temporary staging directory ($STAGING_DIR)..."
rm -rf "$STAGING_DIR"

# --- Script End ---
echo "Enhanced build successful!"
echo "JupyterLite site generated directly in: $DEPLOY_DIR"
echo "The site includes:"
echo "- Processed original notebooks with cross-compatibility"
echo "- Processed labs_v2 notebooks with cross-compatibility in labs_v2/ directory"
echo "- A results directory for student work"
echo "- The lab_cross_compatibility.py helper module"
echo "- Class data files"
echo "- Images (if available) for both original and labs_v2 notebooks"
echo "Remember to check/update .gitignore if needed and add $DEPLOY_DIR to Git."

exit 0