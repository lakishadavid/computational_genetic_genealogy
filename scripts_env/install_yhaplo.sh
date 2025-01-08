#!/bin/bash
# https://github.com/23andMe/yhaplo

set -x

echo "install_yhaplo.sh: running..."

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

user_home="${base_directory%/bagg_analysis}"

echo "Using base_directory: $base_directory"
echo "Using utils_directory: $utils_directory"
echo "user_home: $user_home"

yhaplo_directory="$utils_directory/yhaplo"

# Try installing Poetry using apt-get first
if ! command -v poetry &> /dev/null; then
    echo "Poetry not found. Trying to install using apt-get..."
    sudo apt-get update -y
    sudo apt-get install -y python3-poetry

    # If apt-get fails, fallback to curl
    if ! command -v poetry &> /dev/null; then
        echo "apt-get failed. Installing Poetry using curl..."
        curl -sSL https://install.python-poetry.org | python3 -
        export PATH="$user_home/.local/bin:$PATH"
        echo 'export PATH="$user_home/.local/bin:$PATH"' >> "$user_home/.bashrc"
        source "$user_home/.bashrc"
    fi
else
    echo "Poetry is already installed."
fi

# Confirm Poetry installation
echo "Poetry version: $(poetry --version)" || { echo "Poetry installation failed"; exit 1; }

# Variables
REPO_URL="https://github.com/23andMe/yhaplo.git"

# Clone or update the repository
if [ -d "$yhaplo_directory" ]; then
    echo "yhaplo repository already exists. Deleting it..."
    rm -rf "$yhaplo_directory" || { echo "Failed to delete $yhaplo_directory."; exit 1; }
fi

echo "Cloning yhaplo repository..."
git clone "$REPO_URL" "$yhaplo_directory" || { echo "Failed to clone yhaplo repository."; exit 1; }
cd "$yhaplo_directory" || { echo "Failed to enter $yhaplo_directory."; exit 1; }

# Note: This script converts the project from pip to poetry management
# Set up virtual environment and use pip for initial installation
python3 -m venv yhaplo_env
source yhaplo_env/bin/activate
pip install --editable .
pip freeze > requirements.txt
yhaplo --version || { echo "yhaplo command failed."; deactivate; exit 1; }
deactivate

# Backup original pyproject.toml
if [ -f "pyproject.toml" ]; then
    mv pyproject.toml pyproject.toml.bak || { echo "Failed to back up pyproject.toml."; exit 1; }
fi

# Initialize Poetry and add dependencies
poetry init --no-interaction

# Use awk to remove specific sections
awk '
# Start of a section to skip
/^\[tool.poetry\]/ || /^\[tool.poetry.dependencies\]/ { skip = 1; next }

# Start of any new section, stop skipping
/^\[/ { skip = 0 }

# Print lines that are not skipped
!skip' pyproject.toml > pyproject.cleaned.toml

# Replace the original file with the cleaned file
mv pyproject.cleaned.toml pyproject.toml

# Build the new [tool.poetry] section of pyproject.toml
echo "" >> pyproject.toml
echo "[tool.poetry]" >> pyproject.toml

# Extract key fields from the original pyproject.toml
name=$(grep -oP '^name = "\K[^"]+' pyproject.toml.bak)
description=$(grep -oP '^description = "\K[^"]+' pyproject.toml.bak)
readme=$(grep -oP '^readme = "\K[^"]+' pyproject.toml.bak)
# python_requirement=$(grep -oP '^requires-python = "\K[^"]+' pyproject.toml.bak)
python_requirement=">=3.10"
license=$(grep -oP '^license = { file = "\K[^"]+' pyproject.toml.bak)
author_name=$(grep -oP '{ name = "\K[^"]+' pyproject.toml.bak)
author_email=$(grep -oP '{ email = "\K[^"]+' pyproject.toml.bak)
authors="\"$author_name <$author_email>\""
dependencies=$(grep -oP '^dependencies = \[\K[^\]]+' pyproject.toml.bak | tr -d ' "')

echo "name = \"$name\"" >> pyproject.toml
echo "version = \"10.1101.088716\"" >> pyproject.toml
echo "description = \"$description\"" >> pyproject.toml
echo "authors = [$authors]" >> pyproject.toml
echo "license = \"file = $license\"" >> pyproject.toml
echo "readme = \"$readme\"" >> pyproject.toml

# Add Python version requirement
echo "" >> pyproject.toml
echo "[tool.poetry.dependencies]" >> pyproject.toml
echo "python = \"$python_requirement\"" >> pyproject.toml

# Add dependencies dynamically
# echo "Dependencies: $dependencies"
IFS=',' read -ra deps <<< "$dependencies"
for dependency in "${deps[@]}"; do
    echo "Adding dependency: $dependency"
    poetry add "$dependency"
done


# Process optional dependencies dynamically
optional_dependencies=$(awk '/^\[project.optional-dependencies\]/ {flag=1; next} /^\[/ {flag=0} flag' pyproject.toml.bak)

if [[ -n "$optional_dependencies" ]]; then
    echo "" >> pyproject.toml
    echo "[tool.poetry.extras]" >> pyproject.toml

    while IFS= read -r line; do
        # Match lines like `group_name = ["dependency1", "dependency2"]`
        if [[ $line =~ ^[[:space:]]*([a-zA-Z0-9_-]+)[[:space:]]*=[[:space:]]*\[(.*)\] ]]; then
            group_name="${BASH_REMATCH[1]}"
            group_deps="${BASH_REMATCH[2]}"

            # Clean up dependencies (remove quotes and spaces, and reformat properly)
            clean_deps=$(echo "$group_deps" | tr -d '", ' | tr ',' '\n' | sed '/^\s*$/d' | sed 's/^/"/;s/$/"/' | paste -sd ',' -)

            # Append the cleaned extras group to the TOML file
            echo "$group_name = [$clean_deps]" >> pyproject.toml

            # Optionally, add each dependency using Poetry
            IFS=',' read -ra deps <<< "$clean_deps"
            for dep in "${deps[@]}"; do
                poetry add $(echo "$dep" | tr -d '"') --optional
            done
        fi
    done <<< "$optional_dependencies"
fi


# Add [tool.poetry.scripts] section
scripts_section=$(awk '/^\[project\.scripts\]/ {flag=1; next} /^\[/ {flag=0} flag' pyproject.toml.bak)

# If the section exists, process it
if [[ -n "$scripts_section" ]]; then
    # Transform the section header
    echo "" >> pyproject.toml
    echo "[tool.poetry.scripts]" >> pyproject.toml
    
    # Append the scripts content
    echo "$scripts_section" >> pyproject.toml
    echo "Transformed [project.scripts] to [tool.poetry.scripts] successfully."
else
    echo "[project.scripts] section not found in pyproject.toml.bak."
fi


# Add the rest of the sections
# Define sections to skip dynamically
# Example use: skip_sections=("build-system" "tool.setuptools_scm" "tool.codespell")
skip_sections=("build-system" "project" "project.optional-dependencies" "tool.setuptools_scm" "project.scripts")

# Function to dynamically add sections to pyproject.toml
add_section_dynamically() {
    local section_name=$1
    local section_content

    # Extract section dynamically, stopping at the next section
    section_content=$(awk "/^\[$section_name\]/ {flag=1; next} /^\[/ {flag=0} flag" pyproject.toml.bak)

    # Add section header
    echo "" >> pyproject.toml
    echo "[$section_name]" >> pyproject.toml

    # Append each line dynamically
    while IFS= read -r line; do
        echo "$line" >> pyproject.toml
    done <<< "$section_content"
}

# Extract all section titles dynamically from pyproject.toml.bak
section_titles=$(grep -oP '^\[.*?\]' pyproject.toml.bak | tr -d '[]')

# Function to check if a section should be skipped
should_skip_section() {
    local section=$1
    for skip in "${skip_sections[@]}"; do
        if [[ "$section" == "$skip" ]]; then
            return 0  # Found in skip list, return true
        fi
    done
    return 1  # Not in skip list, return false
}

# Loop through each section title and add it dynamically
while IFS= read -r section; do
    if should_skip_section "$section"; then
        echo "Skipping $section section to avoid duplication."
        continue
    fi
    add_section_dynamically "$section"
done <<< "$section_titles"

# delete venv
rm -rf yhaplo_env

# This regenerates the lock file to match the pyproject.toml.
poetry lock --no-update
poetry check

# Test yhaplo with Poetry
echo "Plain install"
poetry install
echo "Install with extras"
# poetry install --extras vcf --extras plot --extras dev
poetry install --all-extras
echo "Test command"
poetry run yhaplo --version || { echo "yhaplo command failed with Poetry."; exit 1; }

echo "Yhaplo installation process completed successfully."