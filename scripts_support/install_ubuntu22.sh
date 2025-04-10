#!/bin/bash
#
# Computational Genetic Genealogy Environment Setup Script for Ubuntu 22.04
# This script automatically sets up the environment without using Docker
# Version: 1.0.0 (Improved Directory Handling)

set -e # Exit on error

echo "============================================================================="
echo "Computational Genetic Genealogy Environment Setup for Ubuntu 22.04"
echo "============================================================================="

# Get the current directory where the script is run from
CURRENT_DIR=$(pwd)

# Define the project directory based on current directory
if [[ $CURRENT_DIR == */computational_genetic_genealogy* ]]; then
    # Already in the project directory or a subdirectory
    PROJECT_BASE_DIR=$(echo "$CURRENT_DIR" | sed 's|\(.*computational_genetic_genealogy\).*|\1|')
    echo "✅ Found project directory: $PROJECT_BASE_DIR"
else
    # Not in a project directory, use home directory by default
    PROJECT_BASE_DIR="${HOME}/computational_genetic_genealogy"
    echo "⚠️ Not in project directory. Using: $PROJECT_BASE_DIR"
    
    # Check if directory exists, if not prompt to create or exit
    if [ ! -d "$PROJECT_BASE_DIR" ]; then
        read -p "Project directory does not exist. Create it? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            mkdir -p "$PROJECT_BASE_DIR"
            echo "✅ Created directory: $PROJECT_BASE_DIR"
        else
            echo "❌ Aborting installation. Please run from project directory."
            exit 1
        fi
    fi
fi

echo "============================================================================="
echo "1. Creating Project Directory Structure"
echo "============================================================================="

mkdir -p "${PROJECT_BASE_DIR}/data" \
         "${PROJECT_BASE_DIR}/results" \
         "${PROJECT_BASE_DIR}/references" \
         "${PROJECT_BASE_DIR}/utils"

echo "✅ Created project subdirectories in ${PROJECT_BASE_DIR}"

echo "============================================================================="
echo "2. Creating Environment Configuration File"
echo "============================================================================="

# Create .env in the project directory just like in Docker version
cat > ${PROJECT_BASE_DIR}/.env << EOF
PROJECT_WORKING_DIR=${PROJECT_BASE_DIR}
PROJECT_DATA_DIR=${PROJECT_BASE_DIR}/data
PROJECT_REFERENCES_DIR=${PROJECT_BASE_DIR}/references
PROJECT_RESULTS_DIR=${PROJECT_BASE_DIR}/results
PROJECT_UTILS_DIR=${PROJECT_BASE_DIR}/utils
USER_HOME=${HOME}
EOF

echo "✅ Created environment configuration file"

echo "============================================================================="
echo "3. Installing System Packages"
echo "============================================================================="

echo "Updating package lists and adding necessary repositories..."
sudo apt update && sudo apt upgrade -y && sudo apt install -y software-properties-common
sudo apt-add-repository -y universe 
sudo apt-add-repository -y multiverse 
sudo apt-add-repository -y ppa:deadsnakes/ppa
sudo apt update -y

echo "Installing main dependencies..."
sudo apt install -y --no-install-recommends \
    build-essential \
    g++ \
    gcc \
    make \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-pip \
    pipx \
    wget \
    curl \
    git \
    unzip \
    libcairo2-dev \
    pkg-config \
    libpng-dev \
    zlib1g-dev \
    libbz2-dev \
    liblzma-dev \
    libncurses-dev \
    libharfbuzz-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    cmake \
    libsystemd-dev \
    libgirepository1.0-dev \
    gir1.2-glib-2.0 \
    libdbus-1-dev \
    graphviz \
    graphviz-dev \
    libpq-dev \
    postgresql-client \
    libtirpc-dev \
    openjdk-17-jdk \
    openjdk-17-jre \
    gawk \
    libboost-all-dev \
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-plain-generic \
    texlive-latex-extra \
    texlive-fonts-extra \
    pandoc \
    r-base \
    libgsl-dev \
    autoconf \
    automake \
    libblas-dev \
    liblapack-dev \
    libatlas-base-dev

# Configure R Library Path for user-specific packages
mkdir -p ~/R/library/
touch ~/.Rprofile
grep -qxF '.libPaths(c("~/R/library/", .libPaths()))' ~/.Rprofile || echo '.libPaths(c("~/R/library/", .libPaths()))' >> ~/.Rprofile
echo "✅ Configured R library path in ~/.Rprofile"

# Clean up
sudo apt-get clean && sudo rm -rf /var/lib/apt/lists/*

# Configure Java Environment
JAVA_HOME_PATH=$(update-alternatives --list java | grep 'java-17-openjdk' | sed 's/\/bin\/java//')
if [ -n "$JAVA_HOME_PATH" ] && ! grep -q "export JAVA_HOME=" ~/.bashrc; then
  echo "export JAVA_HOME=$JAVA_HOME_PATH" >> ~/.bashrc
  echo "export PATH=\$JAVA_HOME/bin:\$PATH" >> ~/.bashrc
  # Also set for the current shell session
  export JAVA_HOME=$JAVA_HOME_PATH
  export PATH=$JAVA_HOME/bin:$PATH
  echo "✅ Configured JAVA_HOME in ~/.bashrc"
else
  echo "⚠️ Could not automatically set JAVA_HOME. Please set it manually if needed."
fi

echo "✅ Installed system packages"

echo "============================================================================="
echo "4. Building Samtools, BCFtools, HTSlib (v1.18) from Source"
echo "============================================================================="

# Create a temporary directory for building
TEMP_BUILD_DIR=$(mktemp -d)
cd "$TEMP_BUILD_DIR"
echo "Building tools in $TEMP_BUILD_DIR..."

# Define version
SAMTOOLS_VERSION=1.18

# HTSlib
wget https://github.com/samtools/htslib/releases/download/${SAMTOOLS_VERSION}/htslib-${SAMTOOLS_VERSION}.tar.bz2
tar -xjf htslib-${SAMTOOLS_VERSION}.tar.bz2
cd htslib-${SAMTOOLS_VERSION}
./configure --prefix=/usr/local # Install system-wide
make
sudo make install
cd ..

# Samtools
wget https://github.com/samtools/samtools/releases/download/${SAMTOOLS_VERSION}/samtools-${SAMTOOLS_VERSION}.tar.bz2
tar -xjf samtools-${SAMTOOLS_VERSION}.tar.bz2
cd samtools-${SAMTOOLS_VERSION}
./configure --prefix=/usr/local
make
sudo make install
cd ..

# BCFtools
wget https://github.com/samtools/bcftools/releases/download/${SAMTOOLS_VERSION}/bcftools-${SAMTOOLS_VERSION}.tar.bz2
tar -xjf bcftools-${SAMTOOLS_VERSION}.tar.bz2
cd bcftools-${SAMTOOLS_VERSION}
./configure --prefix=/usr/local
make
sudo make install
cd ..

# Clean up build directory
cd "$PROJECT_BASE_DIR" # Go back to project dir
rm -rf "$TEMP_BUILD_DIR"

# Update library cache
sudo ldconfig

echo "✅ Samtools, BCFtools, HTSlib v${SAMTOOLS_VERSION} built and installed."

# Verify installation
echo "Verifying tools..."
bcftools --version | head -n 1
samtools --version | head -n 1
tabix --version | head -n 1

echo "============================================================================="
echo "5. Installing Poetry (Python Dependency Manager)"
echo "============================================================================="

# Install Poetry using pipx
pipx ensurepath
pipx install poetry

# Make Poetry available in PATH immediately and permanently
export PATH="$HOME/.local/bin:$PATH"
if ! grep -q '\.local\/bin' ~/.bashrc; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

# Verify installation
poetry --version
echo "✅ Poetry installed"

echo "============================================================================="
echo "6. Setting up Git Repository"
echo "============================================================================="

# Change to the project directory
cd "$PROJECT_BASE_DIR"

# Clone the repository if it doesn't already exist
if [ ! -f "$PROJECT_BASE_DIR/pyproject.toml" ]; then
    # Move to a temporary location
    cd /tmp
    # Clone the repository
    git clone https://github.com/lakishadavid/computational_genetic_genealogy.git temp_repo
    # Move all files from the cloned repo to the project directory
    cp -r temp_repo/* $PROJECT_BASE_DIR/
    cp -r temp_repo/.* $PROJECT_BASE_DIR/ 2>/dev/null || true
    # Clean up
    rm -rf temp_repo
    # Return to project directory
    cd "$PROJECT_BASE_DIR"
    echo "✅ Repository cloned to $PROJECT_BASE_DIR"
else
    echo "✅ Repository already exists in $PROJECT_BASE_DIR"
fi

echo "============================================================================="
echo "7. Installing Python Project Dependencies"
echo "============================================================================="

cd "$PROJECT_BASE_DIR"
poetry config virtualenvs.in-project true
poetry install --no-root

echo "✅ Python dependencies installed"

echo "============================================================================="
echo "8. Updating PATH for Utility Scripts"
echo "============================================================================="

UTILS_DIR="${PROJECT_BASE_DIR}/utils"
EXPORT_LINE="export PATH=\"\$PATH:${UTILS_DIR}\"" # Add utils dir to PATH

# Check if the line already exists
if ! grep -qF "$EXPORT_LINE" ~/.bashrc; then
    echo -e "\n# Add project utils directory to PATH\n${EXPORT_LINE}" >> ~/.bashrc
    echo "✅ Added utils directory (${UTILS_DIR}) to PATH in ~/.bashrc."
else
    echo "✅ Utils directory already in PATH in ~/.bashrc."
fi
# Also set for current shell
export PATH="$PATH:${UTILS_DIR}"

echo "============================================================================="
echo "9. Installing JAR Files (Beagle, HapIBD, RefinedIBD)"
echo "============================================================================="

# Download Java tools
UTILS_DIR="${PROJECT_BASE_DIR}/utils"

# Define JARs and URLs
BEAGLE_JAR="beagle.27Feb25.75f.jar"
HAP_IBD_JAR="hap-ibd.jar"
REFINED_IBD_JAR="refined-ibd.17Jan20.102.jar"
REFINED_IBD_MERGE_JAR="merge-ibd-segments.17Jan20.102.jar"

BEAGLE_URL="https://faculty.washington.edu/browning/beagle/${BEAGLE_JAR}"
HAP_IBD_URL="https://faculty.washington.edu/browning/${HAP_IBD_JAR}"
REFINED_IBD_URL="https://faculty.washington.edu/browning/refined-ibd/${REFINED_IBD_JAR}"
REFINED_IBD_MERGE_URL="https://faculty.washington.edu/browning/refined-ibd/${REFINED_IBD_MERGE_JAR}"

# Download each JAR file
wget -nv -O "${UTILS_DIR}/${BEAGLE_JAR}" "${BEAGLE_URL}"
wget -nv -O "${UTILS_DIR}/${HAP_IBD_JAR}" "${HAP_IBD_URL}"
wget -nv -O "${UTILS_DIR}/${REFINED_IBD_JAR}" "${REFINED_IBD_URL}"
wget -nv -O "${UTILS_DIR}/${REFINED_IBD_MERGE_JAR}" "${REFINED_IBD_MERGE_URL}"
chmod +x "${UTILS_DIR}"/*.jar

# Test Beagle installation
java -Xmx1g -jar "${UTILS_DIR}/${BEAGLE_JAR}" || echo "Beagle test command finished (ignore non-zero exit code if help message shown)."

echo "✅ JAR files installed"

echo "============================================================================="
echo "10. Installing LiftOver"
echo "============================================================================="

# Download LiftOver binary and make executable
wget -nv http://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/liftOver -O "${UTILS_DIR}/liftOver"
chmod +x "${UTILS_DIR}/liftOver"

# Download hg19->hg38 chain file
wget -nv http://hgdownload.cse.ucsc.edu/goldenPath/hg19/liftOver/hg19ToHg38.over.chain.gz -P "${PROJECT_BASE_DIR}/references/"

# Verify executable exists
[ -x "${UTILS_DIR}/liftOver" ] && echo "✅ LiftOver installed successfully."

echo "============================================================================="
echo "11. Installing BonsaiTree"
echo "============================================================================="

BONSAI_DIR="${UTILS_DIR}/bonsaitree"

# Clone the repository
if [ ! -d "$BONSAI_DIR" ]; then
    git clone https://github.com/23andMe/bonsaitree.git "${BONSAI_DIR}"
fi

# Install BonsaiTree using Poetry then pip
cd "${BONSAI_DIR}"
poetry env use python3.12
# Explicitly add ALL setup_requires and install_requires from setup.py
poetry add Cython funcy numpy scipy six setuptools-scm wheel pandas frozendict
# Install the package itself using pip, but tell it *not* to handle dependencies
poetry run pip install . --no-deps

# Verify installation
poetry run python -c "from bonsaitree.v3.bonsai import build_pedigree; print('✅ BonsaiTree module imported successfully.')"

# Return to project directory
cd "${PROJECT_BASE_DIR}"

echo "============================================================================="
echo "12. Installing IBIS, Ped-Sim, RFMix2 (Source Build)"
echo "============================================================================="

# Define repositories and directories
RFMIX2_REPO="https://github.com/slowkoni/rfmix.git"
IBIS_REPO="https://github.com/williamslab/ibis.git"
PED_SIM_REPO="https://github.com/williamslab/ped-sim.git"
RFMIX2_DIR="${UTILS_DIR}/rfmix2"
IBIS_DIR="${UTILS_DIR}/ibis"
PED_SIM_DIR="${UTILS_DIR}/ped-sim"

# Build IBIS
if [ ! -d "$IBIS_DIR" ]; then
    git clone --recurse-submodules "${IBIS_REPO}" "${IBIS_DIR}"
    cd "${IBIS_DIR}" && make
    # Verify build
    [ -x "${IBIS_DIR}/ibis" ] && echo "✅ IBIS built successfully."
else
    echo "✅ IBIS directory already exists: ${IBIS_DIR}"
fi

# Build Ped-Sim
if [ ! -d "$PED_SIM_DIR" ]; then
    git clone --recurse-submodules "${PED_SIM_REPO}" "${PED_SIM_DIR}"
    cd "${PED_SIM_DIR}" && make && chmod +x ped-sim
    # Verify build
    [ -x "${PED_SIM_DIR}/ped-sim" ] && echo "✅ Ped-Sim built successfully."
else
    echo "✅ Ped-Sim directory already exists: ${PED_SIM_DIR}"
fi

# Build RFMix2
if [ ! -d "$RFMIX2_DIR" ]; then
    git clone "${RFMIX2_REPO}" "${RFMIX2_DIR}"
    cd "${RFMIX2_DIR}"
    aclocal && autoheader && autoconf && automake --add-missing && ./configure && make
    # Verify build
    [ -f "${RFMIX2_DIR}/rfmix" ] && echo "✅ RFMix2 built successfully."
else
    echo "✅ RFMix2 directory already exists: ${RFMIX2_DIR}"
fi

# Return to project directory
cd "${PROJECT_BASE_DIR}"

echo "============================================================================="
echo "13. Installing PLINK2 Binary"
echo "============================================================================="

# Download and install PLINK2
PLINK2_FILE_URL="https://s3.amazonaws.com/plink2-assets/alpha6/plink2_linux_x86_64_20241206.zip"
PLINK2_ZIP_FILE="${UTILS_DIR}/plink2_linux_x86_64_20241206.zip"
PLINK2_BINARY="${UTILS_DIR}/plink2"

if [ ! -f "$PLINK2_BINARY" ]; then
    wget -nv "${PLINK2_FILE_URL}" -O "${PLINK2_ZIP_FILE}"
    unzip "${PLINK2_ZIP_FILE}" -d "${UTILS_DIR}"
    rm "${PLINK2_ZIP_FILE}"
    chmod +x ${PLINK2_BINARY}
fi

# Verify installation
if [ -f "$PLINK2_BINARY" ] && [ -x "$PLINK2_BINARY" ]; then
    echo "✅ PLINK2 installed successfully."
    ${PLINK2_BINARY} --version
fi

echo "============================================================================="
echo "14. Installing Jupyter for Notebook Support"
echo "============================================================================="

# Install Jupyter in the system Python
pip3 install jupyter notebook nbconvert ipywidgets matplotlib ipympl

# Also install in the Poetry environment
cd "${PROJECT_BASE_DIR}"
poetry add jupyter notebook nbconvert ipywidgets matplotlib ipympl python-dotenv

# Create Jupyter configuration
mkdir -p ~/.jupyter
jupyter notebook --generate-config

# Configure Jupyter to allow remote connections
jupyter_config=~/.jupyter/jupyter_notebook_config.py
if [ -f "$jupyter_config" ]; then
    # Set up configurations for remote access
    sed -i "s/# c.NotebookApp.ip = 'localhost'/c.NotebookApp.ip = '0.0.0.0'/g" "$jupyter_config"
    sed -i "s/# c.NotebookApp.allow_origin = ''/c.NotebookApp.allow_origin = '*'/g" "$jupyter_config"
    sed -i "s/# c.NotebookApp.open_browser = True/c.NotebookApp.open_browser = False/g" "$jupyter_config"
    
    echo "✅ Configured Jupyter for remote access"
fi

# Copy initial class data if it exists
CLASS_DATA_SOURCE="${PROJECT_BASE_DIR}/data/class_data"
if [ -d "$CLASS_DATA_SOURCE" ]; then
    echo "Copying initial class data..."
    mkdir -p "${PROJECT_BASE_DIR}/data"
    cp -r "$CLASS_DATA_SOURCE" "${PROJECT_BASE_DIR}/data/"
    echo "✅ Initial class data copied"
fi

echo "✅ Jupyter installed and configured for notebook support"

echo "============================================================================="
echo "15. Final Setup and Environment Verification"
echo "============================================================================="

# Add activation script to a standard location
sudo bash -c "cat > /usr/local/bin/activate_cgg << 'EOF'
#!/bin/bash
# Add Poetry binary directory to PATH
export PATH=\"\$HOME/.local/bin:\$PATH\"

# Add utils directory to PATH
export PATH=\"\$PATH:${PROJECT_BASE_DIR}/utils\"

# Activate Python virtual environment
source ${PROJECT_BASE_DIR}/.venv/bin/activate

# Change to project directory
cd ${PROJECT_BASE_DIR}

echo \"Computational Genetic Genealogy environment activated\"

# Check environment quickly
echo -e \"\nEnvironment paths:\"
echo \"PROJECT_WORKING_DIR=\$PROJECT_WORKING_DIR\"
echo \"PROJECT_DATA_DIR=\$PROJECT_DATA_DIR\"
echo \"PROJECT_REFERENCES_DIR=\$PROJECT_REFERENCES_DIR\"
echo \"PROJECT_RESULTS_DIR=\$PROJECT_RESULTS_DIR\"
echo \"PROJECT_UTILS_DIR=\$PROJECT_UTILS_DIR\"
EOF"
sudo chmod +x /usr/local/bin/activate_cgg

# Make lab scripts executable if they exist
if [ -d "${PROJECT_BASE_DIR}/scripts_env" ]; then
    chmod -R +x "${PROJECT_BASE_DIR}/scripts_env/"
    echo "✅ Made scripts executable"
fi

# Create a verification script to check tool installation
sudo bash -c "cat > /usr/local/bin/verify_cgg_env << 'EOF'
#!/bin/bash
# Environment verification script
set -e

echo \"=============================================================================\" 
echo \"Computational Genetic Genealogy Environment Verification\"
echo \"=============================================================================\" 

# Check Python and Poetry
echo -e \"\n--- Python and Poetry ---\"
python3.12 --version
poetry --version

# Check Java
echo -e \"\n--- Java Installation ---\"
java -version
echo \"JAVA_HOME=\$JAVA_HOME\"

# Check Samtools/BCFtools/Tabix
echo -e \"\n--- Genomics Tools ---\"
echo \"Samtools: \$(samtools --version | head -n 1)\"
echo \"BCFtools: \$(bcftools --version | head -n 1)\"
echo \"Tabix: \$(tabix --version | head -n 1)\"

# Check R
echo -e \"\n--- R Installation ---\"
R --version | head -n 1

# Check JAR Files
echo -e \"\n--- JAR Files ---\"
UTILS_DIR=\"\$PROJECT_UTILS_DIR\"
JARS=(\"beagle.27Feb25.75f.jar\" \"hap-ibd.jar\" \"refined-ibd.17Jan20.102.jar\" \"merge-ibd-segments.17Jan20.102.jar\")
for jar in \"\${JARS[@]}\"; do
    if [ -f \"\$UTILS_DIR/\$jar\" ]; then
        echo \"✅ Found \$jar\"
    else
        echo \"❌ Missing \$jar\"
    fi
done

# Check Other Tools
echo -e \"\n--- Other Tools ---\"
if [ -x \"\$UTILS_DIR/liftOver\" ]; then
    echo \"✅ Found LiftOver executable\"
else
    echo \"❌ Missing LiftOver\"
fi

if [ -x \"\$UTILS_DIR/plink2\" ]; then
    echo \"✅ Found PLINK2 executable\"
    \"\$UTILS_DIR/plink2\" --version | head -n 1
else
    echo \"❌ Missing PLINK2\"
fi

# Check Source-Built Tools
echo -e \"\n--- Source-Built Tools ---\"
if [ -x \"\$UTILS_DIR/ibis/ibis\" ]; then
    echo \"✅ Found IBIS executable\"
else
    echo \"❌ Missing IBIS\"
fi

if [ -x \"\$UTILS_DIR/ped-sim/ped-sim\" ]; then
    echo \"✅ Found Ped-Sim executable\"
else
    echo \"❌ Missing Ped-Sim\"
fi

if [ -f \"\$UTILS_DIR/rfmix2/rfmix\" ]; then
    echo \"✅ Found RFMix2 executable\"
else
    echo \"❌ Missing RFMix2\"
fi

if [ -d \"\$UTILS_DIR/bonsaitree\" ]; then
    echo \"✅ Found BonsaiTree directory\"
else
    echo \"❌ Missing BonsaiTree\"
fi

# Check Jupyter
echo -e \"\n--- Jupyter ---\"
jupyter --version | head -n 1

echo -e \"\nVerification complete! If any tools are missing, run the installation script again.\"
echo \"=============================================================================\" 
EOF"
sudo chmod +x /usr/local/bin/verify_cgg_env

# Create a script for running Jupyter
sudo bash -c "cat > /usr/local/bin/start_jupyter << 'EOF'
#!/bin/bash
# Start Jupyter Notebook server with proper configuration
source /usr/local/bin/activate_cgg
cd ${PROJECT_BASE_DIR}
echo \"Starting Jupyter Notebook server...\"
jupyter notebook --ip=0.0.0.0 --no-browser
EOF"
sudo chmod +x /usr/local/bin/start_jupyter

# Create a log of installed tools and versions
LOG_FILE="${PROJECT_BASE_DIR}/environment_setup_log.txt"
{
    echo "=== Computational Genetic Genealogy Environment Setup Log ==="
    echo "Date: $(date)"
    echo "Ubuntu Version: $(lsb_release -ds)"
    echo ""
    echo "--- Core Tools ---"
    echo "Python: $(python3.12 --version 2>&1)"
    echo "Pip: $(python3.12 -m pip --version 2>&1)"
    echo "Poetry: $(poetry --version 2>&1)"
    echo "Java: $(java -version 2>&1 | head -n 1)"
    echo "R: $(R --version | head -n 1)"
    echo "Jupyter: $(jupyter --version 2>&1 | head -n 1)"
    echo ""
    echo "--- Bioinformatics Tools ---"
    echo "Samtools: $(samtools --version | head -n 1)"
    echo "BCFtools: $(bcftools --version | head -n 1)"
    echo "Tabix: $(tabix --version | head -n 1)"
    echo "PLINK2: $(${PLINK2_BINARY} --version 2>&1 | head -n 1)"
    echo ""
    echo "--- Installed JAR Files ---"
    echo "Beagle: ${UTILS_DIR}/${BEAGLE_JAR}"
    echo "HapIBD: ${UTILS_DIR}/${HAP_IBD_JAR}"
    echo "RefinedIBD: ${UTILS_DIR}/${REFINED_IBD_JAR}"
    echo "Merge-IBD-Segments: ${UTILS_DIR}/${REFINED_IBD_MERGE_JAR}"
    echo ""
    echo "--- Source-Built Tools ---"
    echo "IBIS: $(test -x "${IBIS_DIR}/ibis" && echo "Installed" || echo "Not found")"
    echo "Ped-Sim: $(test -x "${PED_SIM_DIR}/ped-sim" && echo "Installed" || echo "Not found")"
    echo "RFMix2: $(test -f "${RFMIX2_DIR}/rfmix" && echo "Installed" || echo "Not found")"
    echo "BonsaiTree: Installed via Poetry"
    echo ""
    echo "--- Environment ---"
    echo "Project Directory: ${PROJECT_BASE_DIR}"
    echo "Environment File: ${PROJECT_BASE_DIR}/.env"
    echo "Python Virtual Environment: ${PROJECT_BASE_DIR}/.venv"
} > "$LOG_FILE"

echo "✅ Environment setup log created at: $LOG_FILE"

echo "============================================================================="
echo "✅ Installation Complete!"
echo "============================================================================="
echo "Your Computational Genetic Genealogy Environment is fully set up:"
echo ""
echo "🖥️  OS: Ubuntu 22.04"
echo "🐍  Python: 3.12 managed by Poetry in .venv"
echo "☕  Java: OpenJDK 17"
echo "🧬  Genomics Tools: Samtools/BCFtools/Tabix v1.18, Beagle, PLINK2, and more"
echo "📓  Jupyter: Installed with PDF export capability"
echo ""
echo "📋  Available Commands:"
echo "    • activate_cgg       - Activate the Python environment and set paths"
echo "    • verify_cgg_env     - Verify all tools are properly installed"
echo "    • start_jupyter      - Launch Jupyter Notebook server"
echo ""
echo "📂  Directory Structure:"
echo "    • ${PROJECT_BASE_DIR}           - Main project directory"
echo "    • ${PROJECT_BASE_DIR}/data      - Data files"
echo "    • ${PROJECT_BASE_DIR}/results   - Analysis results"
echo "    • ${PROJECT_BASE_DIR}/references - Reference files"
echo "    • ${PROJECT_BASE_DIR}/utils     - Utility scripts and tools"
echo ""
echo "🔧  VS Code Tips:"
echo "    • When opening notebooks in VS Code, select the Python interpreter:"
echo "      .venv (Poetry) from the computational_genetic_genealogy directory"
echo "    • To export notebooks to PDF: Use the Jupyter extension or run:"
echo "      poetry run jupyter nbconvert --to pdf path/to/notebook.ipynb"
echo ""
echo "🚀  To get started right now:"
echo "    1. Run: activate_cgg"
echo "    2. Run: verify_cgg_env    (to verify all tools)"
echo "    3. Run: start_jupyter     (to launch Jupyter)"
echo ""
echo "All tools are installed and ready to use."
echo "============================================================================="

# Run verification to confirm all tools are installed correctly
echo -e "\nRunning environment verification..."
/usr/local/bin/verify_cgg_env