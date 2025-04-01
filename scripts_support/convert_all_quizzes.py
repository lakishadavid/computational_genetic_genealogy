#!/usr/bin/env python3
import os
import sys
import glob
import subprocess
from pathlib import Path

def convert_all_files(base_dir, script_path):
    """Convert all CSV files in quizzes and assignments directories to Canvas-compatible zip files."""
    # Find all CSV files in the quizzes directory
    quiz_dir = os.path.join(base_dir, "docs", "quizzes")
    quiz_files = glob.glob(os.path.join(quiz_dir, "*.csv"))
    
    # Find all CSV files in the assignments directory
    assignment_dir = os.path.join(base_dir, "docs", "assignments")
    assignment_files = glob.glob(os.path.join(assignment_dir, "*.csv"))
    
    # Process quiz files
    print(f"Found {len(quiz_files)} quiz CSV files to convert")
    for quiz_file in quiz_files:
        file_name = os.path.basename(quiz_file)
        quiz_name = os.path.splitext(file_name)[0].replace("_", " ")
        
        # Run the converter script
        cmd = ["poetry", "run", "python", script_path, quiz_file, quiz_name]
        print(f"Converting {file_name}...")
        try:
            result = subprocess.run(cmd, cwd=base_dir, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error converting {file_name}: {result.stderr}")
            else:
                print(f"Successfully converted {file_name}")
                if result.stdout:
                    print(result.stdout)
        except Exception as e:
            print(f"Exception while converting {file_name}: {e}")
    
    # Process assignment files
    print(f"\nFound {len(assignment_files)} assignment CSV files to convert")
    for assignment_file in assignment_files:
        file_name = os.path.basename(assignment_file)
        assignment_name = os.path.splitext(file_name)[0].replace("_", " ")
        
        # Run the converter script
        cmd = ["poetry", "run", "python", script_path, assignment_file, assignment_name]
        print(f"Converting {file_name}...")
        try:
            result = subprocess.run(cmd, cwd=base_dir, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error converting {file_name}: {result.stderr}")
            else:
                print(f"Successfully converted {file_name}")
                if result.stdout:
                    print(result.stdout)
        except Exception as e:
            print(f"Exception while converting {file_name}: {e}")

def main():
    # Get base directory (where computational_genetic_genealogy is located)
    base_dir = Path(__file__).resolve().parent.parent
    
    # Path to the converter script
    script_path = os.path.join(base_dir, "scripts_support", "improved-quiz-converter.py")
    
    # Check if the converter script exists
    if not os.path.exists(script_path):
        print(f"Error: Converter script not found at {script_path}")
        sys.exit(1)
    
    # Convert all files
    convert_all_files(base_dir, script_path)
    
    print("\nAll conversions completed!")

if __name__ == "__main__":
    main()