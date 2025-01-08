#!/bin/bash

echo "install_java.sh: running..."

# Define utils_directory prioritizing /home/ubuntu
if [ -d "/home/ubuntu/bagg_analysis/utils" ]; then
    utils_directory="/home/ubuntu/bagg_analysis/utils"
else
    # Fall back to finding any other matching directory
    utils_directory=$(find /home -type d -path "*/bagg_analysis/utils" 2>/dev/null | head -n 1)
fi

# Ensure the utils directory exists
if [ -z "$utils_directory" ]; then
    echo "Error: utils_directory not found in /home/ubuntu or /home/*/bagg_analysis/utils."
    exit 1
fi

echo "Using utils_directory: $utils_directory"

echo "Starting Java installation process..."

# Check if Java is already installed
if command -v java &> /dev/null; then
    echo "Java is already installed. Version: $(java -version 2>&1 | head -n 1)"
    exit 0
fi

# Update the package list
echo "Updating package list..."
sudo apt-get update -y

# Install Java
echo "Installing Java (default-jdk)..."
sudo apt-get install -y default-jdk

# Verify installation
if command -v java &> /dev/null; then
    echo "Java installation successful. Version: $(java -version 2>&1 | head -n 1)"
else
    echo "Java installation failed. Please check the log at $LOGFILE for details."
    exit 1
fi

# Verify Java Home
JAVA_HOME=$(readlink -f /usr/bin/java | sed "s:/bin/java::")
if [ -n "$JAVA_HOME" ]; then
    echo "JAVA_HOME detected: $JAVA_HOME"
    if ! grep -q "export JAVA_HOME=$JAVA_HOME" "$HOME/.bashrc"; then
        echo "Adding JAVA_HOME to .bashrc..."
        echo "export JAVA_HOME=$JAVA_HOME" >> "$HOME/.bashrc"
        echo "export PATH=\$JAVA_HOME/bin:\$PATH" >> "$HOME/.bashrc"
        source "$HOME/.bashrc"
    else
        echo "JAVA_HOME already set in .bashrc."
    fi
else
    echo "Failed to detect JAVA_HOME. Please set it manually if required."
fi

echo "Java installation process completed."
