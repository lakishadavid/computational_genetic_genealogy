#!/bin/bash
# https://faculty.washington.edu/browning/beagle/beagle.html

echo "install_beagle.sh: running..."

# Function to determine if we're running in a Docker container
in_docker() {
    [ -f /.dockerenv ] || grep -Eq '(lxc|docker)' /proc/1/cgroup
}

# Function to handle sudo_cmd based on environment
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

# Define variables
BEAGLE_VERSION="17Dec24.224"
BEAGLE_JAR="beagle.${BEAGLE_VERSION}.jar"
BREF3_JAR="bref3.${BEAGLE_VERSION}.jar"
UNBREF3_JAR="unbref3.${BEAGLE_VERSION}.jar"
BEAGLE_URL="https://faculty.washington.edu/browning/beagle/${BEAGLE_JAR}"
BREF3_URL="https://faculty.washington.edu/browning/beagle/${BREF3_JAR}"
UNBREF3_URL="https://faculty.washington.edu/browning/beagle/${UNBREF3_JAR}"

# Check for Java installation
if ! command -v java &> /dev/null; then
    echo "Java is not installed. Running $base_directory/scripts_env/install_java.sh to install Java..."

    # Run the install_java.sh script
    if [ -f "$base_directory/scripts_env/install_java.sh" ]; then
        bash "$base_directory/scripts_env/install_java.sh"
        if [ $? -ne 0 ]; then
            echo "Failed to install Java. Please check the logs."
            exit 1
        fi
    else
        echo "Java installation script not found at $base_directory/scripts_env/install_java.sh."
        exit 1
    fi
else
    echo "Java is already installed."
fi

# Download Beagle
if [ ! -f "$utils_directory/$BEAGLE_JAR" ]; then
    echo "Downloading Beagle to $utils_directory..."
    wget -P "$utils_directory" "$BEAGLE_URL"
    if [ $? -ne 0 ]; then
        echo "Failed to download Beagle."
        exit 1
    fi
else
    echo "Beagle already downloaded at $utils_directory/$BEAGLE_JAR."
fi

# Download bref3 utility
if [ ! -f "$utils_directory/$BREF3_JAR" ]; then
    echo "Downloading bref3 utility to $utils_directory..."
    wget -P "$utils_directory" "$BREF3_URL"
    if [ $? -ne 0 ]; then
        echo "Failed to download bref3 utility."
        exit 1
    fi
else
    echo "bref3 utility already downloaded at $utils_directory/$BREF3_JAR."
fi

# Download unbref3 utility
if [ ! -f "$utils_directory/$UNBREF3_JAR" ]; then
    echo "Downloading unbref3 utility to $utils_directory..."
    wget -P "$utils_directory" "$UNBREF3_URL"
    if [ $? -ne 0 ]; then
        echo "Failed to download unbref3 utility."
        exit 1
    fi
else
    echo "unbref3 utility already downloaded at $utils_directory/$UNBREF3_JAR."
fi


# Derive the user's home directory from base_directory
user_home="${base_directory%/bagg_analysis}"
echo "Derived user home directory: $user_home"

# Add utils_directory to PATH
if ! grep -q "export PATH=\$PATH:$utils_directory" "$user_home/.bashrc"; then
    echo "export PATH=\$PATH:$utils_directory" >> "$user_home/.bashrc"
    echo "utils_directory added to PATH."
    source "$user_home/.bashrc"
else
    echo "utils_directory already in PATH."
fi


# Test Beagle installation
echo "Testing Beagle installation..."
java -jar "$utils_directory/$BEAGLE_JAR" 2>&1
if [ $? -ne 0 ]; then
    echo "Beagle test run failed."
    exit 1
else
    echo "Beagle installed successfully."
fi