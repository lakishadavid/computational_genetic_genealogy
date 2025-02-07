import os
import subprocess
import json
import sys
import logging
from inputimeout import inputimeout, TimeoutOccurred
import argparse

from dotenv import load_dotenv

# Determine the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Assuming your project root is one level up from the script's directory
project_root = os.path.dirname(script_dir)
# Construct the full path to the .env file located in the project root
env_path = os.path.join(project_root, '.env')

# Load environment variables from the .env file; 'override=True' ensures that variables in the .env file overwrite any existing environment variables
load_dotenv(dotenv_path=env_path, override=True)

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

def prompt_chromosome_selection():
    """Prompt the user to select chromosomes to process with a timeout and default option."""
    print("Choose an option for chromosomes to process:")
    print("a) Range: 1 to 22")
    print("b) Range: 1 to 22 plus X")
    print("c) Multiple chromosomes: 1 and 20 (default)")
    print("d) Single chromosome: chromosome 20")
    print("e) Single chromosomes: chromosome X")
    print("f) Custom range: Enter start and end chromosomes")

    # Default selection if input times out
    default_selection = "c"

    try:
        selection = inputimeout(prompt="Enter your choice (a, b, c, d, e, or f): ", timeout=20).strip().lower()
    except TimeoutOccurred:
        print("\nNo input provided. Defaulting to 'c'.")
        selection = default_selection

    options = {
        "a": list(range(1, 23)),  # Sequential range 1 to 22
        "b": list(range(1, 23)) + ["X"],  # Range 1 to 22 plus X
        "c": [1, 20],  # Non-sequential chromosomes
        "d": [20],  # Single chromosome
        "e": ["X"],  # Single chromosome
    }

    if selection == "f":
        try:
            start = input("Enter start chromosome (1-22 or X): ").strip()
            end = input("Enter end chromosome (1-22 or X): ").strip()
            
            # Convert start and end to appropriate types
            if start.upper() == "X":
                start = "X"
            else:
                start = int(start)
                if not 1 <= start <= 22:
                    raise ValueError("Start chromosome must be between 1 and 22 or X")
            
            if end.upper() == "X":
                end = "X"
            else:
                end = int(end)
                if not 1 <= end <= 22:
                    raise ValueError("End chromosome must be between 1 and 22 or X")
            
            # Generate chromosome range
            if start == "X" or end == "X":
                if start == "X":
                    chromosomes = ["X"]
                else:
                    chromosomes = list(range(start, 23)) + ["X"]
            else:
                if start <= end:
                    chromosomes = list(range(start, end + 1))
                else:
                    chromosomes = list(range(end, start + 1))
            
            return "f", chromosomes
            
        except ValueError as e:
            logging.info(f"Invalid input: {str(e)}")
            sys.exit(1)
    elif selection not in options:
        logging.info("Invalid choice. Please choose a, b, c, d, e, or f.")
        sys.exit(1)

    return selection, options[selection]

def index_downloaded_files(vcf_path):        
        if os.path.isfile(vcf_path):
            logging.info(f"Indexing {vcf_path}...")
            # Execute tabix with the vcf preset to create an index file (.tbi)
            result = subprocess.run(["tabix", "-f", "-p", "vcf", vcf_path],
                                    stdout=None, stderr=None)
            if result.returncode != 0:
                error_message = result.stderr.decode().strip()
                logging.error(f"Failed to index {vcf_path}: {error_message}")
            else:
                logging.info(f"Successfully indexed {vcf_path}.")
        else:
            logging.error(f"File {vcf_path} not found.")
            
def index_files(chromosomes, destination_dir):
    """
    Index VCF files for all specified chromosomes.

    Parameters:
        chromosomes (list): List of chromosomes to index.
        destination_dir (str): Directory where the VCF files are stored.
    """
    for chromosome in chromosomes:
        new_vcf_filename = f"onethousandgenomes_sequenced_phased.chr{chromosome}.vcf.gz"
        vcf_path = os.path.join(destination_dir, new_vcf_filename)
        index_downloaded_files(vcf_path)
        if not os.path.isfile(vcf_path + ".tbi"):
            logging.info(f"{new_vcf_filename} was not indexed.")

def download_files(base_url, chromosomes, destination_dir):
    """
    Download VCF files for the specified chromosomes.

    Parameters:
        base_url (str): Base URL where the VCF files are hosted.
        chromosomes (list): List of chromosomes to download.
        destination_dir (str): Directory where the downloaded files will be saved.
    """
    for chromosome in chromosomes:
        if chromosome == "X":
            vcf_filename = f"1kGP_high_coverage_Illumina.chr{chromosome}.filtered.SNV_INDEL_SV_phased_panel.v2.vcf.gz"
        else:
            vcf_filename = f"1kGP_high_coverage_Illumina.chr{chromosome}.filtered.SNV_INDEL_SV_phased_panel.vcf.gz"

        # Use a new filename for saving the downloaded file
        new_vcf_filename = f"onethousandgenomes_sequenced_phased.chr{chromosome}.vcf.gz"
        vcf_url = f"{base_url}/{vcf_filename}"

        logging.info(f"\nDownloading {vcf_filename}...")
        vcf_path = os.path.join(destination_dir, new_vcf_filename)
        result = subprocess.run(
            ["wget", "-O", vcf_path, vcf_url],
            stdout=None, stderr=None
        )
        if result.returncode != 0:
            logging.info(f"Failed to download {vcf_filename}. Skipping...")
            continue

        # Confirm that the file was successfully downloaded
        if not os.path.isfile(vcf_path):
            logging.info(f"{vcf_filename} was not downloaded.")
            continue
        
        index_downloaded_files(vcf_path)
        if not os.path.isfile(vcf_path + ".tbi"):
            logging.info(f"{vcf_filename} was not indexed")

        logging.info(f"Successfully downloaded and verified files for chromosome {chromosome}.")


def main():
    # poetry run python -m scripts_support.onethousandgenomes_download
    # poetry run python -m scripts_support.onethousandgenomes_download --only-index
    
    parser = argparse.ArgumentParser(description="Script description")
    parser.add_argument('--only-index', action='store_true', help='Run indexing only')
    args = parser.parse_args()

    try:
        working_directory = os.getenv('PROJECT_WORKING_DIR', default=None)
        data_directory = os.getenv('PROJECT_DATA_DIR', default=None)
        references_directory = os.getenv('PROJECT_REFERENCES_DIR', default=None)
        results_directory = os.getenv('PROJECT_RESULTS_DIR', default=None)
        utils_directory = os.getenv('PROJECT_UTILS_DIR', default=None)

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

    # Ensure onethousandgenomes_seq directory exists
    onethousandgenomes_seq = os.path.join(references_directory, "onethousandgenomes_seq")
    logging.info(f"onethousandgenomes_seq directory: {onethousandgenomes_seq}")
    os.makedirs(onethousandgenomes_seq, exist_ok=True)

    # Prompt user for chromosome selection
    base_url = "https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage/working/20220422_3202_phased_SNV_INDEL_SV"
    selection, chromosomes = prompt_chromosome_selection()

    # logging.info selection and chromosomes
    logging.info(f"You selected option {selection}.")
    logging.info(f"Chromosome(s) to process: {chromosomes}")
    
    # Check for the '--only-index' flag to decide which action to perform.
    if args.only_index:
        logging.info("Index-only mode activated. Indexing previously downloaded files.")
        index_files(chromosomes, onethousandgenomes_seq)
    else:
        download_files(base_url, chromosomes, onethousandgenomes_seq)

    logging.info("All tasks completed.")

if __name__ == "__main__":
    main()
