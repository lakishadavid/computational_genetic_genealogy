#!/usr/bin/env python3
"""
Preprocess Jupyter notebooks for JupyterLite compatibility.
Removes environment setup code and other elements that don't work in JupyterLite.
"""

import json
import sys
import re
from pathlib import Path


def remove_env_setup_code(notebook_path, output_path):
    """Remove environment setup code from a Jupyter notebook"""
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    # Process each cell
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            # Find and remove the environment setup code
            source = ''.join(cell['source'])
            
            # Pattern to match the env setup code block
            if ('def find_comp_gen_dir():' in source and 
                'load_env_file()' in source and
                'computational_genetic_genealogy' in source):
                # Replace with a simple comment explaining this was removed for JupyterLite
                cell['source'] = [
                    "# Environment setup code removed for JupyterLite compatibility\n",
                    "# In JupyterLite, files are accessed directly from the files directory\n"
                ]
    
    # Write the modified notebook
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1)
    
    print(f"Processed: {notebook_path} -> {output_path}")


def process_directory(input_dir, output_dir):
    """Process all notebooks in a directory"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Process all Lab*.ipynb files
    count = 0
    for notebook_path in input_path.glob("Lab*.ipynb"):
        output_file = output_path / notebook_path.name
        remove_env_setup_code(notebook_path, output_file)
        count += 1
    
    print(f"Processed {count} notebooks from {input_dir} to {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python preprocess_notebooks.py <input_dir> <output_dir>")
        sys.exit(1)
    
    process_directory(sys.argv[1], sys.argv[2])