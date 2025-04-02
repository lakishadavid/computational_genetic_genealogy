#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
STAGING_DIR="jupyterlite_staging"       # Temporary area for preparing content
# BUILD_OUTPUT_DIR="jupyterlite_build_temp" # REMOVED - Building directly
DEPLOY_DIR="docs/jupyterlite_app"       # Final location AND build target
LAB_SRC_DIR="labs"
DATA_SRC_DIR="data/class_data"
ROOT_CONFIG_FILE="jupyter_lite_config.json"

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
cp "$LAB_SRC_DIR"/Lab*.ipynb "$STAGING_DIR/"

echo "Copying class data ($DATA_SRC_DIR) to $STAGING_DIR/class_data..."
cp -r "$DATA_SRC_DIR"/. "$STAGING_DIR/class_data/"

# 4. Run the JupyterLite build command directly into DEPLOY_DIR
echo "Running JupyterLite build directly into $DEPLOY_DIR using $ROOT_CONFIG_FILE..."
# NOTE: Output dir is now DEPLOY_DIR
poetry run jupyter lite build \
    --config "$ROOT_CONFIG_FILE" \
    --contents "$STAGING_DIR" \
    --output-dir "$DEPLOY_DIR"

# 5. Create the final deployment directory within docs (Not needed, build creates it)
# echo "Creating deployment directory $DEPLOY_DIR..."
# mkdir -p "$DEPLOY_DIR"

# 6. Copy built application to the deployment directory (REMOVED - Built directly)
# echo "Copying built application from $BUILD_OUTPUT_DIR to $DEPLOY_DIR..."
# cp -r "$BUILD_OUTPUT_DIR"/. "$DEPLOY_DIR/"

# 7. Clean up temporary staging directory ONLY
echo "Cleaning up temporary staging directory ($STAGING_DIR)..."
rm -rf "$STAGING_DIR"
# rm -rf "$BUILD_OUTPUT_DIR" # REMOVED

# --- Script End ---
echo "Build successful!"
echo "JupyterLite site generated directly in: $DEPLOY_DIR"
echo "Add $DEPLOY_DIR to Git, commit, and push to deploy via GitHub Pages."
echo "The expected base URL on GitHub Pages will be: https://lakishadavid.github.io/computational_genetic_genealogy/$(basename $DEPLOY_DIR)/lab/index.html"

exit 0