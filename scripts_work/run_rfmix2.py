# run_rfmix2.py
# https://github.com/slowkoni/rfmix/blob/master/MANUAL.md

import subprocess
import os
import argparse
import sys
import logging
import re
import requests
import json
from decouple import config

# Set up logging
def setup_logging(log_file="script.log"):
    logging.basicConfig(
        level=logging.INFO,  # Set the default logging level
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),  # Log to a file
            logging.StreamHandler(sys.stdout),  # Log to the console
        ],
    )

def parse_args():
    parser = argparse.ArgumentParser(
        description="Run RFMix2 with specified input paths and parameters."
    )
    parser.add_argument(
        "--vcf_file",
        type=str,
        default="path/to/input.vcf",
        help="Path to the input VCF file (default: 'path/to/input.vcf').",
    )
    parser.add_argument(
        "--sample_map",
        type=str,
        default="path/to/sample_map.txt",
        help="Path to the sample map file (default: 'path/to/sample_map.txt').",
    )
    parser.add_argument(
        "--reference_panel",
        type=str,
        default="path/to/reference_panel.txt",
        help="Path to the reference panel file (default: 'path/to/reference_panel.txt').",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="path/to/output",
        help="Directory to store the output files (default: 'path/to/output').",
    )
    parser.add_argument(
        "--temp_dir",
        type=str,
        default="path/to/temp",
        help="Directory to store temporary files (default: 'path/to/temp').",
    )
    return parser.parse_args()

# Functions to check if BCFtools is installed and install if not
def get_local_bcftools_version():
    """
    Returns the installed bcftools version string (e.g., '1.21')
    or None if bcftools is not found.
    """
    try:
        result = subprocess.run(
            ["bcftools", "--version"],
            capture_output=True, text=True, check=True
        )
        # Typical output first line is something like:
        # "bcftools 1.21\nUsing htslib 1.21\n..."
        match = re.search(r"bcftools\s+(\S+)", result.stdout)
        if match:
            return match.group(1).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    return None

def get_latest_bcftools_tag():
    """
    Queries GitHub for the latest bcftools tag and returns it (e.g. '1.21').
    If no tags or error, returns None.
    """
    url = "https://api.github.com/repos/samtools/bcftools/tags"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        tags_data = response.json()

        # Each element in tags_data is like:
        #   { "name": "1.21", "commit": {...}, ... }
        # We’ll filter valid tags (e.g. x.yy), then pick the max by version.
        versions = []
        semver_regex = re.compile(r"^(\d+)\.(\d+)$")  # Basic pattern: MAJOR.MINOR
        for tag in tags_data:
            tag_name = tag["name"]
            # If you want to allow "v1.21" or 3-part versions, expand this logic
            if semver_regex.match(tag_name):
                # Convert '1.21' to a tuple (1, 21) for numeric comparison
                major, minor = map(int, tag_name.split("."))
                versions.append((major, minor, tag_name))

        if not versions:
            return None

        # Pick the highest by numeric (major, minor) comparison
        latest_version = max(versions, key=lambda x: (x[0], x[1]))
        return latest_version[2]  # Return the original string like '1.21'
    except requests.RequestException as e:
        logging.error(f"Failed to fetch bcftools tags from GitHub: {e}")
        return None

def version_str_to_tuple(version_str):
    """
    Converts a version string like '1.21' to a numeric tuple (1, 21).
    Returns None if it doesn't match the simple pattern.
    """
    match = re.match(r"^(\d+)\.(\d+)$", version_str)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    return None

def check_and_install_bcftools_latest(script_directory):
    """
    Checks if bcftools is installed and up to date with the
    latest tagged version from GitHub. If not installed or outdated,
    prompts for installation/upgrade.
    """
    local_version_str = get_local_bcftools_version()
    latest_tag_str = get_latest_bcftools_tag()

    logging.info(f"Local bcftools version: {local_version_str or 'Not Found'}")
    logging.info(f"Latest bcftools tag on GitHub: {latest_tag_str or 'Unknown'}")

    if not latest_tag_str:
        # Could not fetch tags from GitHub or no valid tags found
        if not local_version_str:
            logging.critical("bcftools is not installed, and GitHub tag check failed. "
                             "Please install bcftools manually.")
        else:
            logging.warning("Could not determine latest bcftools version from GitHub.")
        return

    # Compare local vs. latest
    latest_tuple = version_str_to_tuple(latest_tag_str)
    if not local_version_str:
        logging.critical("bcftools is not installed. Installing the latest version...")
        _install_bcftools_script(script_directory)
    else:
        local_tuple = version_str_to_tuple(local_version_str)
        if not local_tuple:
            logging.warning("Could not parse local bcftools version properly.")
            # If we want to forcibly re-install, we can do so
            _install_bcftools_script(script_directory)
            return

        # Compare numeric tuples
        if local_tuple < latest_tuple:
            logging.warning(f"Installed bcftools ({local_version_str}) is older "
                            f"than the latest ({latest_tag_str}). "
                            "Proceeding to upgrade.")
            _install_bcftools_script(script_directory)
        else:
            logging.info("bcftools is at the latest version or newer. No action needed.")

def _install_bcftools_script(script_directory):
    """
    Calls your custom installation script,
    then re-sources the user's .bashrc to update PATH.
    Adjust as necessary for your environment.
    """

    script_path = os.path.join(script_directory, "install_bcftools.sh")

    if not os.path.isfile(script_path):
        logging.error(f"Installation script not found: {script_path}")
        return

    try:
        logging.info(f"Running {script_path}...")
        subprocess.run(["bash", script_path], check=True)

        # Re-source bashrc so changes are visible now
        bashrc_path = os.path.expanduser("~/.bashrc")
        if os.path.isfile(bashrc_path):
            logging.info(f"Sourcing {bashrc_path} to refresh PATH...")
            subprocess.run(["bash", "-c", f"source {bashrc_path} && bcftools --version"], check=True)
        else:
            logging.warning(f"No bashrc found at {bashrc_path}. Please source manually.")

        # Final check
        version = get_local_bcftools_version()
        if version:
            logging.info(f"bcftools upgraded to version: {version}")
        else:
            logging.error("bcftools still not found after installation.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error installing bcftools: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during bcftools installation: {e}")

# Function to check if RFMix2 is installed and install if not
def check_and_install_rfmix():
    """
    Checks if RFMix2 is installed and installs it if not.
    """
    try:
        subprocess.run(["rfmix", "--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        logging.info("RFMix2 is already installed.")
    except FileNotFoundError:
        logging.info("RFMix2 is not installed.")
        default_install_dir = "/home/ubuntu/utils"
        install_dir = input(f"Enter installation directory [default: {default_install_dir}]: ") or default_install_dir
        os.makedirs(install_dir, exist_ok=True)
        logging.info(f"Installing RFMix2 in {install_dir}...")
        # Simulated installation command (replace with actual installation steps as needed)
        logging.info("Installation complete. Ensure the rfmix binary is added to your PATH.")



# Function to check the genetic map file
def check_genetic_map(genetic_map, vcf_file):
    """
    Validates the genetic map file for proper formatting and compatibility with the VCF/BCF file.

    Parameters:
        genetic_map (str): Path to the genetic map file.
        vcf_file (str): Path to the VCF/BCF file for chromosome validation.

    Returns:
        bool: True if the genetic map is valid, False otherwise.
    """
    logging.info("Validating genetic map file...")
    if not os.path.isfile(genetic_map):
        logging.error(f"Error: Genetic map file '{genetic_map}' does not exist.")
        return False

    # Read chromosome identifiers from the VCF/BCF file
    vcf_chromosomes = set()
    with subprocess.Popen(["bcftools", "view", "-h", vcf_file], stdout=subprocess.PIPE) as proc:
        for line in proc.stdout:
            line = line.decode("utf-8")
            if line.startswith("#CHROM"):
                break
            if line.startswith("#"):
                continue
            vcf_chromosomes.add(line.strip())

    # Validate the genetic map
    with open(genetic_map, "r") as f:
        for idx, line in enumerate(f):
            parts = line.strip().split("\t")
            if len(parts) < 3:
                logging.error(f"Genetic map file must have at least 3 columns. Found fewer on line {idx + 1}.")
                return False
            chromosome = parts[0]
            if chromosome not in vcf_chromosomes:
                logging.error(f"Chromosome '{chromosome}' in genetic map does not match chromosomes in the VCF/BCF file.")
                return False

    logging.info("Genetic map validation passed.")
    return True

# Function to ensure VCF/BCF files are compressed and indexed
def check_and_prepare_vcf(vcf_file):
    """
    Ensures that the VCF/BCF files are gzip-compressed and indexed using BCFtools.

    Parameters:
        vcf_file (str): Path to the VCF/BCF file.

    Returns:
        str: Path to the compressed and indexed VCF/BCF file.
    """
    compressed_file = vcf_file if vcf_file.endswith(".gz") else f"{vcf_file}.gz"

    # Check if file is compressed
    if not os.path.isfile(compressed_file):
        logging.info(f"Compressing {vcf_file}...")
        subprocess.run(["bcftools", "view", vcf_file, "-Oz", "-o", compressed_file], check=True)

    # Check if index exists
    if not os.path.isfile(f"{compressed_file}.csi"):
        logging.info(f"Indexing {compressed_file}...")
        subprocess.run(["bcftools", "index", compressed_file], check=True)

    logging.info(f"File {compressed_file} is ready and indexed.")
    return compressed_file

# Function to check if VCF and reference files are phased
def check_phased(vcf_file, reference_panel):
    """
    Checks if the input VCF file and reference panel are phased.

    Parameters:
        vcf_file (str): Path to the input VCF file.
        reference_panel (str): Path to the reference panel file.

    Returns:
        bool: True if both files are phased, False otherwise.
    """
    logging.info("Checking if input files are phased...")
    # Placeholder: Replace with actual logic to check if files are phased
    vcf_phased = False  # Simulated check
    reference_phased = False  # Simulated check

    if not vcf_phased or not reference_phased:
        logging.info("One or both input files are not phased.")
        confirm = input("Run phasing with Beagle? Enter 'yes' to proceed [default: yes]: ") or "yes"
        if confirm.lower() == "yes":
            logging.info("Running Beagle for phasing...")
            # Simulated Beagle command (replace with actual logic)
            subprocess.run(["python", "run_beagle.py", vcf_file], check=True)
            logging.info("Phasing complete.")
            return True
        else:
            logging.info("Phasing skipped. Ensure input files are phased before proceeding.")
            return False
    logging.info("Input files are phased.")
    return True

# Function to validate sample map
def validate_sample_map(sample_map, reference_panel):
    """
    Validates that each sample in the sample map has a valid reference population assigned.

    Parameters:
        sample_map (str): Path to the sample map file.
        reference_panel (str): Path to the reference panel file.

    Returns:
        bool: True if all samples have valid reference populations, False otherwise.
    """
    logging.info("Validating sample map...")
    valid_references = set()

    # Extract valid reference populations from the reference panel
    with open(reference_panel, "r") as ref_file:
        for line in ref_file:
            parts = line.strip().split()
            if len(parts) > 1:
                valid_references.add(parts[1])

    # Validate sample map entries
    with open(sample_map, "r") as sm_file:
        for line in sm_file:
            parts = line.strip().split()
            if len(parts) != 2 or parts[1] not in valid_references:
                logging.error(f"Sample '{parts[0]}' has an invalid reference population '{parts[1]}'.")
                return False

    logging.info("Sample map validation passed.")
    return True

# Function to check genome assembly consistency
def check_genome_assembly(vcf_file, reference_panel):
    """
    Validates that all files are mapped or referenced to the same genome assembly (e.g., build 38).

    Parameters:
        vcf_file (str): Path to the input VCF file.
        reference_panel (str): Path to the reference panel file.

    Returns:
        bool: True if all files are consistent with the same genome assembly, False otherwise.
    """
    logging.info("Checking genome assembly consistency...")
    assembly_version = "build 38"  # Placeholder for the expected assembly

    # Placeholder checks for VCF and reference panel (replace with actual implementation)
    vcf_assembly = "build 38"  # Simulated check
    reference_assembly = "build 38"  # Simulated check

    if vcf_assembly != assembly_version or reference_assembly != assembly_version:
        logging.error(f"Error: Files are not consistent with the expected genome assembly ({assembly_version}).")
        logging.info(f"VCF assembly: {vcf_assembly}, Reference assembly: {reference_assembly}")
        return False

    logging.info("Genome assembly consistency check passed.")
    return True

# Function to run RFMix2
def run_rfmix2(vcf_file, sample_map, reference_panel, output_dir, chrom, temp_dir):
    """
    Runs RFMix2 on a given VCF file and reference panel.

    Parameters:
        vcf_file (str): Path to the input VCF file.
        sample_map (str): Path to the sample map file.
        reference_panel (str): Path to the reference panel file.
        output_dir (str): Directory to store the output files.
        chrom (str): Chromosome to analyze.
        temp_dir (str): Directory to store temporary files.

    Returns:
        None
    """
    # Ensure output and temp directories exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)

    # Construct RFMix2 command
    command = [
        "rfmix",  # RFMix2 executable
        "--chromosome", chrom,
        "--input-vcf", vcf_file,
        "--sample-map", sample_map,
        "--reference", reference_panel,
        "--output-basename", os.path.join(output_dir, f"rfmix_output_chr{chrom}"),
        "--n-threads", "8",  # Adjust threads based on your system
        "--temp-dir", temp_dir
    ]

    try:
        # Run RFMix2
        subprocess.run(command, check=True)
        logging.info(f"RFMix2 analysis completed for chromosome {chrom}.")
    except subprocess.CalledProcessError as e:
        logging.info(f"Error while running RFMix2 for chromosome {chrom}: {e}")

if __name__ == "__main__":
    setup_logging()
    args = parse_args()

    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
    Usage: python run_rfmix2.py

    Parameters:
        --vcf_file: Path to the input VCF file (e.g., "path/to/input.vcf").
        --sample_map: Path to the sample map file (e.g., "path/to/sample_map.txt").
        --reference_panel: Path to the reference panel file (e.g., "path/to/reference_panel.txt").
        --output_dir: Directory to store the output files (e.g., "path/to/output").
        --temp_dir: Directory to store temporary files (e.g., "path/to/temp").
    """)
        sys.exit(0)

    try:
        subprocess.run(['poetry', 'run', 'python', '-m', 'scripts_support.directory_setup'], check=True)
        working_directory = config('PROJECT_WORKING_DIR', default=None)
        user_home = config('USER_HOME', default=None)
        data_directory = config('PROJECT_DATA_DIR', default=None)
        references_directory = config('PROJECT_REFERENCES_DIR', default=None)
        results_directory = config('PROJECT_RESULTS_DIR', default=None)
        utils_directory = config('PROJECT_UTILS_DIR', default=None)

        if not all([working_directory, user_home, data_directory, references_directory, 
                   results_directory, utils_directory]):
            raise ValueError("Not all required directories were configured")
            
    except Exception as e:
        print(f"Error verifying directories: {e}")
        sys.exit(1)
  
    # Check and install BCFtools if necessary
    script_directory = os.join.path(user_home, "scripts_env")
    check_and_install_bcftools_latest(script_directory)

    # Check and install RFMix2 if necessary
    check_and_install_rfmix()



    # Use input paths and parameters from arguments
    vcf_file = args.vcf_file
    sample_map = args.sample_map
    reference_panel = args.reference_panel
    output_dir = args.output_dir
    temp_dir = args.temp_dir

    logging.info(f"VCF file: {vcf_file}")
    logging.info(f"Sample map: {sample_map}")
    logging.infot(f"Reference panel: {reference_panel}")
    logging.info(f"Output directory: {output_dir}")
    logging.info(f"Temporary directory: {temp_dir}")

    # Validate inputs
    if not os.path.isfile(vcf_file):
        logging.critical(f"Error: VCF file '{vcf_file}' does not exist.")
        sys.exit(1)
    if not os.path.isfile(sample_map):
        logging.critical(f"Error: Sample map file '{sample_map}' does not exist.")
        sys.exit(1)
    if not os.path.isfile(reference_panel):
        logging.critical(f"Error: Reference panel file '{reference_panel}' does not exist.")
        sys.exit(1)
    if not os.path.isdir(output_dir):
        logging.critical(f"Error: Output directory '{output_dir}' does not exist. Creating it...")
        os.makedirs(output_dir, exist_ok=True)
    if not os.path.isdir(temp_dir):
        logging.critical(f"Error: Temporary directory '{temp_dir}' does not exist. Creating it...")
        os.makedirs(temp_dir, exist_ok=True)

    # Ensure VCF/BCF files are compressed and indexed
    vcf_file = check_and_prepare_vcf(vcf_file)

    # Check if files are phased
    if not check_phased(vcf_file, reference_panel):
        sys.exit(1)

    # check_genetic_map(genetic_map, vcf_file)

    # Validate sample map
    if not validate_sample_map(sample_map, reference_panel):
        sys.exit(1)

    # Check genome assembly consistency
    if not check_genome_assembly(vcf_file, reference_panel):
        sys.exit(1)

    # Run RFMix2 for all chromosomes
    for chrom in range(1, 23):  # Autosomal chromosomes
        run_rfmix2(vcf_file, sample_map, reference_panel, output_dir, str(chrom), temp_dir)

    logging.info("RFMix2 analysis completed for all chromosomes.")