#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"

highlight "Setting up Python environment for directory configuration..."

# Ensure Python and pip are installed
if ! command -v python3 &> /dev/null; then
    error_msg "Python3 is not installed. Installing..."
    sudo_cmd apt-get update
    sudo_cmd apt-get install -y python3 python3-pip
fi

# Install required Python packages
highlight "Installing required Python packages..."
pip3 install --user python-decouple

# Run the Python directory setup script
highlight "Running directory setup script..."
python3 "${SCRIPT_DIR}/user/directory_setup.py"

if [ $? -ne 0 ]; then
    error_msg "Directory setup failed."
    exit 1
fi

success_msg "Directory setup completed successfully."