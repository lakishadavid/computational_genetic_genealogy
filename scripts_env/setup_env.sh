#!/bin/bash

# How to run this script:
# bash scripts_env/setup_env.sh
# sudo bash scripts_env/setup_env.sh

set -e  # Exit immediately if a command exits with a non-zero status
set -o pipefail  # Exit on pipe errors
# set -x  # Print commands before execution

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"

separator
highlight "Starting environment setup..."

# For system packages, use sudo if not in Docker
if ! in_docker; then
    highlight "Installing system packages (requires sudo)..."
    sudo bash "${SCRIPT_DIR}/system/packages.sh"
else
    highlight "Installing system packages..."
    bash "${SCRIPT_DIR}/system/packages.sh"
fi

# Setup paths (as user)
highlight "Setting up paths..."
bash "${SCRIPT_DIR}/user/path_setup.sh"

# Install and configure Poetry (as user)
highlight "Setting up Poetry..."
bash "${SCRIPT_DIR}/user/poetry_setup.sh"

# Run the installation scripts (as user)
highlight "Running installation scripts..."
bash "${SCRIPT_DIR}/user/run_install_scripts.sh"

separator
highlight "✅ Setup completed! Your environment is ready."
separator
echo "Your environment has been configured with:"
echo "- Updated system packages"
echo "- ~/.local/bin added to PATH"
echo "- System dependencies installed"
echo "- Poetry installed and configured"
echo "- Project dependencies installed"
echo "- Python kernel installed for Jupyter Notebooks"
echo "==============================================="
echo ""
echo ""
echo "==============================================="
echo "Now launching interactive directory setup..."
echo "Please follow the prompts to configure your directories."
echo "==============================================="

# Setup directories (as user)
highlight "Setting up directories..."
bash "${SCRIPT_DIR}/user/directory_setup.sh"