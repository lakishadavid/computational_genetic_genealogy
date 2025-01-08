import os
import json
import logging
import sys
import argparse
from pathlib import Path
from typing import Dict, Optional
from decouple import config
from dotenv import set_key

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
    Find and confirm the project root directory.
    """
    logging.info("Finding working directory...")
    
    # First check environment variable
    env_working_dir = config('PROJECT_WORKING_DIR', default=None)
    if env_working_dir and os.path.isdir(env_working_dir):
        if not interactive or get_user_confirmation(
            f"Use working directory from environment: {env_working_dir}?"
        ):
            return env_working_dir
    
    # If a custom path is provided, validate it
    if custom_path:
        expanded_path = os.path.expanduser(os.path.expandvars(custom_path))
        if os.path.isdir(expanded_path):
            if not interactive or get_user_confirmation(
                f"Use custom working directory: {expanded_path}?"
            ):
                return expanded_path
    
    # Default directory detection logic
    default_paths = [
        "/home/ubuntu/bagg_analysis",
        os.path.join(os.getenv("HOME", ""), "bagg_analysis")
    ]
    
    for path in default_paths:
        if os.path.isdir(path):
            if not interactive or get_user_confirmation(
                f"Use default working directory: {path}?"
            ):
                return path
    
    if interactive:
        custom_input = input("Please enter a custom working directory path: ")
        expanded_custom = os.path.expanduser(os.path.expandvars(custom_input))
        if os.path.isdir(expanded_custom):
            return expanded_custom
        else:
            create = get_user_confirmation(
                f"Directory {expanded_custom} doesn't exist. Create it?"
            )
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
        print("\nProposed directory structure:")
        print(json.dumps(directories, indent=2))
        if not get_user_confirmation("Do you want to use these directories?"):
            print("Please provide alternative paths (press Enter to keep current):")
            for key in directories:
                if key != 'working_directory':  # Skip working directory as it's already confirmed
                    new_path = input(f"{key} [{directories[key]}]: ").strip()
                    if new_path:
                        directories[key] = (
                            new_path if os.path.isabs(new_path)
                            else os.path.join(working_directory, new_path)
                        )
    
    # Ensure all directories exist
    for name, directory in directories.items():
        try:
            if not os.path.exists(directory):
                if not interactive or get_user_confirmation(
                    f"Create directory {directory}?"
                ):
                    os.makedirs(directory)
                    logging.info(f"Created {name}: {directory}")
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

"""
# In other scripts:
from directory_setup import verify_directories
from decouple import config

try:
    # First try to get directories from .env
    data_dir = config('PROJECT_DATA_DIR', default=None)
    references_dir = config('PROJECT_REFERENCES_DIR', default=None)
    
    if not all([data_dir, references_dir]):
        # If any required directories are missing, run verification
        directories = verify_directories()
        data_dir = directories['data_directory']
        references_dir = directories['references_directory']
    
    # Continue with script...
except Exception as e:
    print(f"Error verifying directories: {e}")
    sys.exit(1)
"""