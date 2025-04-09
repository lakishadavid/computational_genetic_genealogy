#!/usr/bin/env python3
"""
Enhanced preprocessor for Jupyter notebooks to ensure compatibility with JupyterLite.
This script extends the original preprocess_notebooks.py with better handling of
paths, environment detection, and cross-compatibility features.
"""

import json
import sys
import re
import os
import shutil
from pathlib import Path
from scripts_support.lab_cross_compatibility import process_notebook_for_jupyterlite

def process_directory(input_dir, output_dir):
    """Process all notebooks in a directory"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create results directory in output for student work
    results_dir = output_path / "results"
    results_dir.mkdir(exist_ok=True)
    
    # Process all Lab*.ipynb files
    count = 0
    for notebook_path in input_path.glob("Lab*.ipynb"):
        output_file = output_path / notebook_path.name
        # Also create a lowercase version for better portability
        lowercase_output = output_path / notebook_path.name.lower()
        
        # Process the notebook
        process_notebook_for_jupyterlite(notebook_path, output_file)
        
        # Create lowercase symlink or copy
        if sys.platform == 'win32':
            # Windows doesn't support symlinks easily, so make a copy
            shutil.copy2(output_file, lowercase_output)
        else:
            # Create symlink on Unix-like systems
            if lowercase_output.exists():
                lowercase_output.unlink()
            os.symlink(notebook_path.name, lowercase_output)
            
        count += 1
    
    print(f"Processed {count} notebooks from {input_dir} to {output_dir}")
    print(f"Created results directory at {results_dir}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m scripts_support.preprocess_notebooks <input_dir> <output_dir>")
        sys.exit(1)
    
    process_directory(sys.argv[1], sys.argv[2])