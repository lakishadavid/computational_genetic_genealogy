#!/usr/bin/env python3

import logging
import subprocess
import sys
from decouple import config

LOGFILE = "/home/lakishadavid/bagg_analysis/results/log/quality_control_vcf.log"
logging.basicConfig(
    filename=LOGFILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'  # a Append mode creates the file if it does not exist
)

# Create a console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)  # Or another desired level
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Attach the console handler to the root logger
logging.getLogger().addHandler(console_handler)

def main():
    try:
        subprocess.run(['poetry', 'run', 'python', '-m', 'scripts_support.directory_setup'], check=True)
        working_directory = config('PROJECT_WORKING_DIR', default=None)
        data_directory = config('PROJECT_DATA_DIR', default=None)
        references_directory = config('PROJECT_REFERENCES_DIR', default=None)
        results_directory = config('PROJECT_RESULTS_DIR', default=None)
        utils_directory = config('PROJECT_UTILS_DIR', default=None)

        if not all([working_directory, data_directory, references_directory, 
                   results_directory, utils_directory]):
            raise ValueError("Not all required directories were configured")
            
    except Exception as e:
        print(f"Error verifying directories: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()