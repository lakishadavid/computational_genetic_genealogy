#!/bin/bash

echo "install_plink2.sh: running..."

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

# Define PLINK2 download URL and file
plink2_file_url="https://s3.amazonaws.com/plink2-assets/alpha6/plink2_linux_x86_64_20241206.zip"
plink2_zip_file="$utils_directory/plink2_linux_x86_64_20241206.zip"
plink2_binary="$utils_directory/plink2"

# Download and unzip PLINK2 if not already present
if [ ! -f "$plink2_binary" ]; then
    echo
    echo "Downloading PLINK2..."
    echo
    wget --progress=bar:force:noscroll "$plink2_file_url" -P "$utils_directory"
    
    # Ensure the file is downloaded before unzipping
    while [ ! -f "$plink2_zip_file" ]; do
        sleep 1
    done

    echo
    echo "Unzipping PLINK2..."
    echo
    unzip "$plink2_zip_file" -d "$utils_directory"

    # Remove the zip file after extraction
    rm "$plink2_zip_file"
fi

# Check if the PLINK2 binary was installed correctly
if [ -f "$plink2_binary" ] && [ -x "$plink2_binary" ]; then
    echo "PLINK2 installed successfully. Version:"
    "$plink2_binary" --version
else
    echo "Error: PLINK2 installation failed. Binary not found or not executable."
    exit 1
fi

echo "PLINK2 installation completed successfully."