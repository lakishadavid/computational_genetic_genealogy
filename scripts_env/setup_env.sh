#!/bin/bash

# setup.sh: Configuration script for computational genetic genealogy environment
# This script:
# - Updates your system packages
# - Adds ~/.local/bin to PATH for installed executables
# - Installs Python kernel for Jupyter Notebooks in VSCode

set -e  # Exit immediately if a command exits with a non-zero status
set -o pipefail  # Exit on pipe errors
# set -x  # Print commands before execution
# revised

echo "Starting environment setup..."

# Update system packages
echo "Updating system packages..."
sudo apt-get update -y

sudo apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    gcc \
    make \
    python3 \
    python3-pip \
    python3-dev \
    graphviz \
    libfreetype-dev \
    pkg-config \
    libpng-dev \
    zlib1g-dev \
    libbz2-dev \
    libharfbuzz-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    wget \
    curl \
    git \
    unzip \
    default-jre \
    gawk \
    libboost-all-dev 

sudo apt-get clean
sudo rm -rf /var/lib/apt/lists/*

# Add local bin to PATH
if ! grep -q "# BEGIN custom PATH additions" ~/.bashrc; then
    cat << 'EOF' >> ~/.bashrc
# BEGIN custom PATH additions
export PATH="$HOME/.local/bin:$PATH"
# END custom PATH additions
EOF
fi

source ~/.bashrc

# Create and set permissions for local directories if they don't exist
if [ ! -d "$HOME/.local" ]; then
    mkdir -p "$HOME/.local"
    sudo chown -R $USER:$USER "$HOME/.local"
fi

# Install Poetry
echo "Installing Poetry..."
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"

# Configure Poetry to install in user space
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true

poetry --version || { echo "Poetry installation failed"; exit 1; }

if [ -d "$HOME/.cache/poetry" ]; then
    sudo chown -R $USER:$USER "$HOME/.cache/poetry"
fi

# Find the computational_genetic_genealogy directory
REPO_PATH=$(find ~ -maxdepth 3 -type d -name "computational_genetic_genealogy" 2>/dev/null | head -n 1)

# Validate that REPO_PATH was found
if [ -z "$REPO_PATH" ]; then
    echo "Error: computational_genetic_genealogy directory not found."
    exit 1
fi

echo "Project directory found: $REPO_PATH"
cd "$REPO_PATH" || { echo "Error: Failed to change directory to $REPO_PATH"; exit 1; }

echo "Installing project dependencies with Poetry..."

if ! command -v poetry &>/dev/null; then
    echo "Error: Poetry is not installed correctly or is not in PATH."
    exit 1
fi

# Ensure we're in the correct project root
if [ -f "pyproject.toml" ] && [ -f "poetry.lock" ]; then
    poetry install --no-root
else
    echo "Warning: pyproject.toml or poetry.lock not found in $(pwd)"
fi

export PATH="$HOME/.local/bin:$PATH"

# Find and run all install scripts in order
echo "Finding installation scripts..."

# Directory containing the install scripts
SCRIPTS_DIR="scripts_env"

# Scripts to exclude
EXCLUDE_SCRIPTS=("setup_env.sh" "install_docker.sh" "mount_efs.sh" "install_yhaplo.sh")

# Function to check if a script should be excluded
should_exclude() {
    local script="$1"
    for exclude in "${EXCLUDE_SCRIPTS[@]}"; do
        if [[ "$(basename "$script")" == "$exclude" ]]; then
            return 0  # true, should exclude
        fi
    done
    return 1  # false, should not exclude
}

# Find and sort install scripts
INSTALL_SCRIPTS=()
for script in "$SCRIPTS_DIR"/install_*.sh; do
    if [[ -f "$script" ]] && ! should_exclude "$script"; then
        INSTALL_SCRIPTS+=("$script")
    fi
done

# Run each script
for script in "${INSTALL_SCRIPTS[@]}"; do
    echo "Running $script..."
    
    if [[ ! -x "$script" ]]; then
        echo "Fixing permissions: Making $script executable..."
        chmod +x "$script"
    fi

    # Run the script
    if ! bash "$script"; then
        echo "Error: Script $script failed."
        exit 1
    fi
done

echo "All installation scripts executed successfully."

echo
echo
echo "==============================================="
echo "Setup completed!"
echo "Your environment has been configured with:"
echo "- Updated system packages"
echo "- ~/.local/bin added to PATH"
echo "- System dependencies"
echo "- Poetry installed and configured"
echo "- Project dependencies installed"
echo "- Python kernel installed for Jupyter Notebooks"
echo "==============================================="
