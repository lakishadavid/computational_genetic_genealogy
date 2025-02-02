#!/bin/bash

echo "install_bcftools.sh: running..."

# ------------------------------------------------------------------------------
# 1. Define directories relative to current location
# ------------------------------------------------------------------------------
base_directory="$(pwd)"  # Current directory (computational_genetic_genealogy)

# ------------------------------------------------------------------------------
# 2. Define utils_directory based on base_directory
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# 3. Install required build dependencies (Ubuntu/Debian)
#    If these are already installed, it won't harm to run again.
# ------------------------------------------------------------------------------
echo
echo "Updating apt-get and installing build dependencies..."
echo
sudo apt-get update
sudo apt-get install -y autoconf automake make gcc libbz2-dev liblzma-dev zlib1g-dev libcurl4-openssl-dev libncurses5-dev libncursesw5-dev

# ------------------------------------------------------------------------------
# 4. Define versions or branches to install (optional)
#    You can pin specific releases here if you wish. For demonstration, we'll use
#    the master (latest) branch. You can also specify tags like '1.17', '1.16', etc.
# ------------------------------------------------------------------------------
SAMTOOLS_VERSION="master"
BCFTOOLS_VERSION="master"
HTSLIB_VERSION="master"

# ------------------------------------------------------------------------------
# 5. Download and install HTSlib
# ------------------------------------------------------------------------------
echo
echo "Installing HTSlib (branch/tag: $HTSLIB_VERSION)..."
echo
htslib_dir="$utils_directory/htslib"
if [ ! -d "$htslib_dir" ]; then
    git clone --recurse-submodules --branch "$HTSLIB_VERSION" https://github.com/samtools/htslib.git "$htslib_dir"
    if [ $? -ne 0 ]; then
        echo "Error cloning HTSlib repository."
        exit 1
    fi
fi

cd "$htslib_dir"
make clean 2>/dev/null
make
if [ $? -ne 0 ]; then
    echo "Error building HTSlib."
    exit 1
fi

sudo make install
if [ $? -ne 0 ]; then
    echo "Error installing HTSlib."
    exit 1
fi

# ------------------------------------------------------------------------------
# 6. Download and install Samtools
# ------------------------------------------------------------------------------
echo
echo "Installing Samtools (branch/tag: $SAMTOOLS_VERSION)..."
echo
samtools_dir="$utils_directory/samtools"
if [ ! -d "$samtools_dir" ]; then
    git clone --recurse-submodules --branch "$SAMTOOLS_VERSION" https://github.com/samtools/samtools.git "$samtools_dir"
    if [ $? -ne 0 ]; then
        echo "Error cloning Samtools repository."
        exit 1
    fi
fi

cd "$samtools_dir"
make clean 2>/dev/null
make
if [ $? -ne 0 ]; then
    echo "Error building Samtools."
    exit 1
fi

sudo make install
if [ $? -ne 0 ]; then
    echo "Error installing Samtools."
    exit 1
fi

# ------------------------------------------------------------------------------
# 7. Download and install Bcftools
# ------------------------------------------------------------------------------
echo
echo "Installing Bcftools (branch/tag: $BCFTOOLS_VERSION)..."
echo
bcftools_dir="$utils_directory/bcftools"
if [ ! -d "$bcftools_dir" ]; then
    git clone --recurse-submodules --branch "$BCFTOOLS_VERSION" https://github.com/samtools/bcftools.git "$bcftools_dir"
    if [ $? -ne 0 ]; then
        echo "Error cloning Bcftools repository."
        exit 1
    fi
fi

cd "$bcftools_dir"
make clean 2>/dev/null
make
if [ $? -ne 0 ]; then
    echo "Error building Bcftools."
    exit 1
fi

sudo make install
if [ $? -ne 0 ]; then
    echo "Error installing Bcftools."
    exit 1
fi

# ------------------------------------------------------------------------------
# 8. Validate installations
# ------------------------------------------------------------------------------
echo
echo "Verifying installations..."
echo
echo "HTSlib version:"
tabix --version || echo "htslib (tabix) not found on PATH."

echo
echo "Samtools version:"
samtools --version || echo "Samtools not found on PATH."

echo
echo "Bcftools version:"
bcftools --version || echo "Bcftools not found on PATH."

echo
echo "All installations completed. Make sure /usr/local/bin (or appropriate path) is in your PATH."
echo "install_samtools_bcftools_htslib.sh: Finished successfully."
