# Computational Genetic Genealogy Analysis Environment

This repository provides the necessary code and instructions to set up a complete development environment for computational genetic genealogy analysis on Ubuntu 24.04. You can choose between setting up the environment directly on your local Ubuntu system (or WSL2) or using a pre-built Docker container.

## Setup Options

1.  **Ubuntu 24.04 Local Setup (Recommended for understanding the components):** Follow the steps below to configure your own Ubuntu 24.04 system. This aims to replicate the functionality of the analysis environment defined in the project's Docker configuration.
2.  **Docker Setup (Recommended for consistency and ease of use):** Use the provided Docker image (`lakishadavid/cgg_image:latest`) for a pre-configured, isolated environment (based on Ubuntu 24.04, Python 3.12, source-built samtools/bcftools, etc.).

## Ubuntu 24.04 Local Setup

> **Note:** This setup requires **Ubuntu 24.04**. If you're using WSL2 with an older Ubuntu version, please see the "Upgrading Ubuntu in WSL2" section below before proceeding.

> **IMPORTANT:** This manual setup places the `.env` file in your **home directory** (`~/.env`), not in the project directory. This matches the Docker setup. Do **NOT** run the `scripts_env/directory_setup.py` script, as it would create the `.env` file in the wrong location.

Follow these steps in your **Ubuntu terminal**:

1.  **Clone the Repository:**

    ```bash
    # Clone into your home directory or another location of your choice
    git clone https://github.com/lakishadavid/computational_genetic_genealogy.git
    # Example: This creates ~/computational_genetic_genealogy if run in home dir
    # Define the path to the cloned repository for subsequent steps
    PROJECT_BASE_DIR="${HOME}/computational_genetic_genealogy" # <<< ADJUST THIS if you cloned elsewhere
    ```

2.  **Create Project Directory Structure:**
    Manually create the standard subdirectories within the cloned repository.

    ```bash
    # Ensure the base directory variable is set correctly from step 1
    echo "Using project base directory: ${PROJECT_BASE_DIR}"

    mkdir -p "${PROJECT_BASE_DIR}/data" \
             "${PROJECT_BASE_DIR}/results" \
             "${PROJECT_BASE_DIR}/references" \
             "${PROJECT_BASE_DIR}/utils"

    echo "✅ Created project subdirectories in ${PROJECT_BASE_DIR}"
    ```

3.  **Create the Environment Configuration File (`~/.env`):**

    ```bash
    # Ensure the base directory variable is set correctly from step 1
    # (Assuming PROJECT_BASE_DIR was set like: PROJECT_BASE_DIR="${HOME}/computational_genetic_genealogy")

    echo "Using project base directory for paths: ${PROJECT_BASE_DIR}"

    # Create or overwrite the .env file in your home directory
    cat > ~/.env << EOF
    PROJECT_WORKING_DIR=${PROJECT_BASE_DIR}
    PROJECT_DATA_DIR=${PROJECT_BASE_DIR}/data
    PROJECT_REFERENCES_DIR=${PROJECT_BASE_DIR}/references
    PROJECT_RESULTS_DIR=${PROJECT_BASE_DIR}/results
    PROJECT_UTILS_DIR=${PROJECT_BASE_DIR}/utils
    USER_HOME=${HOME}
    EOF

    echo "✅ Created ~/.env file in your home directory (~/.env)."

    # Verify the contents (optional, run this command separately after the block above)
    # cat ~/.env
    ```

4.  **Install System Packages:**
    Install required system dependencies using `apt`. Note that `bcftools`, `samtools`, and `tabix` are **not** installed here; they will be built from source later.

    ```bash
    # Update package lists and add necessary repositories
    sudo apt update && sudo apt upgrade -y && sudo apt install -y software-properties-common
    sudo apt-add-repository -y universe && sudo apt-add-repository -y multiverse && sudo apt-add-repository -y ppa:deadsnakes/ppa
    sudo apt update -y

    # Install main dependencies (excluding samtools/bcftools/tabix via apt)
    # Added openjdk-21-jdk, libncurses-dev
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
        libatlas-base-dev

    # Clean up
    sudo apt-get clean && sudo rm -rf /var/lib/apt/lists/*

    # Configure Java Environment
    JAVA_HOME_PATH=$(update-alternatives --list java | grep 'java-21-openjdk' | sed 's/\/bin\/java//')
    if [ -n "$JAVA_HOME_PATH" ] && ! grep -q "export JAVA_HOME=" ~/.bashrc; then
      echo "export JAVA_HOME=$JAVA_HOME_PATH" >> ~/.bashrc
      echo "export PATH=\$JAVA_HOME/bin:\$PATH" >> ~/.bashrc
      echo "✅ Configured JAVA_HOME in ~/.bashrc."
    fi
    ```

5.  **Build Samtools, BCFtools, HTSlib (v1.18) from Source:**
    This ensures you have the specific versions used in the reference environment.

    ```bash
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
    cd ~ # Go back home
    rm -rf "$TEMP_BUILD_DIR"

    # Update library cache
    sudo ldconfig

    echo "✅ Samtools, BCFtools, HTSlib v${SAMTOOLS_VERSION} built and installed."
    ```

    _Verify installation:_

    ```bash
    bcftools --version | head -n 1
    samtools --version | head -n 1
    tabix --version | head -n 1
    ```

6.  **Install Poetry (Python Dependency Manager):**

    ```bash
    pipx ensurepath
    pipx install poetry
    # Add pipx path to current and future shells
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc # Apply for current session
    ```

    _Verify installation:_ `poetry --version`

7.  **Install Python Project Dependencies:**
    Navigate into the _cloned_ repository directory (`PROJECT_BASE_DIR`) and use Poetry.

    ```bash
    # Ensure the base directory variable is set correctly from step 1
    echo "Changing to project base directory: ${PROJECT_BASE_DIR}"
    cd "$PROJECT_BASE_DIR"

    poetry config virtualenvs.in-project true
    poetry install --no-root
    ```

    This creates a `.venv` directory inside the project folder.

8.  **Update PATH for Utility Scripts:**
    Manually add the project's `utils` directory to your `~/.bashrc` so tools installed there can be found easily.

    ```bash
    # Ensure the base directory variable is set correctly from step 1
    UTILS_DIR="${PROJECT_BASE_DIR}/utils"
    EXPORT_LINE="export PATH=\"\$PATH:${UTILS_DIR}\"" # Add utils dir to PATH

    # Check if the line already exists
    if ! grep -qF "$EXPORT_LINE" ~/.bashrc; then
        echo -e "\n# Add project utils directory to PATH\n${EXPORT_LINE}" >> ~/.bashrc
        echo "✅ Added utils directory (${UTILS_DIR}) to PATH in ~/.bashrc."
    else
        echo "✅ Utils directory already in PATH in ~/.bashrc."
    fi
    # Apply changes to the current terminal session
    source ~/.bashrc
    ```

9.  **Install JAR Files (Beagle, HapIBD, RefinedIBD):**

    ```bash
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
    ```

10. **Install LiftOver:**

    ```bash
    # Download LiftOver binary and make executable
    wget -nv http://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/liftOver -O "${UTILS_DIR}/liftOver"
    chmod +x "${UTILS_DIR}/liftOver"

    # Download hg19->hg38 chain file
    wget -nv http://hgdownload.cse.ucsc.edu/goldenPath/hg19/liftOver/hg19ToHg38.over.chain.gz -P "${PROJECT_BASE_DIR}/references/"

    # Verify executable exists
    [ -x "${UTILS_DIR}/liftOver" ] && echo "✅ LiftOver installed successfully."
    ```

11. **Install BonsaiTree:**

    ```bash
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
    ```

12. **Install IBIS, Ped-Sim, RFMix2 (Source Build):**

    ```bash
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
    ```

13. **Install PLINK2 Binary:**

    ```bash
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
    ```

14. **Configure sudo for Notebook (Optional):**
    This step allows specific `sudo` commands (like `apt` or `rm`) to be run within notebook cells using `!sudo ...` without requiring a password. This can be convenient but modifies system configuration (`/etc/sudoers.d`). **Only run this if you understand the security implications and find it necessary.** You will need to copy and paste the command block into your Ubuntu terminal and enter your password there.

    ```bash
    # --- DO NOT RUN THIS DIRECTLY IN JUPYTER NOTEBOOK ---
    # --- COPY AND PASTE THE COMMANDS BELOW INTO YOUR UBUNTU TERMINAL WINDOW ---

    echo "$(whoami) ALL=(ALL) NOPASSWD: /usr/bin/apt-add-repository, /usr/bin/apt, /usr/bin/apt-get, /usr/bin/dpkg, /bin/rm" | sudo tee /etc/sudoers.d/$(whoami)-notebook
    sudo chmod 0440 /etc/sudoers.d/$(whoami)-notebook
    echo "Passwordless sudo configured for specific commands in /etc/sudoers.d/$(whoami)-notebook"

    # --- Then you can run commands like !sudo apt update -y in the notebook ---
    ```

15. **Final Steps: Running Lab0_Code_Environment.ipynb**

    After completing all the above setup steps, you should:

    1. Open VS Code:
       ```bash
       # Using the variable defined during setup:
       code "$PROJECT_BASE_DIR"
       # Or using the direct path:
       # code ~/computational_genetic_genealogy
       ```
    2. Install the recommended extensions if prompted (especially **Python** and **Jupyter** from Microsoft).
    3. Select the Python Interpreter: Open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`) > Type `Python: Select Interpreter` > Choose the interpreter associated with `./.venv` in your project folder (e.g., `Python 3.12 ('.venv': Poetry)`).
    4. Open the `instructions/Lab0_Code_Environment.ipynb` notebook located within your project folder.
    5. Follow the instructions **within the notebook** to:
       - Verify your environment setup
       - Install any remaining tools
       - Copy initial `class_data`
       - Optionally configure passwordless sudo for notebook commands

16. **Important Note on `scripts_env/directory_setup.py`:**
    This project includes a script `scripts_env/directory_setup.py` which can also configure directories and create a `.env` file. However, that script places the `.env` file _inside the project directory_ (`${PROJECT_BASE_DIR}/.env`), whereas the Docker environment uses `~/.env`. To ensure the local setup aligns closely with the Docker environment, these manual instructions use `~/.env` and **do not run** `scripts_env/directory_setup.py`.

## Project Directory Structure

The manual setup in steps 1-2 creates the following directory structure:

- `${PROJECT_BASE_DIR}/data`: For storing input data files
- `${PROJECT_BASE_DIR}/references`: For reference files and databases
- `${PROJECT_BASE_DIR}/results`: For analysis outputs and results
- `${PROJECT_BASE_DIR}/utils`: For installed tools and utility scripts

These directories are essential for organizing your work and match the structure used in the Docker setup. The initial `class_data` will be copied into the `data` directory when running Lab0_Code_Environment.ipynb.

Tip: Keep these directories organized as you work through the labs. When you generate results, save them to the `results` directory to easily find them later.

## Upgrading Ubuntu in WSL2

If you're using WSL2 with an older version of Ubuntu (e.g., 22.04), you'll need to upgrade to **Ubuntu 24.04**:

### Check Your Current Version

```bash
lsb_release -a
```

### Upgrading from Ubuntu 22.04 to 24.04

1. **Update your package lists and upgrade installed packages**:

   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install the update-manager-core package**:

   ```bash
   sudo apt install update-manager-core -y
   ```

3. **Run the release upgrade**:

   ```bash
   sudo do-release-upgrade -d
   ```

4. **Follow the prompts** during the upgrade process. The upgrade may take some time and will ask you questions along the way.

5. **Restart your WSL instance** after the upgrade completes:

   ```bash
   exec sudo /sbin/reboot
   ```

   Or from Windows PowerShell:

   ```powershell
   wsl --shutdown
   ```

   Then restart Ubuntu from your Start menu.

6. **Verify your new Ubuntu version**:
   ```bash
   lsb_release -a
   ```

### Alternative: Install Fresh Ubuntu 24.04 in WSL

If upgrading causes issues, you can install a fresh copy of Ubuntu 24.04:

1. **From Windows PowerShell (as administrator)**:

   ```powershell
   # List your WSL distributions
   wsl --list

   # Optionally backup your data first
   # Copy your important files to Windows

   # Unregister your current Ubuntu (this will remove it)
   wsl --unregister Ubuntu

   # Install Ubuntu 24.04
   wsl --install -d Ubuntu-24.04
   ```

2. **Set up the new Ubuntu** by following the prompts to create a username and password.

## Docker Setup

This method uses the pre-built Docker image `lakishadavid/cgg_image:latest`, which already contains the complete environment (based on Ubuntu 24.04, Python 3.12, source-built samtools/bcftools, etc.).

1.  **Install Docker:** Ensure you have Docker Desktop (Windows/Mac) or Docker Engine (Linux) installed. See [Docker's official documentation](https://docs.docker.com/get-docker/).

2.  **Pull the Docker Image:**

    ```bash
    docker pull lakishadavid/cgg_image:latest
    ```

3.  **Run the Container:**
    Launch a terminal window and run the container interactively. This command also maps local directories for data persistence using volumes. **Crucially, map your local cloned repository and data folders to the corresponding paths inside the container.**

    ```bash
    # --- METHOD 1: If your terminal is currently INSIDE your local cloned repo folder ---
    # Assumes you have 'data', 'references', 'results' subdirs in your current folder. Create them if needed: mkdir -p data references results
    docker run -it --rm \
       -v "$(pwd)/data:/home/ubuntu/computational_genetic_genealogy/data" \
       -v "$(pwd)/references:/home/ubuntu/computational_genetic_genealogy/references" \
       -v "$(pwd)/results:/home/ubuntu/computational_genetic_genealogy/results" \
       -v "$(pwd):/home/ubuntu/computational_genetic_genealogy" \
       lakishadavid/cgg_image:latest bash

    # --- METHOD 2: Using ABSOLUTE paths for local directories ---
    # Replace /path/to/your/local/computational_genetic_genealogy with the actual path
    # Replace /path/to/your/local/data etc. if they are separate from the repo clone
    # Example:
    # LOCAL_REPO_PATH="/home/myuser/projects/computational_genetic_genealogy"
    # LOCAL_DATA_PATH="${LOCAL_REPO_PATH}/data" # Or separate path like /mnt/mydata/cgg_data
    # LOCAL_REFS_PATH="${LOCAL_REPO_PATH}/references" # Or separate path
    # LOCAL_RESULTS_PATH="${LOCAL_REPO_PATH}/results" # Or separate path
    #
    # docker run -it --rm \
    #    -v "${LOCAL_DATA_PATH}:/home/ubuntu/computational_genetic_genealogy/data" \
    #    -v "${LOCAL_REFS_PATH}:/home/ubuntu/computational_genetic_genealogy/references" \
    #    -v "${LOCAL_RESULTS_PATH}:/home/ubuntu/computational_genetic_genealogy/results" \
    #    -v "${LOCAL_REPO_PATH}:/home/ubuntu/computational_genetic_genealogy" \
    #    lakishadavid/cgg_image:latest bash
    ```

    - `-it`: Runs interactively.
    - `--rm`: Removes container on exit.
    - `-v local_path:container_path`: Maps host directory `local_path` to container directory `container_path`.
      - **Host Paths:** Use `$(pwd)` for current directory or provide full absolute paths.
      - **Container Paths:** MUST be `/home/ubuntu/computational_genetic_genealogy` and its subdirectories as shown. This is the structure _inside_ the image.
    - `lakishadavid/cgg_image:latest`: The image name.
    - `bash`: Starts a shell inside the container.

    You are now inside the container at `/home/ubuntu/computational_genetic_genealogy`. All tools are pre-installed.

## Using VS Code

Visual Studio Code provides a great experience for working with this project, both locally and with Docker.

### For Ubuntu Local Setup

1.  Open the project folder in VS Code:
    ```bash
    # Using the variable defined during setup:
    code "$PROJECT_BASE_DIR"
    # Or using the direct path:
    # code ~/computational_genetic_genealogy
    ```
2.  Install the recommended extensions if prompted (especially **Python** and **Jupyter** from Microsoft).
3.  Select the Python Interpreter: Open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`) > Type `Python: Select Interpreter` > Choose the interpreter associated with `./.venv` in your project folder (e.g., `Python 3.12 ('.venv': Poetry)`).

### For Docker Setup

1.  Install the **Dev Containers** extension in VS Code (published by Microsoft).
2.  Run the Docker container using the `docker run ...` command from the "Docker Setup" section above. Make sure the container is running.
3.  In VS Code, open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`).
4.  Select "Dev Containers: Attach to Running Container..." and choose the `lakishadavid/cgg_image:latest` container from the list.
5.  A new VS Code window will open, connected _inside_ the container.
6.  Open the project folder _within the container_: `File > Open Folder... > /home/ubuntu/computational_genetic_genealogy`.
7.  Install any recommended extensions (like Python, Jupyter) _inside the container_ if prompted.
8.  VS Code should automatically detect and select the Python interpreter located at `/home/ubuntu/computational_genetic_genealogy/.venv/bin/python`. If not, select it manually using the Command Palette (`Python: Select Interpreter`).

## Stopping the Container (Docker Only)

To stop and exit the interactive container session started with `docker run -it ...`:

1.  Inside the container's terminal, type `exit` and press Enter.
2.  Alternatively, press `Ctrl+D`.

If you started the container with the `--rm` flag (as recommended in the example `docker run` commands), the container will be automatically removed upon exit. Its state is not saved, but the data in your mapped volumes remains on your host machine.

If you started the container _without_ `--rm`, it will only be stopped. You can see stopped containers with `docker ps -a`. You can restart a stopped container using `docker start <container_id_or_name>` and re-attach to it using `docker attach <container_id_or_name>` (or `docker start -ai <container_id_or_name>`).

## Troubleshooting

Common issues encountered during local setup:

- **Command Not Found (poetry, bcftools, etc.):**
  - Ensure `$HOME/.local/bin` (for Poetry) and `${PROJECT_BASE_DIR}/utils` (for tools installed by Lab0) are correctly added to your `PATH` in `~/.bashrc`.
  - Run `source ~/.bashrc` in your terminal or open a new terminal window after modifying `.bashrc`.
  - Verify installation: `which poetry`, `which bcftools`, `which plink2`. Check the versions: `poetry --version`, `bcftools --version`.
- **Errors Building Samtools/BCFtools:**
  - Ensure all build dependencies listed in the `apt install` command (like `build-essential`, `zlib1g-dev`, `libncurses-dev`, `libbz2-dev`, `liblzma-dev`) were installed successfully.
  - Make sure you run `sudo make install` and `sudo ldconfig` after building.
- **Permission Errors:**
  - Use `sudo` for system-wide commands (`apt`, `make install`, `ldconfig`).
  - Ensure your user owns the project directory (`PROJECT_BASE_DIR`) and its contents. If needed: `sudo chown -R $(whoami):$(whoami) "$PROJECT_BASE_DIR"`.
- **`~/.env` File Issues:**
  - Verify the file exists in your home directory (`ls -a ~ | grep .env`).
  - Verify its contents contain the correct **absolute paths** (`cat ~/.env`).
  - Ensure the `Lab0_Code_Environment.ipynb` notebook has permissions to read it.
- **Errors During Tool Installation in Lab0 Notebook:**
  - Carefully read the error output in the specific notebook cell that failed.
  - Ensure the environment variables (`PROJECT_UTILS_DIR`, etc.) loaded correctly in the initial code cell by checking the log output. If not, verify `~/.env`.
  - Make sure prerequisite steps from this README were completed successfully.
- **Java Issues:**
  - Verify OpenJDK 21 is installed: `apt list --installed | grep openjdk-21-jdk`.
  - Verify `JAVA_HOME` is set in your active shell environment: `echo $JAVA_HOME`. Check `~/.bashrc` if it's not set.
  - Verify `java` command works: `java -version`.
- **PDF Conversion Fails:**
  - Ensure `texlive-*` packages were installed via `apt`.
  - Try running the `poetry run jupyter nbconvert ...` command directly in the terminal for more detailed error messages.

## License

This project is licensed under the MIT License.
