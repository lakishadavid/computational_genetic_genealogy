###############################################################################
# Base Configuration
###############################################################################
FROM ubuntu:24.04

# Metadata
LABEL maintainer="LaKisha David <ltdavid2@illinois.edu>"
LABEL description="A Docker container for genetic genealogy analysis"
LABEL version="1.0.0"

###############################################################################
# User Setup
###############################################################################
ARG USERNAME=ubuntu
ARG USER_UID=1000
ARG USER_GID=1000
ARG WORKSPACE_DIR=/home/ubuntu

###############################################################################
# System Setup
###############################################################################

# Revise list of places to search for packages
RUN apt update && apt upgrade -y && apt install -y software-properties-common
RUN apt-add-repository -y universe && apt-add-repository -y multiverse && apt-add-repository -y ppa:deadsnakes/ppa 
RUN apt update && apt upgrade -y

# Update repositories and install dependencies
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    software-properties-common \
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
    libcairo2 \
    libcairo2-dev \
    pkg-config \
    libpng-dev \
    zlib1g-dev \
    libbz2-dev \
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
    default-jre \
    default-jdk \
    gawk \
    libboost-all-dev \
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-plain-generic \
    pandoc \
    r-base \
    liblzma-dev \
    libgsl-dev \
    bcftools \
    samtools \
    tabix \
    autoconf \
    automake \
    libblas-dev \
    liblapack-dev \
    libatlas-base-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

###############################################################################
# User Setup
###############################################################################
# Create the user if it doesn’t exist and ensure correct ownership
RUN groupadd --gid ${USER_GID} ${USERNAME} || true && \
    useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME} || true && \
    chown -R ${USERNAME}:${USERNAME} ${WORKSPACE_DIR}

###############################################################################
# Python and Poetry Setup
###############################################################################

RUN apt update && apt install -y pipx
USER ${USERNAME}
RUN pipx ensurepath && pipx install poetry

USER root
ENV PATH="/home/${USERNAME}/.local/bin:$PATH"

###############################################################################
# Project Structure Setup
###############################################################################
# Create project directories and initialize Python packages
RUN install -d -m 775 -o ${USERNAME} -g ${USERNAME} \
    ${WORKSPACE_DIR}/computational_genetic_genealogy/results \
    ${WORKSPACE_DIR}/computational_genetic_genealogy/data \
    ${WORKSPACE_DIR}/computational_genetic_genealogy/references \
    ${WORKSPACE_DIR}/computational_genetic_genealogy/utils && \
    touch ${WORKSPACE_DIR}/computational_genetic_genealogy/references/__init__.py \
    ${WORKSPACE_DIR}/computational_genetic_genealogy/data/__init__.py \
    ${WORKSPACE_DIR}/computational_genetic_genealogy/results/__init__.py \
    ${WORKSPACE_DIR}/computational_genetic_genealogy/utils/__init__.py && \
    chown -R ${USERNAME}:${USERNAME} ${WORKSPACE_DIR}

# Set up environment configuration
RUN touch ${WORKSPACE_DIR}/.env && \
    echo "PROJECT_UTILS_DIR=${WORKSPACE_DIR}/computational_genetic_genealogy/utils" >> ${WORKSPACE_DIR}/.env && \
    echo "PROJECT_RESULTS_DIR=${WORKSPACE_DIR}/computational_genetic_genealogy/results" >> ${WORKSPACE_DIR}/.env && \
    echo "PROJECT_DATA_DIR=${WORKSPACE_DIR}/computational_genetic_genealogy/data" >> ${WORKSPACE_DIR}/.env && \
    echo "PROJECT_REFERENCES_DIR=${WORKSPACE_DIR}/computational_genetic_genealogy/references" >> ${WORKSPACE_DIR}/.env && \
    echo "PROJECT_WORKING_DIR=${WORKSPACE_DIR}/computational_genetic_genealogy" >> ${WORKSPACE_DIR}/.env && \
    echo "USER_HOME=${WORKSPACE_DIR}" >> ${WORKSPACE_DIR}/.env && \
    chown ${USERNAME}:${USERNAME} ${WORKSPACE_DIR}/.env

###############################################################################
# Setup Scripts and Dependencies
###############################################################################
# Copy project files
COPY . ${WORKSPACE_DIR}/computational_genetic_genealogy/
RUN chown -R ${USERNAME}:${USERNAME} ${WORKSPACE_DIR}/computational_genetic_genealogy
RUN chmod -R +x ${WORKSPACE_DIR}/computational_genetic_genealogy/scripts_env/

###############################################################################
# Install Project Dependencies via Poetry
###############################################################################
# Switch to project directory
WORKDIR ${WORKSPACE_DIR}/computational_genetic_genealogy

# Install project dependencies as the user
USER ${USERNAME}
RUN poetry config virtualenvs.in-project true && poetry install --no-root

###############################################################################
# Install System Dependencies
###############################################################################
ENV UTILS_DIR="${WORKSPACE_DIR}/computational_genetic_genealogy/utils"

USER root

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" && \
    unzip -q /tmp/awscliv2.zip -d /tmp && \
    /tmp/aws/install && \
    rm -rf /tmp/awscliv2.zip /tmp/aws

RUN R --version

# Check if Java is installed and install if missing
RUN if command -v java > /dev/null; then \
    echo "Java is already installed. Version: $(java -version 2>&1 | head -n 1)"; \
    else \
    apt-get update && \
    apt-get install -y --no-install-recommends default-jdk && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    echo "Java installation successful. Version: $(java -version 2>&1 | head -n 1)"; \
    fi

# Set JAVA_HOME globally
RUN JAVA_HOME=$(readlink -f /usr/bin/java | sed "s:/bin/java::") && \
    echo "JAVA_HOME detected: $JAVA_HOME" && \
    echo "export JAVA_HOME=$JAVA_HOME" >> /etc/environment && \
    echo "export PATH=\$JAVA_HOME/bin:\$PATH" >> /etc/environment

# Ensure JAVA_HOME is available in the shell
ENV JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"
ENV PATH="${JAVA_HOME}/bin:${PATH}"

ENV BCFTOOLS_PLUGINS="/usr/lib/x86_64-linux-gnu/bcftools"
# Verify installations
RUN bcftools --version && samtools --version && tabix --version

### beagle, hap_ibd, refined_ibd, merge ####################################################

# Define genomic analysis tool variables with updated links
ENV BEAGLE_JAR="beagle.27Feb25.75f.jar"
ENV HAP_IBD_JAR="hap-ibd.jar"
ENV REFINED_IBD_JAR="refined-ibd.17Jan20.102.jar"
ENV REFINED_IBD_MERGE_JAR="merge-ibd-segments.17Jan20.102.jar"

# Ensure utils directory exists and download files with verbose output and error handling
RUN mkdir -p "${UTILS_DIR}" && \
    wget -v -O "${UTILS_DIR}/${BEAGLE_JAR}" "https://faculty.washington.edu/browning/beagle/${BEAGLE_JAR}" || \
    (echo "Failed to download Beagle JAR" && exit 1) && \
    wget -v -O "${UTILS_DIR}/${HAP_IBD_JAR}" "https://faculty.washington.edu/browning/${HAP_IBD_JAR}" || \
    (echo "Failed to download Hap-IBD JAR" && exit 1) && \
    wget -v -O "${UTILS_DIR}/${REFINED_IBD_JAR}" "https://faculty.washington.edu/browning/refined-ibd/${REFINED_IBD_JAR}" || \
    (echo "Failed to download Refined-IBD JAR" && exit 1) && \
    wget -v -O "${UTILS_DIR}/${REFINED_IBD_MERGE_JAR}" "https://faculty.washington.edu/browning/refined-ibd/${REFINED_IBD_MERGE_JAR}" || \
    (echo "Failed to download Refined-IBD Merge JAR" && exit 1)

# Verify downloads and file permissions
RUN ls -l "${UTILS_DIR}" && \
    chmod +x "${UTILS_DIR}"/*.jar && \
    echo "Verifying Beagle JAR:" && \
    java -Xmx1g -jar "${UTILS_DIR}/${BEAGLE_JAR}" 2>&1 | grep -q "Browning" && \
    echo "✅ Beagle JAR verified successfully." || \
    echo "⚠️ Beagle JAR verification showed unexpected output (may be OK if just missing arguments)"

### BonsaiTree installation script ######################################################

# Set up BonsaiTree
ENV BONSAI_DIR="${UTILS_DIR}/bonsaitree"

# Clone BonsaiTree repository
RUN git clone https://github.com/23andMe/bonsaitree.git "${BONSAI_DIR}"

# Install BonsaiTree dependencies
WORKDIR ${BONSAI_DIR}
RUN poetry env use python3 && \
    if [ -f "requirements.txt" ]; then \
    echo "Adding dependencies from requirements.txt..." && \
    grep -vE '^\s*(#|$)' requirements.txt | while IFS= read -r dependency; do \
    package=$(echo "$dependency" | sed 's/[<>=!~].*//') && \
    poetry add "$package" || echo "Failed to add dependency: $package"; \
    done; \
    fi && \
    echo "Adding additional dependencies..." && \
    poetry add pandas frozendict Cython funcy numpy scipy && \
    poetry install --no-root

# Install setuptools in the Poetry environment and verify installation
RUN poetry run pip install setuptools && \
    echo 'try:' > verify_bonsai.py && \
    echo '    from bonsaitree.v3.bonsai import build_pedigree' >> verify_bonsai.py && \
    echo '    print("Bonsai module imported successfully.")' >> verify_bonsai.py && \
    echo 'except ImportError as e:' >> verify_bonsai.py && \
    echo '    print(f"Failed to import Bonsai: {e}")' >> verify_bonsai.py && \
    echo '    exit(1)' >> verify_bonsai.py && \
    poetry run python verify_bonsai.py && \
    rm verify_bonsai.py

# liftover tool installation
ENV LIFTOVER_DIR="${UTILS_DIR}/liftover"
RUN mkdir -p "${LIFTOVER_DIR}" && \
    wget http://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/liftOver -O "${UTILS_DIR}/liftOver" && \
    chmod +x "${UTILS_DIR}/liftOver" && \
    wget http://hgdownload.cse.ucsc.edu/goldenPath/hg19/liftOver/hg19ToHg38.over.chain.gz -P "${WORKSPACE_DIR}/computational_genetic_genealogy/references/"


### rfmix2, ibis, ped-sim, plink2 #######################################################################

WORKDIR ${WORKSPACE_DIR}/computational_genetic_genealogy

# Define repositories
ENV RFMIX2_REPO="https://github.com/slowkoni/rfmix.git"
ENV IBIS_REPO="https://github.com/williamslab/ibis.git"
ENV PED_SIM_REPO="https://github.com/williamslab/ped-sim.git"
ENV PLINK2_FILE_URL="https://s3.amazonaws.com/plink2-assets/alpha6/plink2_linux_x86_64_20241206.zip"

# Define install directories
ENV RFMIX2_DIR="${UTILS_DIR}/rfmix2"
ENV IBIS_DIR="${UTILS_DIR}/ibis"
ENV PED_SIM_DIR="${UTILS_DIR}/ped-sim"
ENV PLINK2_BINARY="${UTILS_DIR}/plink2"

# Clone or update RFMix2 repository
RUN set -eux; \
    if [ -d "${RFMIX2_DIR}" ]; then \
    echo "📂 RFMix2 directory already exists at ${RFMIX2_DIR}."; \
    else \
    echo "⬇️ Cloning RFMix2 repository..."; \
    git clone "${RFMIX2_REPO}" "${RFMIX2_DIR}"; \
    fi

# Build RFMix2
WORKDIR ${RFMIX2_DIR}
RUN set -eux; \
    echo "🔨 Generating build files for RFMix2..."; \
    aclocal && autoheader && autoconf && automake --add-missing && ./configure && make || \
    (echo "❌ Error: RFMix2 build failed." && exit 1)

# Verify RFMix2 installation
RUN if [ -f "${RFMIX2_DIR}/rfmix" ]; then \
    echo "✅ RFMix2 installed successfully."; \
    else \
    echo "❌ RFMix2 binary not found. Build might have failed."; \
    exit 1; \
    fi

# Clone or update IBIS repository
RUN set -eux; \
    if [ -d "${IBIS_DIR}" ]; then \
    echo "📂 IBIS directory already exists at ${IBIS_DIR}."; \
    if [ -d "${IBIS_DIR}/.git" ]; then \
    echo "🔄 Updating IBIS repository..."; \
    cd "${IBIS_DIR}" && git pull origin master; \
    else \
    echo "⚠️ Directory exists but is not a Git repository. Consider removing it manually."; \
    exit 1; \
    fi; \
    else \
    echo "⬇️ Cloning IBIS repository..."; \
    git clone --recurse-submodules "${IBIS_REPO}" "${IBIS_DIR}"; \
    fi

# Build IBIS
WORKDIR ${IBIS_DIR}
RUN make || (echo "❌ IBIS build failed." && exit 1)

# Verify IBIS installation
RUN if [ -x "${IBIS_DIR}/ibis" ]; then \
    echo "✅ IBIS installed successfully."; \
    else \
    echo "❌ IBIS executable not found. Build might have failed."; \
    exit 1; \
    fi

# Clone or update Ped-Sim repository
RUN set -eux; \
    if [ -d "${PED_SIM_DIR}" ]; then \
    echo "📂 Ped-Sim directory already exists at ${PED_SIM_DIR}."; \
    if [ -d "${PED_SIM_DIR}/.git" ]; then \
    echo "🔄 Updating Ped-Sim repository..."; \
    cd "${PED_SIM_DIR}" && git pull origin master; \
    else \
    echo "⚠️ Directory exists but is not a Git repository. Consider removing it manually."; \
    exit 1; \
    fi; \
    else \
    echo "⬇️ Cloning Ped-Sim repository..."; \
    git clone --recurse-submodules "${PED_SIM_REPO}" "${PED_SIM_DIR}"; \
    fi

# Build Ped-Sim
WORKDIR ${PED_SIM_DIR}
RUN make || (echo "❌ Ped-Sim build failed." && exit 1)

# Ensure Ped-Sim is executable
RUN chmod +x ${PED_SIM_DIR}/ped-sim

# Verify Ped-Sim installation
RUN if [ -x "${PED_SIM_DIR}/ped-sim" ]; then \
    echo "✅ Ped-Sim installed successfully."; \
    else \
    echo "❌ Ped-Sim executable not found. Build might have failed."; \
    exit 1; \
    fi

# Download and extract PLINK2 if it is not already installed
RUN set -eux; \
    if [ ! -f "${PLINK2_BINARY}" ]; then \
    echo "⬇️ Downloading PLINK2..."; \
    wget --progress=bar:force:noscroll "${PLINK2_FILE_URL}" -P "${UTILS_DIR}"; \
    echo "📂 Unzipping PLINK2..."; \
    unzip "${UTILS_DIR}/plink2_linux_x86_64_20241206.zip" -d "${UTILS_DIR}"; \
    rm "${UTILS_DIR}/plink2_linux_x86_64_20241206.zip"; \
    chmod +x ${PLINK2_BINARY}; \
    fi

# Verify PLINK2 installation
RUN if [ -f "${PLINK2_BINARY}" ] && [ -x "${PLINK2_BINARY}" ]; then \
    echo "✅ PLINK2 installed successfully."; \
    "${PLINK2_BINARY}" --version; \
    else \
    echo "❌ PLINK2 installation failed. Binary not found or not executable."; \
    exit 1; \
    fi

###############################################################################
# Volume Configuration
###############################################################################
VOLUME ["${WORKSPACE_DIR}/computational_genetic_genealogy/data", "${WORKSPACE_DIR}/computational_genetic_genealogy/references", "${WORKSPACE_DIR}/computational_genetic_genealogy/results"]

###############################################################################
# Container Startup
###############################################################################
# Add entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

WORKDIR ${WORKSPACE_DIR}/computational_genetic_genealogy
USER ${USERNAME}

# Use entrypoint script
ENTRYPOINT ["/docker-entrypoint.sh"]