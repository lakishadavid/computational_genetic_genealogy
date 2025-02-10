#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status
set -o pipefail  # Exit on pipe errors
# set -x  # Print commands before execution

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"

# 🛠️ **Detect current user**
USER_ID=$(id -u)
USER_NAME=$(whoami)

# 🛠️ **Print environment debugging info**
highlight "🛠️ Environment Debugging:"
echo "🔹 Running as user: $USER_NAME (UID: $USER_ID)"

# 🛠️ **Ensure the script is not being run as root for user setup**
if [[ "$USER_ID" -eq 0 ]]; then
    highlight "❌ Error: This script should not be run as root for user setup!"
    echo "Please restart as a normal user: "
    echo "   bash scripts_env/setup_env.sh"
    exit 1
fi

# 🛠️ **Install system packages (requires sudo)**
highlight "Installing system packages (requires sudo)..."
sudo bash "${SCRIPT_DIR}/system/packages.sh"

# 🛠️ **User-specific setup (must NOT be root)**
highlight "Setting up paths..."
bash "${SCRIPT_DIR}/user/path_setup.sh"

highlight "Setting up Poetry..."
bash "${SCRIPT_DIR}/user/poetry_setup.sh"

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
echo "==============================================="
echo "Now launching interactive directory setup..."
echo "Please follow the prompts to configure your directories."
echo "==============================================="

# 🛠️ **Setup directories (as user)**
highlight "Setting up directories..."
bash "${SCRIPT_DIR}/user/directory_setup.sh"