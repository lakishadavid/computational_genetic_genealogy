#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
STAGING_DIR="jupyterlite_staging"       # Temporary area for preparing content
BUILD_OUTPUT_DIR="jupyterlite_build_temp" # Temporary build output directory
DEPLOY_DIR="docs/jupyterlite_app"       # Final location within docs for GitHub Pages
LAB_SRC_DIR="labs"
DATA_SRC_DIR="data/class_data"

# --- Script Start ---
echo "Starting JupyterLite build and deployment preparation..."

# 1. Clean up previous build/deployment artifacts
echo "Cleaning up previous directories ($STAGING_DIR, $BUILD_OUTPUT_DIR, $DEPLOY_DIR)..."
rm -rf "$STAGING_DIR"
rm -rf "$BUILD_OUTPUT_DIR"
rm -rf "$DEPLOY_DIR" # Remove the old deployment target dir

# 2. Create staging directories
echo "Creating staging directory structure in $STAGING_DIR..."
mkdir -p "$STAGING_DIR/class_data"

# 3. Copy content to staging area
echo "Copying Lab notebooks ($LAB_SRC_DIR/Lab*.ipynb) to $STAGING_DIR..."
cp "$LAB_SRC_DIR"/Lab*.ipynb "$STAGING_DIR/"

echo "Copying class data ($DATA_SRC_DIR) to $STAGING_DIR/class_data..."
cp -r "$DATA_SRC_DIR"/. "$STAGING_DIR/class_data/"

# 4. Run the JupyterLite build command into the temporary output dir
echo "Running JupyterLite build into $BUILD_OUTPUT_DIR..."
poetry run jupyter lite build --contents "$STAGING_DIR" --output-dir "$BUILD_OUTPUT_DIR"

# 5. Create the final deployment directory within docs
echo "Creating deployment directory $DEPLOY_DIR..."
mkdir -p "$DEPLOY_DIR"

# 6. Copy built application to the deployment directory
echo "Copying built application from $BUILD_OUTPUT_DIR to $DEPLOY_DIR..."
# Copy the *contents* of the build output directory
cp -r "$BUILD_OUTPUT_DIR"/. "$DEPLOY_DIR/"

# 7. Clean up temporary directories (staging and build output)
echo "Cleaning up temporary directories ($STAGING_DIR and $BUILD_OUTPUT_DIR)..."
rm -rf "$STAGING_DIR"
rm -rf "$BUILD_OUTPUT_DIR"

# --- Script End ---
echo "Build successful!"
echo "JupyterLite site generated and placed in: $DEPLOY_DIR"
echo "Add $DEPLOY_DIR to Git, commit, and push to deploy via GitHub Pages."
echo "The expected base URL on GitHub Pages will be: https://lakishadavid.github.io/computational_genetic_genealogy/$(basename $DEPLOY_DIR)/lab/index.html"

exit 0