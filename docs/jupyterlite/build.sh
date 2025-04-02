#!/bin/bash
# Minimal JupyterLite build script

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

# Create minimal config
cat > "$SCRIPT_DIR/jupyter_lite_config.json" << EOF
{
  "LiteBuildConfig": {}
}
EOF

# Build JupyterLite with minimal configuration
echo "Running minimal JupyterLite build..."
poetry run jupyter lite build --output-dir="$SCRIPT_DIR/app"

# Verify build success
if [ ! -d "$SCRIPT_DIR/app" ]; then
  echo "Error: Build failed - app directory not created"
  exit 1
fi

# Check if basic interface works
echo "Build complete! Try accessing the basic JupyterLite interface at:"
echo "http://localhost:8000/lab/ (using python -m http.server 8000 in the app directory)"