"""
Utilities for making labs compatible between local VS Code and JupyterLite environments.
This module provides functions to handle the differences between persistent local
environments and non-persistent JupyterLite environments.
"""

import os
from pathlib import Path
import pandas as pd
from IPython.display import display, HTML
import re

def is_jupyterlite():
    """Detect if code is running in JupyterLite environment"""
    try:
        import piplite
        return True
    except ImportError:
        return False

def setup_environment():
    """Setup paths and directories based on environment"""
    if is_jupyterlite():
        # JupyterLite paths - everything is relative to the files directory
        DATA_DIR = "class_data"
        RESULTS_DIR = "results"  # This will be temporary in JupyterLite
        
        # Create results directory if it doesn't exist
        os.makedirs(RESULTS_DIR, exist_ok=True)
        
        print("Running in JupyterLite environment - using ephemeral storage")
        return DATA_DIR, RESULTS_DIR
    else:
        # Local environment - use the existing path discovery code
        def find_comp_gen_dir():
            """Find the computational_genetic_genealogy directory."""
            current = Path.cwd()
            while current != current.parent:
                target = current / 'computational_genetic_genealogy'
                if target.is_dir():
                    return target
                current = current.parent
            raise FileNotFoundError("Could not find computational_genetic_genealogy directory")
            
        # Load environment variables from .env if available
        try:
            from dotenv import load_dotenv
            comp_gen_dir = find_comp_gen_dir()
            env_path = comp_gen_dir / '.env'
            if env_path.exists():
                load_dotenv(env_path, override=True)
        except ImportError:
            print("Warning: dotenv not available. Using default paths.")
        except FileNotFoundError:
            print("Warning: Unable to find computational_genetic_genealogy directory. Using current directory.")
            comp_gen_dir = Path.cwd()
            
        # Set directories from environment variables or use defaults
        DATA_DIR = os.getenv('PROJECT_DATA_DIR', str(Path(comp_gen_dir) / 'data'))
        RESULTS_DIR = os.getenv('PROJECT_RESULTS_DIR', str(Path(comp_gen_dir) / 'results'))
        
        # Ensure results directory exists
        os.makedirs(RESULTS_DIR, exist_ok=True)
        
        print(f"Running in local environment - using persistent storage in {RESULTS_DIR}")
        return DATA_DIR, RESULTS_DIR

def save_results(dataframe, filename, description=""):
    """
    Save results with environment awareness
    
    Args:
        dataframe: The pandas DataFrame to save
        filename: Name of the file to save
        description: Description of the file for the download link
        
    Returns:
        str: Path to the saved file
    """
    DATA_DIR, RESULTS_DIR = setup_environment()
    full_path = os.path.join(RESULTS_DIR, filename)
    dataframe.to_csv(full_path)
    
    if is_jupyterlite():
        download_link = f"""
        <div class="alert alert-info">
            <p><strong>JupyterLite Note:</strong> Your results are temporary. 
            <a href="results/{filename}" download="{filename}" target="_blank">
                Click here to download {description}</a>
            </p>
        </div>
        """
        display(HTML(download_link))
    
    return full_path

def run_external_tool(cmd, jupyterlite_alternative=None):
    """
    Run external command with environment awareness
    
    Args:
        cmd: The command to run in the local environment
        jupyterlite_alternative: A function to run in JupyterLite instead
        
    Returns:
        The command output or the result of jupyterlite_alternative
    """
    if is_jupyterlite():
        if jupyterlite_alternative:
            return jupyterlite_alternative()
        else:
            print("This functionality is not available in JupyterLite. Download the notebook to run locally.")
            return None
    else:
        # Run the actual command locally
        import subprocess
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout

def save_plot(plt, filename, description="plot"):
    """
    Save a matplotlib plot with environment awareness
    
    Args:
        plt: The matplotlib.pyplot instance
        filename: Name of the file to save
        description: Description of the plot for the download link
        
    Returns:
        str: Path to the saved file
    """
    DATA_DIR, RESULTS_DIR = setup_environment()
    full_path = os.path.join(RESULTS_DIR, filename)
    plt.savefig(full_path, dpi=300, bbox_inches='tight')
    
    if is_jupyterlite():
        plt.show()  # Show the plot
        download_link = f"""
        <div class="alert alert-info">
            <p><strong>JupyterLite Note:</strong> Your plot is temporary. 
            <a href="results/{filename}" download="{filename}" target="_blank">
                Click here to download the {description}</a>
            </p>
        </div>
        """
        display(HTML(download_link))
    else:
        plt.show()
    
    return full_path

def notebook_template():
    """
    Return a template for notebook environment setup
    """
    template = """
# Environment setup for cross-compatibility
from scripts_support.lab_cross_compatibility import setup_environment, is_jupyterlite

# Set up environment-specific paths
DATA_DIR, RESULTS_DIR = setup_environment()

# Now paths can be used consistently across environments
data_file_path = os.path.join(DATA_DIR, "example_data.csv")
results_file_path = os.path.join(RESULTS_DIR, "results.csv")
"""
    return template

def process_notebook_for_jupyterlite(notebook_path, output_path):
    """
    Process notebook for JupyterLite compatibility
    
    Args:
        notebook_path: Path to the source notebook
        output_path: Path to save the processed notebook
    """
    import json
    
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    # Identify cells that need modification
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            
            # Replace environment setup
            if ('find_comp_gen_dir()' in source and 'load_env_file()' in source):
                # Replace with the environment detection pattern
                cell['source'] = [
                    "# Environment setup for cross-compatibility\n",
                    "from scripts_support.lab_cross_compatibility import setup_environment, is_jupyterlite\n\n",
                    "# Set up environment-specific paths\n",
                    "DATA_DIR, RESULTS_DIR = setup_environment()\n\n",
                    "# Now you can use DATA_DIR and RESULTS_DIR consistently across environments\n"
                ]
            
            # Replace file paths in all cells
            if isinstance(cell['source'], list):
                cell['source'] = replace_file_paths(cell['source'])
            else:
                cell['source'] = replace_file_paths([cell['source']])
            
    # Write the modified notebook
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1)

def replace_file_paths(source_lines):
    """
    Replace absolute path references with environment variables
    
    Args:
        source_lines: List of source code lines
        
    Returns:
        List of modified source code lines
    """
    if not isinstance(source_lines, list):
        source_lines = [source_lines]
        
    new_lines = []
    for line in source_lines:
        # Replace references to environment variables with the new pattern
        line = re.sub(r'os\.getenv\([\'"]PROJECT_DATA_DIR[\'"]\)', 'DATA_DIR', line)
        line = re.sub(r'os\.getenv\([\'"]PROJECT_RESULTS_DIR[\'"]\)', 'RESULTS_DIR', line)
        
        # Replace os.path.join with direct string paths for JupyterLite
        line = re.sub(r'os\.path\.join\(os\.getenv\([\'"]PROJECT_DATA_DIR[\'"]\), [\'"](.+?)[\'"]\)', r'os.path.join(DATA_DIR, "\1")', line)
        line = re.sub(r'os\.path\.join\(os\.getenv\([\'"]PROJECT_RESULTS_DIR[\'"]\), [\'"](.+?)[\'"]\)', r'os.path.join(RESULTS_DIR, "\1")', line)
        
        new_lines.append(line)
    
    return new_lines