import os
import subprocess
import sys
import json
import zipfile
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging
from decouple import config


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def check_and_install_tools(tools):
    """
    Verifies that required tools are installed and installs them if they are missing.

    Parameters:
    - tools (list): List of required tools to check and install.
    """
    for tool in tools:
        result = subprocess.run(["which", tool], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print(f"Tool {tool} is not installed. Installing...")
            try:
                # Install using apt (for Ubuntu/Debian systems)
                subprocess.run(["sudo", "apt-get", "update"], check=True)
                subprocess.run(["sudo", "apt-get", "install", "-y", tool], check=True)
                print(f"Tool {tool} installed successfully.")
            except subprocess.CalledProcessError as e:
                raise EnvironmentError(f"Failed to install {tool}: {e}")
        else:
            print(f"Tool {tool} is already installed.")

def download_array_manifest(references_dir):
    print("Downloading and extracting Illumina manifest file...")
    # https://support.illumina.com/array/array_kits/infinium-global-diversity-array.html
    # https://support.illumina.com/downloads/infinium-global-diversity-array-v1-product-files.html

    # Define the URL and paths
    url = "https://webdata.illumina.com/downloads/productfiles/global-diversity-array/infinium-global-diversity-array-8-v1-0-D2-manifest-file-csv.zip"
    zip_file = os.path.join(references_dir, "infinium-global-diversity-array.zip")

    # Download the manifest ZIP file
    try:
        print(f"Downloading manifest file from {url}...")
        subprocess.run(["wget", url, "-O", zip_file], check=True)
        print(f"Download complete: {zip_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading the manifest file: {e}")
        raise

    # Extract the ZIP file
    try:
        print("Extracting manifest file...")
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(references_dir)
        csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
        if len(csv_files) == 1:
            manifest_file = os.path.join(references_dir, csv_files[0])
            print(f"Manifest file located: {manifest_file}")
            return manifest_file
        else:
            raise ValueError("Unexpected number of CSV files found in the ZIP archive.")
    except zipfile.BadZipFile as e:
        print(f"Error extracting ZIP file: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error during extraction: {e}")
        raise

def get_snp_set(manifest_file):
    print("Reading SNP set from manifest file...")

    # Validate file existence
    if not os.path.exists(manifest_file):
        raise FileNotFoundError(f"Manifest file not found: {manifest_file}")

    # Read the first 8 lines to extract column headers
    try:
        print("Extracting column headers...")
        column_headers = []
        with open(manifest_file, 'r') as file:
            for i in range(8):
                line = file.readline()
                if i == 7:
                    column_headers = line.strip().split(',')

        print("Parsing SNP data...")
        snp_set = pd.read_csv(manifest_file, skiprows=8, header=None, low_memory=False)
        snp_set.columns = column_headers
        print(f"SNP set successfully parsed with {len(snp_set)} entries.")
        return snp_set
    except pd.errors.ParserError as e:
        print(f"Error parsing the SNP manifest file: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

def prepare_snp_subset_file(snp_set, references_directory):
    """
    Prepares a SNP subset file for bcftools based on the SNP set from the Illumina manifest.

    Parameters:
    - snp_set (pd.DataFrame): DataFrame containing SNPs with columns 'Chr' and 'MapInfo'.
    - references_directory (str): Directory to save the SNP subset file.

    Returns:
    - str: Path to the SNP subset file.
    """
    # Drop rows with NaN values in 'MapInfo' column
    snp_set = snp_set.dropna(subset=['MapInfo'])

    # Ensure 'Chr' and 'MapInfo' columns are correctly formatted
    snp_set.loc[:, 'Chr'] = 'chr' + snp_set['Chr'].astype(str)
    snp_set.loc[:, 'MapInfo'] = snp_set['MapInfo'].astype(int)


    # Create a new DataFrame with the required columns formatted for bcftools
    formatted_df = snp_set[['Chr', 'MapInfo']].rename(columns={'Chr': 'CHROM', 'MapInfo': 'POS'})

    # Save the SNP subset file
    output_path = os.path.join(references_directory, "snp_file.txt")
    print(f"Saving SNP subset file to {output_path}...")
    formatted_df.to_csv(output_path, header=False, index=False, sep='\t')

    print(f"SNP subset file saved: {output_path}")
    return output_path

def subset_1000_genomes(references_directory, snp_file_path):
    """
    Subsets 1000 Genomes VCF files using Illumina SNPs and saves results in a new directory.

    Parameters:
    - references_directory (str): Path to the directory containing 1000 Genomes VCF files.
    - snp_file_path (str): Path to the SNP subset file for bcftools.
    """
    # Define directories
    input_dir = os.path.join(references_directory, "onethousandgenomes_seq")
    output_dir = os.path.join(references_directory, "onethousandgenomes_genotype")
    os.makedirs(output_dir, exist_ok=True)

    # Identify available chromosome files in the input directory
    print("Scanning input directory for VCF files...")
    available_files = [f for f in os.listdir(input_dir) if f.endswith(".vcf.gz") and not f.endswith(".vcf.gz.tbi")]

    # Extract chromosome identifiers from valid VCF filenames
    chromosomes = sorted(
        set(f.split(".")[1].replace("chr", "") for f in available_files if "chr" in f)
    )

    if not chromosomes:
        print("No valid VCF files found in the input directory. Exiting...")
        return

    print(f"Found VCF files for chromosomes: {', '.join(chromosomes)}")

    # Create chr-to-num mapping file
    mapping_file = os.path.join(output_dir, "chr_to_num.txt")
    with open(mapping_file, 'w') as f:
        for i in range(1, 23):
            f.write(f"chr{i}\t{i}\n")
        f.write("chrX\tX\n")
        f.write("chrY\tY\n")

    # Function to process a single chromosome
    def process_chromosome(chromosome):
        print(f"Starting process for chromosome {chromosome} at {datetime.now()}")

        input_vcf = os.path.join(input_dir, f"onethousandgenomes_sequenced_phased.chr{chromosome}.vcf.gz")
        output_vcf = os.path.join(output_dir, f"onethousandgenomes_genotyped_phased.chr{chromosome}.vcf.gz")

        # Check if input VCF and index files exist
        if not os.path.exists(input_vcf) or not os.path.exists(input_vcf + ".tbi"):
            print(f"Required files missing for chromosome {chromosome}: VCF or its index. Skipping...")
            return
                
        # First subset, then rename chromosomes
        try:
            temp_vcf = os.path.join(output_dir, f"temp.chr{chromosome}.vcf.gz")
            subprocess.run(
                ["bcftools", "view", "-R", snp_file_path, input_vcf, "-Oz", "-o", temp_vcf],
                check=True
            )
            
            # Now rename chromosomes
            subprocess.run([
                "bcftools", "annotate",
                "--rename-chrs", mapping_file,
                "-Oz", "-o", output_vcf,
                temp_vcf
            ], check=True)
            
            # Clean up
            os.remove(temp_vcf)
            
            print(f"Subsetted and renamed VCF saved for chromosome {chromosome}.")
        except subprocess.CalledProcessError as e:
            print(f"Error processing VCF file for chromosome {chromosome}: {e}")
            if os.path.exists(temp_vcf):
                os.remove(temp_vcf)
            return

        # Index the subset VCF file
        try:
            subprocess.run(["tabix", "-p", "vcf", output_vcf], check=True)
            print(f"Indexing completed for chromosome {chromosome}.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to index VCF file for chromosome {chromosome}: {e}")
            return

        # Count SNPs in the subsetted file
        try:
            result = subprocess.run(
                ["bcftools", "view", "-v", "snps", output_vcf],
                stdout=subprocess.PIPE,
                text=True
            )
            snp_count = sum(1 for line in result.stdout.splitlines() if not line.startswith("#"))
            print(f"Number of SNPs in chromosome {chromosome}: {snp_count}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to count SNPs in chromosome {chromosome}: {e}")
            return

        print(f"Finished processing for chromosome {chromosome} at {datetime.now()}")

    # max_threads = max(1, os.cpu_count() // 2)  # Use half the available CPU cores
    # with ThreadPoolExecutor(max_workers=max_threads) as executor:
    #     executor.map(process_chromosome, chromosomes)
    for chromosome in chromosomes:
        process_chromosome(chromosome)

    print("All chromosomes processed successfully.")


def main():
    logging.info("\nopen_snps.py: running...\n")  # Add a blank line before and after
    
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

    # Check and install required tools
    required_tools = ["wget", "bcftools", "tabix"]
    try:
        check_and_install_tools(required_tools)
    except EnvironmentError as e:
        logging.error(f"\nTool check and installation failed: {e}\n")
        return
    logging.info("")

    # Download and parse Illumina manifest
    try:
        manifest_file = download_array_manifest(references_directory)
        logging.info("")
        snp_set = get_snp_set(manifest_file)
        logging.info("")
        logging.info(f"SNP set loaded with {len(snp_set)} entries.")
        logging.info("")
        # Prepare SNP subset file
        snp_subset_path = prepare_snp_subset_file(snp_set, references_directory)
        logging.info(f"SNP subset file ready at {snp_subset_path}.")
        logging.info("")
        # Subset 1000 Genomes data
        subset_1000_genomes(references_directory, snp_subset_path)
    except Exception as e:
        logging.error(f"\nError during manifest processing: {e}\n")
        return

if __name__ == "__main__":
    main()