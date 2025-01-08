import os
import subprocess
import sys
from scripts_support.confirm_directories import find_working_directory


def find_install_scripts(directory):
    """
    Find all scripts in the specified directory that start with 'install_'.

    Args:
        directory (str): The directory to search for scripts.

    Returns:
        list: A sorted list of paths to scripts starting with 'install_'.
    """
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Directory {directory} does not exist.")
    
    # Find all scripts starting with 'install_' and sort them
    return sorted(
        os.path.join(directory, filename)
        for filename in os.listdir(directory)
        if filename.startswith("install_") and filename.endswith(".sh")
    )

def run_scripts(scripts):
    """
    Run a list of scripts sequentially.

    Args:
        scripts (list): List of script paths to execute.

    Raises:
        RuntimeError: If any script fails to execute.
    """
    for script in scripts:
        print(f"Running {script}...")
        if not os.access(script, os.X_OK):
            print(f"Error: {script} is not executable. Skipping...")
            continue
        
        result = subprocess.run(["bash", script], text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Error: Script {script} failed with exit code {result.returncode}.")
    print("All install scripts executed successfully.")

def main():
    working_directory = find_working_directory()
    script_dir = os.path.join(working_directory, "scripts_env")

    try:
        # Find all scripts starting with 'install_'
        install_scripts = find_install_scripts(script_dir)

        if not install_scripts:
            print(f"No install scripts found in {script_dir}.")
            return

        # Run the install scripts
        run_scripts(install_scripts)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
