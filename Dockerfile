###############################################################################
# Base Configuration
###############################################################################
FROM ubuntu:22.04

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

# Create user with specified UID/GID
RUN groupadd --gid ${USER_GID} ${USERNAME} && \
    useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME} && \
    chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}

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

# Set up script permissions
RUN chmod -R +x ${WORKSPACE_DIR}/computational_genetic_genealogy/scripts_env/

# Run installations
WORKDIR ${WORKSPACE_DIR}/computational_genetic_genealogy
RUN bash ${WORKSPACE_DIR}/computational_genetic_genealogy/scripts_env/system/packages.sh && \
    bash ${WORKSPACE_DIR}/computational_genetic_genealogy/scripts_env/user/run_install_scripts.sh

USER ${USERNAME}
WORKDIR ${WORKSPACE_DIR}/computational_genetic_genealogy
RUN bash ${WORKSPACE_DIR}/computational_genetic_genealogy/scripts_env/user/path_setup.sh && \
    bash ${WORKSPACE_DIR}/computational_genetic_genealogy/scripts_env/user/poetry_setup.sh

###############################################################################
# Volume Configuration
###############################################################################
VOLUME ["${WORKSPACE_DIR}/data", "${WORKSPACE_DIR}/references", "${WORKSPACE_DIR}/results"]

###############################################################################
# Container Startup
###############################################################################
USER ${USERNAME}
WORKDIR ${WORKSPACE_DIR}/computational_genetic_genealogy

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
echo "   -v \$(pwd)/data:/home/ubuntu/data \\" && \
echo "   -v \$(pwd)/references:/home/ubuntu/references \\" && \
echo "   -v \$(pwd)/results:/home/ubuntu/results \\" && \
echo "   lakishadavid/cgg_image:latest" && \
echo "" && \
echo "   (Replace \$(pwd)/results and \$(pwd)/references with your actual local paths)" && \
exec bash