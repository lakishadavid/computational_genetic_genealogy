#!/bin/bash

echo "install_bonsaitree.sh: running..."

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

bonsai_dir="$utils_directory/bonsaitree"

echo "Bonsai installation directory: $bonsai_dir"

# Clone the Bonsai repository
if [ ! -d "$bonsai_dir" ]; then
    echo "Cloning the Bonsai repository..."
    git clone https://github.com/23andMe/bonsaitree.git "$bonsai_dir" || { echo "Failed to clone the repository."; exit 1; }
else
    echo "Bonsai repository already cloned at $bonsai_dir."
fi

cd "$bonsai_dir" || { echo "Failed to enter $bonsai_dir."; exit 1; }

# Use the currently installed Python for Poetry
poetry env use python3 || { echo "Failed to configure Poetry to use the default Python."; exit 1; }

# Activate the Poetry environment
echo "Activating the Poetry environment..."
source $(poetry env info --path)/bin/activate || {
    echo "Failed to activate Poetry environment."
    exit 1
}

# Upgrade setuptools in the Poetry environment
echo "Ensuring setuptools is installed and up-to-date..."
poetry run pip install --upgrade setuptools || { echo "Failed to install setuptools. Exiting."; exit 1; }

# Initialize Poetry project
if [ ! -f pyproject.toml ]; then
    echo "Initializing Poetry project..."
    poetry init --no-interaction || { echo "Poetry initialization failed."; exit 1; }
fi

# Add dependencies from requirements.txt while ignoring specified versions
if [ -f "$bonsai_dir/requirements.txt" ]; then
    echo "Adding dependencies from requirements.txt (ignoring versions)..."
    echo "This may take a while..., but you should see some activity periodically."
    grep -vE '^\s*(#|$)' "$bonsai_dir/requirements.txt" | while IFS= read -r dependency; do
        # Extract the package name by removing any version constraints
        package=$(echo "$dependency" | sed 's/[<>=!~].*//')
        poetry add "$package" || echo "Failed to add dependency: $package"
    done
else
    echo "No requirements.txt found. Skipping dependency installation."
fi

# Add additional dependencies
echo "Adding additional dependencies..."
poetry add pandas frozendict Cython || { echo "Failed to add additional dependencies."; exit 1; }

# Add additional dependencies from setup.py
echo "Adding additional dependencies..."
poetry add pandas frozendict Cython funcy numpy scipy || { echo "Failed to add additional dependencies."; exit 1; }

# Install all dependencies
poetry install --no-root || { echo "Dependency installation failed."; exit 1; }

# Verify the installation
echo "Verifying Bonsai installation..."
cat <<EOF > verify_bonsai.py
try:
    from bonsaitree.v3.bonsai import build_pedigree
    print("Bonsai module imported successfully.")
except ImportError as e:
    print(f"Failed to import Bonsai: {e}")
    exit(1)
EOF

poetry run python verify_bonsai.py
if [ $? -ne 0 ]; then
    echo "Bonsai verification failed. Please check the installation."
    rm verify_bonsai.py
    exit 1
else
    echo "Bonsai installed successfully."
    rm verify_bonsai.py
fi