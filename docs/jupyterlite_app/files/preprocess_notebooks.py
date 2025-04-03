#!/usr/bin/env python3
import os
import json
import sys
import re
from pathlib import Path

# Directory containing the notebooks to preprocess
src_dir = sys.argv[1]
# Directory to store preprocessed notebooks
out_dir = sys.argv[2]

# Skip these notebooks (don't modify)
skip_notebooks = ["Lab0_Code_Environment.ipynb"]

def preprocess_notebook(notebook_path, output_path):
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    cells = notebook['cells']
    
    # Identify cells to remove or modify
    filtered_cells = []
    for cell in cells:
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            
            # Remove cells containing:
            # - poetry install commands
            # - os.makedirs calls
            # - find_comp_gen_dir function
            # - Setting environment variables with os.environ
            # - Changing directories with os.chdir
            if (
                'poetry install' in source or 
                'os.makedirs' in source or
                'def find_comp_gen_dir' in source or
                'comp_gen_dir = find_comp_gen_dir()' in source or
                'load_env_file()' in source or
                'os.environ[' in source or
                'os.chdir(' in source or
                # Keep the cell if it doesn't match any of the above conditions
                False
            ):
                continue
                
            # Keep this cell, but modify specific parts if needed
            # - Replace absolute paths like /home/lakishadavid/... with relative paths
            new_source = []
            for line in cell['source']:
                # Replace paths with browser-compatible alternatives
                line = re.sub(r'/home/lakishadavid/computational_genetic_genealogy/data', 'class_data', line)
                line = re.sub(r'/home/lakishadavid/computational_genetic_genealogy/results', 'results', line)
                new_source.append(line)
            
            cell['source'] = new_source
            
        filtered_cells.append(cell)
    
    # Update the notebook with the filtered cells
    notebook['cells'] = filtered_cells
    
    # Write the modified notebook
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1)

def main():
    for filename in os.listdir(src_dir):
        if not filename.endswith('.ipynb'):
            continue
            
        if filename in skip_notebooks:
            # Copy without modification
            source_path = os.path.join(src_dir, filename)
            target_path = os.path.join(out_dir, filename)
            with open(source_path, 'r', encoding='utf-8') as f_in, open(target_path, 'w', encoding='utf-8') as f_out:
                f_out.write(f_in.read())
            print(f"Copied without modification: {filename}")
            continue
        
        notebook_path = os.path.join(src_dir, filename)
        output_path = os.path.join(out_dir, filename)
        
        print(f"Processing: {filename}")
        preprocess_notebook(notebook_path, output_path)

if __name__ == "__main__":
    main()
