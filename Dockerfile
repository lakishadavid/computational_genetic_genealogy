###############################################################################
# Base Configuration
###############################################################################
FROM ubuntu:24.04

# Metadata
LABEL maintainer="LaKisha David <ltdavid2@illinois.edu>"
LABEL description="A Docker container for genetic genealogy analysis - Ubuntu 24.04 base"
LABEL version="1.1.0" 

###############################################################################
# User Setup Arguments
###############################################################################
ARG USERNAME=ubuntu
ARG USER_UID=1000
ARG USER_GID=1000
ARG WORKSPACE_DIR=/home/ubuntu
ARG PROJECT_DIR_NAME=computational_genetic_genealogy

###############################################################################
# Environment Variables (Define early for use throughout)
###############################################################################
ENV WORKSPACE_DIR=${WORKSPACE_DIR}
ENV PROJECT_DIR=${WORKSPACE_DIR}/${PROJECT_DIR_NAME}
ENV UTILS_DIR=${PROJECT_DIR}/utils
ENV REFERENCES_DIR=${PROJECT_DIR}/references
ENV DATA_DIR=${PROJECT_DIR}/data
ENV RESULTS_DIR=${PROJECT_DIR}/results
ENV DEBIAN_FRONTEND=noninteractive

###############################################################################
# System Setup
###############################################################################

# Update repositories, add PPAs, install base dependencies
# Note: bcftools, samtools, tabix removed from this list - will be built from source
# Added openjdk-21-jdk/jre, libncurses-dev
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends software-properties-common && \
    add-apt-repository -y universe && add-apt-repository -y multiverse && add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get update -y && \
    apt-get install -y --no-install-recommends \
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
    openjdk-21-jdk \
    openjdk-21-jre \
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
    libatlas-base-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME explicitly for OpenJDK 21
ENV JAVA_HOME="/usr/lib/jvm/java-21-openjdk-amd64"
ENV PATH="${JAVA_HOME}/bin:${PATH}"

###############################################################################
# Build HTSlib, Samtools, BCFtools v1.18 from Source
###############################################################################
RUN BUILD_DIR=$(mktemp -d) && cd "$BUILD_DIR" && \
    SAMTOOLS_VERSION=1.18 && \
    # HTSlib
    wget https://github.com/samtools/htslib/releases/download/${SAMTOOLS_VERSION}/htslib-${SAMTOOLS_VERSION}.tar.bz2 && \
    tar -xjf htslib-${SAMTOOLS_VERSION}.tar.bz2 && \
    cd htslib-${SAMTOOLS_VERSION} && ./configure --prefix=/usr/local && make && make install && cd .. && \
    # Samtools
    wget https://github.com/samtools/samtools/releases/download/${SAMTOOLS_VERSION}/samtools-${SAMTOOLS_VERSION}.tar.bz2 && \
    tar -xjf samtools-${SAMTOOLS_VERSION}.tar.bz2 && \
    cd samtools-${SAMTOOLS_VERSION} && ./configure --prefix=/usr/local && make && make install && cd .. && \
    # BCFtools
    wget https://github.com/samtools/bcftools/releases/download/${SAMTOOLS_VERSION}/bcftools-${SAMTOOLS_VERSION}.tar.bz2 && \
    tar -xjf bcftools-${SAMTOOLS_VERSION}.tar.bz2 && \
    cd bcftools-${SAMTOOLS_VERSION} && ./configure --prefix=/usr/local && make && make install && cd .. && \
    # Cleanup
    cd / && rm -rf "$BUILD_DIR" && \
    # Update library cache
    ldconfig

# Verify source build versions
RUN samtools --version | head -n 1 && \
    bcftools --version | head -n 1 && \
    # Tabix is part of the HTSlib installation
    tabix --version | head -n 1

###############################################################################
# User Setup (Create user)
###############################################################################
RUN groupadd --gid ${USER_GID} ${USERNAME} || true && \
    useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME} || true && \
    # Give user ownership of workspace AFTER it might have been created by root steps
    mkdir -p ${WORKSPACE_DIR} && chown -R ${USERNAME}:${USERNAME} ${WORKSPACE_DIR}

###############################################################################
# Python and Poetry Setup
###############################################################################

USER ${USERNAME}
# Ensure pipx path is configured for the user and install poetry
RUN pipx ensurepath && pipx install poetry
# Add pipx path to the environment for subsequent steps run as root or user
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"
USER root

###############################################################################
# Project Structure Setup
###############################################################################
# Create project directories using defined ENV VARS and set ownership
RUN install -d -m 775 -o ${USERNAME} -g ${USERNAME} \
    ${PROJECT_DIR}/results \
    ${PROJECT_DIR}/data \
    ${PROJECT_DIR}/references \
    ${PROJECT_DIR}/utils && \
    # Create __init__.py files where appropriate (optional but good practice)
    touch ${PROJECT_DIR}/references/__init__.py \
    ${PROJECT_DIR}/data/__init__.py \
    ${PROJECT_DIR}/results/__init__.py \
    ${PROJECT_DIR}/utils/__init__.py && \
    chown -R ${USERNAME}:${USERNAME} ${PROJECT_DIR}

# Set up environment configuration file in HOME directory
RUN touch ${WORKSPACE_DIR}/.env && \
    echo "PROJECT_WORKING_DIR=${PROJECT_DIR}" >> ${WORKSPACE_DIR}/.env && \
    echo "PROJECT_UTILS_DIR=${UTILS_DIR}" >> ${WORKSPACE_DIR}/.env && \
    echo "PROJECT_RESULTS_DIR=${RESULTS_DIR}" >> ${WORKSPACE_DIR}/.env && \
    echo "PROJECT_DATA_DIR=${DATA_DIR}" >> ${WORKSPACE_DIR}/.env && \
    echo "PROJECT_REFERENCES_DIR=${REFERENCES_DIR}" >> ${WORKSPACE_DIR}/.env && \
    echo "USER_HOME=${WORKSPACE_DIR}" >> ${WORKSPACE_DIR}/.env && \
    chown ${USERNAME}:${USERNAME} ${WORKSPACE_DIR}/.env

###############################################################################
# Copy Project Code and Set Permissions
###############################################################################
COPY --chown=${USERNAME}:${USERNAME} . ${PROJECT_DIR}/
# Ensure scripts are executable
RUN chmod -R +x ${PROJECT_DIR}/scripts_env/

###############################################################################
# Install Project Python Dependencies via Poetry
###############################################################################
WORKDIR ${PROJECT_DIR}
USER ${USERNAME}
RUN poetry config virtualenvs.in-project true && poetry install --no-root
USER root

###############################################################################
# Install Additional Tools (AWS CLI, JARs, Source Tools, Binaries)
###############################################################################

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" && \
    unzip -q /tmp/awscliv2.zip -d /tmp && \
    /tmp/aws/install && \
    rm -rf /tmp/awscliv2.zip /tmp/aws

# Verify R (installed earlier)
RUN R --version | head -n 1

### Download JARs (Beagle, HapIBD, RefinedIBD, Merge) #########################
ENV BEAGLE_JAR="beagle.27Feb25.75f.jar"
ENV HAP_IBD_JAR="hap-ibd.jar"
ENV REFINED_IBD_JAR="refined-ibd.17Jan20.102.jar"
ENV REFINED_IBD_MERGE_JAR="merge-ibd-segments.17Jan20.102.jar"
RUN wget -nv -O "${UTILS_DIR}/${BEAGLE_JAR}" "https://faculty.washington.edu/browning/beagle/${BEAGLE_JAR}" && \
    wget -nv -O "${UTILS_DIR}/${HAP_IBD_JAR}" "https://faculty.washington.edu/browning/${HAP_IBD_JAR}" && \
    wget -nv -O "${UTILS_DIR}/${REFINED_IBD_JAR}" "https://faculty.washington.edu/browning/refined-ibd/${REFINED_IBD_JAR}" && \
    wget -nv -O "${UTILS_DIR}/${REFINED_IBD_MERGE_JAR}" "https://faculty.washington.edu/browning/refined-ibd/${REFINED_IBD_MERGE_JAR}" && \
    chmod +x "${UTILS_DIR}"/*.jar
# Optional: Verify Beagle JAR download integrity/basic execution
RUN java -Xmx1g -jar "${UTILS_DIR}/${BEAGLE_JAR}" || echo "Beagle JAR executed (ignore non-zero exit if help shown)."

### BonsaiTree installation ##################################################
ENV BONSAI_DIR="${UTILS_DIR}/bonsaitree"
# Clone the repository as root first
RUN git clone https://github.com/23andMe/bonsaitree.git "${BONSAI_DIR}" && \
    chown -R ${USERNAME}:${USERNAME} "${BONSAI_DIR}"

# Switch to the directory
WORKDIR ${BONSAI_DIR}

# Now switch to the user who owns the directory
USER ${USERNAME}

# Install BonsaiTree dependencies via Poetry, then build/install package with pip --no-deps
RUN poetry env use python3.12 && \
    # Explicitly add ALL setup_requires and install_requires from setup.py
    echo "Adding all BonsaiTree dependencies via Poetry..." && \
    poetry add Cython funcy numpy scipy six setuptools-scm wheel pandas frozendict && \
    # Install the package itself using pip, but tell it *not* to handle dependencies
    echo "Building and installing BonsaiTree package itself (dependencies handled by Poetry)..." && \
    poetry run pip install . --no-deps && \
    # Verify installation by importing
    echo "Verifying BonsaiTree installation..." && \
    poetry run python -c "from bonsaitree.v3.bonsai import build_pedigree; print('Bonsai module imported successfully.')"

# Switch back to root and the original project directory
USER root
WORKDIR ${PROJECT_DIR}

### LiftOver tool installation ###############################################
RUN wget -nv http://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/liftOver -O "${UTILS_DIR}/liftOver" && \
    chmod +x "${UTILS_DIR}/liftOver" && \
    wget -nv http://hgdownload.cse.ucsc.edu/goldenPath/hg19/liftOver/hg19ToHg38.over.chain.gz -P "${REFERENCES_DIR}/"

### Build RFMix2, IBIS, Ped-Sim ##############################################
# Define repositories and directories
ENV RFMIX2_REPO="https://github.com/slowkoni/rfmix.git"
ENV IBIS_REPO="https://github.com/williamslab/ibis.git"
ENV PED_SIM_REPO="https://github.com/williamslab/ped-sim.git"
ENV RFMIX2_DIR="${UTILS_DIR}/rfmix2"
ENV IBIS_DIR="${UTILS_DIR}/ibis"
ENV PED_SIM_DIR="${UTILS_DIR}/ped-sim"

# Build RFMix2
RUN git clone "${RFMIX2_REPO}" "${RFMIX2_DIR}" && \
    cd "${RFMIX2_DIR}" && \
    aclocal && autoheader && autoconf && automake --add-missing && ./configure && make && \
    # Verify build
    test -f "${RFMIX2_DIR}/rfmix" || (echo "RFMix2 build failed" && exit 1)

# Build IBIS
RUN git clone --recurse-submodules "${IBIS_REPO}" "${IBIS_DIR}" && \
    cd "${IBIS_DIR}" && make && \
    # Verify build
    test -x "${IBIS_DIR}/ibis" || (echo "IBIS build failed" && exit 1)

# Build Ped-Sim
RUN git clone --recurse-submodules "${PED_SIM_REPO}" "${PED_SIM_DIR}" && \
    cd "${PED_SIM_DIR}" && make && chmod +x ped-sim && \
    # Verify build
    test -x "${PED_SIM_DIR}/ped-sim" || (echo "Ped-Sim build failed" && exit 1)

### Install PLINK2 Binary ###################################################
ENV PLINK2_FILE_URL="https://s3.amazonaws.com/plink2-assets/alpha6/plink2_linux_x86_64_20241206.zip"
ENV PLINK2_ZIP_FILE="${UTILS_DIR}/plink2_linux_x86_64_20241206.zip"
ENV PLINK2_BINARY="${UTILS_DIR}/plink2"
RUN wget -nv "${PLINK2_FILE_URL}" -O "${PLINK2_ZIP_FILE}" && \
    unzip "${PLINK2_ZIP_FILE}" -d "${UTILS_DIR}" && \
    rm "${PLINK2_ZIP_FILE}" && \
    chmod +x ${PLINK2_BINARY} && \
    # Verify install
    ${PLINK2_BINARY} --version

###############################################################################
# Volume Configuration & Final Setup
###############################################################################
VOLUME ["${DATA_DIR}", "${REFERENCES_DIR}", "${RESULTS_DIR}"]

# Ensure final ownership and permissions if needed
RUN chown -R ${USERNAME}:${USERNAME} ${PROJECT_DIR} ${WORKSPACE_DIR}/.env

# Add entrypoint script
COPY --chown=${USERNAME}:${USERNAME} docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

WORKDIR ${PROJECT_DIR}
USER ${USERNAME}

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["bash"]