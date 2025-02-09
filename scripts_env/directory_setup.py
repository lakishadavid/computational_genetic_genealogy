import os
import json
import logging
import sys
import argparse
import shutil
from typing import Dict, Optional
from decouple import config

def load_env_directories() -> Dict[str, str]:
    """Load directory paths from .env file if they exist."""
    env_vars = {
        'PROJECT_WORKING_DIR': config('PROJECT_WORKING_DIR', default=None),
        'PROJECT_UTILS_DIR': config('PROJECT_UTILS_DIR', default=None),
        'PROJECT_RESULTS_DIR': config('PROJECT_RESULTS_DIR', default=None),
        'PROJECT_DATA_DIR': config('PROJECT_DATA_DIR', default=None),
        'PROJECT_REFERENCES_DIR': config('PROJECT_REFERENCES_DIR', default=None),
        'USER_HOME': config('USER_HOME', default=None)
    }
    return env_vars

def save_env_directories(directories: Dict[str, str]) -> None:
    """Save directory paths to .env file while preserving other existing content."""
    env_path = os.path.join(directories['working_directory'], '.env')
    
    env_mapping = {
        'utils_directory': 'PROJECT_UTILS_DIR',
        'results_directory': 'PROJECT_RESULTS_DIR',
        'data_directory': 'PROJECT_DATA_DIR',
        'references_directory': 'PROJECT_REFERENCES_DIR',
        'working_directory': 'PROJECT_WORKING_DIR',
        'user_home': 'USER_HOME'
    }
    
    # Read the entire file content first
    lines = []
    dir_vars_found = set()
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                # Keep track of which directory variables we've seen
                if '=' in line:
                    key = line.split('=')[0].strip()
                    if key in env_mapping.values():
                        dir_vars_found.add(key)
                        # Update this directory variable
                        dir_key = next(k for k, v in env_mapping.items() if v == key)
                        if dir_key in directories and directories[dir_key]:
                            value = directories[dir_key]
                            if ' ' in value:
                                value = f'"{value}"'
                            line = f"{key}={value}\n"
                lines.append(line)
    
    # Write the updated content back
    with open(env_path, 'w') as f:
        # Write existing content with updated directory paths
        f.writelines(lines)
        
        # Append any new directory variables that weren't in the file
        for dir_key, env_key in env_mapping.items():
            if env_key not in dir_vars_found and dir_key in directories and directories[dir_key]:
                value = directories[dir_key]
                if ' ' in value:
                    value = f'"{value}"'
                f.write(f'{env_key}={value}\n')

def get_user_confirmation(prompt: str) -> bool:
    """Get user confirmation for a given prompt."""
    while True:
        response = input(f"{prompt} (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        print("Please answer 'y' or 'n'")

def find_working_directory(custom_path: Optional[str] = None, interactive: bool = True) -> str:
    """
    Find the full path to the working directory across different operating systems.
    
    Prioritizes:
    1. Environment variable
    2. Custom path 
    3. Script's current directory
    4. Fallback default paths
    5. Interactive user input
    """
    logging.info("Finding working directory...")

    # Helper function to validate and potentially expand a path
    def validate_path(path: str) -> Optional[str]:
        if not path:
            return None
        expanded_path = os.path.abspath(os.path.expanduser(os.path.expandvars(path)))
        return expanded_path if os.path.isdir(expanded_path) else None

    # Check environment variable
    env_working_dir = validate_path(os.getenv('PROJECT_WORKING_DIR', ''))
    if env_working_dir:
        if not interactive or get_user_confirmation(f"Use working directory from environment: {env_working_dir}?"):
            return env_working_dir

    # Check custom path
    if custom_path:
        validated_custom_path = validate_path(custom_path)
        if validated_custom_path:
            if not interactive or get_user_confirmation(f"Use custom working directory: {validated_custom_path}?"):
                return validated_custom_path

    # Use script's directory as the base for finding 'computational_genetic_genealogy'
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(script_dir, 'computational_genetic_genealogy')
    
    if os.path.isdir(target_dir):
        return target_dir

    # Search parent directories for the target directory
    current_dir = script_dir
    while current_dir != os.path.dirname(current_dir):  # Stop at root
        potential_target = os.path.join(current_dir, 'computational_genetic_genealogy')
        if os.path.isdir(potential_target):
            return potential_target
        current_dir = os.path.dirname(current_dir)

    # Fallback to default paths
    default_paths = [
        os.path.join(os.path.expanduser('~'), 'computational_genetic_genealogy'),
        os.path.join(os.path.expanduser('~'), 'bagg_analysis')
    ]
    
    for path in default_paths:
        if os.path.isdir(path):
            if not interactive or get_user_confirmation(f"Use default working directory: {path}?"):
                return path

    # Interactive prompt if all else fails
    if interactive:
        custom_input = input("Please enter a custom working directory path: ")
        expanded_custom = validate_path(custom_input)
        
        if expanded_custom:
            return expanded_custom
        
        create = get_user_confirmation(f"Directory {custom_input} doesn't exist. Create it?")
        if create:
            os.makedirs(expanded_custom)
            return expanded_custom

    raise FileNotFoundError(
        "No valid working directory found. Please specify a custom directory path."
    )


def get_directories(
    working_directory: str,
    custom_dirs: Optional[Dict[str, str]] = None,
    interactive: bool = True
) -> Dict[str, str]:
    """
    Configure and confirm directory structure.
    """
    # First validate working directory exists
    if not os.path.exists(working_directory):
        if interactive:
            confirm = get_user_confirmation(
                f"Working directory {working_directory} does not exist. Create it?"
            )
            if not confirm:
                raise FileNotFoundError(f"Working directory {working_directory} does not exist.")
            os.makedirs(working_directory)
        else:
            os.makedirs(working_directory)
    
    # Confirm working directory before proceeding
    if interactive:
        print(f"\nProposed working directory: {working_directory}")
        if not get_user_confirmation("Do you want to use this working directory?"):
            raise FileNotFoundError("Working directory not confirmed.")

    # First check environment variables
    env_dirs = load_env_directories()
    
    # Default directory configuration
    directories = {
        'working_directory': working_directory,
        'user_home': env_dirs['USER_HOME'] or os.path.expanduser("~"),
        'utils_directory': env_dirs['PROJECT_UTILS_DIR'] or os.path.join(working_directory, "utils"),
        'results_directory': env_dirs['PROJECT_RESULTS_DIR'] or os.path.join(working_directory, "results"),
        'data_directory': env_dirs['PROJECT_DATA_DIR'] or (
            "/mnt/efs" if os.path.exists("/mnt/efs") else os.path.join(working_directory, "data")
        ),
        'references_directory': env_dirs['PROJECT_REFERENCES_DIR'] or os.path.join(working_directory, "references")
    }
    
    # Override with custom directories if provided
    if custom_dirs:
        for key, value in custom_dirs.items():
            if value:
                directories[key] = (
                    value if os.path.isabs(value) else os.path.join(working_directory, value)
                )
    
    if interactive:
        print("\nProposed additional directories:")
        # Remove working directory from display to avoid redundancy
        display_dirs = {k: v for k, v in directories.items() if k != 'working_directory'}
        print(json.dumps(display_dirs, indent=2))
        
        if not get_user_confirmation("Do you want to use these directories?"):
            print("Please provide alternative paths (press Enter to keep current):")
            for key in [k for k in directories.keys() if k != 'working_directory']:
                new_path = input(f"{key} [{directories[key]}]: ").strip()
                if new_path:
                    directories[key] = (
                        new_path if os.path.isabs(new_path)
                        else os.path.join(working_directory, new_path)
                    )
    
    # Ensure all non-working directories exist
    for name, directory in [
        (name, dir_path) for name, dir_path in directories.items() 
        if name != 'working_directory'
    ]:
        try:
            if not os.path.exists(directory):
                if not interactive or get_user_confirmation(f"Create directory {directory}?"):
                    os.makedirs(directory)
                    logging.info(f"Created {name}: {directory}")
                else:
                    logging.warning(f"Directory {name} at {directory} was not created.")
            else:
                logging.info(f"Using existing {name}: {directory}")
        except OSError as e:
            logging.error(f"Failed to create {name} at {directory}: {e}")
            raise
    
    return directories

def verify_directories() -> Dict[str, str]:
    """
    Verify existing directory configurations from .env file.
    If verification fails or user requests reconfiguration, runs the setup script.
    
    Returns:
        Dictionary of verified directory paths
    """
    env_dirs = load_env_directories()
    
    # Check if all required environment variables are set
    required_vars = {
        'PROJECT_WORKING_DIR': 'working directory',
        'USER_HOME': 'user home directory',
        'PROJECT_DATA_DIR': 'data directory',
        'PROJECT_REFERENCES_DIR': 'references directory',
        'PROJECT_UTILS_DIR': 'utils directory',
        'PROJECT_RESULTS_DIR': 'results directory'
    }
    
    missing_vars = [name for var, name in required_vars.items() if not env_dirs.get(var)]
    
    if missing_vars:
        print(f"Missing directory configurations for: {', '.join(missing_vars)}")
        print("Running directory setup...")
        return setup_directories(interactive=True)
    
    # Show current configuration
    print("\nCurrent directory configuration:")
    directories = {
        'working_directory': env_dirs['PROJECT_WORKING_DIR'],
        'user_home': env_dirs['USER_HOME'],
        'utils_directory': env_dirs['PROJECT_UTILS_DIR'],
        'results_directory': env_dirs['PROJECT_RESULTS_DIR'],
        'data_directory': env_dirs['PROJECT_DATA_DIR'],
        'references_directory': env_dirs['PROJECT_REFERENCES_DIR']
    }
    print(json.dumps(directories, indent=2))
    
    if get_user_confirmation("Are these directories correct?"):
        return directories
    else:
        print("Running directory setup...")
        return setup_directories(interactive=True)

def setup_directories(
    working_dir: Optional[str] = None,
    custom_dirs: Optional[Dict[str, str]] = None,
    interactive: bool = True
) -> Dict[str, str]:
    """
    Main function for setting up directories, can be called from other scripts.
    """
    try:
        working_directory = find_working_directory(working_dir, interactive)
        directories = get_directories(working_directory, custom_dirs, interactive)
        save_env_directories(directories)
        return directories
    except Exception as e:
        logging.error(f"Error configuring directories: {e}")
        raise

def post_process(directories: Dict[str, str], repo_path: str) -> None:
    """
    After directory setup is complete, update ~/.bashrc with the utilities directory and,
    if the user-defined data directory is different from the default, copy the repository's
    Data directory to the user-defined data directory.
    """
    # Update ~/.bashrc with the utilities directory if not already present.
    bashrc_path = os.path.expanduser("~/.bashrc")
    utils_dir = directories.get('utils_directory')
    export_line = f'export PATH=$PATH:{utils_dir}'
    try:
        with open(bashrc_path, 'r') as f:
            bashrc_content = f.read()
    except FileNotFoundError:
        bashrc_content = ""
    if export_line not in bashrc_content:
        with open(bashrc_path, 'a') as f:
            f.write(f'\n{export_line}\n')
        print(f"Updated {bashrc_path} to include the utilities directory: {utils_dir}")
    else:
        print("Utilities directory already present in ~/.bashrc")
    
    # Define the default data directory and compare with the user-defined data directory.
    default_data_dir = os.path.realpath(os.path.expanduser("~/computational_genetic_genealogy/data"))
    user_data_dir = os.path.realpath(directories.get('data_directory'))
    
    if user_data_dir != default_data_dir:
        if os.path.exists(user_data_dir):
            try:
                copy_directory = os.path.join(default_data_dir, "class_data")
                paste_direcotry = os.path.join(user_data_dir, "class_data")
                # Create the directory if it doesn't exist
                if not os.path.exists(paste_direcotry):
                    os.makedirs(paste_direcotry)
                shutil.copytree(copy_directory, paste_direcotry, dirs_exist_ok=True)
                print(f"Data successfully copied from {copy_directory} to {paste_direcotry}.")
            except Exception as e:
                print(f"Error copying data: {e}")
        else:
            print(f"Warning: The directory {paste_direcotry} was not found, but you can still find the data in ~/computational_genetic_genealogy/data.")
    else:
        print("Data directory is the default; skipping data copy block.")
        
def print_environment_ready_message():
    print("\n")
    print("=" * 60 + "\n")
    print("🚀 Your development environment is ready!\n")
    print("=" * 60 + "\n")
    print("📢 Begin coding in your configured environment!\n")

    if shutil.which("code"):
        print("📢 To start working with VS Code, simply enter the following command in this terminal window:")
        print("\n")
        print("    code .")
    else:
        print("⚠️  The 'code' command is not available in your PATH.")
        print("Please ensure Visual Studio Code is installed and its command line tools are set up.")
        print("For instructions, see: https://code.visualstudio.com/docs/setup/setup-overview")
    
    print("\n")
    print("=" * 60 + "\n")
        
def main():
    """Command-line interface for directory setup."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(
        description="Set up and configure project directories"
    )
    parser.add_argument(
        '--working-dir',
        help='Custom working directory path'
    )
    parser.add_argument(
        '--user-home',
        help='User home directory path'
    )
    parser.add_argument(
        '--utils-dir',
        help='Custom utils directory path'
    )
    parser.add_argument(
        '--results-dir',
        help='Custom results directory path'
    )
    parser.add_argument(
        '--data-dir',
        help='Custom data directory path'
    )
    parser.add_argument(
        '--references-dir',
        help='Custom references directory path'
    )
    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='Run without user confirmation prompts'
    )
    
    args = parser.parse_args()
    
    custom_dirs = {
        'user_home': args.user_home,
        'utils_directory': args.utils_dir,
        'results_directory': args.results_dir,
        'data_directory': args.data_dir,
        'references_directory': args.references_dir
    }
    
    try:
        directories = setup_directories(
            args.working_dir,
            custom_dirs,
            interactive=not args.non_interactive
        )
        print("\nConfigured directories:")
        print(json.dumps(directories, indent=2))
        
        # Use the working directory as the repository path (adjust if needed)
        repo_path = directories.get('working_directory')
        post_process(directories, repo_path)
        
        # Call the function to display the message
        print_environment_ready_message()
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # Examples of how to run this script:
    #
    # Basic interactive run (interactive):
    # python directory_setup.py
    #
    # Set specific directories (interactive with suggestions):
    # python directory_setup.py --working-dir ~/my_project --data-dir /mnt/efs
    #
    # Non-interactive with all paths:
    # python directory_setup.py \
    #     --working-dir ~/my_project \
    #     --data-dir /mnt/efs \
    #     --utils-dir utils \
    #     --results-dir results \
    #     --references-dir references \
    #     --non-interactive
    main()