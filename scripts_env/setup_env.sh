#!/bin/bash

set -e
set -o pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"

# Detect current user
USER_ID=$(id -u)
USER_NAME=$(whoami)

# Print environment debugging info
highlight "🛠️ Environment Debugging:"
echo "🔹 Running as user: $USER_NAME (UID: $USER_ID)"

# Ensure the script is not being run as root
if [[ "$USER_ID" -eq 0 ]]; then
    highlight "❌ Error: This script should not be run as root!"
    echo "Please restart as a normal user: "
    echo "   bash scripts_env/setup_env.sh"
    exit 1
fi

# Set up directory structure first
highlight "Setting up directory structure..."
bash "${SCRIPT_DIR}/user/directory_setup.sh"

# Install system packages (requires sudo)
highlight "Installing system packages (requires sudo)..."
sudo bash "${SCRIPT_DIR}/system/packages.sh"

# User-specific setup
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
echo "- Project directory structure"
echo "- Updated system packages"
echo "- ~/.local/bin added to PATH"
echo "- System dependencies installed"
echo "- Poetry installed and configured"
echo "- Project dependencies installed"
echo "- Python kernel installed for Jupyter Notebooks"

separator
echo "🚀 Your development environment is ready!"
separator

echo "📢 Begin coding in your configured environment!"
echo

# Check if VS Code is available
if command -v code >/dev/null 2>&1; then
    echo "📢 To start working with VS Code, simply enter the following command in this terminal window:"
    echo
    echo "    code ."
    echo
else
    echo "⚠️  The 'code' command is not available in your PATH."
    echo "Please ensure Visual Studio Code is installed and its command line tools are set up."
    echo "For instructions, see: https://code.visualstudio.com/docs/setup/setup-overview"
    echo
fi

separator