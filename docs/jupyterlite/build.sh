#!/bin/bash
# Build script for JupyterLite with Poetry

# Setup error handling
set -e

# Change to the script directory
cd "$(dirname "$0")"

echo "===== Building JupyterLite environment with Poetry ====="

# Install dependencies
echo "Installing dependencies with Poetry..."
poetry install --no-root

# Clean any previous build
echo "Cleaning previous build..."
rm -rf _output
rm -rf app
rm -rf .jupyter_lite_build.log
rm -rf .jupyterlite.doit.db

# Create directory structure
mkdir -p notebooks
mkdir -p _output
mkdir -p app

# Ensure permissions are correct
chmod -R 755 .

# Build JupyterLite
echo "Building JupyterLite..."
poetry run jupyter lite build --config jupyter_lite_config.json

# Copy notebooks to the build
echo "Copying notebooks to the build..."
if [ -d "_output" ]; then
    mkdir -p _output/files/notebooks
    if [ -d "notebooks" ] && [ "$(ls -A notebooks)" ]; then
        cp -r notebooks/* _output/files/notebooks/
    else
        echo "Warning: notebooks directory is empty or does not exist"
    fi
else
    echo "Warning: _output directory was not created during build"
fi

# Move build to the final location
echo "Moving build to the final location..."
if [ -d "_output" ]; then
    rm -rf app
    mv _output app
    echo "Build moved to app directory"
else
    echo "Error: _output directory does not exist, build may have failed"
    exit 1
fi

echo "===== JupyterLite build complete ====="
echo "The JupyterLite environment is now available in the 'app' directory"
echo "Access it via: https://lakishadavid.github.io/computational_genetic_genealogy/jupyterlite/app/"