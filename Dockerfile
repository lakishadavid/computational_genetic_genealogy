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
RUN apt-get update -y

RUN apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    gcc \
    make \
    python3 \
    python3-pip \
    python3-dev \
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
    libboost-all-dev 
    
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
ARG WORKSPACE_DIR=/home/ubuntu
WORKDIR ${WORKSPACE_DIR}

# Ensure ~/.local exists and
RUN mkdir -p /home/ubuntu/.local

# Add ~/.local/bin to PATH only if it's not already in ~/.bashrc
RUN if ! grep -qxF 'export PATH="$HOME/.local/bin:$PATH"' /home/ubuntu/.bashrc; then \
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> /home/ubuntu/.bashrc && \
        echo "Added ~/.local/bin to PATH in ~/.bashrc"; \
    else \
        echo "~/.local/bin is already in PATH in ~/.bashrc"; \
    fi

# Ensure correct ownership dynamically
RUN chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}/.local

# Create directories with correct ownership and permissions
RUN install -d -m 775 -o ${USERNAME} -g ${USERNAME} \
    ${WORKSPACE_DIR}/results ${WORKSPACE_DIR}/data ${WORKSPACE_DIR}/references ${WORKSPACE_DIR}/utils && \
    touch ${WORKSPACE_DIR}/references/__init__.py \
          ${WORKSPACE_DIR}/data/__init__.py \
          ${WORKSPACE_DIR}/results/__init__.py \
          ${WORKSPACE_DIR}/utils/__init__.py && \
    chown -R ${USERNAME}:${USERNAME} ${WORKSPACE_DIR}

# Set Poetry installation directory explicitly
ENV POETRY_HOME=/home/ubuntu/.local
ENV PATH="${POETRY_HOME}/bin:${PATH}"

# Install Poetry only if not already installed
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s ${POETRY_HOME}/bin/poetry /usr/local/bin/poetry

USER ${USERNAME}
WORKDIR ${WORKSPACE_DIR}

# Set Poetry path explicitly so it is recognized immediately
ENV PATH="/home/ubuntu/.local/bin:$PATH"

# Use bash shell to ensure correct environment behavior
SHELL ["/bin/bash", "-c"]

# Ensure Poetry works immediately
RUN poetry --version && \
    poetry config virtualenvs.create true && \
    poetry config virtualenvs.in-project true

# Fix Poetry cache permissions if needed
RUN if [ -d "/home/ubuntu/.cache/pypoetry" ] && [ "$(stat -c '%U' /home/ubuntu/.cache/pypoetry)" != "ubuntu" ]; then \
        chown -R ubuntu:ubuntu /home/ubuntu/.cache/pypoetry; \
    fi
    
# Install Python packages as user
COPY --chown=${USERNAME}:${USERNAME} pyproject.toml poetry.lock ./
RUN poetry install --no-root

# Copy with correct ownership
COPY --chown=${USERNAME}:${USERNAME} . .

# Create .env file and populate it with default values
RUN touch /home/ubuntu/.env && \
    echo "Creating .env file with default values..." && \
    echo "PROJECT_UTILS_DIR=/home/ubuntu/utils" >> /home/ubuntu/.env && \
    echo "PROJECT_RESULTS_DIR=/home/ubuntu/results" >> /home/ubuntu/.env && \
    echo "PROJECT_DATA_DIR=/home/ubuntu/data" >> /home/ubuntu/.env && \
    echo "PROJECT_REFERENCES_DIR=/home/ubuntu/references" >> /home/ubuntu/.env && \
    echo "PROJECT_WORKING_DIR=/home/ubuntu/computational_genetic_genealogy" >> /home/ubuntu/.env && \
    echo "USER_HOME=/home/ubuntu" >> /home/ubuntu/.env

# Add /home/ubuntu/utils to PATH and ensure persistence
RUN echo 'export PATH=$PATH:/home/ubuntu/utils' >> /home/ubuntu/.bashrc
USER root
RUN echo 'export PATH=$PATH:/home/ubuntu/utils' >> /etc/profile

# Define the directory containing install scripts
ARG SCRIPTS_DIR=/home/ubuntu/scripts_env

# Define scripts to exclude
ENV EXCLUDE_SCRIPTS="setup_env.sh install_docker.sh mount_efs.sh install_yhaplo.sh"
RUN if [ -d "$SCRIPTS_DIR" ]; then \
        find "$SCRIPTS_DIR" -maxdepth 1 -type f -name "install_*.sh" | sort | while read script; do \
            script_name=$(basename "$script"); \
            if echo "$EXCLUDE_SCRIPTS" | grep -wq "$script_name"; then \
                echo "Skipping $script_name"; \
            else \
                echo "Running $script..."; \
                chmod +x "$script" && \
                sed -i 's|--prefix="$bcftools_dir"|--prefix="/usr/local"|g' "$script" && \
                sed -i 's|--prefix="$samtools_dir"|--prefix="/usr/local"|g' "$script" && \
                sed -i 's|--prefix="$htslib_dir"|--prefix="/usr/local"|g' "$script" && \
                bash "$script" || (echo "Error: $script failed" && exit 1); \
                echo "Completed $script_name successfully"; \
            fi; \
        done; \
        echo "All scripts processing complete."; \
    else \
        echo "No install scripts found, skipping script execution."; \
    fi && \
    echo "Starting ownership change..." && \
    chown -R ${USERNAME}:${USERNAME} /home/${USERNAME} && \
    echo "Build step complete."

# Stay as user
USER ${USERNAME}

CMD echo "===============================================" && \
echo "✅ Setup completed!" && \
echo "Your environment has been configured with:" && \
echo "- Updated system packages" && \
echo "- ~/.local/bin added to PATH" && \
echo "- System dependencies installed" && \
echo "- Poetry installed and configured" && \
echo "- Project dependencies installed" && \
echo "- Python kernel installed for Jupyter Notebooks" && \
echo "===============================================" && \
echo "" && \
echo "🚀 Your development container is ready!" && \
echo "" && \
echo "📢 To connect VS Code to this running container:" && \
echo "1️⃣ Open VS Code." && \
echo "2️⃣ Install the 'Remote - Containers' extension (if not already installed)." && \
echo "3️⃣ Open the Command Palette (Ctrl+Shift+P on Windows/Linux or Cmd+Shift+P on macOS, or via the menu: View > Command Palette)" && \
echo "   and select 'Remote-Containers: Attach to Running Container'." && \
echo "4️⃣ Choose this container from the list and start coding!" && \
echo "" && \
echo "💡 Note: If you wish to run a new container instance, you must first stop the current container." && \
echo "   To stop the container, type 'exit' or press Ctrl+D. This halts the container while preserving it" && \
echo "   for later reattachment." && \
echo "" && \
echo "💡 To resume your previous session, first locate your container's ID or name by running:" && \
echo "   docker ps -a" && \
echo "   Then, restart and attach to the container using:" && \
echo "   docker start -ai <container_id_or_name>" && \
echo "   (Data in mounted volumes persists between runs.)" && \
echo "" && \
echo "📂 This container leverages Docker volumes to persist your work (e.g., data, references, and results)" && \
echo "    on your local machine. Using volumes ensures that your data remains intact even if" && \
echo "    the container is stopped or removed, allowing you to continue your work seamlessly." && \
echo "    To mount local directories, run:" && \
echo "" && \
echo "   docker run -it \\" && \
echo "   -v \$(pwd)/references:/home/ubuntu/data \\" && \
echo "   -v \$(pwd)/references:/home/ubuntu/references \\" && \
echo "   -v \$(pwd)/results:/home/ubuntu/results \\" && \
echo "   lakishadavid/cgg_image:latest" && \
echo "" && \
echo "   (Replace \$(pwd)/results and \$(pwd)/references with your actual local paths)" && \
exec bash