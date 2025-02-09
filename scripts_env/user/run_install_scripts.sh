#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../utils/common.sh"

# Check if running as root
if [ "$(id -u)" == "0" ] && ! in_docker; then
    error_msg "Installation scripts should not be run as root."
    exit 1
fi

separator
highlight "Executing install scripts..."
separator

# Directory containing the install scripts
SCRIPTS_DIR="scripts_env"

# Scripts to exclude
EXCLUDE_SCRIPTS=("install_docker.sh" "install_bonsaitree.sh" "install_yhaplo.sh")

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

# Find all install scripts except excluded ones
INSTALL_SCRIPTS=()
for script in "$SCRIPTS_DIR"/install_*.sh; do
    if [[ -f "$script" ]] && ! should_exclude "$script"; then
        INSTALL_SCRIPTS+=("$script")
    fi
done

# Ensure install scripts were found
if [[ ${#INSTALL_SCRIPTS[@]} -eq 0 ]]; then
    echo "No installation scripts found in $SCRIPTS_DIR."
    exit 1
fi

# Run each script
for script in "${INSTALL_SCRIPTS[@]}"; do
    highlight "Running $script..."
    
    if [[ ! -x "$script" ]]; then
        echo "Fixing permissions: Making $script executable..."
        chmod +x "$script"
    fi

    # Run the script
    if ! bash "$script"; then
        error_msg "Error: Script $script failed."
        exit 1
    fi
done

success_msg "All installation scripts executed successfully."