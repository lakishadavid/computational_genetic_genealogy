#!/usr/bin/env python3

import os
import io
import sys
import requests
import logging
import argparse
import pandas as pd
import zipfile
from requests.adapters import HTTPAdapter
import urllib3
from urllib3.util import Retry
import time
import subprocess
from decouple import config

def configure_logging(log_filename, log_file_debug_level="INFO", console_debug_level="INFO"):
    """
    Configure logging for both file and console handlers.

    Args:
        log_file_path (str): Path to the log file where logs will be written.
    """
    # Create a root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set the root logger to DEBUG to allow all levels

    # File handler: Logs INFO and above to the file
    LOGFILE = log_filename
    file_handler = logging.FileHandler(LOGFILE)
    file_handler.setLevel(log_file_debug_level)  # File captures only INFO and above
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Console handler: Logs DEBUG and above to the console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_debug_level)  # Console shows DEBUG and above
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # Add handlers to the root logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def create_session_with_retries():
    """Create a requests session with retry strategy"""
    retry_strategy = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    http = urllib3.PoolManager(retries=retry_strategy)
    return http

class MultiSourceGeneticMap:
    def __init__(self):
        self.ucsc_base_url = "https://api.genome.ucsc.edu"
        self.session = create_session_with_retries()
        
        # Updated PLINK2 URLs for different assemblies
        self.plink2_urls = {
            "hg19": "https://www.cog-genomics.org/static/bin/plink/gref-hg19.zip",
            "hg38": "https://www.cog-genomics.org/static/bin/plink/gref-hg38.zip",
            "b37": "https://www.cog-genomics.org/static/bin/plink/gref-b37.zip"
        }

    def download_with_progress(self, url, output_path):
        """Download file with progress tracking"""
        response = self.session.request('GET', url, preload_content=False)

        if response.status != 200:
            raise Exception(f"HTTP error occurred: {response.status} {response.reason}")
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        progress_increment = max(1, total_size // 50) if total_size > 0 else block_size
        
        with open(output_path, 'wb') as f:
            downloaded = 0
            last_print = 0
            while True:
                chunk = response.read(block_size)
                if not chunk:
                    break
                    
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0 and downloaded - last_print >= progress_increment:
                    last_print = downloaded
                    progress = (downloaded / total_size) * 100
                    logging.info(f"Download progress: {progress:.1f}%")
                    
        response.release_conn()

    def download_from_ucsc(self, assembly="hg38", output_file=None):
        """Download recombination rate data from UCSC Genome Browser"""
        query_params = {
            'db': assembly,
            'hgta_group': 'map',
            'hgta_track': 'recomb1000GAvg',
            'hgta_table': 'recomb1000GAvg',
            'hgta_regionType': 'genome',
            'hgta_outputType': 'primaryTable'
        }

        logging.info(f"Retrieving recombination rate data from UCSC for {assembly}")
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                url = f"{self.ucsc_base_url}/getData/track"
                response = self.session.request(
                    'GET',
                    url,
                    fields=query_params,
                    timeout=30.0
                )
                if response.status != 200:
                    raise Exception(f"HTTP error occurred: {response.status} {response.reason}")
                    
                data = response.data.decode('utf-8')
                df = pd.read_csv(io.StringIO(data), sep='\t')
                df = self._process_ucsc(df)
                
                if output_file:
                    df.to_csv(output_file, index=False)
                    logging.info(f"UCSC data saved to {output_file}")
                return df
                
            except (requests.exceptions.RequestException, pd.errors.EmptyDataError) as e:
                if attempt < max_retries - 1:
                    logging.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    time.sleep(retry_delay)
                else:
                    raise Exception(f"Failed to download UCSC data after {max_retries} attempts: {str(e)}")

    def download_from_beagle(self, assembly, output_dir):
        """Downloads and processes Beagle genetic maps"""
        assembly_map_files = {
            "GRCh36": "plink.GRCh36.map.zip",
            "GRCh37": "plink.GRCh37.map.zip",
            "GRCh38": "plink.GRCh38.map.zip"
        }

        if assembly not in assembly_map_files:
            raise ValueError(f"Unsupported assembly '{assembly}'. Must be one of {list(assembly_map_files.keys())}.")

        file_name = assembly_map_files[assembly]
        url = f"https://bochet.gcc.biostat.washington.edu/beagle/genetic_maps/{file_name}"
        output_path = os.path.join(output_dir, file_name)

        try:
            logging.info(f"Downloading Beagle map from {url}")
            self.download_with_progress(url, output_path)
            
            # Verify zip file integrity
            try:
                with zipfile.ZipFile(output_path, 'r') as zip_ref:
                    # Test zip file before extraction
                    test_result = zip_ref.testzip()
                    if test_result is not None:
                        raise zipfile.BadZipFile(f"Corrupted file found in ZIP: {test_result}")
                    
                    # Extract files
                    logging.info(f"Extracting files to {output_dir}")
                    zip_ref.extractall(output_dir)
                    
                    # Log extracted files
                    extracted_files = zip_ref.namelist()
                    logging.info(f"Extracted {len(extracted_files)} files: {', '.join(extracted_files)}")
            
            except zipfile.BadZipFile as e:
                raise Exception(f"Invalid ZIP file downloaded: {str(e)}")
            
            # Clean up zip file
            os.remove(output_path)
            logging.info("ZIP file cleaned up")
            
        except Exception as e:
            logging.error(f"Error processing Beagle files: {str(e)}")
            if os.path.exists(output_path):
                os.remove(output_path)
            raise

    def preprocess_ibis_map(self, assembly, output_dir):
        """
        Converts Beagle genetic map files to IBIS format by rearranging columns
        and replacing '.' with '0'.
        Rearrange the columns: 
        1. Chromosome (as is)
        2. Physical position (currently in the 4th column)
        3. Placeholder or recombination rate (currently in the 2nd column)
        4. Genetic position (currently in the 3rd column)
        """
        beagle_map_dir = os.path.join(references_directory, "genetic_maps/beagle_genetic_maps")
        ibis_map_dir = os.path.join(references_directory, "genetic_maps/ibis_genetic_maps")
        os.makedirs(ibis_map_dir, exist_ok=True)
        
        for map_file in os.listdir(beagle_map_dir):
            if map_file.endswith(".map"):
                beagle_map_filename = os.path.join(beagle_map_dir, map_file)
                ibis_map_filename = os.path.join(ibis_map_dir, map_file)
                print(f"Processing {beagle_map_filename} to create IBIS map...")
                command = f"awk '{{print $1, $4, ($2 == \".\" ? 0 : $2), $3}}' {beagle_map_filename} > {ibis_map_filename}"
                subprocess.run(command, shell=True, check=True)
        print("All Beagle genetic maps converted to IBIS format.")


    def download_from_plink2(self, assembly="hg38", output_file=None):
        """Download PLINK2 genetic maps"""
        if assembly not in self.plink2_urls:
            raise ValueError(f"Unsupported assembly '{assembly}'. Must be one of {list(self.plink2_urls.keys())}.")
        
        url = self.plink2_urls[assembly]
        temp_zip = output_file + '.zip'
        
        try:
            logging.info(f"Downloading PLINK2 map for {assembly}")
            self.download_with_progress(url, temp_zip)
            
            # Extract the map file
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                map_files = [f for f in zip_ref.namelist() if f.endswith('.map')]
                if not map_files:
                    raise Exception("No .map files found in the downloaded archive")
                
                logging.info(f"Extracting {map_files[0]} to {output_file}")
                with zip_ref.open(map_files[0]) as source, open(output_file, 'wb') as target:
                    target.write(source.read())
            
            # Clean up
            os.remove(temp_zip)
            logging.info("Download and extraction completed successfully")
            
        except Exception as e:
            logging.error(f"Error downloading PLINK2 map: {str(e)}")
            if os.path.exists(temp_zip):
                os.remove(temp_zip)
            raise

def main(references_directory):
    # FIX: The IBIS option works, but needs work for the naming conventions to make sense
    parser = argparse.ArgumentParser(
        description="Download and process genetic map data from multiple sources."
    )
    parser.add_argument("--data-source", required=True, choices=["UCSC", "BEAGLE", "PLINK2", "IBIS"],
                        help="Specify the data source: UCSC, BEAGLE, PLINK2, or IBIS")
    parser.add_argument("--assembly", required=True,
                        help="Genome assembly (e.g., hg38, GRCh38)")
    parser.add_argument("--output-file", 
                        help="Path to save the downloaded/processed data")
    parser.add_argument("--references-directory",
                        default=references_directory,
                        help="Base references directory to store output")
    args = parser.parse_args()

    # Set up output directories
    genetic_maps_dir = os.path.join(args.references_directory, "genetic_maps")
    os.makedirs(genetic_maps_dir, exist_ok=True)

    # Create source-specific subdirectories
    source_dirs = {
        "BEAGLE": os.path.join(genetic_maps_dir, "beagle_genetic_maps"),
        "PLINK2": os.path.join(genetic_maps_dir, "plink2_genetic_maps"),
        "UCSC": os.path.join(genetic_maps_dir, "ucsc_genetic_maps"),
        "IBIS": os.path.join(genetic_maps_dir, "ibis_genetic_maps")
    }
    
    for directory in source_dirs.values():
        os.makedirs(directory, exist_ok=True)

    # Set default output file if not specified
    if not args.output_file:
        filename = f"{args.data_source.lower()}_{args.assembly}.{'csv' if args.data_source == 'UCSC' else 'map'}"
        args.output_file = os.path.join(source_dirs[args.data_source], filename)

    retrieve = MultiSourceGeneticMap()

    try:
        if args.data_source == "UCSC":
            retrieve.download_from_ucsc(assembly=args.assembly, output_file=args.output_file)
        elif args.data_source == "BEAGLE":
            retrieve.download_from_beagle(assembly=args.assembly, output_dir=source_dirs["BEAGLE"])
        elif args.data_source == "IBIS":
            retrieve.preprocess_ibis_map(assembly=args.assembly, output_dir=source_dirs["IBIS"])
        elif args.data_source == "PLINK2":
            retrieve.download_from_plink2(assembly=args.assembly, output_file=args.output_file)
        
        logging.info("Process completed successfully")

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # # Run commands
    # # For UCSC data:
    # poetry run python -m scripts_support.genetic_maps_download --data-source UCSC --assembly hg38

    # # For Beagle data:
    # poetry run python -m scripts_support.genetic_maps_download --data-source BEAGLE --assembly GRCh38 

    # # For PLINK2 data:
    # poetry run python -m scripts_support.genetic_maps_download --data-source PLINK2 --assembly hg38

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

    log_filename = os.path.join(results_directory, "log.txt")
    configure_logging(log_filename, log_file_debug_level="INFO", console_debug_level="INFO")

    # logging.info directories
    logging.info(f"Results Directory: {results_directory}")
    logging.info(f"Data Directory: {data_directory}")
    logging.info(f"References Directory: {references_directory}")
    logging.info(f"Utils Directory: {utils_directory}")


    main(references_directory)