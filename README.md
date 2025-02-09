# cgg_image

**cgg_image** is a Docker image or Ubuntu setup that creates a complete development environment. Choose your preferred setup method below.

## Ubuntu Setup (Non-Docker)

To set up directly on Ubuntu:
```
cd computational_genetic_genealogy
bash scripts_env/setup_env.sh
```
The setup script:
- Updates system packages
- Adds `~/.local/bin` to PATH
- Installs system dependencies
- Installs and configures Python kernel for Jupyter Notebooks in VSCode
- Installs Poetry and Python packages
- Sets up various utilities
- Creates an `.env` file with your file paths
- Adds `utils_directory` to PATH
- Copies data directory if needed

## Docker Setup 

### Run the Container

To launch an interactive session, run:
```
docker run -it lakishadavid/cgg_image:latest
```
When started, the container displays setup confirmation and useful instructions.

## Using VS Code

### For Ubuntu Setup
1. **Open VS Code**
2. **Install the Python extension** 
3. **Select Python Interpreter**:
   - Windows/Linux: `Ctrl+Shift+P`
   - macOS: `Cmd+Shift+P`
   - Select "Python: Select Interpreter"
   - Choose the environment created by setup script

### For Docker Setup
1. **Open VS Code**
2. **Install the "Remote - Containers" extension** if you haven't already
3. **Open the Command Palette**:
   - Windows/Linux: `Ctrl+Shift+P`
   - macOS: `Cmd+Shift+P`
   - Alternatively, via **View > Command Palette**
4. **Select** `Remote-Containers: Attach to Running Container` and choose the container

## Data Management

### For Ubuntu Setup
The setup script configures your directories and paths in the `.env` file:
- `data/`
- `references/`
- `results/`

### For Docker Setup: Data Persistence with Volumes

This image leverages Docker volumes to ensure your work (data, references, and results) is preserved even if the container stops or is removed.

To mount local directories, run:
```
docker run -it 
-v $(pwd)/data:/home/ubuntu/data 
-v $(pwd)/references:/home/ubuntu/references 
-v $(pwd)/results:/home/ubuntu/results 
lakishadavid/cgg_image:latest
```
*(Replace `$(pwd)/data`, `$(pwd)/references`, and `$(pwd)/results` with your actual local paths.)*

For example, if your home directory was `mynewsystem`, you created a subdirectory there called `ANTHprojects`,
and you created multiple subdirectories there called `genetic_data`, `genetic_refs`, and `genetic_results`, 
you would enter the following:

```
docker run -it 
-v /home/mynewsystem/ANTHprojects/genetic_data:/home/ubuntu/data 
-v /home/mynewsystem/ANTHprojects/genetic_refs:/home/ubuntu/references 
-v /home/mynewsystem/ANTHprojects/genetic_results:/home/ubuntu/results 
lakishadavid/cgg_image:latest
```

Keep the paths on the right as they are (e.g., `/home/ubuntu/...`). These are the file paths within the container.
Also, keep the image name the same (e.g., `lakishadavid/cgg_image:latest`). This is the actual name of the image.

## Stopping and Resuming the Container (Docker Only)

- **Stopping:**  
  To stop the container, simply type `exit` or press `Ctrl+D`. The container stops but remains available for reattachment (unless it was started with the `--rm` flag).

- **Resuming:**  
  1. Find your container's ID or name with:
  ```
  docker ps -a
  ```
  2. Restart and attach to the container with:
  ```
  docker start -ai <container_id_or_name>
  ```
  Data stored in mounted volumes persists between container sessions.

## License

This project is licensed under the MIT License.
