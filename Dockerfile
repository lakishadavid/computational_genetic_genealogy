# Base image: Use an appropriate Linux distro
FROM ubuntu:22.04

# Metadata for documentation
LABEL maintainer="LaKisha David <ltdavid2@illinois.edu>"
LABEL description="A Docker container for genomic analysis"
LABEL version="1.0.0"

# Set a non-root user for better security
ARG USERNAME=ubuntu
ARG USER_UID=1000
ARG USER_GID=1000

# Update and install necessary dependencies
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    curl \
    git \
    unzip \
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
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set up the non-root user
RUN groupadd --gid ${USER_GID} ${USERNAME} && \
    useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME} && \
    chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}

USER ${USERNAME}

# Install Python packages required for genomic analysis
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Set working directory inside the container
WORKDIR /home/${USERNAME}/workspace

# Copy scripts to the container
COPY scripts/ /home/${USERNAME}/workspace/scripts/
RUN chmod +x /home/${USERNAME}/workspace/scripts/*.sh

# Entry point for initializing the container
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Define environment variables
ENV PATH="/home/${USERNAME}/workspace/scripts:$PATH"

# Expose relevant ports if needed
EXPOSE 8888

# Default command for running the container
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bash"]