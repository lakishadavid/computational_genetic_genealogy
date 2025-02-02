#!/bin/bash
# https://github.com/williamslab/ibis

echo "install_ibis.sh: running..."

# ------------------------------------------------------------------------------
# 1. Define directories relative to current location
# ------------------------------------------------------------------------------
base_directory="$(pwd)"  # Current directory (computational_genetic_genealogy)

# Define utils_directory based on base_directory
utils_directory="$base_directory/utils"

# Ensure the utils_directory exists
if [ ! -d "$utils_directory" ]; then
    mkdir -p "$utils_directory"
    if [ $? -ne 0 ]; then
        echo "Failed to create utils_directory: $utils_directory"
        exit 1
    fi
fi

echo "Using base_directory: $base_directory"
echo "Using utils_directory: $utils_directory"

# Define IBIS repository details
IBIS_REPO="https://github.com/williamslab/ibis.git"

# Check for Git installation
if ! command -v git &> /dev/null; then
    echo "Git is not installed. Please install Git and rerun this script."
    exit 1
fi

# Clone IBIS repository
if [ ! -d "$utils_directory/ibis" ]; then
    echo "Cloning IBIS repository into $utils_directory..."
    git clone --recurse-submodules "$IBIS_REPO" "$utils_directory/ibis"
    if [ $? -ne 0 ]; then
        echo "Failed to clone IBIS repository."
        exit 1
    fi
else
    echo "IBIS repository already exists in $utils_directory/ibis."
fi

# Navigate to IBIS directory and build
cd "$utils_directory/ibis" || { echo "Failed to navigate to $utils_directory/ibis."; exit 1; }
echo "Building IBIS using make..."
make
if [ $? -ne 0 ]; then
    echo "Failed to build IBIS. Please check the logs for details."
    exit 1
fi

echo
echo

# Verify IBIS installation
if [ -x "./ibis" ]; then
    echo "IBIS installed successfully..."
else
    echo "IBIS executable not found. Build might have failed."
    exit 1
fi
