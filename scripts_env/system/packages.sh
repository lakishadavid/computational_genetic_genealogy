#!/bin/bash

source "$(dirname "$0")/../utils/common.sh"

if [ "$(id -u)" != "0" ]; then
    error_msg "System installation requires root privileges"
    exit 1
fi

separator
highlight "🚀 Running system-level installations..."
separator

# Update system packages
echo "Updating system packages..."
sudo_cmd apt-get update -y

sudo_cmd apt-get install -y --no-install-recommends \
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

sudo_cmd apt-get clean
sudo_cmd rm -rf /var/lib/apt/lists/*