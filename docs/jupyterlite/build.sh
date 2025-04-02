#!/bin/bash
# Build script for JupyterLite with Poetry - With Exclusion Feature

# Setup error handling
set -e

# Get absolute path to script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Script directory: $SCRIPT_DIR"

# Project root directory
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
echo "Project root: $ROOT_DIR"

# Labs directory containing original notebooks
LABS_DIR="$ROOT_DIR/labs"
echo "Labs directory: $LABS_DIR"

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
rm -rf "$ROOT_DIR/_output"
rm -rf "$ROOT_DIR/lab1" "$ROOT_DIR/lab2" "$ROOT_DIR/lab3"

# Create directory structure
mkdir -p "$SCRIPT_DIR/notebooks"
mkdir -p "$SCRIPT_DIR/_output"
mkdir -p "$SCRIPT_DIR/app"

# Prepare the contents array for jupyter_lite_config.json
echo "Preparing jupyter_lite_config.json contents..."
CONFIG_CONTENTS="["

# Find and copy only Lab notebooks from labs directory
echo "Finding and copying only Lab notebooks from labs directory..."
for NOTEBOOK in "$LABS_DIR"/Lab*.ipynb; do
    if [ -f "$NOTEBOOK" ]; then
        NOTEBOOK_NAME=$(basename "$NOTEBOOK")
        
        # Skip instructor notebooks
        if [[ "$NOTEBOOK_NAME" == *"For_Instructor"* ]]; then
            echo "Skipping instructor notebook: $NOTEBOOK_NAME"
            continue
        fi
        
        echo "Processing notebook: $NOTEBOOK_NAME"
        
        # Convert filename to lowercase for consistency
        LOWERCASE_NAME=$(echo "$NOTEBOOK_NAME" | tr '[:upper:]' '[:lower:]')
        
        # Extract lab number
        if [[ $NOTEBOOK_NAME =~ Lab([0-9]+) ]]; then
            LAB_NUM=${BASH_REMATCH[1]}
            LAB_DIR="$SCRIPT_DIR/notebooks/lab$LAB_NUM"
            mkdir -p "$LAB_DIR"
            
            # Copy the notebook
            cp "$NOTEBOOK" "$LAB_DIR/$LOWERCASE_NAME"
            
            # Add to config contents
            if [ "$CONFIG_CONTENTS" != "[" ]; then
                CONFIG_CONTENTS="$CONFIG_CONTENTS,"
            fi
            CONFIG_CONTENTS="$CONFIG_CONTENTS\"$LAB_DIR/$LOWERCASE_NAME\""
        fi
    fi
done

# Close the contents array
CONFIG_CONTENTS="$CONFIG_CONTENTS]"

# Ensure permissions are correct
chmod -R 755 "$SCRIPT_DIR"

# Dynamically create jupyter_lite_config.json
echo "Creating dynamic jupyter_lite_config.json..."
cat > "$SCRIPT_DIR/jupyter_lite_config.json" << EOF
{
  "LiteBuildConfig": {
    "contents": $CONFIG_CONTENTS
  }
}
EOF

# Build JupyterLite
echo "Building JupyterLite..."
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

# Create class_data directory and copy relevant files
echo "Setting up class_data directory..."
mkdir -p "$SCRIPT_DIR/_output/files/class_data"
touch "$SCRIPT_DIR/_output/files/class_data/README.md"
echo "# Class Data Directory\nThis directory contains datasets for computational genetic genealogy labs." > "$SCRIPT_DIR/_output/files/class_data/README.md"

# Copy all lab notebooks to the root directory for easier access
echo "Copying all notebooks to root for direct access..."
find "$SCRIPT_DIR/notebooks" -name "*.ipynb" -exec cp {} "$SCRIPT_DIR/_output/files/" \;

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

# After the build is complete, update the jupyter_lite_config.json
# to include class_data directory for future builds
echo "Updating jupyter_lite_config.json for future builds..."

# Create a JSON array of notebook paths, excluding instructor notebooks
NOTEBOOK_PATHS=$(find "$SCRIPT_DIR/notebooks" -name "*.ipynb" -not -name "*For_Instructor*" | sed 's/^/      "/;s/$/"/' | tr '\n' ',' | sed 's/,$//')

cat > "$SCRIPT_DIR/jupyter_lite_config.json" << EOF
{
  "LiteBuildConfig": {
    "contents": [
$NOTEBOOK_PATHS,
      {"from": "$SCRIPT_DIR/app/files/class_data", "to": "class_data"}
    ]
  }
}
EOF

echo "===== JupyterLite build complete ====="
echo "The JupyterLite environment is now available in the 'app' directory at:"
echo "$SCRIPT_DIR/app"
echo "Access it via: https://lakishadavid.github.io/computational_genetic_genealogy/jupyterlite/app/"