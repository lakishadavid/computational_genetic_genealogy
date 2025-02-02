import os
import subprocess
import json
import sys
import logging
from inputimeout import inputimeout, TimeoutOccurred
from dotenv import load_dotenv
notebook_dir = os.getcwd()
project_root = os.path.dirname(notebook_dir)
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path, override=True)

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

def install_dependencies():
    """Install necessary dependencies using apt-get."""
    logging.info("Installing dependencies...")
    subprocess.run(["sudo", "apt-get", "update", "-qq", "-y"])
    subprocess.run(["sudo", "apt-get", "install", "-qq", "-y", "tabix", "bcftools", "default-jre", "wget", "unzip", "jq"])

def prompt_chromosome_selection():
    """Prompt the user to select chromosomes to process with a timeout and default option."""
    print("Choose an option for chromosomes to process:")
    print("a) Range: 1 to 22")
    print("b) Range: 1 to 22 plus X")
    print("c) Multiple chromosomes: 1 and 20 (default)")
    print("d) Single chromosome: chromosome 20")
    print("e) Single chromosomes: chromosome X")

    # Default selection if input times out
    default_selection = "c"

    try:
        selection = inputimeout(prompt="Enter your choice (a, b, c, d, or e): ", timeout=20).strip().lower()
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

    if selection not in options:
        logging.info("Invalid choice. Please choose a, b, c, d, or e.")
        sys.exit(1)

    return selection, options[selection]

def download_files(selection, base_url, chromosomes, destination_dir):
    """Download VCF and index files for the specified chromosomes."""
    for chromosome in chromosomes:
        vcf_filename = f"1kGP_high_coverage_Illumina.chr{chromosome}.filtered.SNV_INDEL_SV_phased_panel.vcf.gz"
        tbi_filename = f"{vcf_filename}.tbi"
        new_vcf_filename = f"onethousandgenomes_sequenced_phased.chr{chromosome}.vcf.gz"

        vcf_url = f"{base_url}/{vcf_filename}"
        tbi_url = f"{vcf_url}.tbi"

        if selection == "e":
            # Download VCF file
            logging.info(f"\nDownloading {vcf_filename}...")
            vcf_filename = f"1kGP_high_coverage_Illumina.chr{chromosome}.filtered.SNV_INDEL_SV_phased_panel.v2.vcf.gz"
            vcf_url = f"{base_url}/{vcf_filename}"
            vcf_path = os.path.join(destination_dir, new_vcf_filename)
            result = subprocess.run(["wget", "-O", vcf_path, vcf_url], stdout=None, stderr=None)
            if result.returncode != 0:
                logging.info(f"Failed to download {vcf_filename}. Skipping...")
                continue

            # Download TBI file
            logging.info(f"\nDownloading {tbi_filename}...")
            tbi_filename = f"{vcf_filename}.tbi"
            tbi_url = f"{vcf_url}.tbi"
            tbi_path = os.path.join(destination_dir, f"{new_vcf_filename}.tbi")
            result = subprocess.run(["wget", "-O", tbi_path, tbi_url], stdout=None, stderr=None)
            if result.returncode != 0:
                logging.info(f"Failed to download {tbi_filename}. Skipping...")
                continue
        else:
            # Download VCF file
            logging.info(f"\nDownloading {vcf_filename}...")
            vcf_path = os.path.join(destination_dir, new_vcf_filename)
            result = subprocess.run(["wget", "-O", vcf_path, vcf_url], stdout=None, stderr=None)
            if result.returncode != 0:
                logging.info(f"Failed to download {vcf_filename}. Skipping...")
                continue

            # Download TBI file
            logging.info(f"\nDownloading {tbi_filename}...")
            tbi_path = os.path.join(destination_dir, f"{new_vcf_filename}.tbi")
            result = subprocess.run(["wget", "-O", tbi_path, tbi_url], stdout=None, stderr=None)
            if result.returncode != 0:
                logging.info(f"Failed to download {tbi_filename}. Skipping...")
                continue

        # Confirm downloads
        if not os.path.isfile(vcf_path):
            logging.info(f"{vcf_filename} was not downloaded.")
            continue

        if not os.path.isfile(tbi_path):
            logging.info(f"{tbi_filename} was not downloaded.")
            continue

        logging.info(f"Successfully downloaded and verified files for chromosome {chromosome}.")

def main():
    # poetry run python -m scripts_support.onethousandgenomes_download

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

    # Step 2: Install dependencies
    install_dependencies()

    # Step 3: Ensure onethousandgenomes_seq directory exists
    onethousandgenomes_seq = os.path.join(references_directory, "onethousandgenomes_seq")
    logging.info(f"onethousandgenomes_seq directory: {onethousandgenomes_seq}")
    os.makedirs(onethousandgenomes_seq, exist_ok=True)

    # Step 4: Prompt user for chromosome selection
    base_url = "https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage/working/20220422_3202_phased_SNV_INDEL_SV"
    selection, chromosomes = prompt_chromosome_selection()

    # logging.info selection and chromosomes
    logging.info(f"You selected option {selection}.")
    logging.info(f"Chromosome(s) to process: {chromosomes}")

    # Step 5: Download files
    download_files(selection, base_url, chromosomes, onethousandgenomes_seq)

    logging.info("All tasks completed.")

if __name__ == "__main__":
    main()
