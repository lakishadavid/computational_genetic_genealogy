#!/bin/bash

# Metadata
MAINTAINER="LaKisha David <ltdavid2@illinois.edu>"
DESCRIPTION="A script for genetic genealogy analysis setup"
VERSION="1.0.0"

# Variables
USERNAME="ubuntu"
USER_UID=1000
USER_GID=1000
WORKSPACE_DIR="/home/$USERNAME"

# Ensure script runs with root privileges
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root. Use sudo." >&2
    exit 1
fi

# Update and install dependencies
echo "Updating system and installing dependencies..."
apt-get update -y && \
apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    curl \
    git \
    unzip \
    python3 \
    python3-pip \
    python3-dev \
    graphviz \
    graphviz-dev \
    g++ \
    gcc \
    make \
    libfreetype6-dev \
    libpng-dev \
    zlib1g-dev \
    libbz2-dev \
    libharfbuzz-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    default-jre \
    gawk \
    libboost-all-dev \
    docker-compose-plugin && \
apt-get clean && \
rm -rf /var/lib/apt/lists/*

# Add non-root user
echo "Setting up non-root user: $USERNAME..."
groupadd --gid $USER_GID $USERNAME
useradd --uid $USER_UID --gid $USER_GID -m $USERNAME
chown -R $USERNAME:$USERNAME $WORKSPACE_DIR

# Create necessary directories
echo "Creating workspace directories..."
mkdir -p $WORKSPACE_DIR/results $WORKSPACE_DIR/data $WORKSPACE_DIR/references $WORKSPACE_DIR/utils
chown -R $USERNAME:$USERNAME $WORKSPACE_DIR/results $WORKSPACE_DIR/data $WORKSPACE_DIR/references $WORKSPACE_DIR/utils

# Install Poetry
echo "Installing Poetry..."
POETRY_HOME="/opt/poetry"
POETRY_VERSION="1.8.5"
PATH="$POETRY_HOME/bin:$PATH"
curl -sSL https://install.python-poetry.org | POETRY_HOME=$POETRY_HOME python3 -
ln -s $POETRY_HOME/bin/poetry /usr/local/bin/poetry
sudo -u $USERNAME poetry config virtualenvs.create true

# Install Python packages
echo "Installing Python packages with Poetry..."
cd $WORKSPACE_DIR
if [ -f "pyproject.toml" ] && [ -f "poetry.lock" ]; then
    sudo -u $USERNAME poetry install --no-root
else
    echo "No pyproject.toml or poetry.lock found. Skipping Python package installation."
fi

echo "Setup complete!"
