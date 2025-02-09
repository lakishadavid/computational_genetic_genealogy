#!/bin/bash
# Script to install ped-sim
# https://github.com/williamslab/ped-sim

echo "install_ped_sim.sh: running..."

# Function to determine if we're running in a Docker container
in_docker() {
    [ -f /.dockerenv ] || grep -Eq '(lxc|docker)' /proc/1/cgroup
}

# Function to handle sudo based on environment
sudo_cmd() {
    if in_docker; then
        "$@"
    else
        sudo "$@"
    fi
}

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

# Check and install required packages
if ! dpkg -l | grep -q libboost-all-dev; then
    echo "Installing required packages..."
    sudo_cmd apt-get update
    sudo_cmd apt-get install -y libboost-all-dev make
    if [ $? -ne 0 ]; then
        echo "Failed to install required packages."
        exit 1
    fi
else
    echo "Required packages are already installed."
fi

# Define ped-sim repository details
PED_SIM_REPO="https://github.com/williamslab/ped-sim.git"

# Check for Git installation
if ! command -v git &> /dev/null; then
    echo "Git is not installed. Please install Git and rerun this script."
    exit 1
fi

# Clone ped-sim repository
if [ ! -d "$utils_directory/ped-sim" ]; then
    echo "Cloning ped-sim repository into $utils_directory..."
    git clone --recurse-submodules "$PED_SIM_REPO" "$utils_directory/ped-sim"
    if [ $? -ne 0 ]; then
        echo "Failed to clone ped-sim repository."
        exit 1
    fi
else
    echo "ped-sim repository already exists in $utils_directory/ped-sim."
fi

# Navigate to ped-sim directory and build
cd "$utils_directory/ped-sim" || { echo "Failed to navigate to $utils_directory/ped-sim."; exit 1; }
echo "Building ped-sim using make..."
make
if [ $? -ne 0 ]; then
    echo "Failed to build ped-sim. Please check the logs for details."
    exit 1
fi

chmod +x ./ped-sim

echo

# Verify ped-sim installation
if [ -x "./ped-sim" ]; then
    echo "ped-sim installed successfully..."
else
    echo "ped-sim executable not found. Build might have failed."
    exit 1
fi