#!/usr/bin/env python3
"""
Complete IBD Detection and Evaluation Workflow

This script implements a complete workflow for:
1. Quality control of VCF files
2. IBD detection using IBIS, Refined-IBD, and Hap-IBD
3. Evaluation of IBD detection results against ground truth

Usage:
    python ibd_complete_workflow.py [--vcf PATH] [--pedigree-def PATH] [--output-dir PATH]

Author: Computational Genetic Genealogy Team
"""

import os
import sys
import subprocess
import argparse
import logging
import shutil
import gzip
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
from intervaltree import IntervalTree
from sklearn.metrics import precision_recall_curve, average_precision_score, roc_curve, auc

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ibd_workflow.log')
    ]
)
logger = logging.getLogger(__name__)

def load_environment():
    """Load environment variables from .env file"""
    try:
        # Load from .env file
        load_dotenv()
        
        # Set global directory paths
        working_directory = os.getenv('PROJECT_WORKING_DIR')
        results_directory = os.getenv('PROJECT_RESULTS_DIR')
        data_directory = os.getenv('PROJECT_DATA_DIR')
        utils_directory = os.getenv('PROJECT_UTILS_DIR')
        references_directory = os.getenv('PROJECT_REFERENCES_DIR')
        
        logger.info(f"Working directory: {working_directory}")
        logger.info(f"Results directory: {results_directory}")
        logger.info(f"Data directory: {data_directory}")
        logger.info(f"Utils directory: {utils_directory}")
        logger.info(f"References directory: {references_directory}")
        
        return working_directory, results_directory, data_directory, utils_directory, references_directory
    except Exception as e:
        logger.error(f"Error loading environment variables: {e}")
        return None, None, None, None, None

# ---------- Lab 7: Pedigree Simulation with ped-sim ----------

def prepare_ped_sim_files(references_dir):
    """
    Prepare necessary files for ped-sim simulation following Lab7's approach
    
    Args:
        references_dir: Directory for reference map files
    
    Returns:
        Path to the refined map file
    """
    logger.info("Preparing files for ped-sim simulation following exactly Lab7 approach")
    
    # Create references directory if it doesn't exist
    os.makedirs(references_dir, exist_ok=True)
    
    # Step 1: Check if we already have the processed b38 file
    refined_map = os.path.join(references_dir, "refined_mf_b38.simmap")
    if os.path.exists(refined_map):
        # Verify the file format - read first few lines and check structure
        try:
            with open(refined_map, 'r') as f:
                header = f.readline().strip()
                first_line = f.readline().strip() if f.readline() else ""
                
            if "#chr\tpos\tmale_cM\tfemale_cM" in header and len(first_line.split('\t')) == 4:
                # Check if second column is an integer
                try:
                    int(first_line.split('\t')[1])
                    logger.info(f"Using existing genetic map: {refined_map}")
                    return refined_map
                except (ValueError, IndexError):
                    logger.warning(f"Existing map file has incorrect format. Recreating it.")
            else:
                logger.warning(f"Existing map file has incorrect header format. Recreating it.")
        except Exception as e:
            logger.warning(f"Error validating existing map file: {e}. Recreating it.")
    
    # If we need to create it, follow Lab7's exact process
    refined_mf_b37_simmap = os.path.join(references_dir, "refined_mf_b37.simmap")
    
    try:
        # 1. Download and extract the raw data if needed
        if not os.path.exists(refined_mf_b37_simmap):
            logger.info("Downloading genetic map data")
            # Download the tarball
            download_url = "https://github.com/cbherer/Bherer_etal_SexualDimorphismRecombination/raw/master/Refined_genetic_map_b37.tar.gz"
            tarball_path = os.path.join(references_dir, "Refined_genetic_map_b37.tar.gz")
            
            # Use subprocess to download
            subprocess.run(["wget", download_url, "-P", references_dir], check=True)
            
            # Extract the tarball
            subprocess.run(["tar", "xvzf", tarball_path, "-C", references_dir], check=True)
            
            # Create the combined map file following exactly Lab7 approach
            logger.info("Creating combined genetic map file")
            with open(refined_mf_b37_simmap, "w") as out_f:
                out_f.write("#chr\tpos\tmale_cM\tfemale_cM\n")
                
                # Process each chromosome
                for chrom in range(1, 23):
                    male_file = os.path.join(references_dir, "Refined_genetic_map_b37", f"male_chr{chrom}.txt")
                    female_file = os.path.join(references_dir, "Refined_genetic_map_b37", f"female_chr{chrom}.txt")
                    
                    if os.path.exists(male_file) and os.path.exists(female_file):
                        # Using paste and awk as in Lab7
                        cmd = f"paste {male_file} {female_file} | awk -v OFS='\t' 'NR > 1 && $2 == $6 {{print $1,$2,$4,$8}}' | sed 's/^chr//'"
                        paste_output = subprocess.check_output(cmd, shell=True, text=True)
                        out_f.write(paste_output)
            
            # Clean up
            os.remove(tarball_path)
            shutil.rmtree(os.path.join(references_dir, "Refined_genetic_map_b37"))
            logger.info(f"Created b37 genetic map: {refined_mf_b37_simmap}")
    
        # Step 2: Convert from b37 to b38 coordinates (Lab7 cell 8)
        logger.info("Step 2: Converting genetic map from b37 to b38 coordinates")
        
        # Download chain file if needed
        chain_file = os.path.join(references_dir, "hg19ToHg38.over.chain.gz")
        if not os.path.exists(chain_file):
            logger.info("Downloading chain file for liftOver")
            chain_url = "https://hgdownload.soe.ucsc.edu/goldenPath/hg19/liftOver/hg19ToHg38.over.chain.gz"
            subprocess.run(["wget", "-O", chain_file, chain_url], check=True)
        
        # Create BED file from b37 simmap - following exact approach in Lab7
        bed_file_b37 = os.path.join(references_dir, "refined_mf_b37.bed")
        cmd = f"awk 'NR>1 {{print \"chr\"$1, $2-1, $2, $3, $4}}' OFS='\t' {refined_mf_b37_simmap} > {bed_file_b37}"
        subprocess.run(cmd, shell=True, check=True)
        
        # Run liftOver
        bed_file_b38 = os.path.join(references_dir, "refined_mf_b38.bed")
        unmapped_file = os.path.join(references_dir, "refined_mf_b38.unmapped")
        
        subprocess.run(["liftOver", bed_file_b37, chain_file, bed_file_b38, unmapped_file], check=True)
        logger.info("Completed liftOver to b38 coordinates")
        
        # Process BED file to create final simmap
        logger.info("Step 3: Processing BED file to create final genetic map")
        
        # Read the BED file
        bed_data = pd.read_csv(bed_file_b38, sep='\t', header=None)
        bed_data.columns = ['chr', 'start', 'pos', 'male_cM', 'female_cM']
        
        # Clean chromosome names (remove 'chr' prefix)
        bed_data['chr'] = bed_data['chr'].str.replace('chr', '', regex=True)
        
        # Convert chromosome to numeric
        bed_data['chr'] = pd.to_numeric(bed_data['chr'], errors='coerce')
        
        # Filter for chromosomes 1-22 and remove NaN values
        mask = (bed_data['chr'] >= 1) & (bed_data['chr'] <= 22) & (bed_data['chr'].notna())
        filtered_data = bed_data[mask].copy()
        
        # Convert chromosome to integer after filtering
        filtered_data['chr'] = filtered_data['chr'].astype(int)
        
        # Sort by chromosome and position
        sorted_data = filtered_data.sort_values(by=['chr', 'pos'])
        
        # Keep only necessary columns
        simmap_data = sorted_data[['chr', 'pos', 'male_cM', 'female_cM']]
        
        # Save to simmap file with header - ensure proper formatting
        with open(refined_map, 'w') as f:
            f.write("#chr\tpos\tmale_cM\tfemale_cM\n")
        
        # Append data without header
        simmap_data.to_csv(refined_map, sep='\t', index=False, header=False, mode='a')
        
        # Validate the output file - ensure pos column is integers
        with open(refined_map, 'r') as f:
            lines = f.readlines()
            
        fixed_lines = [lines[0]]  # Keep header
        for line in lines[1:]:  # Process data lines
            parts = line.strip().split('\t')
            if len(parts) >= 4:
                # Ensure position is integer
                try:
                    pos_val = int(float(parts[1]))
                    # Replace the original position with integer
                    parts[1] = str(pos_val)
                except ValueError:
                    logger.warning(f"Invalid position value: {parts[1]} - skipping line")
                    continue
                
                fixed_lines.append('\t'.join(parts) + '\n')
        
        # Write back the fixed file
        with open(refined_map, 'w') as f:
            f.writelines(fixed_lines)
        
        logger.info(f"Created and validated final genetic map: {refined_map}")
        
        # Final check of the corrected file
        with open(refined_map, 'r') as f:
            head_lines = [next(f) for _ in range(5) if f]
        logger.info(f"Final genetic map first few lines for verification:")
        for line in head_lines:
            logger.info(line.strip())
            
        return refined_map
        
    except Exception as e:
        logger.error(f"Error processing genetic map file: {e}")
        return None

def prepare_input_vcf(vcf_file, output_dir, references_dir):
    """
    Prepare input VCF file for ped-sim according to Lab7 approach
    
    Args:
        vcf_file: Path to input VCF file (should be phased)
        output_dir: Directory for output files
        references_dir: Directory containing reference files
        
    Returns:
        Path to the pruned VCF file ready for ped-sim
    """
    logger.info("Preparing input VCF for ped-sim following Lab7 approach")
    
    # Check input VCF
    if not os.path.exists(vcf_file):
        logger.error(f"Input VCF file not found: {vcf_file}")
        return None
    
    # Create necessary directories following Lab7 structure
    ped_sim_dir = os.path.join(output_dir, "ped_sim")
    os.makedirs(ped_sim_dir, exist_ok=True)
    
    # Define output paths
    output_prefix = "merged_opensnps_autosomes_pruned"
    pruned_vcf = os.path.join(ped_sim_dir, f"{output_prefix}.vcf.gz")
    
    # Check if pruned VCF already exists
    if os.path.exists(pruned_vcf) and os.path.exists(f"{pruned_vcf}.tbi"):
        # Verify that it's a valid VCF
        try:
            result = subprocess.run(
                ["bcftools", "query", "-l", pruned_vcf],
                check=True, 
                stdout=subprocess.PIPE, 
                text=True
            )
            pruned_count = len(result.stdout.strip().split('\n'))
            logger.info(f"Using existing pruned VCF: {pruned_vcf} with {pruned_count} samples")
            return pruned_vcf
        except Exception as e:
            logger.warning(f"Existing pruned VCF seems invalid: {e}. Creating a new one.")
    
    # Check input sample size first
    try:
        result = subprocess.run(
            ["bcftools", "query", "-l", vcf_file],
            check=True, 
            stdout=subprocess.PIPE, 
            text=True
        )
        sample_count = len(result.stdout.strip().split('\n'))
        logger.info(f"Input sample size: {sample_count}")
    except Exception as e:
        logger.error(f"Error checking sample size: {e}")
        return None
    
    try:
        # Following the exact commands from Lab7
        logger.info("Step 1: Converting VCF to PLINK format")
        dataset_prefix = os.path.join(ped_sim_dir, "dataset")
        subprocess.run(
            ["plink2", "--vcf", vcf_file, "--make-bed", "--out", dataset_prefix],
            check=True
        )
        
        logger.info("Step 2: Removing close relatives using KING with cutoff 0.125")
        unrelated_prefix = os.path.join(ped_sim_dir, "dataset_unrelated")
        subprocess.run(
            ["plink2", 
             "--bfile", dataset_prefix,
             "--king-cutoff", "0.125",
             "--make-bed", 
             "--out", unrelated_prefix],
            check=True
        )
        
        logger.info("Step 3: Converting filtered dataset back to VCF")
        pruned_vcf_uncompressed = os.path.join(ped_sim_dir, f"{output_prefix}.vcf")
        subprocess.run(
            ["plink2",
             "--bfile", unrelated_prefix,
             "--export", "vcf",
             "--out", os.path.join(ped_sim_dir, output_prefix)],
            check=True
        )
        
        logger.info("Step 4: Compressing and indexing pruned VCF")
        try:
            # Remove any existing compressed file
            if os.path.exists(pruned_vcf):
                os.remove(pruned_vcf)
            
            # Compress the VCF
            subprocess.run(
                f"bgzip -c {pruned_vcf_uncompressed} > {pruned_vcf}",
                shell=True,
                check=True
            )
            
            # Sort the VCF before indexing
            sorted_vcf = f"{os.path.splitext(pruned_vcf)[0]}_sorted.vcf.gz"
            subprocess.run(
                ["bcftools", "sort", "-Oz", "-o", sorted_vcf, pruned_vcf],
                check=True
            )
            
            # Replace the original with the sorted version
            shutil.move(sorted_vcf, pruned_vcf)
            
            # Index the sorted VCF
            subprocess.run(
                ["bcftools", "index", "--tbi", pruned_vcf],
                check=True
            )
        except Exception as e:
            logger.warning(f"Warning during VCF compression/indexing: {e}")
            logger.info("Attempting alternative indexing approach...")
            
            # Try alternative approach using bcftools
            try:
                # Regenerate VCF with bcftools
                bcf_temp = f"{os.path.splitext(pruned_vcf_uncompressed)[0]}.bcf"
                subprocess.run(
                    ["bcftools", "view", "-Ob", "-o", bcf_temp, pruned_vcf_uncompressed],
                    check=True
                )
                
                # Index the BCF
                subprocess.run(
                    ["bcftools", "index", bcf_temp],
                    check=True
                )
                
                # Convert back to compressed VCF
                subprocess.run(
                    ["bcftools", "view", "-Oz", "-o", pruned_vcf, bcf_temp],
                    check=True
                )
                
                # Index the compressed VCF
                subprocess.run(
                    ["bcftools", "index", "--tbi", pruned_vcf],
                    check=True
                )
                
                # Clean up temporary BCF file
                if os.path.exists(bcf_temp):
                    os.remove(bcf_temp)
            except Exception as e2:
                logger.error(f"Error during alternative VCF indexing: {e2}")
                return None
        
        # Remove uncompressed VCF to save space
        if os.path.exists(pruned_vcf_uncompressed):
            os.remove(pruned_vcf_uncompressed)
        
        # Check final pruned VCF sample size
        try:
            result = subprocess.run(
                ["bcftools", "query", "-l", pruned_vcf],
                check=True, 
                stdout=subprocess.PIPE, 
                text=True
            )
            pruned_count = len(result.stdout.strip().split('\n'))
            logger.info(f"Final pruned sample size: {pruned_count}")
            
            if pruned_count == 0:
                logger.error("Error: Pruned VCF has 0 samples! Something went wrong.")
                return None
        except Exception as e:
            logger.error(f"Error checking pruned sample size: {e}")
        
        return pruned_vcf
        
    except Exception as e:
        logger.error(f"Error during VCF preparation: {e}")
        return None

def verify_vcf_phased(vcf_file):
    """
    Verify that a VCF file contains phased genotypes
    
    Args:
        vcf_file: Path to VCF file to check
        
    Returns:
        True if VCF is phased, False otherwise
    """
    logger.info(f"Verifying that VCF file is phased: {vcf_file}")
    
    if not os.path.exists(vcf_file):
        logger.error(f"VCF file not found: {vcf_file}")
        return False
    
    try:
        # Use bcftools to check the first few genotypes
        cmd = f"bcftools view {vcf_file} | grep -v '^#' | head -n 10"
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, text=True)
        
        # Look for phased genotype separator '|' instead of unphased '/'
        phased = False
        for line in result.stdout.splitlines():
            fields = line.split('\t')
            if len(fields) > 9:  # At least one sample column
                genotypes = fields[9:]
                for gt in genotypes:
                    # Check GT field (first field in sample column)
                    gt_value = gt.split(':')[0]
                    if '|' in gt_value:  # Found phased genotype
                        phased = True
                    if '/' in gt_value and '|' not in gt_value:
                        logger.error(f"Unphased genotype found: {gt_value}")
                        return False
        
        if phased:
            logger.info("VCF appears to be properly phased")
            return True
        else:
            logger.warning("No phased genotypes found in VCF sample")
            return False
    except Exception as e:
        logger.error(f"Error checking if VCF is phased: {e}")
        return False

def run_ped_sim(vcf_file, pedigree_def_file, output_dir, utils_dir, references_dir):
    """
    Run ped-sim to simulate IBD segments based on a pedigree definition
    
    Args:
        vcf_file: Path to input VCF file (MUST BE PHASED - ped-sim requires phased genotypes)
        pedigree_def_file: Path to pedigree definition file
        output_dir: Directory for output files
        utils_dir: Directory containing ped-sim executable
        references_dir: Directory containing reference maps
    
    Returns:
        Tuple of (truth_segments_file, simulated_vcf_file)
    """
    logger.info(f"Running ped-sim simulation using {vcf_file} and pedigree {pedigree_def_file}")
    
    # First verify the VCF is phased
    if not verify_vcf_phased(vcf_file):
        logger.error("Input VCF is not phased. Ped-sim requires phased genotypes.")
        return None, None
    
    # Step 1: Ensure needed directories exist
    ped_sim_dir = os.path.join(output_dir, "ped_sim")
    os.makedirs(ped_sim_dir, exist_ok=True)
    
    # Step 2: Prepare genetic map
    logger.info("Step 1: Preparing genetic map for ped-sim")
    refined_map = prepare_ped_sim_files(references_dir)
    if not refined_map:
        logger.error("Failed to prepare genetic map")
        return None, None
    
    # Step 3: Prepare input VCF
    logger.info("Step 2: Preparing input VCF for ped-sim")
    pruned_vcf = prepare_input_vcf(vcf_file, output_dir, references_dir)
    if not pruned_vcf:
        logger.error("Failed to prepare input VCF")
        return None, None
    
    # Verify that pedigree definition file exists
    if not os.path.exists(pedigree_def_file):
        logger.error(f"Pedigree definition file not found: {pedigree_def_file}")
        return None, None
    
    # Define paths
    ped_sim_exec = os.path.join(utils_dir, "ped-sim/ped-sim")
    if not os.path.exists(ped_sim_exec):
        logger.error(f"ped-sim executable not found at {ped_sim_exec}")
        return None, None
    
    # Set up interference file path
    interfere_file = os.path.join(utils_dir, "ped-sim/interfere/nu_p_campbell.tsv")
    os.makedirs(os.path.dirname(interfere_file), exist_ok=True)
    
    # Create interference file if it doesn't exist
    if not os.path.exists(interfere_file):
        logger.info(f"Creating interference file at {interfere_file}")
        try:
            os.makedirs(os.path.dirname(interfere_file), exist_ok=True)
            with open(interfere_file, "w") as f:
                f.write("nu p\n")
                f.write("6.0 0.0\n")
            logger.info("Created basic interference file")
        except Exception as e:
            logger.error(f"Error creating interference file: {e}")
            return None, None
    
    # Set up output name
    ped_sim_basename = "merged_opensnps_autosomes_ped_sim"
    output_prefix = os.path.join(ped_sim_dir, ped_sim_basename)
    
    # Check if output files already exist
    expected_seg = f"{output_prefix}.seg"
    expected_fam = f"{output_prefix}-everyone.fam"
    expected_vcf = f"{output_prefix}.vcf.gz"
    
    if os.path.exists(expected_seg) and os.path.exists(expected_fam) and os.path.exists(expected_vcf):
        logger.info(f"Found existing ped-sim output files: {expected_seg} and {expected_vcf}")
        
        # Verify and fix simulated VCF format if needed
        logger.info("Verifying and fixing simulated VCF format if needed")
        try:
            # Check if the VCF is properly bgzipped
            test_cmd = f"bcftools view -h {expected_vcf}"
            test_result = subprocess.run(test_cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            
            if test_result.returncode != 0 and "not compressed with bgzip" in test_result.stderr.decode():
                logger.warning("Simulated VCF is not properly bgzipped. Fixing...")
                # Uncompress then recompress with bgzip
                temp_vcf = f"{output_prefix}.temp.vcf"
                
                # Uncompress
                with gzip.open(expected_vcf, 'rb') as f_in:
                    with open(temp_vcf, 'wb') as f_out:
                        f_out.write(f_in.read())
                
                # Recompress with bgzip
                fixed_vcf = f"{output_prefix}.fixed.vcf.gz"
                subprocess.run(f"bgzip -c {temp_vcf} > {fixed_vcf}", shell=True, check=True)
                
                # Replace original with fixed version
                os.remove(expected_vcf)
                shutil.move(fixed_vcf, expected_vcf)
                
                # Index the fixed VCF
                subprocess.run(["bcftools", "index", "--tbi", expected_vcf], check=True)
                
                # Clean up
                os.remove(temp_vcf)
                logger.info(f"Fixed VCF format and created index: {expected_vcf}")
            else:
                logger.info("Simulated VCF is in valid format")
        except Exception as e:
            logger.warning(f"Error while verifying/fixing VCF format: {e}")
        
        return expected_seg, expected_vcf
    
    # Run ped-sim
    logger.info(f"Step 3: Running ped-sim with input VCF {pruned_vcf}")
    try:
        # Following the exact command from Lab7
        cmd = [
            ped_sim_exec,
            "-d", pedigree_def_file,
            "-m", refined_map,
            "-o", output_prefix,
            "-i", pruned_vcf,
            "--intf", interfere_file,
            "--seed", "1234",
            "--fam",
            "--mrca"
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Execute ped-sim with full logging
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Log output for debugging
        logger.info("Ped-sim output:")
        logger.info(result.stdout)
        
        if result.stderr:
            logger.warning("Ped-sim warnings/errors:")
            logger.warning(result.stderr)
        
        # Check if output files were created
        if os.path.exists(expected_vcf):
            logger.info(f"Ped-sim VCF output: {expected_vcf}")
            
            # Generate statistics for the VCF
            try:
                stats_output = f"{output_prefix}.vchk"
                subprocess.run(
                    ["bcftools", "stats", "-s", "-", expected_vcf, ">", stats_output],
                    shell=True,
                    check=True
                )
                logger.info(f"Generated VCF stats: {stats_output}")
            except Exception as e:
                logger.warning(f"Could not generate VCF stats: {e}")
        else:
            logger.error(f"Ped-sim VCF output not found: {expected_vcf}")
            return None, None
        
        if os.path.exists(expected_fam):
            logger.info(f"Ped-sim FAM output: {expected_fam}")
        else:
            logger.warning(f"Ped-sim FAM output not found: {expected_fam}")
            
        if not os.path.exists(expected_seg):
            logger.error(f"Ped-sim segments file not found: {expected_seg}")
            return None, None
            
        logger.info(f"Ped-sim segments file: {expected_seg}")
        
        # Create a dictionary file mapping numeric IDs to user IDs (for evaluation)
        seg_dict_file = f"{output_prefix}.seg_dict.txt"
        if not os.path.exists(seg_dict_file):
            try:
                # Extract unique IDs from segments file
                with open(expected_seg, 'r') as seg_file:
                    ids = set()
                    for line in seg_file:
                        parts = line.strip().split("\t")
                        if len(parts) >= 2:
                            ids.add(parts[0])
                            ids.add(parts[1])
                
                # Create mapping dictionary
                with open(seg_dict_file, 'w') as dict_file:
                    for id_val in sorted(ids):
                        dict_file.write(f"{id_val}\t{id_val}\n")
                
                logger.info(f"Created segment ID mapping file: {seg_dict_file}")
            except Exception as e:
                logger.warning(f"Could not create segment ID mapping: {e}")
        
        # Return both the segments file and VCF file
        return expected_seg, expected_vcf
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running ped-sim: {e}")
        if e.stdout:
            logger.error(f"Stdout: {e.stdout}")
        if e.stderr:
            logger.error(f"Stderr: {e.stderr}")
        return None, None
    except Exception as e:
        logger.error(f"Unexpected error during ped-sim: {e}")
        return None, None

# ---------- Lab 3: Quality Control and Phasing Functions ----------

def perform_quality_control(vcf_file, output_dir):
    """
    Perform quality control on a VCF file
    
    Args:
        vcf_file: Path to input VCF file
        output_dir: Directory for QC results
    
    Returns:
        Path to the processed VCF file after QC
    """
    logger.info(f"Performing quality control on {vcf_file}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get filename without extension
    base_name = os.path.basename(vcf_file).split('.')[0]
    
    # Define output file paths
    qc_log_file = os.path.join(output_dir, f"{base_name}_qc.log")
    qc_stats_file = os.path.join(output_dir, f"{base_name}_qc_stats.txt")
    filtered_vcf = os.path.join(output_dir, f"{base_name}_filtered.vcf.gz")
    
    # If filtered VCF already exists, use it
    if os.path.exists(filtered_vcf):
        logger.info(f"Using existing filtered VCF: {filtered_vcf}")
        return filtered_vcf
    
    try:
        # Check if bcftools is available
        try:
            subprocess.run(["which", "bcftools"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            logger.warning("bcftools not found. Skipping QC.")
            return vcf_file
        
        # Use bcftools to check VCF file integrity and get basic stats
        logger.info("Checking VCF file integrity...")
        try:
            subprocess.run(["bcftools", "stats", vcf_file], 
                          stdout=open(qc_stats_file, 'w'),
                          stderr=open(qc_log_file, 'w'),
                          check=True)
        except subprocess.CalledProcessError as e:
            logger.warning(f"Could not run bcftools stats: {e}. Continuing with filtering.")
        
        # Filter the VCF file to remove problematic variants
        logger.info("Filtering VCF file...")
        try:
            subprocess.run([
                "bcftools", "view",
                "--exclude", "F_MISSING > 0.1",  # Exclude variants with >10% missing data
                "--min-alleles", "2",            # Keep only biallelic and multiallelic sites
                "--max-alleles", "4",            # Limit to max 4 alleles for compatibility
                "-Oz",                           # Output compressed VCF
                "-o", filtered_vcf,
                vcf_file
            ], check=True)
            
            # Index the filtered VCF
            logger.info("Indexing filtered VCF...")
            subprocess.run(["bcftools", "index", filtered_vcf], check=True)
            
            logger.info(f"Quality control completed. Filtered VCF: {filtered_vcf}")
            return filtered_vcf
        except subprocess.CalledProcessError as e:
            logger.warning(f"Could not filter VCF: {e}. Using original VCF file.")
            return vcf_file
    except Exception as e:
        logger.error(f"Unexpected error during quality control: {e}")
        return vcf_file

def perform_qc_and_phase_vcf(vcf_file, output_dir, utils_dir, references_dir):
    """
    Perform QC and phase a VCF file using Beagle
    
    Args:
        vcf_file: Path to input VCF file
        output_dir: Directory for output files
        utils_dir: Directory containing Beagle JAR
        references_dir: Directory containing genetic maps and reference panels
    
    Returns:
        Path to the phased VCF file
    """
    logger.info(f"Performing QC and phasing on VCF file: {vcf_file}")
    
    # Get base name of the VCF file
    base_name = os.path.basename(vcf_file).split('.')[0]
    
    # Setup directory structure
    processed_dir = os.path.join(output_dir, "processed_data")
    unphased_dir = os.path.join(processed_dir, "unphased_samples")
    phased_dir = os.path.join(processed_dir, "phased_samples")
    
    # Create directories if they don't exist
    os.makedirs(unphased_dir, exist_ok=True)
    os.makedirs(phased_dir, exist_ok=True)
    
    # Define output file path for the merged phased VCF
    merged_vcf = os.path.join(output_dir, f"{base_name}_phased.vcf.gz")
    
    # If merged phased VCF already exists, use it
    if os.path.exists(merged_vcf) and os.path.exists(f"{merged_vcf}.tbi"):
        logger.info(f"Using existing phased VCF: {merged_vcf}")
        return merged_vcf
    
    # Define path to Beagle JAR
    beagle_jar = os.path.join(utils_dir, "beagle.17Dec24.224.jar")
    
    # Check if JAR exists
    if not os.path.exists(beagle_jar):
        logger.error(f"Beagle JAR file not found: {beagle_jar}")
        return None
    
    # Step 1: Split by chromosome and perform QC
    logger.info("Step 1: Splitting VCF by chromosome and performing QC")
    
    # Process each chromosome
    for chrom in range(1, 23):
        logger.info(f"Processing chromosome {chrom}...")
        
        # Define output file for QC'd chromosome
        qc_vcf = os.path.join(unphased_dir, f"{base_name}_qcfinished_chr{chrom}.vcf.gz")
        
        # Skip if already exists
        if os.path.exists(qc_vcf) and os.path.exists(f"{qc_vcf}.tbi"):
            logger.info(f"Using existing QC'd VCF for chromosome {chrom}")
            continue
        
        # Extract chromosome, apply QC, and sort
        cmd = f"""
        bcftools view "{vcf_file}" \
            --regions "{chrom}" \
            --types snps \
            -m2 -M2 \
            -i 'strlen(REF)=1 && strlen(ALT)=1' | \
        bcftools norm --rm-dup exact | \
        bcftools view \
            -q 0.05:minor \
            -i 'F_MISSING < 0.05' | \
        bcftools sort -Oz -o "{qc_vcf}"
        """
        
        try:
            logger.info(f"Running QC for chromosome {chrom}")
            subprocess.run(cmd, shell=True, check=True)
            
            # Index the QC'd VCF
            subprocess.run(["bcftools", "index", "-f", qc_vcf], check=True)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"QC failed for chromosome {chrom}: {e}")
            continue
    
    # Step 2: Phase each chromosome
    logger.info("Step 2: Phasing each chromosome")
    
    phased_chr_files = []
    
    for chrom in range(1, 23):
        logger.info(f"Phasing chromosome {chrom}")
        
        # Define input and output files
        input_vcf = os.path.join(unphased_dir, f"{base_name}_qcfinished_chr{chrom}.vcf.gz")
        ref_vcf = os.path.join(references_dir, f"onethousandgenomes_genotype/onethousandgenomes_genotyped_phased.chr{chrom}.vcf.gz")
        map_file = os.path.join(references_dir, f"genetic_maps/beagle_genetic_maps/plink.chr{chrom}.GRCh38.map")
        output_prefix = os.path.join(phased_dir, f"{base_name}_phased_chr{chrom}_temp")
        phased_vcf = f"{output_prefix}.vcf.gz"
        sorted_vcf = os.path.join(phased_dir, f"{base_name}_phased_chr{chrom}.vcf.gz")
        
        # Check if input VCF exists
        if not os.path.exists(input_vcf):
            logger.warning(f"QC'd VCF file not found for chromosome {chrom}: {input_vcf}")
            continue
        
        try:
            # Run Beagle phasing
            if os.path.exists(ref_vcf):
                logger.info(f"Running Beagle with reference panel for chromosome {chrom}")
                subprocess.run([
                    "java", "-jar", beagle_jar,
                    f"gt={input_vcf}",
                    f"ref={ref_vcf}",
                    f"map={map_file}",
                    f"out={output_prefix}"
                ], check=True)
            else:
                logger.info(f"Running Beagle without reference panel for chromosome {chrom}")
                subprocess.run([
                    "java", "-jar", beagle_jar,
                    f"gt={input_vcf}",
                    f"map={map_file}",
                    f"out={output_prefix}"
                ], check=True)
            
            # Check if output was created
            if not os.path.exists(phased_vcf):
                logger.warning(f"Phasing failed for chromosome {chrom}. Output file not found.")
                continue
            
            # Index the file
            subprocess.run(["tabix", "-f", "-p", "vcf", phased_vcf], check=True)
            
            # Add INFO field definition and sort
            logger.info(f"Sorting VCF for chromosome {chrom}")
            
            # Create a temporary header file
            header_file = os.path.join(phased_dir, f"header_chr{chrom}.txt")
            with open(header_file, 'w') as f:
                f.write('##INFO=<ID=END,Number=1,Type=Integer,Description="End position of the variant">\n')
            
            # Run bcftools commands separately
            try:
                # First annotate
                annotated_vcf = os.path.join(phased_dir, f"{base_name}_phased_chr{chrom}_annotated.vcf.gz")
                subprocess.run([
                    "bcftools", "annotate", 
                    "--header-lines", header_file,
                    "-Oz", "-o", annotated_vcf, 
                    phased_vcf
                ], check=True)
                
                # Then sort
                subprocess.run([
                    "bcftools", "sort",
                    "-Oz", "-o", sorted_vcf,
                    annotated_vcf
                ], check=True)
                
                # Remove temporary files
                if os.path.exists(annotated_vcf):
                    os.remove(annotated_vcf)
                if os.path.exists(header_file):
                    os.remove(header_file)
                    
            except subprocess.CalledProcessError as e:
                logger.error(f"Error during annotation and sorting for chromosome {chrom}: {e}")
                continue
            
            # Index the sorted file
            subprocess.run(["tabix", "-f", "-p", "vcf", sorted_vcf], check=True)
            
            # If sorted file and index exist, remove temp files
            if os.path.exists(sorted_vcf) and os.path.exists(f"{sorted_vcf}.tbi"):
                os.remove(phased_vcf)
                os.remove(f"{phased_vcf}.tbi")
                if os.path.exists(f"{phased_vcf}.log"):
                    os.remove(f"{phased_vcf}.log")
                
                phased_chr_files.append(sorted_vcf)
                logger.info(f"Successfully phased chromosome {chrom}")
            else:
                logger.warning(f"Failed to create sorted phased VCF for chromosome {chrom}")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error during phasing for chromosome {chrom}: {e}")
            continue
    
    # Step 3: Merge all phased chromosomes
    logger.info("Step 3: Merging all phased chromosomes")
    
    if len(phased_chr_files) == 0:
        logger.error("No phased chromosome files available for merging")
        return None
    
    try:
        # Merge all phased chromosome files
        logger.info(f"Merging {len(phased_chr_files)} phased chromosome files")
        cmd = ["bcftools", "concat", "-Oz", "-o", merged_vcf] + phased_chr_files
        subprocess.run(cmd, check=True)
        
        # Index the merged VCF
        subprocess.run(["tabix", "-f", "-p", "vcf", merged_vcf], check=True)
        
        logger.info(f"Successfully created merged phased VCF: {merged_vcf}")
        return merged_vcf
    except subprocess.CalledProcessError as e:
        logger.error(f"Error merging phased files: {e}")
        return None

# ---------- Lab 4-6: IBD Detection Functions ----------

def run_ibis_detection(vcf_file, output_dir, utils_dir, references_dir):
    """
    Run IBIS IBD detection
    
    Args:
        vcf_file: Path to input VCF file
        output_dir: Directory for output files
        utils_dir: Directory containing IBIS executable
        references_dir: Directory containing genetic maps
    
    Returns:
        Path to the IBIS results file
    """
    logger.info(f"Running IBIS IBD detection on {vcf_file}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Define paths
    base_name = os.path.basename(vcf_file).split('.')[0]
    plink_prefix = os.path.join(output_dir, f"{base_name}_plink")
    gm_prefix = os.path.join(output_dir, f"{base_name}_gm")
    ibis_output = os.path.join(output_dir, f"{base_name}_ibis")
    ibis_executable = os.path.join(utils_dir, "ibis/ibis")
    
    # Check if output already exists
    expected_output = f"{ibis_output}.seg"
    if os.path.exists(expected_output):
        logger.info(f"Using existing IBIS output: {expected_output}")
        return expected_output
    
    try:
        # Convert VCF to PLINK format
        logger.info("Converting VCF to PLINK format...")
        subprocess.run([
            "plink2",
            "--vcf", vcf_file,
            "--make-bed",
            "--out", plink_prefix
        ], check=True)
        
        # For merged VCF files containing all chromosomes, determine chromosomes in file
        is_merged_vcf = True
        chrom = None
        
        # Try to determine from the filename if it's a chromosome-specific file
        for i in range(1, 23):
            if f"chr{i}" in vcf_file:
                is_merged_vcf = False
                chrom = i
                break
                
        # If no chromosome found in filename, check VCF header
        if is_merged_vcf:
            logger.info("Detecting chromosomes in VCF file...")
            try:
                # Use bcftools to check chromosomes in the VCF
                result = subprocess.run(
                    ["bcftools", "index", "--stats", vcf_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )
                
                # Parse the result to find chromosomes
                chroms_in_vcf = set()
                for line in result.stdout.split('\n'):
                    if line.startswith('#'):
                        continue
                    parts = line.split('\t')
                    if len(parts) >= 1:
                        chr_name = parts[0]
                        # Only consider numeric chromosomes 1-22
                        if chr_name.isdigit() and 1 <= int(chr_name) <= 22:
                            chroms_in_vcf.add(int(chr_name))
                
                if len(chroms_in_vcf) > 1:
                    logger.info(f"Detected multiple chromosomes in VCF: {sorted(chroms_in_vcf)}")
                elif len(chroms_in_vcf) == 1:
                    chrom = list(chroms_in_vcf)[0]
                    is_merged_vcf = False
                    logger.info(f"Detected single chromosome {chrom} in VCF")
            except Exception as e:
                logger.warning(f"Could not determine chromosomes from VCF: {e}")
                
        # Add genetic map to BIM file
        if is_merged_vcf:
            logger.info("Handling merged VCF file with multiple chromosomes")
            
            # Create a temporary combined genetic map
            temp_map_file = os.path.join(output_dir, "combined_genetic_map.map")
            with open(temp_map_file, 'w') as outfile:
                for chr_num in range(1, 23):
                    chr_map = os.path.join(references_dir, f"genetic_maps/ibis_genetic_maps/plink.chr{chr_num}.GRCh38.map")
                    if os.path.exists(chr_map):
                        logger.info(f"Adding chromosome {chr_num} to combined map")
                        with open(chr_map, 'r') as infile:
                            for line in infile:
                                outfile.write(line)
            
            genetic_map = temp_map_file
            logger.info(f"Created combined genetic map for all chromosomes at {genetic_map}")
        else:
            # Single chromosome file
            if chrom is None:
                logger.warning("Could not determine chromosome, using chromosome 1 as fallback")
                chrom = 1
            
            logger.info(f"Using genetic map for chromosome {chrom}")
            genetic_map = os.path.join(references_dir, f"genetic_maps/ibis_genetic_maps/plink.chr{chrom}.GRCh38.map")
        
        # Create BIM file with genetic map positions
        try:
            logger.info("Creating BIM file with genetic map positions")
            
            # Make sure the input BIM file exists
            if not os.path.exists(f"{plink_prefix}.bim"):
                logger.error(f"Input BIM file not found: {plink_prefix}.bim")
                return None
            
            # First, load the genetic map
            genetic_map_data = {}
            if os.path.exists(genetic_map):
                logger.info(f"Loading genetic map from {genetic_map}")
                with open(genetic_map, 'r') as f:
                    # Skip header if present
                    first_line = f.readline()
                    if first_line.startswith('#') or 'chr' in first_line.lower():
                        # Skip header
                        pass
                    else:
                        # Parse first line if it's data
                        parts = first_line.strip().split()
                        if len(parts) >= 3:
                            pos = int(parts[1])
                            # Use male cM map
                            cm = float(parts[2])
                            key = (parts[0], pos)
                            genetic_map_data[key] = cm
                    
                    # Parse remaining lines
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 3:
                            try:
                                chrom = parts[0].replace('chr', '')
                                pos = int(parts[1])
                                # Use male cM map
                                cm = float(parts[2])
                                key = (chrom, pos)
                                genetic_map_data[key] = cm
                            except (ValueError, IndexError):
                                continue
                
                logger.info(f"Loaded {len(genetic_map_data)} positions from genetic map")
            else:
                logger.warning(f"Genetic map not found: {genetic_map}")
                logger.info("Creating BIM file without genetic mapping")
            
            # Now read the BIM file and create a new one with genetic positions
            with open(f"{plink_prefix}.bim", 'r') as infile, open(f"{gm_prefix}.bim", 'w') as outfile:
                for line in infile:
                    parts = line.strip().split()
                    if len(parts) >= 6:
                        chrom = parts[0]
                        rs_id = parts[1]
                        # The genetic position will be updated if found in map
                        gen_pos = "0"  
                        phys_pos = int(parts[3])
                        allele1 = parts[4]
                        allele2 = parts[5]
                        
                        # Look up genetic position
                        key = (chrom, phys_pos)
                        if key in genetic_map_data:
                            gen_pos = str(genetic_map_data[key])
                        
                        # Update the BIM line with the genetic position
                        new_line = f"{chrom}\t{rs_id}\t{gen_pos}\t{phys_pos}\t{allele1}\t{allele2}\n"
                        outfile.write(new_line)
            
            logger.info(f"Successfully created BIM file with genetic map positions: {gm_prefix}.bim")
            
            # Verify the file was created
            if not os.path.exists(f"{gm_prefix}.bim") or os.path.getsize(f"{gm_prefix}.bim") == 0:
                logger.error(f"Failed to create BIM file: {gm_prefix}.bim")
                # As a fallback, copy the original BIM file
                logger.info("Using original BIM file as fallback")
                shutil.copy(f"{plink_prefix}.bim", f"{gm_prefix}.bim")
        
        except Exception as e:
            logger.error(f"Error creating BIM file with genetic map: {e}")
            # As a fallback, copy the original BIM file
            logger.info("Using original BIM file as fallback due to error")
            shutil.copy(f"{plink_prefix}.bim", f"{gm_prefix}.bim")
        
        # Copy other PLINK files
        shutil.copy(f"{plink_prefix}.bed", f"{gm_prefix}.bed")
        shutil.copy(f"{plink_prefix}.fam", f"{gm_prefix}.fam")
        
        # Run IBIS
        logger.info("Running IBIS...")
        subprocess.run([
            ibis_executable,
            f"{gm_prefix}.bed",
            f"{gm_prefix}.bim",
            f"{gm_prefix}.fam",
            "-ibd2",
            "-min_l", "7", "-mt", "436", "-er", ".004",
            "-min_l2", "2", "-mt2", "186", "-er2", ".008",
            "-o", ibis_output,
            "-printCoef", "-noFamID"
        ], check=True)
        
        logger.info(f"IBIS detection completed. Output: {ibis_output}.seg")
        return f"{ibis_output}.seg"
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error during IBIS detection: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during IBIS detection: {e}")
        return None

def run_refined_ibd_detection(vcf_file, output_dir, utils_dir, references_dir):
    """
    Run Refined-IBD detection
    
    Args:
        vcf_file: Path to input VCF file
        output_dir: Directory for output files
        utils_dir: Directory containing Refined-IBD JAR
        references_dir: Directory containing genetic maps
    
    Returns:
        Path to the Refined-IBD results file
    """
    logger.info(f"Running Refined-IBD detection on {vcf_file}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Define paths
    base_name = os.path.basename(vcf_file).split('.')[0]
    refined_ibd_jar = os.path.join(utils_dir, "refined-ibd.17Jan20.102.jar")
    merge_ibd_jar = os.path.join(utils_dir, "merge-ibd-segments.17Jan20.102.jar")
    
    # Check if JARs exist
    if not os.path.exists(refined_ibd_jar):
        logger.error(f"Refined-IBD JAR file not found: {refined_ibd_jar}")
        return None
    
    output_prefix = os.path.join(output_dir, f"{base_name}_refinedibd")
    expected_output = f"{output_prefix}.ibd"
    
    # Check if output already exists
    if os.path.exists(expected_output):
        logger.info(f"Using existing Refined-IBD output: {expected_output}")
        return expected_output
    
    # Check if vcf_file is a merged file or chromosome-specific
    is_merged_vcf = True
    for i in range(1, 23):
        if f"chr{i}" in vcf_file:
            is_merged_vcf = False
            break
    
    if is_merged_vcf:
        logger.info("Detected merged VCF file with multiple chromosomes")
        logger.info("For Refined-IBD, processing each chromosome separately and combining results")
        
        # Create directory for per-chromosome files
        chr_dir = os.path.join(output_dir, "per_chromosome")
        os.makedirs(chr_dir, exist_ok=True)
        
        # Split VCF by chromosome
        all_outputs = []
        
        for chrom in range(1, 23):
            logger.info(f"Processing chromosome {chrom}...")
            
            # Extract single chromosome from VCF
            chr_vcf = os.path.join(chr_dir, f"{base_name}_chr{chrom}.vcf.gz")
            
            # Check if file already exists
            if not os.path.exists(chr_vcf):
                try:
                    # Extract chromosome using bcftools
                    subprocess.run([
                        "bcftools", "view",
                        "-r", str(chrom),
                        "-O", "z",
                        "-o", chr_vcf,
                        vcf_file
                    ], check=True)
                    
                    # Index the file
                    subprocess.run(["bcftools", "index", "--tbi", chr_vcf], check=True)
                except Exception as e:
                    logger.warning(f"Error extracting chromosome {chrom}: {e}")
                    continue
            
            # Define chromosome-specific genetic map
            genetic_map = os.path.join(references_dir, f"genetic_maps/beagle_genetic_maps/plink.chr{chrom}.GRCh38.map")
            
            if not os.path.exists(genetic_map):
                logger.warning(f"Genetic map not found for chromosome {chrom}: {genetic_map}")
                continue
                
            # Run up to 3 instances of Refined-IBD 
            chr_outputs = []
            for run in range(1, 4):
                # Define chromosome-specific output
                chr_output_prefix = os.path.join(chr_dir, f"{base_name}_chr{chrom}_run{run}_refinedibd")
                
                # Run Refined-IBD for this chromosome
                try:
                    logger.info(f"Running Refined-IBD run {run} for chromosome {chrom}...")
                    subprocess.run([
                        "java", "-jar", refined_ibd_jar,
                        "gt=" + chr_vcf,
                        "out=" + chr_output_prefix,
                        "map=" + genetic_map,
                        "window=50", "length=1.5", "lod=3"
                    ], check=True)
                    
                    # Check if output was created
                    chr_output = f"{chr_output_prefix}.ibd"
                    if os.path.exists(chr_output):
                        logger.info(f"Refined-IBD run {run} completed for chromosome {chrom}")
                        chr_outputs.append(chr_output)
                    else:
                        logger.warning(f"No output produced for chromosome {chrom} run {run}")
                except Exception as e:
                    logger.warning(f"Error running Refined-IBD for chromosome {chrom} run {run}: {e}")
            
            # Merge the runs for this chromosome if multiple runs succeeded
            if len(chr_outputs) > 0:
                if len(chr_outputs) > 1:
                    # Concatenate outputs
                    merged_chr_file = os.path.join(chr_dir, f"{base_name}_chr{chrom}_merged.ibd")
                    with open(merged_chr_file, 'w') as outfile:
                        for run_file in chr_outputs:
                            with open(run_file, 'r') as infile:
                                for line in infile:
                                    outfile.write(line)
                    
                    # Use merge-ibd-segments to postprocess
                    merged_post_file = os.path.join(chr_dir, f"{base_name}_chr{chrom}_refinedibd.ibd")
                    try:
                        # Use merge-ibd-segments to post-process if JAR exists
                        if os.path.exists(merge_ibd_jar):
                            with open(merged_post_file, 'w') as outfile:
                                subprocess.run([
                                    "java", "-jar", merge_ibd_jar,
                                    chr_vcf, genetic_map, "0.6", "1"
                                ], stdin=open(merged_chr_file), stdout=outfile, check=True)
                            all_outputs.append(merged_post_file)
                        else:
                            # Just use the concatenated file
                            all_outputs.append(merged_chr_file)
                    except Exception as e:
                        logger.warning(f"Error merging IBD segments for chromosome {chrom}: {e}")
                        # Use the concatenated file as fallback
                        all_outputs.append(merged_chr_file)
                else:
                    # Only one run, just add it directly
                    all_outputs.append(chr_outputs[0])
            
                    # Combine all chromosome outputs
        if all_outputs:
            logger.info(f"Combining results from {len(all_outputs)} chromosomes")
            
            with open(expected_output, 'w') as outfile:
                for idx, chr_file in enumerate(all_outputs):
                    with open(chr_file, 'r') as infile:
                        # Skip header in subsequent files
                        for line in infile:
                            outfile.write(line)
            
            logger.info(f"Combined Refined-IBD output: {expected_output}")
            return expected_output
        else:
            logger.error("No chromosome results were produced")
            return None
    
    else:
        # Single chromosome processing
        chrom = None
        # Try to determine from the filename
        for i in range(1, 23):
            if f"chr{i}" in vcf_file:
                chrom = i
                break
                
        if chrom is None:
            logger.warning("Could not determine chromosome, using chromosome 1 as fallback")
            chrom = 1
        
        logger.info(f"Processing single chromosome {chrom}")
        genetic_map = os.path.join(references_dir, f"genetic_maps/beagle_genetic_maps/plink.chr{chrom}.GRCh38.map")
        
        if not os.path.exists(genetic_map):
            logger.error(f"Genetic map not found: {genetic_map}")
            return None
        
        try:
            # Run Refined-IBD
            logger.info(f"Running Refined-IBD with genetic map for chromosome {chrom}...")
            subprocess.run([
                "java", "-jar", refined_ibd_jar,
                "gt=" + vcf_file,
                "out=" + output_prefix,
                "map=" + genetic_map,
                "window=50", "length=1.5", "lod=3"
            ], check=True)
            
            # Check if output file was created
            if os.path.exists(expected_output):
                logger.info(f"Refined-IBD detection completed. Output: {expected_output}")
                return expected_output
            else:
                logger.error(f"Refined-IBD output file not found: {expected_output}")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error during Refined-IBD detection: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during Refined-IBD detection: {e}")
            return None

def run_hap_ibd_detection(vcf_file, output_dir, utils_dir, references_dir):
    """
    Run Hap-IBD detection
    
    Args:
        vcf_file: Path to input VCF file
        output_dir: Directory for output files
        utils_dir: Directory containing Hap-IBD JAR
        references_dir: Directory containing genetic maps
    
    Returns:
        Path to the Hap-IBD results file
    """
    logger.info(f"Running Hap-IBD detection on {vcf_file}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Define paths
    base_name = os.path.basename(vcf_file).split('.')[0]
    hap_ibd_jar = os.path.join(utils_dir, "hap-ibd.jar")
    
    # Check if JAR exists
    if not os.path.exists(hap_ibd_jar):
        logger.error(f"Hap-IBD JAR file not found: {hap_ibd_jar}")
        return None
    
    output_prefix = os.path.join(output_dir, f"{base_name}_hapibd")
    expected_output = f"{output_prefix}.ibd.gz"
    
    # Check if output already exists
    if os.path.exists(expected_output):
        logger.info(f"Using existing Hap-IBD output: {expected_output}")
        return expected_output
    
    # Check if this is a merged file with multiple chromosomes
    is_merged_vcf = True
    for i in range(1, 23):
        if f"chr{i}" in vcf_file:
            is_merged_vcf = False
            break
    
    if is_merged_vcf:
        logger.info("Detected merged VCF file with multiple chromosomes")
        logger.info("For Hap-IBD, processing each chromosome separately and combining results")
        
        # Create directory for per-chromosome files
        chr_dir = os.path.join(output_dir, "per_chromosome")
        os.makedirs(chr_dir, exist_ok=True)
        
        # Split VCF by chromosome
        all_outputs = []
        
        for chrom in range(1, 23):
            logger.info(f"Processing chromosome {chrom}...")
            
            # Extract single chromosome from VCF
            chr_vcf = os.path.join(chr_dir, f"{base_name}_chr{chrom}.vcf.gz")
            
            # Check if file already exists
            if not os.path.exists(chr_vcf):
                try:
                    # Extract chromosome using bcftools
                    subprocess.run([
                        "bcftools", "view",
                        "-r", str(chrom),
                        "-O", "z",
                        "-o", chr_vcf,
                        vcf_file
                    ], check=True)
                    
                    # Index the file
                    subprocess.run(["bcftools", "index", "--tbi", chr_vcf], check=True)
                except Exception as e:
                    logger.warning(f"Error extracting chromosome {chrom}: {e}")
                    continue
            
            # Define chromosome-specific genetic map
            genetic_map = os.path.join(references_dir, f"genetic_maps/beagle_genetic_maps/plink.chr{chrom}.GRCh38.map")
            
            if not os.path.exists(genetic_map):
                logger.warning(f"Genetic map not found for chromosome {chrom}: {genetic_map}")
                continue
                
            # Define chromosome-specific output
            chr_output_prefix = os.path.join(chr_dir, f"{base_name}_chr{chrom}_hapibd")
            
            # Run Hap-IBD for this chromosome
            try:
                logger.info(f"Running Hap-IBD for chromosome {chrom}...")
                subprocess.run([
                    "java", "-jar", hap_ibd_jar,
                    f"gt={chr_vcf}",
                    f"out={chr_output_prefix}",
                    f"map={genetic_map}"
                ], check=True)
                
                # Check if output was created
                chr_output = f"{chr_output_prefix}.ibd.gz"
                if os.path.exists(chr_output):
                    logger.info(f"Hap-IBD completed for chromosome {chrom}")
                    all_outputs.append(chr_output)
                else:
                    logger.warning(f"No output produced for chromosome {chrom}")
            except Exception as e:
                logger.warning(f"Error running Hap-IBD for chromosome {chrom}: {e}")
        
        # Combine all chromosome outputs
        if all_outputs:
            logger.info(f"Combining results from {len(all_outputs)} chromosomes")
            
            try:
                # Use gzip concatenation for gzipped files
                with gzip.open(expected_output, 'wb') as outfile:
                    for chr_file in all_outputs:
                        with gzip.open(chr_file, 'rb') as infile:
                            outfile.write(infile.read())
                
                logger.info(f"Combined Hap-IBD output: {expected_output}")
                return expected_output
            except Exception as e:
                logger.error(f"Error combining chromosome outputs: {e}")
                
                # Return the first output as a fallback if combining failed
                if all_outputs:
                    logger.warning(f"Using first chromosome output as fallback: {all_outputs[0]}")
                    return all_outputs[0]
                    
                return None
        else:
            logger.error("No chromosome results were produced")
            return None
    
    else:
        # Single chromosome processing
        chrom = None
        # Try to determine from the filename
        for i in range(1, 23):
            if f"chr{i}" in vcf_file:
                chrom = i
                break
                
        if chrom is None:
            logger.warning("Could not determine chromosome, using chromosome 1 as fallback")
            chrom = 1
        
        logger.info(f"Processing single chromosome {chrom}")
        genetic_map = os.path.join(references_dir, f"genetic_maps/beagle_genetic_maps/plink.chr{chrom}.GRCh38.map")
        
        if not os.path.exists(genetic_map):
            logger.error(f"Genetic map not found: {genetic_map}")
            return None
        
        try:
            # Run Hap-IBD
            logger.info(f"Running Hap-IBD with genetic map for chromosome {chrom}...")
            subprocess.run([
                "java", "-jar", hap_ibd_jar,
                f"gt={vcf_file}",
                f"out={output_prefix}",
                f"map={genetic_map}"
            ], check=True)
            
            # Check if output file was created
            if os.path.exists(expected_output):
                logger.info(f"Hap-IBD detection completed. Output: {expected_output}")
                return expected_output
            else:
                logger.error(f"Hap-IBD output file not found: {expected_output}")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error during Hap-IBD detection: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during Hap-IBD detection: {e}")
            return None

# ---------- Lab 8: Evaluation Functions ----------

def load_truth_segments(file_path):
    """Load ground truth IBD segments from ped-sim"""
    logger.info(f"Loading truth segments from: {file_path}")
    
    try:
        # Read the truth segments file
        df = pd.read_csv(file_path, sep="\t", header=None)
        df.columns = ["id1", "id2", "chromosome", "physical_position_start", 
                     "physical_position_end", "IBD_type", "genetic_position_start", 
                     "genetic_position_end", "genetic_length"]
        
        # Add segment length
        df['length'] = df['physical_position_end'] - df['physical_position_start']
        df['tool'] = 'Truth'
        
        # Standardize column names for evaluation
        df['sample1'] = df['id1']
        df['sample2'] = df['id2']
        df['chrom'] = df['chromosome']
        df['start'] = df['physical_position_start']
        df['end'] = df['physical_position_end']
        df['cM'] = df['genetic_length']
        df['segment_id'] = range(len(df))
        
        # Add placeholder haplotype columns if needed for consistent evaluation
        df['sample1_haplotype'] = 0
        df['sample2_haplotype'] = 0
        
        # Summary statistics
        logger.info(f"Loaded {len(df)} truth segments")
        
        if len(df) == 0:
            logger.error("No truth segments loaded. Unable to continue.")
            return pd.DataFrame()
            
        return df
    except Exception as e:
        logger.error(f"Error loading truth segments: {e}")
        return pd.DataFrame()

def load_ibis_segments(file_path):
    """Load IBIS output file"""
    try:
        df = pd.read_csv(file_path, sep="\t", header=None)
        df.columns = ["sample1", "sample2", "chrom", 
                    "phys_start_pos", "phys_end_pos", 
                    "IBD_type", "genetic_start_pos", 
                    "genetic_end_pos", "genetic_seg_length", 
                    "marker_count", "error_count", "error_density"]
        
        # Map IBIS columns to standardized column names for evaluation
        df['start'] = df['phys_start_pos']
        df['end'] = df['phys_end_pos']
        df['cM'] = df['genetic_seg_length']
        df['segment_id'] = range(len(df))
        df['tool'] = 'IBIS'
        df['length'] = df['end'] - df['start']
        
        # Create LOD-like score based on error density (lower error = higher score)
        # Invert error_density to make higher values better
        df['LOD'] = 1.0 / (df['error_density'] + 0.001)  # Add small constant to avoid division by zero
        
        # Add haplotype columns if needed for consistent evaluation
        df['sample1_haplotype'] = 0  # Placeholder if IBIS doesn't specify haplotypes
        df['sample2_haplotype'] = 0
        
        logger.info(f"Loaded {len(df)} IBIS segments")
        return df
    except Exception as e:
        logger.error(f"Error loading IBIS file: {e}")
        return pd.DataFrame()

def load_refined_ibd_segments(file_path):
    """Load Refined-IBD output file"""
    try:
        df = pd.read_csv(file_path, sep="\t", header=None)
        df.columns = ["sample1", "sample1_haplotype", "sample2", 
                      "sample2_haplotype", "chrom", "start", "end", "LOD", "cM"]
        # Create a unique segment ID for each segment
        df['segment_id'] = range(len(df))
        df['tool'] = 'RefinedIBD'
        df['length'] = df['end'] - df['start']
        
        logger.info(f"Loaded {len(df)} Refined-IBD segments")
        return df
    except Exception as e:
        logger.error(f"Error loading Refined-IBD file: {e}")
        return pd.DataFrame()

def load_hap_ibd_segments(file_path):
    """Load Hap-IBD output file"""
    try:
        # Check if the file is gzipped
        open_func = gzip.open if file_path.endswith('.gz') else open
        
        with open_func(file_path, 'rt') as f:
            df = pd.read_csv(f, sep="\t", header=None)
            
        df.columns = ["sample1", "sample1_haplotype", "sample2", 
                      "sample2_haplotype", "chrom", "start", "end", "cM"]
        df['segment_id'] = range(len(df))
        df['tool'] = 'HapIBD'
        df['length'] = df['end'] - df['start']
        
        # Since LOD isn't in the HapIBD output, create a placeholder or use cM as proxy
        df['LOD'] = df['cM']  # Using cM as a proxy for confidence
        
        logger.info(f"Loaded {len(df)} Hap-IBD segments")
        return df
    except Exception as e:
        logger.error(f"Error loading Hap-IBD file: {e}")
        return pd.DataFrame()

def map_sample_ids(truth_df, mapping_file):
    """Map sample IDs in truth data using a mapping dictionary file"""
    logger.info(f"Mapping sample IDs using: {mapping_file}")
    
    if not os.path.exists(mapping_file):
        logger.warning(f"Mapping file not found: {mapping_file}")
        return truth_df
    
    try:
        # Read the mapping dictionary
        sample_id_map = {}
        with open(mapping_file, 'r') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    original_id, numeric_id = parts
                    # Create mapping from original ID to user ID format
                    sample_id_map[original_id] = f"user{numeric_id}"
        
        logger.info(f"Loaded {len(sample_id_map)} sample ID mappings")
        
        # Make a copy of the truth dataframe
        mapped_df = truth_df.copy()
        
        # Apply the mapping to id1 and id2 columns
        mapped_df['sample1'] = mapped_df['sample1'].map(lambda x: f"user{sample_id_map.get(x, x.replace('user', ''))}" if x in sample_id_map else x)
        mapped_df['sample2'] = mapped_df['sample2'].map(lambda x: f"user{sample_id_map.get(x, x.replace('user', ''))}" if x in sample_id_map else x)
        
        # Also update the original id columns
        mapped_df['id1'] = mapped_df['sample1']
        mapped_df['id2'] = mapped_df['sample2']
        
        logger.info(f"Sample ID mapping example: {mapped_df['sample1'].iloc[0]} -> {mapped_df['sample2'].iloc[0]}")
        
        return mapped_df
    except Exception as e:
        logger.error(f"Error mapping sample IDs: {e}")
        return truth_df

def create_interval_tree(truth_df):
    """Create an interval tree from truth segments for efficient overlap checking"""
    trees = {}
    
    logger.info("Building interval trees from truth data...")
    
    # Clean up the dataframe - ensure numeric columns are numeric and no NaNs
    for col in ['start', 'end', 'chrom']:
        if col in truth_df.columns:
            # Convert to numeric and fill NaNs with 0
            truth_df[col] = pd.to_numeric(truth_df[col], errors='coerce').fillna(0).astype(int)
    
    # Filter out any rows with invalid start/end positions
    valid_rows = (truth_df['start'] < truth_df['end']) & (truth_df['start'] >= 0)
    if (~valid_rows).any():
        logger.warning(f"Filtering out {(~valid_rows).sum()} rows with invalid start/end positions")
        truth_df = truth_df[valid_rows].reset_index(drop=True)
    
    # Add haplotype columns if they don't exist
    if 'sample1_haplotype' not in truth_df.columns:
        truth_df['sample1_haplotype'] = 0
    if 'sample2_haplotype' not in truth_df.columns:
        truth_df['sample2_haplotype'] = 0
    
    # Ensure string columns are strings
    for col in ['sample1', 'sample2']:
        if col in truth_df.columns:
            truth_df[col] = truth_df[col].astype(str)
    
    # Create a small subset for evaluation to avoid memory issues
    if len(truth_df) > 1000:
        logger.info(f"Large dataset detected ({len(truth_df)} rows). Using a small subset for evaluation.")
        # Take a small random sample
        truth_subset = truth_df.sample(n=min(1000, len(truth_df))).reset_index(drop=True)
        logger.info(f"Using {len(truth_subset)} randomly selected segments for evaluation")
    else:
        truth_subset = truth_df
    
    # Create trees with and without haplotype information
    for _, row in truth_subset.iterrows():
        try:
            # Ensure chrom, start and end are integers
            chrom = int(row['chrom'])
            start = int(row['start'])
            end = int(row['end'])
            
            # Skip invalid intervals
            if start >= end or start < 0 or end < 0:
                continue
                
            # Create keys in both orders to handle either order in tool data
            pairs = [
                # With haplotypes
                ((str(row['sample1']), int(row['sample1_haplotype'])), 
                 (str(row['sample2']), int(row['sample2_haplotype'])), 
                 chrom),
                ((str(row['sample2']), int(row['sample2_haplotype'])), 
                 (str(row['sample1']), int(row['sample1_haplotype'])), 
                 chrom),
                # Without haplotypes
                ((str(row['sample1']), None), (str(row['sample2']), None), chrom),
                ((str(row['sample2']), None), (str(row['sample1']), None), chrom)
            ]
            
            for sample1, sample2, chr_num in pairs:
                pair_key = (sample1, sample2)
                if (pair_key, chr_num) not in trees:
                    trees[(pair_key, chr_num)] = IntervalTree()
                
                trees[(pair_key, chr_num)].addi(start, end, row['segment_id'])
        except (ValueError, TypeError) as e:
            logger.debug(f"Skipping row due to error: {e}, values: {row[['chrom', 'start', 'end']]}")
            continue
    
    logger.info(f"Created {len(trees)} interval trees")
    return trees

def calculate_overlap(segment, tree):
    """Calculate overlap between a segment and truth segments in the tree"""
    overlaps = tree.overlap(segment['start'], segment['end'])
    if not overlaps:
        return 0, None
    
    # Find the best overlapping segment
    best_overlap = 0
    best_truth_id = None
    
    for interval in overlaps:
        overlap_start = max(segment['start'], interval.begin)
        overlap_end = min(segment['end'], interval.end)
        overlap_length = overlap_end - overlap_start
        
        if overlap_length > best_overlap:
            best_overlap = overlap_length
            best_truth_id = interval.data
    
    return best_overlap / (segment['end'] - segment['start']), best_truth_id

def evaluate_tool(tool_df, truth_trees):
    """Evaluate IBD detection performance for a specific tool"""
    # If the DataFrame is empty, return it without processing
    if len(tool_df) == 0:
        logger.warning(f"Tool: {tool_df.name if hasattr(tool_df, 'name') else 'Unknown'} - No segments to evaluate")
        return tool_df
        
    # Add columns for evaluation metrics
    tool_df['detected_truth'] = False
    tool_df['overlap_pct'] = 0.0
    tool_df['truth_id'] = None
    
    # Debug counters
    total_segments = len(tool_df)
    matched_segments = 0
    
    for idx, row in tool_df.iterrows():
        # Check if we have both sample pair in regular and reversed order
        sample_pairs = [
            # Regular order
            ((row['sample1'], row.get('sample1_haplotype', 0)), 
             (row['sample2'], row.get('sample2_haplotype', 0)),
             row['chrom']),
            # Reversed order
            ((row['sample2'], row.get('sample2_haplotype', 0)), 
             (row['sample1'], row.get('sample1_haplotype', 0)),
             row['chrom'])
        ]
        
        found_match = False
        for sample1, sample2, chrom in sample_pairs:
            pair_key = (sample1, sample2)
            if (pair_key, chrom) in truth_trees:
                overlap_pct, truth_id = calculate_overlap(row, truth_trees[(pair_key, chrom)])
                if overlap_pct > 0:
                    tool_df.at[idx, 'overlap_pct'] = overlap_pct
                    tool_df.at[idx, 'truth_id'] = truth_id
                    tool_df.at[idx, 'detected_truth'] = (overlap_pct >= 0.5)  # Consider >=50% overlap a true positive
                    matched_segments += 1 if overlap_pct >= 0.5 else 0
                    found_match = True
                    break
        
        # Try without haplotypes if no match found and haplotypes present
        if not found_match and 'sample1_haplotype' in row:
            # Create keys without haplotype information
            sample_pairs_no_hap = [
                ((row['sample1'], None), (row['sample2'], None), row['chrom']),
                ((row['sample2'], None), (row['sample1'], None), row['chrom'])
            ]
            
            for sample1, sample2, chrom in sample_pairs_no_hap:
                pair_key = (sample1, sample2)
                if (pair_key, chrom) in truth_trees:
                    overlap_pct, truth_id = calculate_overlap(row, truth_trees[(pair_key, chrom)])
                    if overlap_pct > 0:
                        tool_df.at[idx, 'overlap_pct'] = overlap_pct
                        tool_df.at[idx, 'truth_id'] = truth_id
                        tool_df.at[idx, 'detected_truth'] = (overlap_pct >= 0.5)
                        matched_segments += 1 if overlap_pct >= 0.5 else 0
                        break
    
    # Get the tool name safely
    tool_name = tool_df['tool'].iloc[0] if len(tool_df) > 0 else "Unknown"
    
    # Calculate percentage safely
    percentage = (matched_segments/total_segments*100) if total_segments > 0 else 0
    
    logger.info(f"Tool: {tool_name} - Matched {matched_segments} of {total_segments} segments ({percentage:.2f}%)")
    return tool_df

def evaluate_all_tools(refined_df, hap_df, ibis_df, truth_df):
    """Evaluate all IBD detection tools"""
    # Create interval trees for truth segments
    truth_trees = create_interval_tree(truth_df)
    
    # Store the size of the truth subset used for evaluation
    truth_subset_size = 1000  # Default value - this should match what's in create_interval_tree
    
    # Evaluate each tool
    refined_eval = evaluate_tool(refined_df, truth_trees)
    hap_eval = evaluate_tool(hap_df, truth_trees)
    ibis_eval = evaluate_tool(ibis_df, truth_trees)
    
    # Combine results
    all_results = pd.concat([refined_eval, hap_eval, ibis_eval], ignore_index=True)
    
    # Add attributes to track sampling
    all_results.attrs['truth_subset_size'] = truth_subset_size
    
    return all_results

def calculate_summary_metrics(all_results, truth_df):
    """Calculate summary statistics for each tool"""
    metrics = []
    
    # Count total truth segments
    total_truth = len(truth_df)
    logger.info(f"Total truth segments: {total_truth}")
    
    # Check if we're working with a sample
    is_sample = 'truth_subset_size' in all_results.attrs and all_results.attrs['truth_subset_size'] < total_truth
    if is_sample:
        sample_size = all_results.attrs['truth_subset_size']
        logger.info(f"Working with a sample of {sample_size} segments out of {total_truth} total segments")
        
    for tool_name in ['RefinedIBD', 'HapIBD', 'IBIS']:
        tool_df = all_results[all_results['tool'] == tool_name]
        
        if len(tool_df) == 0:
            logger.warning(f"No segments found for {tool_name}, skipping metrics")
            continue
        
        # Count true positives (segments with >50% overlap)
        true_positives = tool_df['detected_truth'].sum()
        
        # Count false positives (segments with ≤50% overlap)
        false_positives = len(tool_df) - true_positives
        
        # Count truth segments detected by this tool
        detected_truth_ids = set([x for x in tool_df['truth_id'] if x is not None])
        detected_truths = len(detected_truth_ids)
        
        if is_sample:
            # When working with a sample, adjust the metrics
            detection_rate = detected_truths / sample_size if sample_size > 0 else 0
            
            # Estimate total detected from the rate
            estimated_detected = int(detection_rate * total_truth)
            
            # Calculate recall using the estimated total detected
            recall = estimated_detected / total_truth if total_truth > 0 else 0
            
            # For precision, we need to adjust the true positives based on the sample
            precision_from_sample = true_positives / len(tool_df) if len(tool_df) > 0 else 0
            # This is our best estimate of precision without further information
            precision = precision_from_sample
        else:
            # Standard metrics calculation with complete data
            recall = detected_truths / total_truth if total_truth > 0 else 0
            precision = true_positives / len(tool_df) if len(tool_df) > 0 else 0
        
        # Calculate F1 score
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Print detailed info
        logger.info(f"\n{tool_name} Summary:")
        logger.info(f"  Total segments: {len(tool_df)}")
        logger.info(f"  True positives: {true_positives} ({true_positives/len(tool_df)*100:.2f}% of segments)")
        logger.info(f"  False positives: {false_positives} ({false_positives/len(tool_df)*100:.2f}% of segments)")
        logger.info(f"  Unique truth segments detected: {detected_truths}")
        
        if is_sample:
            logger.info(f"  Detection rate in sample: {detection_rate:.4f}")
            logger.info(f"  Estimated total detected: {estimated_detected} ({estimated_detected/total_truth*100:.2f}% of truth)")
        else:
            logger.info(f"  Truth segments detected: {detected_truths} ({detected_truths/total_truth*100:.2f}% of truth)")
            
        logger.info(f"  Precision: {precision:.4f}")
        logger.info(f"  Recall: {recall:.4f}")
        logger.info(f"  F1 Score: {f1:.4f}")
        
        metrics.append({
            'Tool': tool_name,
            'Total Segments': len(tool_df),
            'True Positives': true_positives,
            'False Positives': false_positives,
            'Detected Truth Segments': detected_truths,
            'Precision': precision,
            'Recall': recall,
            'F1 Score': f1
        })
    
    metrics_df = pd.DataFrame(metrics)
    return metrics_df

def plot_summary_barplot(metrics_df, output_dir):
    """Plot summary metrics as a bar chart"""
    plt.figure(figsize=(14, 10))
    
    # Melt the dataframe to make it suitable for grouped bar chart
    plot_metrics = ['Precision', 'Recall', 'F1 Score']
    plot_df = pd.melt(metrics_df, id_vars=['Tool'], value_vars=plot_metrics, 
                      var_name='Metric', value_name='Value')
    
    # Create grouped bar chart
    sns.barplot(x='Tool', y='Value', hue='Metric', data=plot_df)
    
    plt.title('Performance Metrics by IBD Detection Tool')
    plt.ylabel('Score')
    plt.ylim(0, 1)
    plt.grid(True, linestyle='--', alpha=0.7, axis='y')
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, 'ibd_performance_metrics.png')
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved performance metrics plot to: {output_path}")

def create_visualizations(all_results, truth_df, output_dir):
    """Create visualizations for the evaluation results"""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Plot 1: Distribution of segment lengths
    plt.figure(figsize=(12, 8))
    
    # Combine all data
    tools_to_plot = []
    for tool in ['RefinedIBD', 'HapIBD', 'IBIS']:
        if len(all_results[all_results['tool'] == tool]) > 0:
            tools_to_plot.append(tool)
    
    plot_data = []
    for tool in tools_to_plot:
        tool_data = all_results[all_results['tool'] == tool][['length', 'tool']]
        plot_data.append(tool_data)
    
    # Add truth data
    plot_data.append(truth_df[['length', 'tool']])
    
    # Combine data
    combined_data = pd.concat(plot_data)
    
    # Convert length from bp to Mbp
    combined_data['length_mbp'] = combined_data['length'] / 1_000_000
    
    # Plot density
    sns.kdeplot(data=combined_data, x='length_mbp', hue='tool', fill=True, alpha=0.5)
    
    plt.title('Distribution of IBD Segment Lengths')
    plt.xlabel('Segment Length (Mbp)')
    plt.ylabel('Density')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, 'ibd_length_distribution.png')
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved length distribution plot to: {output_path}")
    
    # Plot 2: Histogram of overlap percentages
    plt.figure(figsize=(12, 8))
    
    for tool, color in zip(tools_to_plot, ['blue', 'green', 'red']):
        tool_df = all_results[all_results['tool'] == tool]
        if len(tool_df) > 0:
            plt.hist(tool_df['overlap_pct'], bins=20, alpha=0.5, color=color, label=tool)
    
    plt.title('Distribution of Overlap with Truth Segments')
    plt.xlabel('Overlap Percentage')
    plt.ylabel('Count')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, 'ibd_overlap_histogram.png')
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved overlap histogram to: {output_path}")

def main():
    """Main function to run the complete IBD workflow"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Complete IBD Detection and Evaluation Workflow')
    parser.add_argument('--vcf', type=str, help='Path to input VCF file. If not specified, will use environment variable.')
    parser.add_argument('--pedigree-def', type=str, help='Path to pedigree definition file for ped-sim. If not specified, will use the default.')
    parser.add_argument('--truth', type=str, help='Path to ground truth segments file. If not specified, will use environment variable.')
    parser.add_argument('--mapping', type=str, help='Path to sample ID mapping file. If not specified, will use environment variable.')
    parser.add_argument('--output-dir', type=str, help='Directory for output files. If not specified, will use environment variable.')
    
    args = parser.parse_args()
    
    # Load environment variables
    working_dir, results_dir, data_dir, utils_dir, references_dir = load_environment()
    if not all([working_dir, results_dir, data_dir]):
        logger.error("Failed to load critical environment variables")
        sys.exit(1)  # Exit on error - no fallback
    
    # Set default paths for input files
    if not args.vcf:
        args.vcf = os.path.join(data_dir, "class_data", "merged_opensnps_data_autosomes.vcf.gz")
    
    # Default pedigree definition file
    if not args.pedigree_def:
        pedigree_def = os.path.join(data_dir, "class_data", "pedigree.def")
        
        # Check if pedigree.def exists
        if not os.path.exists(pedigree_def):
            logger.error(f"Pedigree definition file not found: {pedigree_def}")
            sys.exit(1)  # Exit on error - no fallback
    else:
        pedigree_def = args.pedigree_def
    
    if not args.truth:
        args.truth = os.path.join(data_dir, "class_data", "merged_opensnps_autosomes_ped_sim.seg")
    
    if not args.mapping:
        args.mapping = os.path.join(data_dir, "class_data", "ped_sim_run2.seg_dict.txt")
    
    if not args.output_dir:
        args.output_dir = os.path.join(results_dir, "ibd_workflow")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Set up paths for intermediate files
    processed_data_dir = os.path.join(args.output_dir, "processed_data")
    ibis_dir = os.path.join(args.output_dir, "ibis")
    refined_dir = os.path.join(args.output_dir, "refined_ibd")
    hap_dir = os.path.join(args.output_dir, "hap_ibd")
    eval_dir = os.path.join(args.output_dir, "evaluation")
    
    # Create directories
    for dir_path in [processed_data_dir, ibis_dir, refined_dir, hap_dir, eval_dir]:
        os.makedirs(dir_path, exist_ok=True)
    
    # Step 1: Quality Control and Phasing of input VCF
    vcf_file = args.vcf
    input_dir = os.path.join(args.output_dir, "input_processed")
    os.makedirs(input_dir, exist_ok=True)
    
    logger.info("Step 1: Quality Control and Phasing of input VCF")
    try:
        phased_input_vcf = perform_qc_and_phase_vcf(vcf_file, input_dir, utils_dir, references_dir)
        if phased_input_vcf:
            vcf_file = phased_input_vcf
            logger.info(f"Using QC'd and phased input VCF: {vcf_file}")
        else:
            logger.error("QC and phasing of input VCF failed.")
            sys.exit(1)  # Exit on error - no fallback
    except Exception as e:
        logger.error(f"QC and phasing of input VCF failed: {e}")
        sys.exit(1)  # Exit on error - no fallback
    
    # Step 2: Pedigree Simulation with ped-sim (Lab 7) - using phased input
    sim_dir = os.path.join(args.output_dir, "ped_sim")
    os.makedirs(sim_dir, exist_ok=True)
    
    logger.info("Step 2: Pedigree Simulation with ped-sim (using phased input)")
    try:
        # Run the ped-sim simulation using phased input
        truth_segments_file, simulated_vcf = run_ped_sim(vcf_file, pedigree_def, sim_dir, utils_dir, references_dir)
        if simulated_vcf and truth_segments_file:
            # Store the truth segments file for evaluation later
            args.truth = truth_segments_file
            logger.info(f"Using simulated VCF file: {simulated_vcf}")
            logger.info(f"Using truth segments file: {truth_segments_file}")
            
            # Verify and fix simulated VCF format if needed
            logger.info("Verifying and fixing simulated VCF format if needed")
            try:
                # Check if the VCF is properly bgzipped
                test_cmd = f"bcftools view -h {simulated_vcf}"
                test_result = subprocess.run(test_cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                
                if test_result.returncode != 0 and "not compressed with bgzip" in test_result.stderr.decode():
                    logger.warning("Simulated VCF is not properly bgzipped. Fixing...")
                    # Uncompress then recompress with bgzip
                    temp_vcf = os.path.join(sim_dir, "temp_uncompressed.vcf")
                    fixed_vcf = os.path.join(sim_dir, "fixed_ped_sim_output.vcf.gz")
                    
                    # Uncompress
                    with gzip.open(simulated_vcf, 'rb') as f_in:
                        with open(temp_vcf, 'wb') as f_out:
                            f_out.write(f_in.read())
                    
                    # Recompress with bgzip
                    subprocess.run(f"bgzip -c {temp_vcf} > {fixed_vcf}", shell=True, check=True)
                    
                    # Replace original with fixed version
                    os.remove(simulated_vcf)
                    shutil.move(fixed_vcf, simulated_vcf)
                    
                    # Index the fixed VCF
                    subprocess.run(["bcftools", "index", "--tbi", simulated_vcf], check=True)
                    
                    # Clean up
                    os.remove(temp_vcf)
                    logger.info(f"Fixed VCF format and created index: {simulated_vcf}")
                else:
                    logger.info("Simulated VCF is in valid format")
            except Exception as e:
                logger.warning(f"Error while verifying/fixing VCF format: {e}")
            
            # Update vcf_file to the simulated one for next steps
            vcf_file = simulated_vcf
        else:
            logger.error("Ped-sim simulation did not produce all required outputs")
            sys.exit(1)  # Exit on error - no fallback
    except Exception as e:
        logger.error(f"Ped-sim simulation failed: {e}")
        sys.exit(1)  # Exit on error - no fallback
    
    # Step 3: Quality Control and Phasing of simulated VCF
    logger.info("Step 3: Quality Control and Phasing of simulated VCF")
    try:
        # Process the simulated VCF
        phased_sim_vcf = perform_qc_and_phase_vcf(vcf_file, processed_data_dir, utils_dir, references_dir)
        if phased_sim_vcf:
            vcf_file = phased_sim_vcf
            logger.info(f"Using QC'd and phased simulated VCF for IBD detection: {vcf_file}")
        else:
            logger.error("QC and phasing of simulated VCF failed. IBD detection requires phased VCF files.")
            sys.exit(1)  # Exit on error - no fallback
    except Exception as e:
        logger.error(f"QC and phasing of simulated VCF failed: {e}")
        sys.exit(1)  # Exit on error - no fallback
    
    # Paths for results
    ibis_output = None
    refined_output = None
    hap_output = None
    
    # Step 4: IBD Detection (Labs 4-6)
    # Check if VCF file exists
    if not os.path.exists(vcf_file):
        logger.error(f"VCF file not found: {vcf_file}")
        sys.exit(1)  # Exit on error - no fallback
    
    # IBIS Detection (Lab 4)
    logger.info("Step 4.1: IBIS IBD Detection")
    try:
        ibis_output = run_ibis_detection(vcf_file, ibis_dir, utils_dir, references_dir)
        if not ibis_output:
            logger.error("IBIS detection did not produce output")
            ibis_output = None
        else:
            logger.info(f"IBIS detection completed successfully: {ibis_output}")
    except Exception as e:
        logger.error(f"IBIS detection failed: {e}")
        ibis_output = None
    
    # Refined-IBD Detection (Lab 5)
    logger.info("Step 4.2: Refined-IBD Detection")
    try:
        refined_output = run_refined_ibd_detection(vcf_file, refined_dir, utils_dir, references_dir)
        if not refined_output:
            logger.error("Refined-IBD detection did not produce output")
            refined_output = None
        else:
            logger.info(f"Refined-IBD detection completed successfully: {refined_output}")
    except Exception as e:
        logger.error(f"Refined-IBD detection failed: {e}")
        refined_output = None
    
    # Hap-IBD Detection (Lab 6)
    logger.info("Step 4.3: Hap-IBD Detection")
    try:
        hap_output = run_hap_ibd_detection(vcf_file, hap_dir, utils_dir, references_dir)
        if not hap_output:
            logger.error("Hap-IBD detection did not produce output")
            hap_output = None
        else:
            logger.info(f"Hap-IBD detection completed successfully: {hap_output}")
    except Exception as e:
        logger.error(f"Hap-IBD detection failed: {e}")
        hap_output = None
        
    # Check if at least one detection method succeeded
    if not ibis_output and not refined_output and not hap_output:
        logger.error("All IBD detection methods failed. Cannot proceed with evaluation.")
        sys.exit(1)  # Exit on error - no fallback
    
    # Step 5: Evaluation (Lab 8)
    logger.info("Step 5: Evaluation")
    
    # Load truth segments
    try:
        truth_df = load_truth_segments(args.truth)
        if len(truth_df) == 0:
            logger.error("Failed to load truth segments")
            sys.exit(1)  # Exit on error - no fallback
    except Exception as e:
        logger.error(f"Error loading truth segments: {e}")
        sys.exit(1)  # Exit on error - no fallback
    
    # Map sample IDs
    try:
        truth_df = map_sample_ids(truth_df, args.mapping)
    except Exception as e:
        logger.warning(f"Error mapping sample IDs: {e}. Using unmapped IDs.")
    
    # Load result files - use empty dataframes for methods that failed
    ibis_df = pd.DataFrame()
    refined_df = pd.DataFrame()
    hap_df = pd.DataFrame()
    
    # Load IBIS results if available
    if ibis_output:
        try:
            ibis_df = load_ibis_segments(ibis_output)
            if len(ibis_df) == 0:
                logger.warning("Loaded IBIS segments file is empty")
            else:
                logger.info(f"Loaded {len(ibis_df)} IBIS segments")
        except Exception as e:
            logger.error(f"Error loading IBIS segments: {e}")
    else:
        logger.warning("Skipping IBIS segment loading as no output was produced")
    
    # Load Refined-IBD results if available
    if refined_output:
        try:    
            refined_df = load_refined_ibd_segments(refined_output)
            if len(refined_df) == 0:
                logger.warning("Loaded Refined-IBD segments file is empty")
            else:
                logger.info(f"Loaded {len(refined_df)} Refined-IBD segments")
        except Exception as e:
            logger.error(f"Error loading Refined-IBD segments: {e}")
    else:
        logger.warning("Skipping Refined-IBD segment loading as no output was produced")
    
    # Load Hap-IBD results if available
    if hap_output:
        try:
            hap_df = load_hap_ibd_segments(hap_output)
            if len(hap_df) == 0:
                logger.warning("Loaded Hap-IBD segments file is empty")
            else:
                logger.info(f"Loaded {len(hap_df)} Hap-IBD segments")
        except Exception as e:
            logger.error(f"Error loading Hap-IBD segments: {e}")
    else:
        logger.warning("Skipping Hap-IBD segment loading as no output was produced")
        
    # Check if we have at least one method with results
    if len(ibis_df) == 0 and len(refined_df) == 0 and len(hap_df) == 0:
        logger.error("No segments were loaded from any IBD detection method. Cannot proceed with evaluation.")
        sys.exit(1)  # Exit on error - no fallback
    
    # Ensure all required columns are present
    for df, tool in [(ibis_df, 'IBIS'), (refined_df, 'RefinedIBD'), (hap_df, 'HapIBD')]:
        if 'segment_id' not in df.columns:
            df['segment_id'] = range(len(df))
        if 'tool' not in df.columns:
            df['tool'] = tool
        # Add other required columns with default values if missing
        for col in ['chrom', 'start', 'end', 'sample1', 'sample2', 'length', 'sample1_haplotype', 'sample2_haplotype']:
            if col not in df.columns:
                df[col] = 0 if col in ['start', 'end', 'length', 'sample1_haplotype', 'sample2_haplotype'] else ''
    
    # Evaluate all tools
    try:
        all_results = evaluate_all_tools(refined_df, hap_df, ibis_df, truth_df)
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        sys.exit(1)  # Exit on error - no fallback
    
    # Calculate summary metrics
    try:
        metrics_df = calculate_summary_metrics(all_results, truth_df)
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        sys.exit(1)  # Exit on error - no fallback
    
    # Save metrics to CSV
    try:
        metrics_path = os.path.join(eval_dir, "ibd_metrics.csv")
        metrics_df.to_csv(metrics_path, index=False)
        logger.info(f"Saved metrics to: {metrics_path}")
    except Exception as e:
        logger.error(f"Error saving metrics: {e}")
    
    # Create visualizations
    try:
        create_visualizations(all_results, truth_df, eval_dir)
    except Exception as e:
        logger.error(f"Error creating visualizations: {e}")
    
    # Create summary bar plot
    try:
        if len(metrics_df) > 0:
            plot_summary_barplot(metrics_df, eval_dir)
    except Exception as e:
        logger.error(f"Error creating summary plot: {e}")
    
    logger.info("IBD workflow completed")
    logger.info(f"Results are available in: {args.output_dir}")

if __name__ == "__main__":
    # Run the main function with command line args
    main()