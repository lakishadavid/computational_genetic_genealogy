#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../utils/common.sh"

# Check if running as root
if [ "$(id -u)" == "0" ] && ! in_docker; then
    error_msg "Directory setup should not be run as root."
    exit 1
fi

separator
highlight "Setting up project directories..."

if in_docker; then
    if [ -t 0 ]; then
        # If a TTY is available, allow interactive execution inside Docker
        poetry run python -m scripts_env.directory_setup < /dev/tty
    else
        # If running in Docker without a terminal (e.g., inside a build), use non-interactive mode
        poetry run python -m scripts_env.directory_setup --non-interactive
    fi
else
    # Running on a real system interactively
    exec poetry run python -m scripts_env.directory_setup < /dev/tty
fi

success_msg "Directory setup completed."