"""
Quality Control Parameters:
===========================
The following quality control steps are applied by default. These can be customized by the user.

Default Parameters:
--autosome: Keep only autosomal SNPs. Excludes X and Y chromosomes to reduce analytical complexities.
--rm-dup exclude-all: Removes duplicate SNPs, keeping the first occurrence only.
--vcf-half-call: Treats half-calls as missing.
--snps-only just-acgt: Excludes variants outside {'A', 'C', 'G', 'T', 'a', 'c', 'g', 't'}.
--min-alleles 2, --max-alleles 2: Retain SNPs where there are exactly 2 alleles (biallelic SNPs).
--geno 0.01: Filters out SNPs with more than 1% missing genotypes.
--maf 0.01: Filters out SNPs with a minor allele frequency below 1%.

Explanation:
1. **Excluding X and Y Chromosomes**:
   - Reduces analytical complexity due to significant differences in allele dosage between these chromosomes.
   - Aligns with models assuming two alleles per locus, which is not applicable to X and Y chromosomes.

2. **Limiting Analysis to Biallelic SNPs**:
   - Ensures high data quality by excluding multiallelic SNPs, which are often artifacts.
   - Mutation rates are low (~10^-8 per generation), making triallelic or tetrallelic SNPs highly unlikely without sequencing errors.

3. **`--geno` and `--maf` Filters**:
   - **`--geno 0.01`**: Excludes SNPs with >1% missing genotypes, focusing on well-supported variants.
   - **`--maf 0.01`**: Excludes SNPs with a minor allele frequency (MAF) below 1%, reducing noise from rare variants.
       - Rare variants (MAF < 1%) are less reliably detected in smaller samples.
       - Common variants (MAF ≥ 1%) are more stable and informative for population-based analyses.
   - **Genetic Genealogy Context**:
       - Rarer variants can offer insights into recent ancestry and family-specific lines.
       - Common variants are useful for understanding distant ancestry and broader population trends.

The applied filters balance data reliability and analytical focus, providing a high-quality dataset for population genetics and genetic genealogy studies.
"""


import logging
import subprocess
import sys
import os
import argparse
import shutil
from collections import Counter
from glob import glob
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

DEFAULT_QC_PARAMS = {
    "autosome": True,
    "rm_dup": "exclude-all",
    "vcf_half_call": True,
    "snps_only": "just-acgt",
    "min_alleles": 2,
    "max_alleles": 2,
    "geno": .5,
    "maf": .001
}
# geno - missingness per variant, considering that different arrays may have different SNPs
# maf - retains alleles with a frequency as low as 0.1% in the population, rare alleles
# mind - missingness per individual, FIX: determine the minimual number of SNPs needed

def parse_arguments():
    parser = argparse.ArgumentParser(description="Quality control for merged VCF files.")
    parser.add_argument("--vcf_file", help="Path to the VCF file to be processed.")
    parser.add_argument("--determined_sex_file")
    parser.add_argument("--failed_sex")
    parser.add_argument("--geno", type=float, default=DEFAULT_QC_PARAMS["geno"], 
                        help="Maximum genotype missingness threshold (default: 0.5).")
    parser.add_argument("--maf", type=float, default=DEFAULT_QC_PARAMS["maf"], 
                        help="Minimum minor allele frequency threshold (default: 0.001).")
    parser.add_argument("--rm-dup", default=DEFAULT_QC_PARAMS["rm_dup"], 
                        help="Remove duplicate SNPs option (default: exclude-all).")
    parser.add_argument("--snps-only", default=DEFAULT_QC_PARAMS["snps_only"], 
                        help="Keep only SNPs with specified nucleotide types (default: just-acgt).")
    parser.add_argument("--min-alleles", type=int, default=DEFAULT_QC_PARAMS["min_alleles"], 
                        help="Minimum allele count for SNPs (default: 2).")
    parser.add_argument("--max-alleles", type=int, default=DEFAULT_QC_PARAMS["max_alleles"], 
                        help="Maximum allele count for SNPs (default: 2).")
    return parser.parse_args()


def check_dependencies(working_directory, utils_directory):
    """Ensure required tools are installed."""
    tools = ["bcftools", "bgzip", "plink2"]
    for tool in tools:
        if not shutil.which(tool):
            logging.error(f"Missing dependency: {tool}. Please install it.")
            sys.exit(1)

    # Find the Beagle jar file dynamically
    beagle_pattern = os.path.join(utils_directory, "beagle.*.jar")
    beagle_files = glob(beagle_pattern)

    if beagle_files:
        # If a matching Beagle jar exists, use the first one (or handle multiple versions as needed)
        beagle_jar = beagle_files[0]
        logging.info(f"Found Beagle jar: {beagle_jar}")
    else:
        logging.info("Beagle not found. Installing...")
        try:
            subprocess.run([f"{working_directory}/scripts_env/install_beagle.sh"], check=True)
            logging.info("Beagle installed successfully.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install Beagle: {e}")
            sys.exit(1)

    logging.info("All dependencies are installed.")
    return beagle_jar
    
def validate_merged_vcf(vcf_path):
    """Validate merged VCF and extract available chromosomes."""
    cmd_counts = ["bcftools", "plugin", "counts", vcf_path]
    result_counts = subprocess.run(cmd_counts, capture_output=True, text=True, check=True)
    logging.info(f"Plugin 'counts' validation output for {vcf_path}:\n{result_counts.stdout}")
    if result_counts.stderr:
        logging.info(f"Plugin 'counts' validation errors:\n{result_counts.stderr}")

    num_samples = 0
    for line in result_counts.stdout.splitlines():
        if line.startswith("Number of samples:"):
            parts = line.split(":")
            if len(parts) == 2:
                num_samples = int(parts[1].strip())
    if not num_samples:
        logging.error(f"No sample count found in VCF file: {vcf_path}")

    num_snps = 0
    for line in result_counts.stdout.splitlines():
        if line.startswith("Number of SNPs:"):
            parts = line.split(":")
            if len(parts) == 2:
                num_snps = int(parts[1].strip())
    if not num_snps:
        logging.error(f"No sample count found in VCF file: {vcf_path}")


    logging.info("Extracting list of chromosomes from the VCF header.")
    cmd_chrom_contig = f"bcftools view -h {vcf_path} | grep '^##contig' | cut -d'=' -f3 | cut -d',' -f1"
    result_chrom_contig = subprocess.run(cmd_chrom_contig, shell=True, capture_output=True, text=True, check=True)
    chromosomes_contig = result_chrom_contig.stdout.splitlines()
    if not chromosomes_contig:
        logging.error(f"No chromosomes found in VCF file: {vcf_path}")
    else:
        logging.debug(f"Chromosomes found in VCF file header: {', '.join(chromosomes_contig)}")


    logging.info("Extracting a list of chromosomes from the CHROM column..")
    cmd_chrom_field = f"bcftools query -f '%CHROM\n' {vcf_path} | sort -u"
    result_chrom_field = subprocess.run(cmd_chrom_field, shell=True, capture_output=True, text=True, check=True)
    chromosomes_field = result_chrom_field.stdout.splitlines()
    if not chromosomes_field:
        logging.error(f"No chromosomes found in VCF file in the CHROM field: {vcf_path}")
    else:
        logging.debug(f"Chromosomes found in VCF file in the CHROM field: {', '.join(chromosomes_field)}")


    if chromosomes_contig != chromosomes_field:
        logging.error("Mismatch between chromosomes in contig and field headers.")
        logging.error(f"Contig chromosomes: {chromosomes_contig}")
        logging.error(f"Field chromosomes: {chromosomes_field}")


    logging.info("Extracting sample IDs from the VCF file.")
    cmd_sample_list = ["bcftools", "query", "-l", vcf_path]
    result_sample_list = subprocess.run(cmd_sample_list, capture_output=True, text=True, check=True)
    sample_ids = result_sample_list.stdout.splitlines()

    if not sample_ids:
        logging.error(f"No sample IDs found in VCF file: {vcf_path}")
    else:
        logging.debug(f"Sample IDs found in VCF file: {', '.join(sample_ids)}")

    return num_samples, num_snps, chromosomes_field, sample_ids

def validate_vcf(vcf_path):
    """Validate merged VCF and extract available chromosomes."""
    cmd_counts = ["bcftools", "plugin", "counts", vcf_path]
    result_counts = subprocess.run(cmd_counts, capture_output=True, text=True, check=True)
    logging.info(f"Plugin 'counts' validation output for {vcf_path}:\n{result_counts.stdout}")
    if result_counts.stderr:
        logging.info(f"Plugin 'counts' validation errors:\n{result_counts.stderr}")

def parse_sex_determination(determined_sex_file, failed_sex):
    """Parse the sex determination log and create a mapping of user IDs to sexes."""
    sex_mapping = {}
    with open(determined_sex_file, 'r') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:  # Skip empty lines
            continue

        user_id, sex = line.split("\t")
        sex_mapping[user_id] = "1" if sex == "Male" else "2"

    with open(failed_sex, 'r') as p:
        lines = p.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        user_id, sex = line.split("\t")
        sex_mapping[user_id] = "0" # Unknown sex

    # Count occurrences of each sex code
    counts = Counter(sex_mapping.values())

    # Print results
    logging.info(f"Count of SEX=0 (Unknown): {counts['0']}")
    logging.info(f"Count of SEX=1 (Male): {counts['1']}")
    logging.info(f"Count of SEX=2 (Female): {counts['2']}")

    return sex_mapping

def write_sex_files(sex_mapping, sample_ids, psam_file_all, psam_file_Y, sex_update_file):
    """Write both PLINK2-compatible .psam files and sex update file."""
    
    # Reorder sex_mapping based on sample_ids
    ordered_sex_mapping = {sample_id: sex_mapping.get(sample_id, "0") for sample_id in sample_ids}
    
    # Write standard .psam file for all chromosomes
    with open(psam_file_all, 'w') as f:
        f.write("#FID\tIID\tSEX\n")  # Header for .psam file
        for user_id, sex_code in ordered_sex_mapping.items():
            if sex_code == "0":
                continue  # Exclude unknown sexes
            f.write(f"{user_id}\t{user_id}\t{sex_code}\n")
    
    # Write .psam file for Y chromosome (males only)
    with open(psam_file_Y, 'w') as f:
        f.write("#FID\tIID\tSEX\n")
        for user_id, sex_code in ordered_sex_mapping.items():
            if sex_code != "1":
                continue  # Exclude non-males
            f.write(f"{user_id}\t{user_id}\t{sex_code}\n")
    
    # Write sex update file for PLINK2 --update-sex
    with open(sex_update_file, 'w') as f:
        f.write("#IID\tSEX\n")  # PLINK2 format for sex update
        for user_id, sex_code in ordered_sex_mapping.items():
            if sex_code == "0":
                continue  # Exclude unknown sexes
            f.write(f"{user_id}\t{sex_code}\n")

def run_command(command, suppress_stdout=True):
    """Run a shell command with error handling, optionally suppressing stdout."""
    if isinstance(command, str):
        command = command.split()  # Split string into a list for subprocess
    try:
        logging.debug(f"Executing command: {' '.join(command)}")
        
        if suppress_stdout:
            # Suppress stdout, capture only stderr
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        else:
            # Allow both stdout and stderr to display
            subprocess.run(command, check=True)
        
        logging.debug(f"Command succeeded: {' '.join(command)}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {' '.join(command)}\nError: {e.stderr.decode('utf-8') if e.stderr else str(e)}")
        sys.exit()

def step_1_convert_vcf_to_plink(vcf_file, output_prefix, plink2_path, snps_only, rm_dup, min_alleles, max_alleles):
    """Convert VCF to PLINK format with user-defined parameters."""
    command = [
        plink2_path,
        "--vcf", vcf_file,
        "--autosome",
        "--snps-only", snps_only,
        "--rm-dup", rm_dup,
        "--min-alleles", str(min_alleles),
        "--max-alleles", str(max_alleles),
        "--make-pgen",
        "--out", output_prefix
    ]
    run_command(command)

def step_2_filter_genotype_and_maf(input_prefix, output_prefix, plink2_path, geno, maf):
    """Filter by genotype missingness and minor allele frequency with user-defined parameters."""
    command = [
        plink2_path,
        "--pfile", input_prefix,
        "--geno", str(geno),
        "--maf", str(maf),
        "--sort-vars",
        "--make-pgen",
        "--out", output_prefix
    ]
    run_command(command)

def step_3_split_by_chromosome(input_prefix, output_dir, sample_file, plink2_path):
    """Step 3: Split by chromosome and export as VCF."""
    for chromosome in range(1, 23):
        output_prefix = os.path.join(output_dir, f"{sample_file}_qc_chr{chromosome}")
        command = [
            plink2_path,
            "--pfile", input_prefix,
            "--chr", str(chromosome),
            "--export", "vcf",
            "--out", output_prefix
        ]
        run_command(command)

        # Command to filter for biallelic variants
        bcftools_input = output_prefix + ".vcf"
        bcftools_output = os.path.join(output_dir, f"{sample_file}_qcfinished_chr{chromosome}.vcf.gz")
        command = [
            "bcftools", "view",
            "-m2", "-M2",  # Keep only biallelic variants
            "-Oz",         # Output in compressed VCF format
            "-o", bcftools_output,
            bcftools_input
        ]
        run_command(command)

        # Index the VCF file
        index_command = ["bcftools", "index", bcftools_output]
        run_command(index_command)
    return 

def step_process_X(vcf_path, output_prefix, sex_update_file, plink2_path):
    """Process chromosome X with PAR splitting."""
    # Step 1: Initial conversion with sex update and PAR splitting
    command = [
        plink2_path,
        "--vcf", vcf_path,
        "--update-sex", sex_update_file,
        "--chr", "X",
        "--split-par", "b38",
        "--snps-only", "just-acgt",
        "--rm-dup", "exclude-all",
        "--make-pgen",
        "--out", f"{output_prefix}_step1"
    ]
    run_command(command)
    
    # Only continue if step 1 succeeded
    if os.path.exists(f"{output_prefix}_step1.pgen"):
        # Step 2: Apply lenient filters
        command = [
            plink2_path,
            "--pfile", f"{output_prefix}_step1",
            "--geno", "0.5",  # Lenient missingness threshold
            "--maf", "0.001",  # Lenient MAF threshold
            "--sort-vars",
            "--make-pgen",
            "--out", f"{output_prefix}_step2"
        ]
        run_command(command)
        
        # Step 3: Export to VCF if step 2 succeeded
        if os.path.exists(f"{output_prefix}_step2.pgen"):
            command = [
                plink2_path,
                "--pfile", f"{output_prefix}_step2",
                "--export", "vcf",
                "--out", output_prefix
            ]
            run_command(command)

            if os.path.exists(f"{output_prefix}.vcf"):
                # Compress and index the VCF file
                compress_command = ["bgzip", "-f", f"{output_prefix}.vcf"]
                index_command = ["bcftools", "index", f"{output_prefix}.vcf.gz"]

                run_command(compress_command)
                run_command(index_command)
                validate_vcf(os.path.join(results_directory, output_prefix + ".vcf.gz" ))

def step_process_Y(vcf_path, output_prefix, psam_file_Y, plink2_path):
    """Process chromosome Y."""
    # First verify psam file contents match VCF
    command = [
        plink2_path,
        "--vcf", vcf_path,
        "--chr", "Y",
        "--write-samples",
        "--out", f"{output_prefix}_samples"
    ]
    run_command(command)
    
    # Step 1: Initial conversion
    command = [
        plink2_path,
        "--vcf", vcf_path,
        "--chr", "Y",
        "--snps-only", "just-acgt",
        "--rm-dup", "exclude-all",
        "--make-pgen",
        "--out", f"{output_prefix}_step1"
    ]
    run_command(command)
    
    # Step 2: Sort variants if step 1 succeeded
    if os.path.exists(f"{output_prefix}_step1.pgen"):
        command = [
            plink2_path,
            "--pfile", f"{output_prefix}_step1",
            "--sort-vars",
            "--make-pgen",
            "--out", f"{output_prefix}_step2"
        ]
        run_command(command)
    
        # Step 3: Export to VCF if step 2 succeeded
        if os.path.exists(f"{output_prefix}_step2.pgen"):
            command = [
                plink2_path,
                "--pfile", f"{output_prefix}_step2",
                "--export", "vcf",
                "--out", output_prefix
            ]
            run_command(command)

            if os.path.exists(f"{output_prefix}.vcf"):
                # Compress and index the VCF file
                compress_command = ["bgzip", "-f", f"{output_prefix}.vcf"]
                index_command = ["bcftools", "index", f"{output_prefix}.vcf.gz"]

                run_command(compress_command)
                run_command(index_command)
                validate_vcf(os.path.join(results_directory, output_prefix + ".vcf.gz" ))

def step_process_MT(vcf_path, output_prefix, plink2_path):
    """Process mitochondrial chromosome."""
    # Step 1: Initial conversion
    command = [
        plink2_path,
        "--vcf", vcf_path,
        "--chr", "MT",
        "--snps-only", "just-acgt",
        "--rm-dup", "exclude-all",
        "--make-pgen",
        "--out", f"{output_prefix}_step1"
    ]
    run_command(command)
    
    # Step 2: Sort variants if step 1 succeeded
    if os.path.exists(f"{output_prefix}_step1.pgen"):
        command = [
            plink2_path,
            "--pfile", f"{output_prefix}_step1",
            "--sort-vars",
            "--make-pgen",
            "--out", f"{output_prefix}_step2"
        ]
        run_command(command)
    
        # Step 3: Export to VCF if step 2 succeeded
        if os.path.exists(f"{output_prefix}_step2.pgen"):
            command = [
                plink2_path,
                "--pfile", f"{output_prefix}_step2",
                "--export", "vcf",
                "--out", output_prefix
            ]
            run_command(command)

            if os.path.exists(f"{output_prefix}.vcf"):
                # Compress and index the VCF file
                compress_command = ["bgzip", "-f", f"{output_prefix}.vcf"]
                index_command = ["bcftools", "index", f"{output_prefix}.vcf.gz"]

                run_command(compress_command)
                run_command(index_command)
                validate_vcf(os.path.join(results_directory, output_prefix + ".vcf.gz" ))

def main(working_directory, utils_directory, results_directory):

    args = parse_arguments()
    vcf_path = args.vcf_file
    determined_sex_file = args.determined_sex_file
    failed_sex = args.failed_sex

    # Check dependencies - find Beagle jar and Plink2
    beagle_jar = check_dependencies(working_directory, utils_directory)
    plink2_path = os.path.join(utils_directory, "plink2")
    if not os.path.exists(plink2_path):
        logging.info("Plink2 not found. Installing Plink2...")
        subprocess.run(["bash", "scripts_env/install_plink2.sh"], check=True)
    logging.info("Dependencies checked.")

    if os.path.exists(vcf_path):
        logging.info(f"Validating merged VCF: {vcf_path}")
        num_samples, num_snps, chromosomes, sample_ids = validate_merged_vcf(vcf_path)
        logging.info(f"Number of samples: {num_samples}, Number of SNPs {num_snps}, Chromosomes: {chromosomes}")

        if determined_sex_file:
            sex_mapping = parse_sex_determination(determined_sex_file, failed_sex)
            base_name = os.path.splitext(determined_sex_file)[0]
            psam_file_all = f"{base_name}_all.psam"
            psam_file_Y = f"{base_name}_Y.psam"
            sex_update_file = f"{base_name}_update_sex.txt"
            write_sex_files(sex_mapping, sample_ids, psam_file_all, psam_file_Y, sex_update_file)

        if (num_samples > 0) and (num_snps > 0) and len(chromosomes) > 0:
            logging.info(f"Validation successful for {vcf_path}.")

            sample_file = os.path.basename(vcf_path).split('.')[0]
            step1_output_prefix = os.path.join(results_directory, f"{sample_file}_autosomes_step1")
            step2_output_prefix = os.path.join(results_directory, f"{sample_file}_autosomes_step2")

            logging.info("Processing autosomes...")
            logging.info("Starting Step 1: Convert VCF to PLINK format.")
            step_1_convert_vcf_to_plink(
                vcf_path, step1_output_prefix, plink2_path,
                args.snps_only, args.rm_dup, args.min_alleles, args.max_alleles
            )

            logging.info("Starting Step 2: Filter by genotype missingness and MAF.")
            step_2_filter_genotype_and_maf(
                step1_output_prefix, step2_output_prefix, plink2_path,
                args.geno, args.maf
            )

            logging.info("Starting Step 3: Split by chromosome and export as VCF.")
            step_3_split_by_chromosome(step2_output_prefix, results_directory, sample_file, plink2_path)

            if ("X" in chromosomes) or ("Y" in chromosomes) or ("MT" in chromosomes):
                sample_file = os.path.basename(vcf_path).split('.')[0]

            if "X" in chromosomes:
                logging.info("Processing chromosome X...")
                try:
                    step_process_X(
                        vcf_path=vcf_path,
                        output_prefix=os.path.join(results_directory, f"{sample_file}_qcfinished_chrX"),
                        sex_update_file=sex_update_file,
                        plink2_path=plink2_path
                    )
                except Exception as e:
                    logging.error(f"Error processing chromosome X: {e}")

            if "Y" in chromosomes:
                logging.info("Processing chromosome Y...")
                try:
                    step_process_Y(
                        vcf_path=vcf_path,
                        output_prefix=os.path.join(results_directory, f"{sample_file}_qcfinished_chrY"),
                        psam_file_Y=psam_file_Y,
                        plink2_path=plink2_path
                    )
                except Exception as e:
                    logging.error(f"Error processing chromosome Y: {e}")

            if "MT" in chromosomes:
                logging.info("Processing chromosome MT...")
                try:
                    step_process_MT(
                        vcf_path=vcf_path,
                        output_prefix=os.path.join(results_directory, f"{sample_file}_qcfinished_chrMT"),
                        plink2_path=plink2_path
                    )
                except Exception as e:
                    logging.error(f"Error processing chromosome MT: {e}")

            logging.info("Phasing chromosomes...")
            script_path = os.path.join(working_directory, "scripts_work/phase_chromosomes.sh")
            input_prefix = f"{sample_file}_qcfinished"
            command = [script_path, results_directory, references_directory, utils_directory, input_prefix, beagle_jar]

            try:
                # subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(command, check=True) # as opposed the the line above to see the output in console
            except subprocess.CalledProcessError as e:
                logging.error(f"Script failed with return code {e.returncode}")
                logging.error(f"Script output: {e.stdout.decode()}")
                logging.error(f"Script error: {e.stderr.decode()}")
                raise

        else:
            logging.error(f"Validation failed for {vcf_path}.")
    else:
        logging.error(f"File not found: {vcf_path}")

    logging.info("Phasing pipeline completed successfully.")

if __name__ == "__main__":
    logging.info("Starting VCF quality control process.")
    """
    poetry run python -m scripts_work.quality_control_vcf \
        --vcf_file data/open_snps_data/opensnps.vcf.gz \
        --determined_sex_file data/open_snps_data/determined_sex.txt \
        --failed_sex data/open_snps_data/failed_sex.txt \
        --geno 0.05 --maf 0.05
    """
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

    log_dir = os.path.join(results_directory, "log")
    os.makedirs(log_dir, exist_ok=True)
    log_filename = os.path.join(log_dir, "quality_control_vcf.log")
    configure_logging(log_filename, log_file_debug_level="INFO", console_debug_level="INFO")

    main(working_directory, utils_directory, results_directory)


# # When using the campus genotype data, use stricter QC values
# # Also add this

#     /home/ubuntu/bagg_analysis/utils/plink2 \
#   --pfile /home/ubuntu/bagg_analysis/results/opensnps_autosomes_step1 \
#   --freq \
#   --missing \
#   --out /home/ubuntu/bagg_analysis/results/opensnps_summary

# opensnps_summary.missing: Check the proportion of missing genotypes per variant.
# opensnps_summary.frq: Check the allele frequencies for all variants