# Base image: Use an appropriate Linux distro
FROM ubuntu:22.04

# Metadata for documentation
LABEL maintainer="LaKisha David <ltdavid2@illinois.edu>"
LABEL description="A Docker container for genetic genealogy analysis"
LABEL version="1.0.0"

# Set a non-root user for better security
ARG USERNAME=ubuntu
ARG USER_UID=1000
ARG USER_GID=1000

# Set up the non-root user
RUN groupadd --gid ${USER_GID} ${USERNAME} && \
    useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME} && \
    chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}

USER root

# Update and install necessary dependencies
RUN apt-get update -y && \
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
    libboost-all-dev
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
ARG WORKSPACE_DIR=/home/ubuntu
WORKDIR ${WORKSPACE_DIR}
RUN mkdir results data references utils
RUN chown -R ubuntu:ubuntu results data references utils

# Install poetry with hash verification
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION=1.8.5
ENV PATH="${POETRY_HOME}/bin:${PATH}"
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python3 - && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Install Python packages
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

# Copy the repository directory to the container
COPY . .

# Copy entrypoint script into the container
# COPY entrypoint.sh /usr/local/bin/entrypoint.sh
# RUN chmod +x /usr/local/bin/entrypoint.sh

# # Set the entrypoint
# ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
USER ${USERNAME}

# Default command
CMD ["bash"]
