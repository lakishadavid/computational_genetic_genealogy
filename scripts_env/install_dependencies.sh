#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status
set -o pipefail  # Exit on pipe errors

echo "Updating package lists..."
sudo apt-get update -y

echo "Installing Ubuntu system dependencies..."

# Development tools
sudo apt-get install -y python3-dev graphviz graphviz-dev
sudo apt-get install -y build-essential g++ gcc make
sudo apt-get install -y libfreetype6-dev libpng-dev zlib1g-dev libbz2-dev libharfbuzz-dev
sudo apt-get install -y libcurl4-openssl-dev libssl-dev libxml2-dev

# Java Runtime Environment
sudo apt-get install -y default-jre gawk

# Boost C++ libraries
sudo apt-get install -y libboost-all-dev

echo "Dependencies installed successfully."