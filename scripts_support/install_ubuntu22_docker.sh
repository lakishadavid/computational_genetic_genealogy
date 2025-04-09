#!/bin/bash
#
# Computational Genetic Genealogy Environment Setup Script for Docker
# This script automatically sets up the environment without using sudo

set -e # Exit on error

echo "============================================================================="
echo "Computational Genetic Genealogy Environment Setup for Docker"
echo "============================================================================="

# Get the current directory where the script is run from
CURRENT_DIR=$(pwd)

# Define the project directory based on current directory
if [[ $CURRENT_DIR == */computational_genetic_genealogy* ]]; then
    # Already in the project directory or a subdirectory
    PROJECT_BASE_DIR=$(echo "$CURRENT_DIR" | sed 's|\(.*computational_genetic_genealogy\).*|\1|')
    echo "✅ Found project directory: $PROJECT_BASE_DIR"
else
    # Not in a project directory, use /app directory by default for Docker
    PROJECT_BASE_DIR="/app"
    echo "⚠️ Not in project directory. Using: $PROJECT_BASE_DIR"
    
    # Create directory if it doesn't exist
    if [ ! -d "$PROJECT_BASE_DIR" ]; then
        mkdir -p "$PROJECT_BASE_DIR"
        echo "✅ Created directory: $PROJECT_BASE_DIR"
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

# In Docker, write to /etc/environment for system-wide availability
cat > /etc/environment << EOF
PROJECT_WORKING_DIR=${PROJECT_BASE_DIR}
PROJECT_DATA_DIR=${PROJECT_BASE_DIR}/data
PROJECT_REFERENCES_DIR=${PROJECT_BASE_DIR}/references
PROJECT_RESULTS_DIR=${PROJECT_BASE_DIR}/results
PROJECT_UTILS_DIR=${PROJECT_BASE_DIR}/utils
USER_HOME=${HOME}
EOF

# Also create .env in home directory for compatibility
cat > ~/.env << EOF
PROJECT_WORKING_DIR=${PROJECT_BASE_DIR}
PROJECT_DATA_DIR=${PROJECT_BASE_DIR}/data
PROJECT_REFERENCES_DIR=${PROJECT_BASE_DIR}/references
PROJECT_RESULTS_DIR=${PROJECT_BASE_DIR}/results
PROJECT_UTILS_DIR=${PROJECT_BASE_DIR}/utils
USER_HOME=${HOME}
EOF

echo "✅ Created environment configuration files"

echo "============================================================================="
echo "3. Installing System Packages"
echo "============================================================================="

echo "Updating package lists and adding necessary repositories..."
apt update && apt upgrade -y && apt install -y software-properties-common
apt-add-repository -y universe 
apt-add-repository -y multiverse 
apt-add-repository -y ppa:deadsnakes/ppa
apt update -y

echo "Installing main dependencies..."
apt install -y --no-install-recommends \
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
    pandoc \
    r-base \
    libgsl-dev \
    autoconf \
    automake \
    libblas-dev \
    liblapack-dev \
    libatlas-base-dev

# Clean up
apt-get clean && rm -rf /var/lib/apt/lists/*

# Configure Java Environment
JAVA_HOME_PATH=$(update-alternatives --list java | grep 'java-17-openjdk' | sed 's/\/bin\/java//')
if [ -n "$JAVA_HOME_PATH" ]; then
  echo "export JAVA_HOME=$JAVA_HOME_PATH" >> /etc/environment
  echo "export PATH=\$JAVA_HOME/bin:\$PATH" >> /etc/environment
  # Also set for the current shell session
  export JAVA_HOME=$JAVA_HOME_PATH
  export PATH=$JAVA_HOME/bin:$PATH
  echo "✅ Configured JAVA_HOME"
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
make install
cd ..

# Samtools
wget https://github.com/samtools/samtools/releases/download/${SAMTOOLS_VERSION}/samtools-${SAMTOOLS_VERSION}.tar.bz2
tar -xjf samtools-${SAMTOOLS_VERSION}.tar.bz2
cd samtools-${SAMTOOLS_VERSION}
./configure --prefix=/usr/local
make
make install
cd ..

# BCFtools
wget https://github.com/samtools/bcftools/releases/download/${SAMTOOLS_VERSION}/bcftools-${SAMTOOLS_VERSION}.tar.bz2
tar -xjf bcftools-${SAMTOOLS_VERSION}.tar.bz2
cd bcftools-${SAMTOOLS_VERSION}
./configure --prefix=/usr/local
make
make install
cd ..

# Clean up build directory
cd "$PROJECT_BASE_DIR" # Go back to project dir
rm -rf "$TEMP_BUILD_DIR"

# Update library cache
ldconfig

echo "✅ Samtools, BCFtools, HTSlib v${SAMTOOLS_VERSION} built and installed."

# Verify installation
echo "Verifying tools..."
bcftools --version | head -n 1
samtools --version | head -n 1
tabix --version | head -n 1

echo "============================================================================="
echo "5. Installing Poetry (Python Dependency Manager)"
echo "============================================================================="

pipx ensurepath
pipx install poetry

# Add pipx path to system environment
echo 'export PATH="$HOME/.local/bin:$PATH"' >> /etc/environment
# Also set for current shell
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
poetry --version
echo "✅ Poetry installed"

echo "============================================================================="
echo "6. Installing Python Project Dependencies"
echo "============================================================================="

cd "$PROJECT_BASE_DIR"
poetry config virtualenvs.in-project true
poetry install --no-root

echo "✅ Python dependencies installed"

echo "============================================================================="
echo "7. Updating PATH for Utility Scripts"
echo "============================================================================="

UTILS_DIR="${PROJECT_BASE_DIR}/utils"
EXPORT_LINE="export PATH=\"\$PATH:${UTILS_DIR}\"" # Add utils dir to PATH

# Add to environment
echo ${EXPORT_LINE} >> /etc/environment
# Also set for current shell
export PATH="$PATH:${UTILS_DIR}"
echo "✅ Added utils directory (${UTILS_DIR}) to PATH"

echo "============================================================================="
echo "8. Installing JAR Files (Beagle, HapIBD, RefinedIBD)"
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
echo "9. Installing LiftOver"
echo "============================================================================="

# Download LiftOver binary and make executable
wget -nv http://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/liftOver -O "${UTILS_DIR}/liftOver"
chmod +x "${UTILS_DIR}/liftOver"

# Download hg19->hg38 chain file
wget -nv http://hgdownload.cse.ucsc.edu/goldenPath/hg19/liftOver/hg19ToHg38.over.chain.gz -P "${PROJECT_BASE_DIR}/references/"

# Verify executable exists
[ -x "${UTILS_DIR}/liftOver" ] && echo "✅ LiftOver installed successfully."

echo "============================================================================="
echo "10. Installing BonsaiTree"
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
echo "11. Installing IBIS, Ped-Sim, RFMix2 (Source Build)"
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
echo "12. Installing PLINK2 Binary"
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
echo "13. Final Setup"
echo "============================================================================="

# Add activation script to a standard location
echo '#!/bin/bash
source '"${PROJECT_BASE_DIR}"'/.venv/bin/activate
cd '"${PROJECT_BASE_DIR}"'
echo "Computational Genetic Genealogy environment activated"
' > /usr/local/bin/activate_cgg
chmod +x /usr/local/bin/activate_cgg

# Make lab scripts executable if they exist
if [ -d "${PROJECT_BASE_DIR}/scripts_env" ]; then
    chmod -R +x "${PROJECT_BASE_DIR}/scripts_env/"
    echo "✅ Made scripts executable"
fi

# Create a log of installed tools and versions
LOG_FILE="${PROJECT_BASE_DIR}/environment_setup_log.txt"
{
    echo "=== Computational Genetic Genealogy Environment Setup Log ==="
    echo "Date: $(date)"
    echo "Environment: Docker"
    echo ""
    echo "--- Core Tools ---"
    echo "Python: $(python3.12 --version 2>&1)"
    echo "Pip: $(python3.12 -m pip --version 2>&1)"
    echo "Poetry: $(poetry --version 2>&1)"
    echo "Java: $(java -version 2>&1 | head -n 1)"
    echo "R: $(R --version | head -n 1)"
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
    echo "Environment File: /etc/environment and ~/.env"
    echo "Python Virtual Environment: ${PROJECT_BASE_DIR}/.venv"
} > "$LOG_FILE"

echo "✅ Environment setup log created at: $LOG_FILE"

echo "============================================================================="
echo "✅ Installation Complete!"
echo "============================================================================="
echo "To activate the environment, use: activate_cgg"
echo "Or manually: source ${PROJECT_BASE_DIR}/.venv/bin/activate"
echo ""
echo "All tools are installed and ready to use."
echo "============================================================================="