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

# Install system
RUN apt install -y --no-install-recommends \
    build-essential \
    g++ \
    gcc \
    make \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-pip \
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
    libboost-all-dev \
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-plain-generic \
    pandoc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


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
# Update package lists and install dependencies
USER root
RUN apt update -y && apt install -y --no-install-recommends \
    libbz2-dev \
    liblzma-dev \
    zlib1g-dev \
    libgsl-dev \
    libcurl4-openssl-dev \
    bcftools \
    samtools \
    tabix && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set environment variable for BCFtools plugins globally
ENV BCFTOOLS_PLUGINS=/usr/lib/x86_64-linux-gnu/bcftools

# Verify installations
RUN bcftools --version && samtools --version && tabix --version

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

# Define BEAGLE version and URLs
ARG BEAGLE_VERSION="17Dec24.224"
ARG UTILS_DIR="/home/ubuntu/computational_genetic_genealogy/utils"

ENV BEAGLE_JAR="beagle.${BEAGLE_VERSION}.jar"
ENV BREF3_JAR="bref3.${BEAGLE_VERSION}.jar"
ENV UNBREF3_JAR="unbref3.${BEAGLE_VERSION}.jar"
ENV BEAGLE_URL="https://faculty.washington.edu/browning/beagle/${BEAGLE_JAR}"
ENV BREF3_URL="https://faculty.washington.edu/browning/beagle/${BREF3_JAR}"
ENV UNBREF3_URL="https://faculty.washington.edu/browning/beagle/${UNBREF3_JAR}"

# Ensure utils directory exists
RUN mkdir -p ${UTILS_DIR}

# Function to download a file only if it does not exist
RUN set -eux; \
    download_if_missing() { \
        local file_path="${UTILS_DIR}/$1"; \
        local file_url="$2"; \
        if [ -f "${file_path}" ]; then \
            echo "✅ File already exists: ${file_path}. Skipping download."; \
        else \
            echo "⬇️ Downloading $file_url..."; \
            wget -P "${UTILS_DIR}" "${file_url}"; \
        fi; \
    } && \
    download_if_missing "$UNBREF3_JAR" "$UNBREF3_URL" && \
    download_if_missing "$BREF3_JAR" "$BREF3_URL" && \
    download_if_missing "$BEAGLE_JAR" "$BEAGLE_URL"

# Set JAVA_HOME and ensure Java is installed
RUN apt update && apt install -y --no-install-recommends default-jdk && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Verify Beagle installation
RUN java -jar "${UTILS_DIR}/$BEAGLE_JAR" || \
    (echo "❌ Beagle test run failed." && exit 1)

# Run the BonsaiTree installation script
RUN bash /home/ubuntu/computational_genetic_genealogy/scripts_env/install_bonsaitree.sh

# Define variables
ARG UTILS_DIR="/home/ubuntu/computational_genetic_genealogy/utils"
ARG HAP_IBD_JAR="hap-ibd.jar"
ARG REFINED_IBD_JAR="refined-ibd.17Jan20.102.jar"
ARG REFINED_IBD_MERGE_JAR="merge-ibd-segments.17Jan20.102.jar"

ENV HAP_IBD_URL="https://faculty.washington.edu/browning/hap-ibd.jar"
ENV REFINED_IBD_URL="https://faculty.washington.edu/browning/refined-ibd/refined-ibd.17Jan20.102.jar"
ENV REFINED_IBD_MERGE_URL="https://faculty.washington.edu/browning/refined-ibd/merge-ibd-segments.17Jan20.102.jar"

# Ensure Java is installed
RUN apt update && apt install -y --no-install-recommends default-jdk && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Ensure utils directory exists
RUN mkdir -p ${UTILS_DIR}

# Download JAR files only if they do not already exist
RUN set -eux; \
    download_if_missing() { \
        local file_path="${UTILS_DIR}/$1"; \
        local file_url="$2"; \
        if [ -f "${file_path}" ]; then \
            echo "✅ File already exists: ${file_path}. Skipping download."; \
        else \
            echo "⬇️ Downloading $file_url..."; \
            wget -P "${UTILS_DIR}" "${file_url}"; \
        fi; \
    } && \
    download_if_missing "$HAP_IBD_JAR" "$HAP_IBD_URL" && \
    download_if_missing "$REFINED_IBD_JAR" "$REFINED_IBD_URL" && \
    download_if_missing "$REFINED_IBD_MERGE_JAR" "$REFINED_IBD_MERGE_URL"

# Test each downloaded JAR file
RUN java -jar "${UTILS_DIR}/$HAP_IBD_JAR" || (echo "❌ Hap-IBD test run failed." && exit 1)
RUN java -jar "${UTILS_DIR}/$REFINED_IBD_JAR" || (echo "❌ Refined-IBD test run failed." && exit 1)
RUN java -jar "${UTILS_DIR}/$REFINED_IBD_MERGE_JAR" || (echo "❌ Refined-IBD Merge test run failed." && exit 1)

# Define utility directory and IBIS repository details
ARG UTILS_DIR="/home/ubuntu/computational_genetic_genealogy/utils"
ARG IBIS_REPO="https://github.com/williamslab/ibis.git"
ARG IBIS_DIR="${UTILS_DIR}/ibis"

# Ensure dependencies are installed
RUN apt update && apt install -y --no-install-recommends \
    git \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Clone or update the IBIS repository
RUN set -eux; \
    mkdir -p ${UTILS_DIR}; \
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

# Build IBIS using make
WORKDIR ${IBIS_DIR}
RUN make || (echo "❌ Build failed." && exit 1)

# Verify IBIS installation
RUN if [ -x "${IBIS_DIR}/ibis" ]; then \
        echo "✅ IBIS installed successfully."; \
    else \
        echo "❌ IBIS executable not found. Build might have failed."; \
        exit 1; \
    fi

# Define utility directory and Ped-Sim repository details
ARG UTILS_DIR="/home/ubuntu/computational_genetic_genealogy/utils"
ARG PED_SIM_REPO="https://github.com/williamslab/ped-sim.git"
ARG PED_SIM_DIR="${UTILS_DIR}/ped-sim"

# Install dependencies
RUN apt update && apt install -y --no-install-recommends \
    git \
    libboost-all-dev \
    make \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Clone or update the Ped-Sim repository
RUN set -eux; \
    mkdir -p ${UTILS_DIR}; \
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

# Build Ped-Sim using make
WORKDIR ${PED_SIM_DIR}
RUN make || (echo "❌ Build failed." && exit 1)

# Ensure Ped-Sim is executable
RUN chmod +x ${PED_SIM_DIR}/ped-sim

# Verify Ped-Sim installation
RUN if [ -x "${PED_SIM_DIR}/ped-sim" ]; then \
        echo "✅ Ped-Sim installed successfully."; \
    else \
        echo "❌ Ped-Sim executable not found. Build might have failed."; \
        exit 1; \
    fi

# Define utility directory and PLINK2 file details
ARG UTILS_DIR="/home/ubuntu/computational_genetic_genealogy/utils"
ARG PLINK2_FILE_URL="https://s3.amazonaws.com/plink2-assets/alpha6/plink2_linux_x86_64_20241206.zip"
ARG PLINK2_ZIP_FILE="${UTILS_DIR}/plink2_linux_x86_64_20241206.zip"
ARG PLINK2_BINARY="${UTILS_DIR}/plink2"

# Ensure wget and unzip are installed
RUN apt update && apt install -y --no-install-recommends \
    wget \
    unzip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Download and extract PLINK2 if it is not already installed
RUN set -eux; \
    mkdir -p ${UTILS_DIR}; \
    if [ ! -f "${PLINK2_BINARY}" ]; then \
        echo "⬇️ Downloading PLINK2..."; \
        wget --progress=bar:force:noscroll "${PLINK2_FILE_URL}" -P "${UTILS_DIR}"; \
        echo "📂 Unzipping PLINK2..."; \
        unzip "${PLINK2_ZIP_FILE}" -d "${UTILS_DIR}"; \
        rm "${PLINK2_ZIP_FILE}"; \
    fi

# Verify PLINK2 installation
RUN if [ -f "${PLINK2_BINARY}" ] && [ -x "${PLINK2_BINARY}" ]; then \
        echo "✅ PLINK2 installed successfully."; \
        "${PLINK2_BINARY}" --version; \
    else \
        echo "❌ Error: PLINK2 installation failed. Binary not found or not executable."; \
        exit 1; \
    fi

# Define RFMix2 repository details
ARG UTILS_DIR="/home/ubuntu/computational_genetic_genealogy/utils"
ARG RFMIX2_REPO="https://github.com/slowkoni/rfmix.git"
ARG RFMIX2_DIR="${UTILS_DIR}/rfmix2"

# Install dependencies
RUN apt update && apt install -y --no-install-recommends \
    autoconf \
    automake \
    make \
    gcc \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Clone or update the RFMix2 repository
RUN set -eux; \
    mkdir -p ${UTILS_DIR}; \
    if [ -d "${RFMIX2_DIR}" ]; then \
        echo "📂 RFMix2 directory already exists at ${RFMIX2_DIR}."; \
    else \
        echo "⬇️ Cloning RFMix2 repository..."; \
        git clone "${RFMIX2_REPO}" "${RFMIX2_DIR}"; \
    fi

# Build RFMix2 from source
WORKDIR ${RFMIX2_DIR}
RUN set -eux; \
    echo "🔨 Generating build files..."; \
    aclocal && \
    autoheader && \
    autoconf && \
    automake --add-missing && \
    ./configure && \
    echo "🔨 Compiling RFMix2..."; \
    make || (echo "❌ Error: RFMix2 build failed." && exit 1)

# Verify RFMix2 build
RUN if [ -f "${RFMIX2_DIR}/rfmix" ]; then \
        echo "✅ RFMix2 built successfully."; \
    else \
        echo "❌ Error: RFMix2 binary not found. Build failed."; \
        exit 1; \
    fi



###############################################################################
# Volume Configuration
###############################################################################
VOLUME ["${WORKSPACE_DIR}/computational_genetic_genealogy/data", "${WORKSPACE_DIR}/computational_genetic_genealogy/references", "${WORKSPACE_DIR}/computational_genetic_genealogy/results"]

###############################################################################
# Container Startup
###############################################################################
USER ${USERNAME}
WORKDIR ${WORKSPACE_DIR}/computational_genetic_genealogy

CMD ["/bin/bash", "-c", "echo '===============================================' && \
echo '✅ Setup completed!' && \
echo 'Your environment has been configured with:' && \
echo '- Updated system packages' && \
echo '- ~/.local/bin added to PATH' && \
echo '- System dependencies installed' && \
echo '- Poetry installed and configured' && \
echo '- Project dependencies installed' && \
echo '- Python kernel installed for Jupyter Notebooks' && \
echo '===============================================' && \
echo '' && \
echo '🚀 Your development container is ready!' && \
echo '' && \
echo '📢 To connect VS Code to this running container:' && \
echo '1️⃣ Open VS Code.' && \
echo '2️⃣ Install the Remote - Containers extension (if not already installed).' && \
echo '3️⃣ Open the Command Palette (Ctrl+Shift+P on Windows/Linux or Cmd+Shift+P on macOS, or via the menu: View > Command Palette)' && \
echo '   and select Remote-Containers: Attach to Running Container.' && \
echo '4️⃣ Choose this container from the list and start coding!' && \
echo '' && \
echo '💡 Note: If you wish to run a new container instance, you must first stop the current container.' && \
echo '   To stop the container, type exit or press Ctrl+D. This halts the container while preserving it' && \
echo '   for later reattachment.' && \
echo '' && \
echo '💡 To resume your previous session, first locate your container ID or name by running:' && \
echo '   docker ps -a' && \
echo '   Then, restart and attach to the container using:' && \
echo '   docker start -ai <container_id_or_name>' && \
echo '   (Data in mounted volumes persists between runs.)' && \
echo '' && \
echo '📂 This container leverages Docker volumes to persist your work (e.g., data, references, and results)' && \
echo '    on your local machine. Using volumes ensures that your data remains intact even if' && \
echo '    the container is stopped or removed, allowing you to continue your work seamlessly.' && \
echo '    To mount local directories, run:' && \
echo '' && \
echo '   docker run -it \\ ' && \
echo '   -v $(pwd)/data:/home/ubuntu/computational_genetic_genealogy/data \\ ' && \
echo '   -v $(pwd)/references:/home/ubuntu/computational_genetic_genealogy/references \\ ' && \
echo '   -v $(pwd)/results:/home/ubuntu/computational_genetic_genealogy/results \\ ' && \
echo '   lakishadavid/cgg_image:latest' && \
echo '' && \
echo '   (Replace $(pwd)/results and $(pwd)/references with your actual local paths)' && \
exec bash"]