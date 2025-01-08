#!/bin/bash
# https://github.com/browning-lab/hap-ibd

echo "install_hap_ibd.sh: running..."

# Define base_directory prioritizing /home/ubuntu
if [ -d "/home/ubuntu/bagg_analysis" ]; then
    base_directory="/home/ubuntu/bagg_analysis"
else
    # Fall back to finding any other matching directory
    base_directory=$(find /home -type d -path "*/bagg_analysis" 2>/dev/null | head -n 1)
fi

# Ensure the base_directory exists
if [ -z "$base_directory" ]; then
    echo "Error: base_directory not found in /home/ubuntu or /home/*/bagg_analysis."
    exit 1
fi

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
HAP_IBD_URL="https://faculty.washington.edu/browning/hap-ibd.jar"
HAP_IBD_JAR="hap-ibd.jar"

# Check for Java installation
if ! command -v java &> /dev/null; then
    echo "Java is not installed. Running $base_directory/scripts_work/install_java.sh to install Java..."

    # Run the install_java.sh script
    if [ -f "$base_directory/scripts_env/install_java.sh" ]; then
        bash "$base_directory/scripts_env/install_java.sh"
        if [ $? -ne 0 ]; then
            echo "Failed to install Java. Please check the logs."
            exit 1
        fi
    else
        echo "Java installation script not found at $base_directory/scripts_work/install_java.sh."
        exit 1
    fi
else
    echo "Java is already installed."
fi

# Download Hap-IBD
if [ ! -f "$utils_directory/$HAP_IBD_JAR" ]; then
    echo "Downloading Hap-IBD to $utils_directory..."
    wget -P "$utils_directory" "$HAP_IBD_URL"
    if [ $? -ne 0 ]; then
        echo "Failed to download Hap-IBD."
        exit 1
    fi
else
    echo "Hap-IBD archive already downloaded at $utils_directory/$HAP_IBD_JAR."
fi

# Verify Hap-IBD installation
echo "Testing Hap-IBD installation..."
java -jar "$utils_directory/hap-ibd.jar" 2>&1
if [ $? -ne 0 ]; then
    echo "Hap-IBD test run failed. Please check your setup."
    exit 1
else
    echo "Hap-IBD installed successfully."
fi