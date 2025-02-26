# cgg_image

**cgg_image** is an Ubuntu setup and Docker image code base that creates a complete development environment. Choose your preferred setup method below.

## Ubuntu Setup (Non-Docker)

To set up directly on Ubuntu:

In your Ubuntu terminal window, enter the following commands:
```
git clone https://github.com/lakishadavid/computational_genetic_genealogy.git
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip -y
pip3 --version
```
This should output something like:
```
pip 24.0 from /usr/lib/python3/dist-packages/pip (python 3.12)
```
Continue to enter commands in your Ubuntu terminal window:
```
sudo apt install pipx -y
pipx ensurepath
```
✅ Open a New Terminal Window
Since `pipx` modified your PATH, close the current terminal and open a new one to apply the changes.

✅ Verify pipx Works.

Enter:
```
pipx --version
```
Your output should be something like `1.4.3`, indicating the `pipx` version number.

Now, use `pipx` to install `poetry`.
```
pipx install poetry
```
The output should let you know what `poetry` version was installed, but you can check by running `poetry --version`.

Congure `poetry` by entering:
```
poetry config virtualenvs.in-project true
```

Now, navigate into the course directory `computational_genetic_genealogy` and install the needed Python packages by using the following commands:
```
cd computational_genetic_genealogy
poetry install --no-root
```
You can now open VS Code and begin the labs. The labs are in the `instructions` directory. Start with `Lab0_Code_Environment.ipynb` to finish setting up your code environment. After this, you won't need to rerun `Lab0_Code_Environment.ipynb` for any lab, even if you restart your computer. To launch VS Code, enter the following in your terminal window:
```
code .
```

Run `Lab0_Code_Environment.ipynb` in the `instructions` directory.

## Docker Setup 

### Run the Container

Launch a terminal window and run:
```
docker pull lakishadavid/cgg_image:latest
docker run -it lakishadavid/cgg_image:latest bash
```
You can then open and connect VS Code to the container, and begin the tutorials or run the scripts in the container terminal window.

## Using VS Code

### For Ubuntu Setup
1. **Open VS Code**
2. **Install the Python extension** 
3. **Select Python Interpreter**:
   - Windows/Linux: `Ctrl+Shift+P` | macOS: `Cmd+Shift+P` | via **View > Command Palette**
   - Select "Python: Select Interpreter"
   - Choose the environment created by setup script

### For Docker Setup
1. **Open VS Code**
2. **Install the "Remote - Containers" extension** if you haven't already
3. **Open the Command Palette**:
   - Windows/Linux: `Ctrl+Shift+P` | macOS: `Cmd+Shift+P` | via **View > Command Palette**
4. **Select** `Remote-Containers: Attach to Running Container` and choose the container
5. **Install the Python extension** 
6. **Select Python Interpreter**:
   - Windows/Linux: `Ctrl+Shift+P` | macOS: `Cmd+Shift+P` | via **View > Command Palette**
   - Select "Python: Select Interpreter"
   - Choose the environment created by setup script

## Data Management

### For Ubuntu Setup
The setup script configures your directories and paths in the `.env` file:
- `data/`
- `references/`
- `results/`

If you your data directory is something other than ~/computational_genetic_genealogy/data, the script will copy
the project data into your specified data directory.

### For Docker Setup: Data Persistence with Volumes

Use Docker volumes to ensure your work (data, references, and results) is preserved even if the container stops or is removed.

To mount local directories, run:
```
docker run -it \
   -v $(pwd)/data:/home/ubuntu/computational_genetic_genealogy/data \
   -v $(pwd)/references:/home/ubuntu/computational_genetic_genealogy/references \
   -v $(pwd)/results:/home/ubuntu/computational_genetic_genealogy/results \
   lakishadavid/cgg_image:latest
```
*(Replace `$(pwd)/data`, `$(pwd)/references`, and `$(pwd)/results` with your actual local paths.)*

For example, if your home directory was `mynewsystem`, you created a subdirectory in `mynewsystem` called `ANTHprojects`,
and you created multiple subdirectories in `ANTHprojects` called `genetic_data`, `genetic_refs`, and `genetic_results`, 
you would enter the following to map your directories to the container directories:

```
docker run -it \
   -v /home/mynewsystem/ANTHprojects/genetic_data:/home/ubuntu/computational_genetic_genealogy/data \
   -v /home/mynewsystem/ANTHprojects/genetic_refs:/home/ubuntu/computational_genetic_genealogy/references \
   -v /home/mynewsystem/ANTHprojects/genetic_results:/home/ubuntu/computational_genetic_genealogy/results \
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
