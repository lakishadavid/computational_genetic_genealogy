#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"

highlight "Installing bcftools, samtools, and htslib..."

# Update package lists
echo "Updating package lists..."
if ! sudo_cmd apt-get update; then
    error_msg "Failed to update package lists"
    exit 1
fi

# Install base dependencies and tools
echo "Installing core packages..."
if ! sudo_cmd apt-get install -y bcftools samtools tabix; then
    error_msg "Failed to install core packages"
    exit 1
fi

# Optional: Install additional development libraries
echo "Installing additional development libraries..."
if ! sudo_cmd apt-get install -y \
    libbz2-dev \
    liblzma-dev \
    zlib1g-dev \
    libgsl-dev \
    libcurl4-openssl-dev; then
    error_msg "Failed to install development libraries"
    exit 1
fi

# Verify installations
separator
highlight "Verifying installations..."

# Function to check and report version
check_version() {
    local cmd=$1
    local name=$2
    echo "Checking $name version:"
    if ! $cmd --version; then
        error_msg "$name not found"
        return 1
    fi
}

check_version "tabix" "HTSlib" || exit 1
check_version "samtools" "Samtools" || exit 1
check_version "bcftools" "BCFtools" || exit 1

success_msg "Installation completed successfully."