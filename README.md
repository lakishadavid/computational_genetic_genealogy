# cgg_image

cgg_image is an Ubuntu 24.04 setup and Docker image code base that creates a complete development environment. Choose your preferred setup method below.

## Ubuntu Setup (Non-Docker)

> **Note:** This setup requires Ubuntu 24.04. If you're using WSL2 with an older Ubuntu version, please see the "Upgrading Ubuntu in WSL2" section below before proceeding.

In your Ubuntu terminal window on your computer, enter the following commands:

```bash
git clone https://github.com/lakishadavid/computational_genetic_genealogy.git
```

You can now open VS Code and begin the labs. The labs are in the instructions directory. Start with Lab0_Code_Environment.ipynb to finish setting up your code environment. After this, you won't need to rerun Lab0_Code_Environment.ipynb for any lab, even if you restart your computer.

To launch VS Code, enter the following in your terminal window:

```bash
cd computational_genetic_genealogy
code .
```

Run Lab0_Code_Environment.ipynb in the instructions directory.

## Upgrading Ubuntu in WSL2

If you're using WSL2 with an older version of Ubuntu, you'll need to upgrade to Ubuntu 24.04:

### Check Your Current Version

```bash
lsb_release -a
```

### Upgrade from Ubuntu 22.04 to 24.04

1. Update and upgrade packages:

   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. Install update manager:

   ```bash
   sudo apt install update-manager-core -y
   ```

3. Start the upgrade:

   ```bash
   sudo do-release-upgrade -d
   ```

4. Follow the prompts and restart WSL after completion:
   ```powershell
   # In Windows PowerShell
   wsl --shutdown
   ```

### Alternative: Fresh Installation

If upgrading causes issues, you can install a fresh Ubuntu 24.04:

1. In Windows PowerShell (as administrator):
   ```powershell
   # Backup important data first!
   wsl --unregister Ubuntu
   wsl --install -d Ubuntu-24.04
   ```

After upgrading or installing Ubuntu 24.04, proceed with the setup instructions.

## Docker Setup

### Run the Container

Launch a terminal window and run:

```bash
docker pull lakishadavid/cgg_image:latest
docker run -it lakishadavid/cgg_image:latest bash
```

You can then open and connect VS Code to the container, and begin the tutorials or run the scripts in the container terminal window.

## Using VS Code

### For Ubuntu Setup

1. Open VS Code
2. Install the Python extension
3. Select Python Interpreter:
   - Windows/Linux: Ctrl+Shift+P | macOS: Cmd+Shift+P | via View > Command Palette
   - Select "Python: Select Interpreter"
   - Choose the environment created by setup script

### For Docker Setup

1. Open VS Code
2. Install the "Remote - Containers" extension if you haven't already
3. Open the Command Palette:
   - Windows/Linux: Ctrl+Shift+P | macOS: Cmd+Shift+P | via View > Command Palette
4. Select Remote-Containers: Attach to Running Container and choose the container
5. Install the Python extension
6. Select Python Interpreter:
   - Windows/Linux: Ctrl+Shift+P | macOS: Cmd+Shift+P | via View > Command Palette
   - Select "Python: Select Interpreter"
   - Choose the environment created by setup script

## Data Management

### For Ubuntu Setup

The setup script configures your directories and paths in the .env file:

- data/
- references/
- results/

If your data directory is something other than ~/computational_genetic_genealogy/data, the script will copy the project data into your specified data directory.

### For Docker Setup: Data Persistence with Volumes

Use Docker volumes to ensure your work (data, references, and results) is preserved even if the container stops or is removed.

To mount local directories, run:

```bash
docker run -it \
   -v $(pwd)/data:/home/ubuntu/computational_genetic_genealogy/data \
   -v $(pwd)/references:/home/ubuntu/computational_genetic_genealogy/references \
   -v $(pwd)/results:/home/ubuntu/computational_genetic_genealogy/results \
   lakishadavid/cgg_image:latest
```

(Replace $(pwd)/data, $(pwd)/references, and $(pwd)/results with your actual local paths.)

The container runs Ubuntu 24.04 with the working directory at `/home/ubuntu/computational_genetic_genealogy`.

For example, if your home directory was mynewsystem, you created a subdirectory in mynewsystem called ANTHprojects, and you created multiple subdirectories in ANTHprojects called genetic_data, genetic_refs, and genetic_results, you would enter the following to map your directories to the container directories:

```bash
docker run -it \
   -v /home/mynewsystem/ANTHprojects/genetic_data:/home/ubuntu/computational_genetic_genealogy/data \
   -v /home/mynewsystem/ANTHprojects/genetic_refs:/home/ubuntu/computational_genetic_genealogy/references \
   -v /home/mynewsystem/ANTHprojects/genetic_results:/home/ubuntu/computational_genetic_genealogy/results \
   lakishadavid/cgg_image:latest
```

Keep the paths on the right as they are (e.g., /home/ubuntu/...). These are the file paths within the container. Also, keep the image name the same (e.g., lakishadavid/cgg_image:latest). This is the actual name of the image.

## Stopping and Resuming the Container (Docker Only)

### Stopping:

To stop the container, simply type exit or press Ctrl+D. The container stops but remains available for reattachment (unless it was started with the --rm flag).

### Resuming:

Find your container's ID or name with:

```bash
docker ps -a
```

Restart and attach to the container with:

```bash
docker start -ai <container_id_or_name>
```

Data stored in mounted volumes persists between container sessions.

## Troubleshooting

### R Package Installation Issues

If you encounter issues with R packages or Python's rpy2 integration, you may need additional system dependencies:

```bash
sudo apt install -y libblas-dev liblapack-dev libatlas-base-dev
```

This is typically needed for R's numerical computing capabilities and Python-R integration through rpy2.

## License

This project is licensed under the MIT License.
