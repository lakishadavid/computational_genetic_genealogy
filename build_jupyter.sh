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
echo "Starting JupyterLite build process directly into deployment directory..."

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

# 3. Copy content to staging area
echo "Copying Lab notebooks ($LAB_SRC_DIR/Lab*.ipynb) to $STAGING_DIR..."
# Ensure only .ipynb files are copied if that's desired
# If you have other 'Lab*' files/dirs you want, change back to Lab*
cp "$LAB_SRC_DIR"/Lab*.ipynb "$STAGING_DIR/"

# 4. Run the JupyterLite build command directly into DEPLOY_DIR
echo "Running JupyterLite build directly into $DEPLOY_DIR using $ROOT_CONFIG_FILE..."
# NOTE: Output dir is now DEPLOY_DIR
poetry run jupyter lite build \
    --config "$ROOT_CONFIG_FILE" \
    --contents "$STAGING_DIR" \
    --output-dir "$DEPLOY_DIR"

# 5. Create symlinks for class data instead of copying
echo "Creating symlinks for class data in $DEPLOY_DIR/files/class_data..."
mkdir -p "$DEPLOY_DIR/files/class_data"

# Remove any existing class_data content to avoid conflicts
rm -rf "$DEPLOY_DIR/files/class_data"/*

# Create symlinks for all content in the class_data directory
for file in "$DATA_SRC_DIR"/*; do
    if [ -d "$file" ]; then
        # For directories, create the directory and symlink contents
        dirname=$(basename "$file")
        mkdir -p "$DEPLOY_DIR/files/class_data/$dirname"
        
        # Symlink files within the directory
        for subfile in "$file"/*; do
            ln -s "$(readlink -f "$subfile")" "$DEPLOY_DIR/files/class_data/$dirname/$(basename "$subfile")"
        done
    else
        # For regular files, create symlink
        ln -s "$(readlink -f "$file")" "$DEPLOY_DIR/files/class_data/$(basename "$file")"
    fi
done

# 6. Create lowercase symlinks for notebooks for better compatibility
echo "Creating lowercase symlinks for notebooks..."
for notebook in "$DEPLOY_DIR/files"/Lab*.ipynb; do
    if [ -f "$notebook" ]; then
        # Create lowercase version of the filename
        lowercase_name=$(basename "$notebook" | tr '[:upper:]' '[:lower:]')
        ln -s "$(basename "$notebook")" "$DEPLOY_DIR/files/$lowercase_name"
    fi
done

# 7. Clean up temporary staging directory ONLY
echo "Cleaning up temporary staging directory ($STAGING_DIR)..."
rm -rf "$STAGING_DIR"

# --- Script End ---
echo "Build successful!"
echo "JupyterLite site generated directly in: $DEPLOY_DIR"
echo "Remember to check/update .gitignore if needed and add $DEPLOY_DIR to Git."
echo "Commit and push to deploy via GitHub Pages."
echo "The expected base URL on GitHub Pages is: https://lakishadavid.github.io/computational_genetic_genealogy/$(basename $DEPLOY_DIR)/lab/index.html"

exit 0