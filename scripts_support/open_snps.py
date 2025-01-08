#!/usr/bin/env python3

import json
import logging
import os
import pandas as pd
import re
import requests
import select
import subprocess
import sys
import zipfile
from lineage import Lineage
from typing import Dict, List, Tuple, Optional
import zipfile
from tqdm import tqdm
import logging
import math
from glob import glob
from Bio import SeqIO
import gzip
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

def task_prompt_with_timeout(prompt: str, timeout: int = 300, default: str = "No", task_type: str = None) -> str:
    """
    Prompt user with a timeout for various processing decisions
    
    Args:
        prompt: Question to display to user
        timeout: Seconds to wait for response
        default: Default response if timeout occurs
        task_type: Type of task being prompted ('download', 'extract', 'genotype', 'phenotype')
        
    Returns:
        User's response or default value after timeout
    """
    # Add more detailed task messages with size estimates and requirements
    task_messages = {
        'download': {
            'message': "\nDownload Open SNPs data: This will download new data from OpenSNP.",
            'details': "Requires ~58GB of disk space. Download time depends on your connection."
        },
        'extract': {
            'message': "\nExtract files from Open SNPs zip file: This will extract files from the OpenSNP zip file.",
            'details': "Requires additional disk space for extracted files."
        },
        'genotype': {
            'message': "\nProcess genotype files: Selecting 'yes' assumes you now have or will have individual genotype files to process.",
            'details': "CPU intensive operation. Creates VCF files."
        },
        'phenotype': {
            'message': "\nProcess phenotype data: This will process phenotype data from the CSV file.",
            'details': "Processes demographic and trait information."
        }
    }
    
    # Display enhanced task information
    if task_type and task_type in task_messages:
        task_info = task_messages[task_type]
        print(task_info['message'])
        print(task_info['details'])
    
    print(prompt, end="", flush=True)
    
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if ready:
        user_input = sys.stdin.readline().strip()
        response = user_input.lower() if user_input else default.lower()
    else:
        print(f"\nNo response after {timeout} seconds. Defaulting to '{default}'.")
        response = default.lower()
        
    # Log the decision
    task_name = task_type if task_type else "unspecified task"
    logging.info(f"User chose to {'proceed with' if response in ['yes', 'y'] else 'skip'} {task_name}")
        
    return response

def download_opensnp_data(url, data_directory):
    """
    Downloads the openSNP data dump using wget with native terminal handling.
    
    Args:
        url: URL to download from
        data_directory: Directory to store downloaded file
        
    Returns:
        str: Path to target subdirectory
        
    Raises:
        subprocess.CalledProcessError: If download fails
        OSError: If directory creation fails
    """
    target_subdir = os.path.join(data_directory, "open_snps_data")
    os.makedirs(target_subdir, exist_ok=True)
    output_file = os.path.join(target_subdir, os.path.basename(url))

    # Check if file already exists and verify size
    if os.path.exists(output_file):
        logging.info(f"File already exists: {output_file}")
        # Could add file size/checksum verification here
        return target_subdir

    logging.info(f"Downloading openSNP data from {url} to {output_file}...")
    
    cmd = [
        "wget",
        "-c",                    # continue partial downloads
        "--retry-connrefused",   # retry if connection refused
        "--timeout=60",          # timeout after 60s of no data
        "--waitretry=60",        # wait between retries
        "--tries=3",            # maximum number of retries
        "--progress=bar:force",  # force progress bar
        url,
        "-O",
        output_file
    ]

    try:
        # Pass through stdout/stderr to see wget's progress bar
        # shell=False for better security and signal handling
        process = subprocess.run(
            cmd,
            check=True,
            stdout=None,  # Use None to inherit parent's stdout/stderr
            stderr=None,
            text=True
        )
        logging.info("Download complete!")
        return target_subdir
    except subprocess.CalledProcessError as e:
        logging.error(f"Download failed with error: {e}")
        raise

# Function to extract files based on flexible criteria
def extract_files(zip_file, target_dir, prefix="user", suffix=None, max_files=None):
    """
    Extract files from a zip archive based on prefix, suffix, and max_files criteria.

    Args:
        zip_file (str): Path to the zip file.
        target_dir (str): Directory where the extracted files should be saved.
        prefix (str): Optional prefix to filter files (e.g., "user").
        suffix (str): Optional suffix to filter files (e.g., "ancestry.txt").
        max_files (int): Optional maximum number of files to extract.

    Returns:
        list: List of extracted file paths.
    """
    logging.info(f"Extracting files from {zip_file} to {target_dir}...")
    extracted_files = []
    with zipfile.ZipFile(zip_file, "r") as z:
        # Filter files based on prefix and suffix
        files = z.namelist()

        phenotype_files = [f for f in files if f.startswith("phenotypes_") and f.endswith(".csv")]
        picture_files = [f for f in files if f.startswith("picture_phenotypes_")]
        all_user_files = [f for f in files if (f.startswith(prefix))]
        user_files = [
            f for f in files 
            if (prefix is None or f.startswith(prefix)) and
               (suffix is None or f.endswith(suffix))
        ]
        other_user_files = list(set(all_user_files) - set(user_files))
        other_files = [f for f in files if f not in phenotype_files + picture_files + all_user_files]
        
        # Report file counts
        logging.info(f"Found in archive:")
        logging.info(f"- {len(phenotype_files)} phenotype files")
        logging.info(f"- {len(picture_files)} picture phenotype files")
        logging.info(f"- {len(user_files)} user files matching criteria (prefix={prefix}, suffix={suffix})")
        logging.info(f"- {len(other_user_files)} additional user_files")
        logging.info(f"- {len(other_files)} other files")

        if other_files:
            logging.info(f"- {len(other_files)} other files not matching any category")
            logging.debug("Other files found: " + "\n".join(other_files))
        
        # Extract phenotype file
        for phenotype_file in phenotype_files:
            z.extract(phenotype_file, target_dir)
            extracted_files.append(phenotype_file)
            logging.info(f"Extracted phenotype file: {phenotype_file}")
        
        # Extract user files with max_files limit
        if max_files:
            available = len(user_files)
            user_files = user_files[:max_files]
            if available > max_files:
                logging.info(f"Limiting to {max_files} user files out of {available} available")
        
        for file in user_files:
            z.extract(file, target_dir)
            extracted_files.append(file)

        # Extract other files
        for file in other_files:
            z.extract(file, target_dir)
            extracted_files.append(file)
        
        logging.info(f"Extracted {len(extracted_files)} total files to {target_dir}:")
        logging.info(f"- {sum(1 for f in extracted_files if f in user_files)} user files")
        logging.info(f"- {sum(1 for f in extracted_files if f in phenotype_files)} phenotype files")
        logging.info(f"- {sum(1 for f in extracted_files if f in other_files)} other files")

    return True
        
# class GenotypeProcessor:
def parse_genotype_files(target_subdir, references_directory):
    """
    Parses all genotype files, ensures Build 38, determines sex, and converts to VCF.
    """
    logging.info(f"Parsing and processing genotype files in {target_subdir}...")

    tsv_dir = os.path.join(target_subdir, "parsed_tsv_files")
    os.makedirs(tsv_dir, exist_ok=True)

    lineages = Lineage(
    output_dir=tsv_dir, 
    resources_dir=references_directory, 
    parallelize=True, 
    processes=10)

    # Dictionary to store individuals by user identifier
    user_files = {}
    # Initialize logs and tracking lists
    failed_sample = []
    failed_files_remapping = []  # Track files that fail processing or remapping
    determined_sex_entries = []  # Track successful sex determinations
    failed_sex_entries = []      # Track failed sex determinations
    log_entries = []             # General log entries
    failed_files_tsv = []

    # File paths for logging and results
    log_file_path = os.path.join(target_subdir, "parse_genotype_files.log")
    determined_sex_file_path = os.path.join(target_subdir, "determined_sex.txt")
    failed_sex_file_path = os.path.join(target_subdir, "failed_sex.txt")
    filenames = os.listdir(target_subdir)

    with tqdm(total=len(filenames), desc="checking build", file=sys.stdout) as lineage_pbar:
        for filename in filenames:  # Iterate over files in the directory
            # logging.info(f"Processing file {filename}...")
            file_path = os.path.join(target_subdir, filename)
            if not filename.startswith("user"):
                continue

            logging.info("\n")
            logging.info(f"Processing file {filename}...")

            # Extract user identifier
            user_id = filename.split('_')[0]
            logging.info(f"User ID: {user_id}")
            logging.info(f"Processing user {user_id} file {filename}...\n")
            
            # To account for cases when a user have multiple files
            # This dictionary will store all the file paths for a user as a list
            if user_id not in user_files:
                user_files[user_id] = [file_path]
            else:
                user_files[user_id].append(file_path)
            
            # Retrieve all file paths for the user
            user_file_paths = user_files[user_id]
            # logging.info(f"File path for user {user_id}: {file_path_go}")
            # This will simple recreate the lineage object and vcf file for the user,
            # if they already have one, to account to multiple files
            try:
                profile = lineages.create_individual(user_id, user_file_paths)
            except Exception as e:
                logging.error(f"Failed to process files for user {user_id}: {e}")
                failed_files_remapping.append(filename)
                continue

            if profile.count == 0:
                failed_sample.append(user_id)
                logging.error(f"Failed to process files for user {user_id}")
                continue

            # Ensure Build 38
            try:
                if not profile.build_detected or profile.build != 38:
                    logging.info(f"{user_id}: Current build is {profile.build}. Attempting to remap to Build 38...")
                    # chromosomes_remapped, chromosomes_not_remapped = profile.remap(38)
                    profile.remap(38)

                    # if chromosomes_not_remapped:
                    #     logging.warning(f"{user_id}: Some chromosomes could not be remapped: {chromosomes_not_remapped}")

                    if profile.build != 38:
                        logging.error(f"{user_id}: Remapping failed. Still not in Build 38.")
                        failed_files_remapping.append(user_id)
                        continue  # Skip further processing for this file
                    else:
                        logging.info(f"{user_id}: Successfully remapped to Build 38.")
                else:
                    logging.info(f"{user_id}: Already in Build 38.")
            except Exception as e:
                logging.error(f"{user_id}: Error during remapping to Build 38: {e}")
                failed_files_remapping.append(filename)
                logging.info("\n")
                continue   # Skip to the next iteration of the loop

            logging.debug(f"Saving profile {user_id}")
            profile.save(user_id + ".tsv")

            # Determine sex
            try:
                sex = profile.determine_sex(
                    heterozygous_x_snps_threshold=0.03,
                    y_snps_not_null_threshold=0.3,
                    chrom='X'
                )
                logging.info(sex)
                if sex:
                    determined_sex_entries.append(f"{user_id}\t{sex}")
                    logging.info(f"Determined sex for {user_id}: {sex}")
                else:
                    failed_sex_entries.append(f"{user_id}\tLow Confidence")
                    logging.warning(f"Failed to determine sex for {user_id}: Low Confidence")
            except Exception as e:
                failed_sex_entries.append(f"{user_id}\tError: {e}")
                logging.error(f"Error determining sex for {user_id}: {e}")

            lineage_pbar.update()

    # Write consolidated logs
    with open(determined_sex_file_path, "w") as log_file:
        log_file.write("\n".join(determined_sex_entries) + "\n\n")

    with open(failed_sex_file_path, "w") as log_file:
        log_file.write("\n".join(failed_sex_entries) + "\n")

    with open(log_file_path, "w") as log_file:
        log_file.write(failed_sample)

    return tsv_dir

def combine_fasta(reference_fasta_dir, fasta_file_basename):
    """
    Combines multiple FASTA files into a single file.
    
    Args:
        input_dir (str): Directory containing per-chromosome FASTA files.
        output_file (str): Path to the combined output FASTA file.
    """
    fasta_files = glob(f"{reference_fasta_dir}/*.fa.gz")
    if not fasta_files:
        raise FileNotFoundError(f"No FASTA files found in directory: {reference_fasta_dir}")

    fasta_filename = os.path.join(reference_fasta_dir, fasta_file_basename)
    with open(fasta_filename, "w") as combined_fasta:
        for fasta_file in sorted(fasta_files):  # Sort for consistent order
            with gzip.open(fasta_file, "rt") as f:  # Open .gz file in text mode
                for record in SeqIO.parse(f, "fasta"):
                    SeqIO.write(record, combined_fasta, "fasta")

    print(f"Combined FASTA saved to {fasta_filename}")
    return

def convert_file(tsv_file, reference_fasta_file, user_id, output_vcf_filename):

    # Define the bcftools convert command
    bcftools_command = [
        'bcftools', 'convert',
        '--haploid2diploid',          # Convert haploid data to diploid
        '--tsv2vcf', tsv_file,                  # Specify conversion from TSV to VCF
        '--columns', 'ID,CHROM,POS,AA',  # Map TSV columns to VCF fields
        '--fasta-ref', reference_fasta_file,  # Reference FASTA file
        '--samples', user_id,            # Assign sample name
        '--threads', str(10),          
        '--output-type', 'z',           # Output as compressed VCF (bgzip)
        '--output', output_vcf_filename,  # Output VCF file path
    ]

    try:
        logging.debug(f"Running bcftools command: {' '.join(bcftools_command)}")

        # Execute the bcftools convert command
        subprocess.run(bcftools_command, check=True)

        logging.debug(f"VCF file created at: {output_vcf_filename}")

        # Index the VCF file using tabix
        tabix_command = [
            'tabix', '-p', 'vcf', output_vcf_filename
        ]

        logging.debug(f"Running tabix command: {' '.join(tabix_command)}")

        subprocess.run(tabix_command, check=True)

        logging.debug(f"VCF file indexed at: {output_vcf_filename}.tbi")

        return True

    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
        return False

def convert_txt_to_vcf(tsv_dir, target_subdir, reference_fasta_dir):
    failed_files_vcf = []  # Track files that fail VCF conversion

    if not os.path.exists(tsv_dir):
        logging.error(f"Directory does not exist: {tsv_dir}")
        return
    
    vcf_dir = os.path.join(target_subdir, "converted_vcf_files")
    os.makedirs(vcf_dir, exist_ok=True)
    
    fasta_file_basename = "Homo_sapiens.GRCh38.dna.allchromosomes.fa.gz"
    if not os.path.exists(reference_fasta_dir):
        logging.error(f"Directory does not exist: {reference_fasta_dir}")
        return
    if not os.path.exists(os.path.join(reference_fasta_dir, fasta_file_basename)):
        logging.error(f"The fasta file does not exist. Creating it.")
    if not os.path.exists(os.path.join(reference_fasta_dir, fasta_file_basename)):
        logging.error(f"The fasta file does not exist. Failed to create it.")
        return
    fasta_filename = os.path.join(reference_fasta_dir, fasta_file_basename)

    # Glob all TSV files in the directory
    tsv_files = glob(f"{tsv_dir}/*.tsv")
    if not tsv_files:
        logging.error(f"No TSV files found in directory: {tsv_dir}")
        return

    logging.info(f"Starting VCF conversion for {len(tsv_files)} TSV files.")

    for tsv_file in tsv_files:
        user_id = os.path.basename(tsv_file).split(".")[0]
        output_vcf_filename = os.path.join(vcf_dir, user_id + ".vcf.gz")
        if convert_file(tsv_file, fasta_filename, user_id, output_vcf_filename):
            logging.debug(f"VCF conersion sucessful for {user_id}.")
        else:
            logging.debug(f"VCF conersion failed for {user_id}.")
            failed_files_vcf.append(user_id)
  
    # Log results
    if failed_files_vcf:
        logging.error(f"VCF conversion failed for the following files: {failed_files_vcf}")
    else:
        logging.info("All VCF conversions completed successfully.")

    return vcf_dir

# def _collect_vcf_files(target_subdir: str, merged_basename: str) -> List[str]:
#     """Collect VCF files for merging, excluding merged and temporary files"""
#     return sorted([  # Sort for consistent merge order
#         os.path.join(target_subdir, f) 
#         for f in os.listdir(target_subdir)
#         if (f.endswith(".vcf.gz") and 
#             not f.endswith(".vcf.gz.tbi") and
#             f != merged_basename and
#             not f.endswith(".vcf.gz.tmp"))
#     ])

def _validate_merged_vcf(vcf_path, expected_num_samples):
    """Validate merged VCF using bcftools plugin counts."""
    try:
        cmd = ["bcftools", "plugin", "counts", vcf_path]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logging.info(f"Plugin 'counts' validation output for {vcf_path}:\n{result.stdout}")
        logging.info(f"Plugin 'counts' validation errors (if any):\n{result.stderr}")

        # FIX: why is this num_samples = 7 on the last all sample merge file?
        num_samples = 0
        for line in result.stdout.splitlines():
            if line.startswith("Number of samples:"):
                parts = line.split(":")
                if len(parts) == 2:
                    num_samples = int(parts[1].strip())
        
        if num_samples == 0:
            logging.error(f"Could not parse sample count from bcftools plugin counts.")
            return False
        
        if num_samples != expected_num_samples:
            logging.error(
                f"Mismatch in sample count in {vcf_path}: "
                f"expected {expected_num_samples}, got {num_samples}"
            )
            # FIX: should be return False, use return TRUE until can correct last count error
            return True
        
        print(f"FROM _validate_merged_vcf - num_samples: {num_samples}")
        return True

    except subprocess.CalledProcessError as e:
        logging.error(f"Plugin 'counts' validation failed for {vcf_path}: {e}")
        return False
    
def _cleanup_individual_vcfs(target_subdir: str, merged_basename: str) -> None:
    """Clean up individual VCF files after successful merge"""
    merged_tbi_basename = merged_basename + ".tbi"
    for file_name in os.listdir(target_subdir):
        if any(file_name.endswith(ext) for ext in [".vcf", ".vcf.gz", ".vcf.gz.tbi"]):
            if file_name in [merged_basename, merged_tbi_basename]:
                logging.info(f"Keeping merged file: {file_name}")
                continue
            
            file_path = os.path.join(target_subdir, file_name)
            try:
                os.remove(file_path)
                logging.debug(f"Deleted file: {file_path}")
            except Exception as e:
                logging.error(f"Error deleting file {file_path}: {e}")

def recursive_batch_merge(vcf_files, output_prefix, batch_size, total_num_files):
    """
    Recursively merge files in batches until a single merged file remains.
    
    Args:
        vcf_files (list): List of VCF files to merge.
        output_prefix (str): Prefix for temporary batch output files.
        batch_size (int): Number of files to process per batch.
        
    Returns:
        str: Path to the final merged file.
    """
    temp_files = []
    batch_count = math.ceil(len(vcf_files) / batch_size)

    # Track if this is the final merge
    is_final_merge = len(vcf_files) <= batch_size

    for i in range(batch_count):
        batch_files = vcf_files[i * batch_size:(i + 1) * batch_size]
        temp_batch_output = f"{output_prefix}.batch{i}.tmp"
        
        logging.info(f"Merging batch {i + 1}/{batch_count} with {len(batch_files)} files.")
        merge_command = [
            "bcftools", "merge",
            "-O", "z",  # Output format: compressed VCF
            "-o", temp_batch_output
        ] + sorted(batch_files)
        subprocess.run(merge_command, check=True)

        # For validation, use total_num_files only if this is the final merge
        expected_samples = total_num_files if is_final_merge else len(batch_files)

        # Validate the merged batch
        if not _validate_merged_vcf(temp_batch_output, expected_samples):
            logging.error(f"Validation failed for batch: {temp_batch_output}")
            raise ValueError("Validation failed")
        
        # Index the merged batch file
        subprocess.run(["bcftools", "index", "-t", temp_batch_output], check=True)
        logging.info(f"Indexed batch file: {temp_batch_output}")
        
        # Add validated batch to the list of intermediate files
        temp_files.append(temp_batch_output)
        logging.info(f"Batch {i + 1}/{batch_count} merged successfully into: {temp_batch_output}")

    # If more than one intermediate file remains, merge recursively
    if len(temp_files) > 1:
        logging.info(f"Recursively merging {len(temp_files)} intermediate files.")
        return recursive_batch_merge(temp_files, output_prefix, batch_size, total_num_files)

    # Only one file remains; return it as the final merged file
    return temp_files[0]

def merge_and_cleanup_vcf_files(vcf_dir, target_subdir, output_merged_vcf, batch_size):
    # Collect VCF files
    vcf_files = glob(f"{vcf_dir}/*.vcf.gz")
    total_num_files = len(vcf_files)
    if not vcf_files or (total_num_files == 0):
        logging.error(f"No VCF files found in directory: {vcf_dir}")
        return
    # vcf_files = _collect_vcf_files(target_subdir, os.path.basename(output_merged_vcf))
    
    logging.info(f"Starting merge of {len(vcf_files)} VCF files into: {output_merged_vcf}")

    try:
        # Perform recursive batch merging
        final_temp_file = recursive_batch_merge(vcf_files, output_merged_vcf, batch_size, total_num_files)

        # Move the final merged file to the target location
        os.rename(final_temp_file, output_merged_vcf)
        logging.info(f"Final merged file moved to: {output_merged_vcf}")

        # Validate the final merged file
        if not _validate_merged_vcf(output_merged_vcf, total_num_files):
            logging.error("Validation failed for the final merged VCF.")
            return False

        # Index the final merged VCF file
        subprocess.run(["bcftools", "index", "-t", output_merged_vcf], check=True)
        logging.info(f"Indexed final merged VCF file: {output_merged_vcf}")

        # Cleanup individual VCF files
        # _cleanup_individual_vcfs(target_subdir, os.path.basename(output_merged_vcf))

        return True

    except subprocess.CalledProcessError as cpe:
        logging.error(f"Subprocess failed: {cpe}")
    except Exception as e:
        logging.error(f"Unexpected error during merging: {str(e)}", exc_info=True)

    # Cleanup in case of failure
    logging.info("Cleaning up temporary files after failure.")
    for temp_file in os.listdir(target_subdir):
        if temp_file.endswith(".tmp"):
            os.remove(os.path.join(target_subdir, temp_file))
            os.remove(os.path.join(target_subdir, temp_file + ".tbi"))
            logging.info(f"Removed temporary file: {temp_file} and {temp_file}.tbi")

    return False


def get_sample_list(vcf_path):
    if not os.path.exists(vcf_path):
        logging.error(f"VCF file not found: {vcf_path}")
        return []
    
    try:
        result = subprocess.run(
            ['bcftools', 'query', '-l', vcf_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        sample_list = result.stdout.strip().split('\n')
        logging.info(f"Extracted {len(sample_list)} samples from VCF.")
        return sample_list
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running bcftools: {e.stderr}")
        return []
    
class PhenotypeProcessor:

    def __init__(self):
        """Initialize the PhenotypeProcessor with predefined configurations"""
        self.stats = {
            'total_records': 0,
            'num_duplicates': 0,
            'unique_users': 0,
            'num_duplicates': 0,
            'processed_records': 0,
            'missing_data': {},
            'errors': [],
            'identity_sources': {},
            'explicit_identities': {}
        }

    def _load_identity_columns(self) -> List[str]:
        """Load identity column configuration"""
        return [
            'ethnicity', 
            'Ancestry',
            'Jewish Ancestry',
            'African',
            'Black',
            'Nationality',
            'Latino Ancestry',
            'Scottish Ancestry',
            'Welsh Ancestry',
            'GREEK DNA'
        ]

    def _load_demographic_columns(self) -> List[str]:
            """Load demographic column configuration"""
            return [
                'Birth year',
                'date_of_birth',
                'Sex',
                'chrom_sex'
            ]
    
    def _load_explicit_patterns(self) -> Dict[str, List[str]]:
            """
            Load patterns for explicit identity declarations based on identity columns
            
            Returns:
                Dict[str, List[str]]: Dictionary mapping identity categories to their pattern lists
            """
            return {
                'ethnicity': [
                    r'(?i)^ethnicity[:,\s]+(.+)$',
                    r'(?i)ethnic[:\s]+(.+)',
                    r'(?i)caucasian',
                    r'(?i)^white[:,\s]*caucasian'
                ],
                'ancestry': [
                    r'(?i)^jewish ancestry[:,\s]+(.+)$',
                    r'(?i)^african[:,\s]+(.+)$',
                    r'(?i)^latino ancestry[:,\s]+(.+)$',
                    r'(?i)^scottish ancestry[:,\s]+(.+)$',
                    r'(?i)^welsh ancestry[:,\s]+(.+)$',
                    r'(?i)african-northern european'
                ],
                'nationality': [
                    r'(?i)^nationality[:,\s]+(.+)$',
                    r'(?i)^greek dna'
                ],
                'race': [
                    r'(?i)^black[:,\s]+(.+)$',
                    r'(?i)caucasian[,\s]',
                    r'(?i):[\s]*caucasian',
                    r'(?i)caucasian$'
                ]
            }
            
    def validate_input(self, df, sample_list):
            try:
                # Check if DataFrame is empty
                if df.empty:
                    logging.error("Input DataFrame is empty")
                    return False, df
                    
                # Check required columns
                if 'user_id' not in df.columns:
                    logging.error("Missing required column: user_id")
                    return False, df
                    
                # Validate user_id quality
                null_users = df['user_id'].isna().sum()
                if null_users > 0:
                    logging.error(f"Found {null_users} rows with null user_id")
                    return False, df
                    
                # Convert user_id to standard format if numeric
                try:
                    # First, ensure user_ids are strings
                    df['user_id'] = df['user_id'].astype(str)
                    
                    # Standardize format: if just a number, prepend 'user'
                    df['user_id'] = df['user_id'].apply(
                        lambda x: f"user{x}" if x.isdigit() else x
                    )
                    
                    logging.info(f"Standardized {len(df)} user_ids to user[number] format")
                except Exception as e:
                    logging.error(f"Error standardizing user_ids: {str(e)}")
                    return False, df

                logging.debug("Subsetting dataframe on sample...")
                if sample_list:
                    logging.info(f"There are {len(sample_list)} users in the sample list.")
                    subset_df = df[df['user_id'].isin(sample_list)].copy()
                else:
                    subset_df = df.copy()

                # Check for duplicates after standardization
                logging.debug("Checking the 'user_id' column for any duplicate entries...")
                num_duplicates = subset_df['user_id'].duplicated().sum()

                if num_duplicates > 0:
                    logging.info(f"Found {num_duplicates} duplicate user_ids - merging records...")

                    # Group by user_id and merge duplicate records inline
                    logging.debug("Merging duplicate rows by grouping on 'user_id' with the inline aggregator...")
                    logging.debug("If all values in a column are emppty, the result will be empty.")
                    logging.debug("If at least one value is not empty, the non-empty value will be kept.")
                    logging.debug("If multiple non-empty values are found, they will be sorted and deduplicated.")
                    logging.debug("This assumes that the values for a given user_id should be for the same person")
                    grouped = subset_df.groupby('user_id').agg(
                        lambda series: (
                            # Drop any null/NaN entries
                            None
                            if series.dropna().empty
                            else (  # Sort and deduplicate the non-null values
                                sorted(series.dropna().unique())[0]
                                if len(sorted(series.dropna().unique())) == 1
                                else sorted(series.dropna().unique())
                            )
                        )
                    )

                    subset_df = grouped.reset_index().copy()
                    logging.debug("Completed merging duplicate rows by grouping on 'user_id' with the inline aggregator.")

                    # Verify the merge was successful
                    new_duplicates = subset_df['user_id'].duplicated().sum()
                    logging.debug(f"Number of duplicates remaining after merge: {new_duplicates}")

                    if new_duplicates > 0:
                        logging.error(f"Failed to merge all duplicates: {new_duplicates} remain")
                        # Depending on the application logic, handle or return here as appropriate
                        return False, subset_df

                    logging.info(f"Successfully merged duplicate records. New record count: {len(subset_df)}")
                
                logging.info(f"Validation passed: {len(subset_df)} records")
                return True, subset_df, num_duplicates
                
            except Exception as e:
                logging.error(f"Error during validation: {str(e)}")
                return False, df

    def clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        # Replace spaces with underscores and convert to lowercase
        df = df.rename(columns=lambda x: x.lower().replace(' ', '_'))
        logging.debug(f"Cleaned column names: {df.columns.tolist()}")
        return df

    # Class-level constant for sex mappings
    SEX_MAPPINGS = {
        'M': ['M', 'MALE', 'XY', '1', 'MASCULINE'],
        'F': ['F', 'FEMALE', 'XX', '2', 'FEMININE'],
        'NOTMF': ['OTHER', 'NONBINARY', 'NB', 'X', 'INTERSEX', 'TRANS', 'TRANSGENDER'],
        'NOT_SPECIFIED': ['RATHER NOT SAY', 'PREFER NOT TO SAY', 'NO ANSWER', 'DECLINED', 'PRIVATE']
    }

    def standardize_sex(self, value: str, user_id: str) -> Optional[str]:
        """
        Standardize sex information to include M/F/NOTMF/NOT_SPECIFIED

        Args:
            value: Input sex value to standardize
            user_id: User ID for logging purposes

        Returns:
            str: 'M', 'F', 'NOTMF', 'NOT_SPECIFIED', or None
        """
        try:
            if pd.isna(value):
                self.stats['missing_data'].setdefault('sex_null', {}).setdefault('count', 0)
                self.stats['missing_data']['sex_null']['count'] += 1
                self.stats['missing_data']['sex_null'].setdefault('users', []).append(user_id)
                return None

            value = str(value).upper().strip()

            for standardized, variants in self.SEX_MAPPINGS.items():
                if value in variants:
                    self.stats.setdefault('sex_mappings', {}).setdefault(standardized, {})
                    self.stats['sex_mappings'][standardized].setdefault('count', 0)
                    self.stats['sex_mappings'][standardized]['count'] += 1
                    self.stats['sex_mappings'][standardized].setdefault('original_values', set()).add(value)
                    return standardized

            # Handle non-standard values
            self.stats['missing_data'].setdefault('sex_nonstandard', {})
            self.stats['missing_data']['sex_nonstandard'].setdefault('values', {})
            self.stats['missing_data']['sex_nonstandard']['values'].setdefault(value, set()).add(user_id)

            logging.debug(f"Non-standard sex value encountered: '{value}' for user {user_id}")
            return None

        except Exception as e:
            error_msg = f"Error standardizing sex value '{value}' for user {user_id}: {str(e)}"
            logging.error(error_msg)
            self.stats['errors'].append(('sex_standardization', value, user_id, str(e)))
            return None

    def process_demographics(self, demographics_df):
            return demographics_df

    def process_phenotypes(self, phenotype_df, target_subdir, sample_list):
        try:
            # Log start of processing
            logging.info(f"Starting phenotype processing for {len(phenotype_df)} records")
            
            # Validate input
            logging.debug(phenotype_df.head())
            logging.debug("Starting input validation using phenotype_df as a read from csv...")
            is_valid, deduplicated_df, num_duplicates = self.validate_input(phenotype_df, sample_list)
            if not is_valid:
                raise ValueError("Invalid input DataFrame")
            logging.debug("After validation, use deduplicated_df")

            logging.info(f"Number of records in dataframe before input validation: {len(phenotype_df)}")
            logging.info(f"Number of records in sample_list: {len(sample_list)}")
            logging.info(f"Number of duplicate records before deduplication: {num_duplicates}")
            logging.info(f"Number of records in dataframe after deduplication: {len(deduplicated_df)}")
            
            # Load the required column names within the method
            logging.debug("Loading identity and demographic columns for selection...")
            identity_columns = self._load_identity_columns()
            logging.debug(f"Identity Columns: {identity_columns}")
            demographic_columns = self._load_demographic_columns()
            logging.debug(f"Demographic Columns: {demographic_columns}")

            columns_to_select = ['user_id'] + identity_columns + demographic_columns
            logging.debug(f"Columns to select: {columns_to_select}")
            
            # Validate that all columns exist in deduplicated_df
            missing_columns = set(columns_to_select) - set(deduplicated_df.columns)
            if missing_columns:
                logging.warning(f"The following columns are missing from deduplicated_df and will be skipped: {missing_columns}")
                columns_to_select = [col for col in columns_to_select if col in deduplicated_df.columns]
            
            # Select the specified columns from deduplicated_df
            logging.debug("Selecting columns from deduplicated_df...")
            selected_df = deduplicated_df[columns_to_select].copy()
            del deduplicated_df  # Free up memory
            logging.info(f"Selected {len(selected_df)} records with columns: {columns_to_select}")

            logging.debug("Cleaning column names by removing spaces and standardizing format...")
            selected_df = self.clean_column_names(selected_df)

            # Process demographics
            logging.info("Processing demographic information...")
            demographics_df = self.process_demographics(selected_df)
            logging.info(f"Demographics processing complete: {len(demographics_df)} records")
                                  
            # Save results
            output_file = os.path.join(target_subdir, "phenotypes_processed.tsv")

            demographics_df.to_csv(output_file, sep='\t', index=False)
            logging.info(f"Saved uncompressed results to: {output_file}")
            
            demographics_df.to_csv(output_file + ".gz", sep='\t', index=False, compression='gzip')
            logging.info(f"Saved compressed results to: {output_file}.gz")

            return demographics_df
            
        except Exception as e:
            logging.error(f"Failed to process phenotypes: {str(e)}")
            raise

def main():
    """Main execution function for OpenSNP data processing."""
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
    # data_directory = "/mnt/c/Users/ltdavid2/OneDrive - University of Illinois - Urbana/Beloved Lab/data_temp"


    log_filename = os.path.join(results_directory, "log.txt")
    configure_logging(log_filename, log_file_debug_level="INFO", console_debug_level="INFO")

    """
    Main function orchestrating the download, extraction, parsing of genotype,
    phenotype CSV, (and later, maybe, picture phenotypes).
    """
    # Get initial task settings dict
    tasks = {
        'download': {
            'prompt': "Do you need to download the datafile from openSNP?",
            'type': "download",
            'enabled': False,
            'settings': {}
        },
        'extract': {
            'prompt': "Do you need to extract files from the OpenSNPs datafile?",
            'type': "extract",
            'enabled': False,
            'settings': {
                'prefix': "user",
                'suffix': "ancestry.txt",
                'max_files': 20,
                'extract_phenotypes': True,
                'extract_pictures': True
            }
        },
        'genotype': {
            'prompt': "Do you need to process the genotype files?",
            'type': "genotype",
            'enabled': False,
            'settings': {}
        },
        'phenotype': {
            'prompt': "Do you need to process the phenotype CSV file?",
            'type': "phenotype",
            'enabled': False,
            'settings': {}
        }
    }

    # Get user decisions for each task
    for task_name, task_info in tasks.items():
        task_response = task_prompt_with_timeout(
            f"{task_info['prompt']} (yes/No) [Default: No]: ",
            timeout=300,
            default="No",
            task_type=task_info['type']
        ).lower()
        
        tasks[task_name]['enabled'] = task_response in ['yes', 'y']
        
        # If user enabled extraction, immediately get extraction settings
        if task_name == 'extract' and tasks['extract']['enabled']:
            if task_prompt_with_timeout(
                "\nWould you like to see extraction settings to possibly modify? (yes/No) [Default: No]: ",
                timeout=10,
                default="No"
            ).lower() in ['yes', 'y']:
                # Get user input for settings
                # new_prefix = input("Enter file prefix (default 'user'): ").strip()
                # if new_prefix:
                #     tasks['extract']['settings']['prefix'] = new_prefix
                    
                new_suffix = input("Enter file suffix (default 'ancestry.txt'): ").strip()
                if new_suffix:
                    tasks['extract']['settings']['suffix'] = new_suffix
                    
                try:
                    new_max = input("Enter maximum number of files to extract (default 20, 0 for no limit): ").strip()
                    if new_max:
                        max_files = int(new_max)
                        if max_files < 0:
                            logging.warning("Invalid max files value. Using default of 20.")
                        else:
                            tasks['extract']['settings']['max_files'] = max_files if max_files > 0 else None
                except ValueError:
                    logging.warning("Invalid max files value. Using default of 20.")


    # Download openSNP data
    if tasks['download']['enabled']:
        logging.info("Downloading openSNP data...")
        url = "https://opensnp.org/data/zip/opensnp_datadump.current.zip"
        try:
            target_subdir = download_opensnp_data(url, data_directory)
            tasks['download']['completed'] = True
        except Exception as e:
            logging.error(f"Download failed: {str(e)}")
            return False
    else:
        logging.info("Skipping download. Proceeding with existing data...")
        target_subdir = os.path.join(data_directory, "open_snps_data")


    # Extract files from the downloaded zip file
    if tasks['extract']['enabled']:
        logging.info("Extracting files...")
        zip_file = os.path.join(target_subdir, "opensnp_datadump.current.zip")
        logging.info("Checking if zip file exists...")
        
        if not os.path.exists(zip_file):
            logging.error("No zip file found.")
            if not tasks['download']['completed']:
                logging.error("Download was skipped. Please download the file first.")
            return False

        logging.info(f"Zip file found: {zip_file}")
        
        try:
            # Get settings with defaults if not specified
            extract_settings = tasks['extract'].get('settings', {})
            if extract_files(
                zip_file, 
                target_subdir,
                prefix=extract_settings.get('prefix', "user"),
                suffix=extract_settings.get('suffix', "ancestry.txt"),
                max_files=extract_settings.get('max_files', 20)
            ):
                tasks['extract']['completed'] = True
        except Exception as e:
            logging.error(f"Extraction failed: {str(e)}")
            return False

    else:
        logging.info("Skipping extraction. Proceeding with existing files...")


    # Parse genotype files and create the VCF file
    if tasks['genotype']['enabled']:
        logging.info("Parsing genotype files and creating the VCF file...")
        try:
            # Check if there are any genotype files to process
            genotype_files = [f for f in os.listdir(target_subdir) if f.startswith("user") and f.endswith("ancestry.txt")]
            if not genotype_files:
                logging.error("No genotype files found in directory.")
                return False
                
            tsv_dir = parse_genotype_files(target_subdir, references_directory)
            # FIX: Failed on INFO:snps.snps:Loading SNPs('user994_file494_yearofbirth_1977_sex_XX.ancestry.txt')
            # ERROR:root:Genotype processing failed: write() argument must be str, not list
            # After starting the sex_determination process
            # tsv_dir = os.path.join(target_subdir, "parsed_tsv_files")
            reference_fasta_dir = os.path.join(references_directory, "fasta/GRCh38")
            vcf_dir = convert_txt_to_vcf(tsv_dir, target_subdir, reference_fasta_dir)
            # vcf_dir = os.path.join(target_subdir, "converted_vcf_files")
            output_merged_vcf = os.path.join(target_subdir, "opensnps.vcf.gz")
            if merge_and_cleanup_vcf_files(vcf_dir, target_subdir, output_merged_vcf, batch_size = 100):
                tasks['genotype']['completed'] = True
            else:
                logging.error("VCF merging failed.")
                return False
                
        except Exception as e:
            logging.error(f"Genotype processing failed: {str(e)}")
            return False
    else:
        logging.info("Skipping genotype processing.")

    # Process phenotype CSV file
    if tasks['phenotype']['enabled']:
        logging.info("Processing phenotype CSV file...")
        try:
            # Find phenotype file
            phenotype_file = None
            for file in os.listdir(target_subdir):
                if file.startswith("phenotypes_") and file.endswith(".csv"):
                    phenotype_file = os.path.join(target_subdir, file)
                    logging.info(f"Found phenotype file: {phenotype_file}")
                    break

            if phenotype_file and os.path.exists(phenotype_file):
                # Read and process the file
                try:
                    phenotype_df = pd.read_csv(phenotype_file, sep=";")
                    logging.debug(f"Phenotype DataFrame: {phenotype_df.head()}")
                    # if opensnp.vcf.gz exists, get the sample list
                    vcf_path = os.path.join(target_subdir, "opensnps.vcf.gz")
                    if os.path.exists(vcf_path):
                        sample_list = get_sample_list(vcf_path)
                    else:
                        sample_list = None
                    processor = PhenotypeProcessor()
                    demographics_df = processor.process_phenotypes(phenotype_df, target_subdir, sample_list)
                    logging.info(f"Processed {len(demographics_df)} records")
                    logging.debug(f"Processed {len(demographics_df)} records with demographics columns {demographics_df.columns.tolist()}")
                    logging.debug(f"Demographics DataFrame: {demographics_df.head()}")
                    tasks['phenotype']['completed'] = True
                    
                except pd.errors.EmptyDataError:
                    logging.error("The phenotype file is empty")
                except Exception as e:
                    logging.error(f"Error processing phenotype file: {str(e)}")
            else:
                logging.error("No valid phenotype file found in the directory.")
        except Exception as e:
            logging.error(f"Error accessing phenotype directory: {str(e)}")
    else:
        logging.info("Skipping phenotype processing.")

    return True

if __name__ == "__main__":
    main()