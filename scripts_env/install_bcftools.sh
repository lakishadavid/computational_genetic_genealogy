#!/bin/bash

echo "install_bcftools.sh: running..."

# Function to determine if we're running in a Docker container
in_docker() {
    [ -f /.dockerenv ] || grep -Eq '(lxc|docker)' /proc/1/cgroup
}

# Function to handle sudo based on environment
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
base_directory="$(realpath "$(dirname "${BASH_SOURCE[0]}")/..")"

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
INSTALL_PREFIX="$HOME/.local"

git config --global --add safe.directory "*"
git config --global --add safe.directory "/home/ubuntu/utils/htslib"
git config --global --add safe.directory "/home/ubuntu/utils/htslib/htscodecs"
# ------------------------------------------------------------------------------
# 3. Install required build dependencies (Ubuntu/Debian)
#    If these are already installed, it won't harm to run again.
# ------------------------------------------------------------------------------
echo
echo "Updating apt-get and installing build dependencies..."
echo
sudo_cmd apt-get update
sudo_cmd apt-get install -y autoconf automake make gcc libbz2-dev liblzma-dev zlib1g-dev 
sudo_cmd apt-get install -y libgsl-dev libcurl4-openssl-dev libncurses5-dev libncursesw5-dev

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
    git -c safe.directory='*' clone --recurse-submodules --branch "$HTSLIB_VERSION" https://github.com/samtools/htslib.git "$htslib_dir"
    if [ $? -ne 0 ]; then
        echo "Error cloning HTSlib repository."
        exit 1
    fi
fi

cd "$htslib_dir"

# Configure installation path explicitly
autoreconf -i
./configure --prefix="$INSTALL_PREFIX"
make -j"$(nproc)"
make install
if [ $? -ne 0 ]; then
    echo "Error installing HTSlib."
    exit 1
fi

# Ensure binaries are executable and in the correct location
chmod +x "/usr/local/bin/tabix"

echo "HTSlib installation completed successfully."

# ------------------------------------------------------------------------------
# 6. Download and install Samtools
# ------------------------------------------------------------------------------
echo
echo "Installing Samtools (branch/tag: $SAMTOOLS_VERSION)..."
echo

samtools_dir="$utils_directory/samtools"
if [ ! -d "$samtools_dir" ]; then
    git -c safe.directory='*' clone --recurse-submodules --branch "$SAMTOOLS_VERSION" https://github.com/samtools/samtools.git "$samtools_dir"
    if [ $? -ne 0 ]; then
        echo "Error cloning Samtools repository."
        exit 1
    fi
fi

cd "$samtools_dir"
autoheader
autoconf -Wno-syntax

# Configure installation path explicitly
./configure --prefix="$INSTALL_PREFIX"

# Compile & install
make -j"$(nproc)"
if [ $? -ne 0 ]; then
    echo "Error building Samtools."
    exit 1
fi

make install
if [ $? -ne 0 ]; then
    echo "Error installing Samtools."
    exit 1
fi

# Ensure binaries are executable and in the correct location
chmod +x "/usr/local/bin/samtools"

echo "Samtools installation completed successfully."

# ------------------------------------------------------------------------------
# 7. Download and install Bcftools
# ------------------------------------------------------------------------------
echo
echo "Installing Bcftools (branch/tag: $BCFTOOLS_VERSION)..."
echo

bcftools_dir="$utils_directory/bcftools"
if [ ! -d "$bcftools_dir" ]; then
    git -c safe.directory='*' clone --recurse-submodules --branch "$BCFTOOLS_VERSION" https://github.com/samtools/bcftools.git "$bcftools_dir"
    if [ $? -ne 0 ]; then
        echo "Error cloning Bcftools repository."
        exit 1
    fi
fi

cd "$bcftools_dir"

# Simple build process following documentation
# Remove the autoheader and complex configure steps
./configure prefix="$INSTALL_PREFIX" --enable-libgsl
make -j"$(nproc)"
if [ $? -ne 0 ]; then
    echo "Error building Bcftools."
    exit 1
fi

make install
if [ $? -ne 0 ]; then
    echo "Error installing Bcftools."
    exit 1
fi

# Set up plugins
echo "export BCFTOOLS_PLUGINS=$bcftools_dir/plugins" >> ~/.bashrc
export BCFTOOLS_PLUGINS="$bcftools_dir/plugins"

# Ensure binaries are in PATH
echo "export PATH=$INSTALL_PREFIX/bin:\$PATH" >> ~/.bashrc
export PATH="$INSTALL_PREFIX/bin:$PATH"

echo "Bcftools installation completed successfully."

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

cd $base_directory