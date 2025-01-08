#!/bin/bash -x
# install_rfmix2.sh

echo "install_rfmix2.sh: running..."

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

# Define utils_directory
utils_directory="$base_directory/utils"

# Ensure the utils_directory exists
if [ ! -d "$utils_directory" ]; then
    echo "Creating utils directory at $utils_directory..."
    mkdir -p "$utils_directory"
    if [ $? -ne 0 ]; then
        echo "Failed to create utils directory."
        exit 1
    fi
fi

# Define RFMix2 installation directory
rfmix2_dir="$utils_directory/rfmix2"

# Install required tools (if missing)
for tool in autoconf make gcc; do
    if ! command -v $tool &> /dev/null; then
        echo "$tool not found. Installing..."
        sudo apt-get update -y && sudo apt-get install -y $tool || {
            echo "Failed to install $tool. Exiting."
            exit 1
        }
    else
        echo "$tool is already installed."
    fi
done

# Clone RFMix2 repository
rfmix_dir="$utils_directory/rfmix2"
if [ ! -d "$rfmix_dir" ]; then
    echo "Cloning RFMix2 repository..."
    git clone https://github.com/slowkoni/rfmix.git "$rfmix_dir" || {
        echo "Failed to clone RFMix2 repository. Exiting."
        exit 1
    }
else
    echo "RFMix2 repository already exists at $rfmix_dir"
fi

# Navigate to RFMix2 directory
if [ -d "$rfmix_dir" ]; then
    cd "$rfmix_dir" || { echo "Failed to enter $rfmix_dir. Exiting."; exit 1; }
else
    echo "Error: RFMix2 directory not found. Exiting."
    exit 1
fi

# Step-by-step generation of configuration files
echo "Generating build files the long way..."

# 1. Create aclocal.m4
echo "Running aclocal..."
aclocal || {
    echo "Error running aclocal. Exiting."
    exit 1
}

# 2. Create config.h.in
echo "Running autoheader..."
autoheader || {
    echo "Error running autoheader. Exiting."
    exit 1
}

# 3. Create configure script
echo "Running autoconf..."
autoconf || {
    echo "Error running autoconf. Exiting."
    exit 1
}

# 4. Create Makefile.in
echo "Running automake with --add-missing..."
automake --add-missing || {
    echo "Error running automake. Exiting."
    exit 1
}

# 5. Configure the build system
echo "Running ./configure..."
./configure || {
    echo "Error running configure. Exiting."
    exit 1
}

# 6. Compile the program
echo "Compiling RFMix2..."
make || {
    echo "Error running make. Exiting."
    exit 1
}

# Verify RFMix2 build
if [ -f "$rfmix_dir/rfmix" ]; then
    echo "RFMix2 built successfully and is ready to use."
else
    echo "Error: RFMix2 binary not found. Build failed."
    exit 1
fi

echo "RFMix2 installation completed successfully."
