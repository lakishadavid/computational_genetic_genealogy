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
    python3.10-dev \
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

# Create directories with correct ownership and permissions
RUN install -d -m 775 -o ${USERNAME} -g ${USERNAME} \
    ${WORKSPACE_DIR}/results ${WORKSPACE_DIR}/data ${WORKSPACE_DIR}/references ${WORKSPACE_DIR}/utils && \
    touch ${WORKSPACE_DIR}/references/__init__.py \
          ${WORKSPACE_DIR}/data/__init__.py \
          ${WORKSPACE_DIR}/results/__init__.py \
          ${WORKSPACE_DIR}/utils/__init__.py && \
    chown -R ${USERNAME}:${USERNAME} ${WORKSPACE_DIR}

# Install poetry with hash verification
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION=1.8.5
ENV PATH="${POETRY_HOME}/bin:${PATH}"
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python3 - && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false && \
    chown -R ${USERNAME}:${USERNAME} ${POETRY_HOME}

USER ${USERNAME}
WORKDIR ${WORKSPACE_DIR}

# Install Python packages as user
COPY --chown=${USERNAME}:${USERNAME} pyproject.toml poetry.lock ./
RUN poetry install --no-root

# Copy with correct ownership
COPY --chown=${USERNAME}:${USERNAME} . .

# Ensure .env setup and directory structure before running
RUN chmod +x /home/ubuntu/setup_docker_env_file.sh

# Ensure script executes correctly
ENTRYPOINT ["/bin/bash", "-c", "/home/ubuntu/setup_docker_env_file.sh && exec bash"]

# Stay as user
USER ${USERNAME}
CMD ["bash"]