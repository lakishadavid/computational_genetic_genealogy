# Computational Genetic Genealogy Analysis Environment

This repository provides the necessary code and instructions to set up a complete development environment for computational genetic genealogy analysis on Ubuntu 24.04. You can choose between setting up the environment directly on your local Ubuntu system (or WSL2) or using a pre-built Docker container.

## Setup Options

1.  **Ubuntu 24.04 Local Setup (Recommended for understanding the components):** Follow the steps below to configure your own Ubuntu 24.04 system. This aims to replicate the functionality of the analysis environment defined in the project's Docker configuration.
2.  **Docker Setup (Recommended for consistency and ease of use):** Use the provided Docker image (`lakishadavid/cgg_image:latest`) for a pre-configured, isolated environment (based on Ubuntu 24.04, Python 3.12, source-built samtools/bcftools, etc.).

## Ubuntu 24.04 Local Setup

> **Note:** This setup requires **Ubuntu 24.04**. If you're using WSL2 with an older Ubuntu version, please see the "Upgrading Ubuntu in WSL2" section below before proceeding.

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
    Create a `.env` file in your **home directory** (`~`) to store essential absolute paths. This location aligns with the Docker environment configuration.
    ```bash # Ensure the base directory variable is set correctly from step 1
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
            ```
            *Verify the contents:* `cat ~/.env`

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

    _Verify installation:_ `bcftools --version && samtools --version`

6.  **Install Poetry (Python Dependency Manager):**

    ````bash
    pipx ensurepath
    pipx install poetry
    # Add pipx path to current and future shells
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc # Apply for current session
    ```    *Verify installation:* `poetry --version`

    ````

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

9.  **Final Tool Installation & Setup (Using Jupyter Notebook):**
    The remaining specific bioinformatics tools (Beagle, BonsaiTree, PLINK2, etc.) and initial data copying are handled via the **`Lab0_Code_Environment.ipynb`** Jupyter Notebook.

    - Open the project in VS Code:
      ```bash
      # Ensure the base directory variable is set correctly from step 1
      code "$PROJECT_BASE_DIR"
      ```
    - Ensure you have the Python and Jupyter extensions installed in VS Code.
    - Open the `instructions/Lab0_Code_Environment.ipynb` notebook located within your project folder.
    - Follow the instructions **within the notebook** to:
      - Select the correct Python interpreter (pointing to the `.venv` within the project folder).
      - Load environment variables from `~/.env`.
      - Verify the initial setup (Java, Samtools, R version checks).
      - Install the remaining tools (JARs, BonsaiTree, LiftOver, RFMix2, IBIS, PedSim, PLINK2) into the `${PROJECT_BASE_DIR}/utils` directory.
      - Copy initial `class_data`.
      - Optionally configure passwordless sudo for notebook commands.

10. **Important Note on `scripts_env/directory_setup.py`:**
    This project includes a script `scripts_env/directory_setup.py` which can also configure directories and create a `.env` file. However, that script places the `.env` file _inside the project directory_ (`${PROJECT_BASE_DIR}/.env`), whereas the Docker environment uses `~/.env`. To ensure the local setup aligns closely with the Docker environment, these manual instructions use `~/.env` and **do not run** `scripts_env/directory_setup.py`.

## Upgrading Ubuntu in WSL2

_(Keep this section as previously provided)_

## Docker Setup

_(Keep this section as previously provided, ensuring volume paths align with `/home/ubuntu/computational_genetic_genealogy/...`)_

## Using VS Code

_(Keep this section as previously provided)_

## Data Management

_(Keep this section, referencing `${PROJECT_BASE_DIR}/data` etc. for local and the Docker paths for container)_

## Stopping the Container (Docker Only)

_(Keep this section)_

## Troubleshooting

_(Keep this section, ensure it mentions checking `~/.env` and PATH includes `~/.local/bin` and the project's `utils` dir)_

## License

This project is licensed under the MIT License.
