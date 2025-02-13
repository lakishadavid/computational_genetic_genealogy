import subprocess
import os
import argparse
import logging
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display, HTML
import IPython
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

def convert_all_vcfs_to_plink(phased_samples_dir, utils_directory):
    """
    Iterates through all phased VCF files in the directory and converts them to PLINK binary files.
    """
    plink2_executable = os.path.join(utils_directory, "plink2")
    
    # Ensure the PLINK2 executable exists
    if not os.path.isfile(plink2_executable):
        raise FileNotFoundError(f"PLINK2 executable not found: {plink2_executable}")

    # Ensure the phased samples directory exists
    if not os.path.isdir(phased_samples_dir):
        raise NotADirectoryError(f"Phased samples directory not found: {phased_samples_dir}")

    # Iterate over all VCF files in the directory
    for vcf_file in os.listdir(phased_samples_dir):
        if vcf_file.startswith("opensnps_phased_") and vcf_file.endswith(".vcf.gz"):  # Only process compressed VCF files
            vcf_path = os.path.join(phased_samples_dir, vcf_file)
            output_prefix = vcf_path.split(".")[0]

            # Construct the PLINK2 command
            command = [
                plink2_executable,
                "--vcf", vcf_path,
                "--autosome",
                "--make-bed",
                "--out", output_prefix
            ]

            try:
                # Execute the command
                subprocess.run(command, check=True)
                print(f"PLINK2 successfully processed: {vcf_file}")
            except subprocess.CalledProcessError as e:
                print(f"Error processing {vcf_file}: {e}")

def add_genetic_map_to_all_bim(phased_samples_dir, references_directory, utils_directory):
    """
    Iterates through all BIM files in the phased samples directory and adds a genetic map
    for IBIS and Beagle compatibility.
    """
    add_map_script = os.path.join(utils_directory, "ibis/add-map-plink.pl")

    # Ensure the add-map script exists
    if not os.path.isfile(add_map_script):
        raise FileNotFoundError(f"Add-map script not found: {add_map_script}")

    # Ensure the phased samples directory exists
    if not os.path.isdir(phased_samples_dir):
        raise NotADirectoryError(f"Phased samples directory not found: {phased_samples_dir}")

    # Iterate over all BIM files in the directory
    for bim_file in os.listdir(phased_samples_dir):
        if bim_file.endswith(".bim"):
            bim_path = os.path.join(phased_samples_dir, bim_file)
            output_bim = bim_path.replace(".bim", "_gm.bim")
            
            # Extract chromosome number from the filename
            chrom_number = bim_file.split("_")[-1].replace(".bim", "").replace("chr", "")
            map_file = os.path.join(references_directory, f"genetic_maps/ibis_genetic_maps/plink.chr{chrom_number}.GRCh38.map")

            # Ensure required files exist
            if not os.path.isfile(bim_path):
                print(f"Skipping {bim_file}: BIM file not found.")
                continue
            if not os.path.isfile(map_file):
                print(f"Skipping {bim_file}: Genetic map file not found for chromosome {chrom_number}.")
                continue

            # Construct and execute the command
            command = f"{add_map_script} {bim_path} {map_file} > {output_bim}"
            try:
                subprocess.run(command, shell=True, check=True)
                print(f"Genetic map added to: {bim_file}")
            except subprocess.CalledProcessError as e:
                print(f"Error processing {bim_file}: {e}")


def run_ibis(phased_samples_dir, results_directory, utils_directory):
    """
    Runs IBIS IBD detection for all chromosome-specific files in the phased samples directory.
    """
    ibis_executable = os.path.join(utils_directory, "ibis/ibis")
    
    # Ensure the IBIS executable exists
    if not os.path.isfile(ibis_executable):
        raise FileNotFoundError(f"IBIS executable not found: {ibis_executable}")

    # Ensure the phased samples directory exists
    if not os.path.isdir(phased_samples_dir):
        raise NotADirectoryError(f"Phased samples directory not found: {phased_samples_dir}")

    # Ensure the results directory exists or create it
    os.makedirs(results_directory, exist_ok=True)

    # Iterate over all chromosome-specific BIM files in the phased samples directory
    for bim_file in os.listdir(phased_samples_dir):
        if bim_file.endswith("_gm.bim"):  # Process files with the genetic map suffix
            chrom_prefix = bim_file.replace("_gm.bim", "")
            bed_file = os.path.join(phased_samples_dir, chrom_prefix + ".bed")
            fam_file = os.path.join(phased_samples_dir, chrom_prefix + ".fam")
            bim_path = os.path.join(phased_samples_dir, bim_file)
            output_prefix = os.path.join(results_directory, chrom_prefix + "_ibis")

            # Ensure required files exist
            if not os.path.isfile(bed_file):
                print(f"Skipping {chrom_prefix}: BED file not found.")
                continue
            if not os.path.isfile(fam_file):
                print(f"Skipping {chrom_prefix}: FAM file not found.")
                continue

            # Construct the IBIS command
            command = [
                ibis_executable,
                bed_file,
                bim_path,
                fam_file,
                "-ibd2",
                "-min_l", "7", "-mt", "436", "-er", ".004",
                "-min_l2", "2", "-mt2", "186", "-er2", ".008",
                "-o", output_prefix,
                "-printCoef", "-noFamID"
            ]

            try:
                # Execute the command
                subprocess.run(command, check=True)
                print(f"IBIS IBD detection completed for: {chrom_prefix}")
            except subprocess.CalledProcessError as e:
                print(f"Error running IBIS for {chrom_prefix}: {e}")



    """
    # IBIS: sample1 sample2 chrom phys_start_pos phys_end_pos IBD_type genetic_start_pos genetic_end_pos genetic_seg_length marker_count error_count error_density
    # Coef: sample1 sample2 kinship_coefficient IBD2_fraction segment_count degree_of_relatedness
    # IBD2: Useful in sibling cases where a pair have matching haplotypes at a locus, having inherited from both parents/sides of the family
    # HBD: ROH, matching haplotypes within the one person, not a comparison with another person
    # HBD: sample_id chrom phys_start_pos phys_end_pos HBD_type genetic_start_pos genetic_end_pos genetic_seg_length marker_count error_count error_density
    # Incoef: sample_id inbreeding_coefficient segment_count

    # IBIS:
    # This file contains detailed information about identity-by-descent (IBD) segments shared between pairs of individuals.
    # Columns:
    # - sample1, sample2: IDs of the two individuals being compared for shared genetic segments.
    # - chrom: Chromosome number where the IBD segment is located.
    # - phys_start_pos, phys_end_pos: Start and end positions of the IBD segment in base pairs (physical positions).
    # - IBD_type: Type of IBD segment (e.g., IBD1 for sharing one parental haplotype or IBD2 for sharing both parental haplotypes).
    # - genetic_start_pos, genetic_end_pos: Start and end positions of the segment in genetic map units (centiMorgans).
    # - genetic_seg_length: Length of the IBD segment in centiMorgans (genetic distance).
    # - marker_count: Number of genetic markers (SNPs) within the segment.
    # - error_count: Total number of mismatches or genotyping errors detected in the segment.
    # - error_density: Average error rate per marker in the segment (error_count divided by marker_count).

    # Coef:
    # This file provides information about pairwise kinship coefficients and degrees of relatedness.
    # Columns:
    # - sample1, sample2: IDs of the two individuals being compared.
    # - kinship_coefficient: A measure of genetic similarity between the individuals, ranging from 0 (no relation) to higher values for close relatives.
    # - IBD2_fraction: Proportion of the genome where both parental haplotypes are shared between the individuals.
    # - segment_count: Total number of IBD segments identified between the individuals.
    # - degree_of_relatedness: Classification of the relationship based on kinship (e.g., siblings, cousins).

    # IBD2:
    # Represents segments where two individuals share both parental haplotypes. 
    # IBD2 is particularly useful in identifying siblings or individuals with close familial ties, as these segments indicate inheritance from both sides of the family.

    # HBD (Runs of Homozygosity):
    # Indicates segments where an individual has matching haplotypes on both chromosomes, likely due to inheritance from a common ancestor.
    # This is a measure of inbreeding or autozygosity (when an individual inherits identical haplotypes from both parents).
    # Columns:
    # - sample_id: ID of the individual being analyzed for HBD segments.
    # - chrom: Chromosome number where the HBD segment is located.
    # - phys_start_pos, phys_end_pos: Start and end positions of the HBD segment in base pairs.
    # - HBD_type: Type or classification of the HBD segment.
    # - genetic_start_pos, genetic_end_pos: Start and end positions of the segment in genetic map units (centiMorgans).
    # - genetic_seg_length: Length of the HBD segment in centiMorgans.
    # - marker_count: Number of genetic markers (SNPs) in the segment.
    # - error_count: Total number of mismatches or genotyping errors detected in the segment.
    # - error_density: Average error rate per marker in the segment.

    # Incoef:
    # Provides inbreeding coefficients for individuals, based on HBD analysis.
    # Columns:
    # - sample_id: ID of the individual being analyzed.
    # - inbreeding_coefficient: A measure of inbreeding for the individual, reflecting the proportion of the genome covered by HBD segments.
    # - segment_count: Total number of HBD segments identified in the individual's genome.
    """

def combine_and_sort_ibis_outputs(results_dir):
    """
    Combines all chromosome-specific IBIS .coef and .seg files, and saves sorted results in the results directory.

    Parameters:
        phased_samples_dir (str): Directory containing chromosome-specific IBIS outputs.
        results_dir (str): Directory to save the combined output files.
    """
    combined_coef_path = os.path.join(results_dir, "ibis_MergedSamples.coef")
    combined_seg_path = os.path.join(results_dir, "ibis_MergedSamples.seg")

    coef_files = []
    seg_files = []

    # Collect .coef and .seg files
    for chrom in range(1, 23):
        coef_file = os.path.join(results_dir, f"opensnps_phased_chr{chrom}_ibis.coef")
        seg_file = os.path.join(results_dir, f"opensnps_phased_chr{chrom}_ibis.seg")

        if os.path.isfile(coef_file):
            coef_files.append(coef_file)
        else:
            print(f"Missing .coef file for chromosome {chrom}. Skipping.")
        
        if os.path.isfile(seg_file):
            seg_files.append(seg_file)
        else:
            print(f"Missing .seg file for chromosome {chrom}. Skipping.")

    if not coef_files and not seg_files:
        print("No .coef or .seg files found. Aborting.")
        return

    # Combine .coef files
    if coef_files:
        with open(combined_coef_path, "w") as outfile:
            for i, coef_file in enumerate(coef_files):
                with open(coef_file, "r") as infile:
                    if i == 0:
                        # Write the header from the first file
                        outfile.write(infile.read())
                    else:
                        # Skip the header for subsequent files
                        next(infile)  # Skip the header line
                        outfile.write(infile.read())
        print(f"Combined .coef files saved to: {combined_coef_path}")
    else:
        print("No .coef files to combine.")

    # Combine and sort .seg files
    if seg_files:
        combined_seg_data = []
        for seg_file in seg_files:
            seg_data = pd.read_csv(seg_file, sep="\t", header=None)
            combined_seg_data.append(seg_data)

        if combined_seg_data:
            combined_seg_df = pd.concat(combined_seg_data, ignore_index=True)
            combined_seg_df.columns = [
                "sample1", "sample2", 
                "chrom", 
                "phys_start_pos", "phys_end_pos", 
                "IBD_type", "genetic_start_pos", 
                "genetic_end_pos", "genetic_seg_length", 
                "marker_count", "error_count", "error_density"
            ]
            sorted_seg_df = combined_seg_df.sort_values(
                by=["chrom", "phys_start_pos", "phys_end_pos", "IBD_type"],
                ascending=[True, True, True, True]
            )
            sorted_seg_df.to_csv(combined_seg_path, sep="\t", index=False, header=False)
            print(f"Combined and sorted .seg file saved to: {combined_seg_path}")
        else:
            print("No valid .seg data to combine.")
    else:
        print("No .seg files to combine.")

    return True

def explore_coefficients(results_directory, filename="ibis_MergedSamples.coef", focus_on_related=True, save_plots=True, output_subdir="segments"):
    """
    Reads and explores the coefficients file from the results directory.
    Includes handling for missing values and options to focus on related individuals.
    
    Parameters:
        results_directory (str): Directory containing the result files.
        filename (str): Filename of the coefficients file.
        focus_on_related (bool): If True, focuses analysis on related individuals (Degree > 0).
        save_plots (bool): If True, saves plots to the specified output directory.
        output_dir (str): Directory to save plots.
    
    Returns:
        pd.DataFrame: Processed coefficients DataFrame for further analysis.
    """
        
    # Ensure output directory exists
    output_dir = os.path.join(results_directory, output_subdir)
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Read the coefficients file
    file_path = os.path.join(results_directory, filename)
    coefficients = pd.read_csv(file_path, sep="\t", low_memory=False)

    # Save both full and filtered data if focus_on_related is True
    full_data = coefficients.copy()
    filtered_data = None

    if focus_on_related:
        print("\nFocusing on related individuals (Degree > 0).")
        filtered_data = full_data[full_data['Degree'] > 0]
        print(f"Filtered DataFrame Info (Degree > 0):")
        filtered_data.info()
        print("\n=== Descriptive Statistics (Filtered) ===")
        print(filtered_data.describe())
        print("\n")
        filtered_file_path = os.path.join(output_dir, "filtered_coefficients.csv")
        filtered_data.to_csv(filtered_file_path, index=False)
        print(f"Filtered coefficients saved to: {filtered_file_path}")

    # Save and print the full data
    print("\nFull DataFrame Info:")
    full_data.info()
    print("\n=== Descriptive Statistics (Full) ===")
    print(full_data.describe())
    print("\n")
    full_file_path = os.path.join(output_dir, "full_coefficients.csv")
    full_data.to_csv(full_file_path, index=False)
    print(f"Full coefficients saved to: {full_file_path}")

    # Analyze both datasets
    datasets = {"Full": full_data, "Filtered": filtered_data} if focus_on_related else {"Full": full_data}

    for name, data in datasets.items():
        if data is not None:
            print(f"\n=== Analyzing {name} Data ===")
            
            # Counts by Degree
            degree_grouped_counts = data['Degree'].value_counts().sort_index()
            degree_grouped_counts_df = degree_grouped_counts.reset_index(name='Count')
            degree_grouped_counts_df.columns = ['Degree', 'Count']
            print(f"=== Counts by Degree ({name}) ===")
            print(degree_grouped_counts_df)
            
            # Save HTML table
            # html_table = degree_grouped_counts_df.to_html(index=False)
            # html_file_path = os.path.join(output_dir, f"{name.lower()}_degree_counts.html")
            # with open(html_file_path, "w") as f:
            #     f.write(html_table)
            # print(f"HTML table for {name} data saved to: {html_file_path}")

            # # Display in Jupyter if available
            # if hasattr(IPython, 'get_ipython') and IPython.get_ipython() is not None:
            #     display(HTML(html_table))

            # # Visualizations
            # def save_or_show_plot(fig, filename):
            #     if save_plots:
            #         fig.savefig(os.path.join(output_dir, f"{name.lower()}_{filename}"))
            #     plt.close(fig)

            # # Degree distribution
            # fig, ax = plt.subplots(figsize=(8, 5))
            # sns.histplot(data['Degree'], bins=10, kde=False, ax=ax)
            # ax.set_title(f'Degree Distribution ({name})')
            # ax.set_xlabel('Degree')
            # ax.set_ylabel('Frequency')
            # save_or_show_plot(fig, "degree_distribution.png")

            # # Other plots
            # if 'Kinship_Coefficient' in data.columns:
            #     fig, ax = plt.subplots(figsize=(8, 5))
            #     sns.histplot(data['Kinship_Coefficient'], bins=30, kde=True, ax=ax)
            #     ax.set_title(f'Kinship Coefficient Distribution ({name})')
            #     ax.set_xlabel('Kinship Coefficient')
            #     ax.set_ylabel('Frequency')
            #     save_or_show_plot(fig, "kinship_coefficient_distribution.png")

            # if 'IBD2_Fraction' in data.columns:
            #     fig, ax = plt.subplots(figsize=(8, 5))
            #     sns.histplot(data['IBD2_Fraction'], bins=30, kde=True, ax=ax)
            #     ax.set_title(f'IBD2 Fraction Distribution ({name})')
            #     ax.set_xlabel('IBD2 Fraction')
            #     ax.set_ylabel('Frequency')
            #     save_or_show_plot(fig, "ibd2_fraction_distribution.png")

            # if all(col in data.columns for col in ['Kinship_Coefficient', 'IBD2_Fraction']):
            #     fig, ax = plt.subplots(figsize=(8, 5))
            #     sns.scatterplot(
            #         data=data,
            #         x='Kinship_Coefficient',
            #         y='IBD2_Fraction',
            #         hue='Degree', palette='viridis', ax=ax
            #     )
            #     ax.set_title(f'Kinship vs. IBD2 Fraction ({name})')
            #     ax.set_xlabel('Kinship Coefficient')
            #     ax.set_ylabel('IBD2 Fraction')
            #     plt.legend(title='Degree')
            #     save_or_show_plot(fig, "kinship_vs_ibd2_fraction.png")

            # # Correlation matrix
            # numeric_cols = ['Kinship_Coefficient', 'IBD2_Fraction', 'Segment_Count']
            # existing_cols = [col for col in numeric_cols if col in data.columns]
            # if existing_cols:
            #     fig, ax = plt.subplots(figsize=(6, 5))
            #     corr = data[existing_cols].corr()
            #     sns.heatmap(corr, annot=True, cmap='Blues', square=True, ax=ax)
            #     ax.set_title(f'Correlation Matrix ({name})')
            #     save_or_show_plot(fig, "correlation_matrix.png")

    print("\nAnalysis completed.")
    return

def explore_segments_ibis(
        results_directory, 
        filename="ibis_MergedSamples.seg",
        min_length=7, 
        min_markers=436, 
        max_error_density=0.004,
        save_plots=True, 
        output_subdir="segments"
):
    """
    Explores and optionally filters the segments DataFrame.
    
    Parameters:
        results_directory (str): Directory containing the segments file.
        filename (str): Filename of the segments file.
        min_length (float): Minimum genetic length threshold for filtering.
        min_markers (int): Minimum marker count threshold for filtering.
        max_error_density (float): Maximum error density threshold for filtering.
        filter_segments_enabled (bool): If True, apply filtering to the segments.
        save_plots (bool): If True, save plots to the specified directory.
        output_dir (str): Directory to save outputs and plots.
    
    Returns:
        pd.DataFrame: The segments DataFrame (filtered or unfiltered based on input).
    """
    # Ensure output directory exists
    output_dir = os.path.join(results_directory, output_subdir)
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Read the segments file
    file_path = os.path.join(results_directory, filename)
    segments = pd.read_csv(file_path, sep="\t", header=None)
    segments.columns = [
        "id1", "id2", "chromosome", "physical_position_start", 
        "physical_position_end", "IBD_type", "genetic_position_start", 
        "genetic_position_end", "genetic_length", "marker_count", 
        "error_count", "error_density"
    ]

    # Ensure numeric columns are properly parsed
    numeric_columns = ["genetic_length", "marker_count", "error_density", "chromosome"]
    for col in numeric_columns:
        if col in segments.columns:
            segments[col] = pd.to_numeric(segments[col], errors='coerce')

    # Drop rows with NaN values in numeric columns
    nan_rows = segments[segments[numeric_columns].isnull().any(axis=1)]
    if not nan_rows.empty:
        nan_file_path = os.path.join(output_dir, "nan_segments_ibis.csv")
        nan_rows.to_csv(nan_file_path, sep="\t", index=False)
        print(f"Rows with NaN values saved to: {nan_file_path}")
    segments = segments.dropna(subset=numeric_columns).reset_index(drop=True)

    # Step 2: Basic info and descriptive statistics
    print("=== Segments DataFrame Info ===")
    segments.info()
    print("\n=== Descriptive Statistics ===")
    print(segments[['genetic_length', 'marker_count', 'error_density']].describe())
    print("\n")

    # Save the unfiltered data
    unfiltered_file_path = os.path.join(output_dir, "unfiltered_segments_ibis.csv")
    segments.to_csv(unfiltered_file_path, sep="\t", index=False)
    print(f"Unfiltered segments saved to: {unfiltered_file_path}")
    print()

    filtered_segments = segments[
        (segments['genetic_length'] >= min_length) &
        (segments['marker_count'] >= min_markers) &
        (segments['error_density'] <= max_error_density)
    ].copy()
    
    print("=== Filtered Segments Info ===")
    filtered_segments.info()
    print("\n=== Descriptive Statistics (Filtered) ===")
    print(filtered_segments[['genetic_length', 'marker_count', 'error_density']].describe())
    print("\n")
    
    # Save filtered segments to a new file
    filtered_filename = "filtered_segments_ibis.csv"
    filtered_file_path = os.path.join(output_dir, filtered_filename)
    filtered_segments.to_csv(filtered_file_path, sep="\t", index=False)
    print(f"Filtered segments saved to: {filtered_file_path}")

    print(f"\nSummary:")
    print(f"Total segments: {len(segments)}")
    print(f"Filtered segments: {len(filtered_segments)}")
    if not nan_rows.empty:
        print(f"Rows with NaN values: {len(nan_rows)} (saved to: {nan_file_path})")


    # # Step 4: Visualizations
    # def save_or_show_plot(fig, filename):
    #     if save_plots:
    #         fig.savefig(os.path.join(output_dir, filename))
    #     plt.close(fig)

    # def plot_distribution(data, column, title, xlabel, ylabel, filename, bins=30, kde=True):
    #     fig, ax = plt.subplots(figsize=(8, 5))
    #     sns.histplot(data[column], bins=bins, kde=kde, ax=ax)
    #     ax.set_title(title)
    #     ax.set_xlabel(xlabel)
    #     ax.set_ylabel(ylabel)
    #     save_or_show_plot(fig, filename)

    # # Visualize genetic_length distribution
    # plot_distribution(
    #     segments, "genetic_length", "Distribution of Genetic Length", 
    #     "Genetic Length (cM)", "Frequency", "genetic_length_distribution_unfiltered.png"
    # )

    # plot_distribution(
    #     filtered_segments, "genetic_length", "Distribution of Genetic Length (Filtered)", 
    #     "Genetic Length (cM)", "Frequency", "genetic_length_distribution_filtered.png"
    # )

    # # Visualize marker_count distribution
    # plot_distribution(
    #     segments, "marker_count", "Distribution of Marker Count", 
    #     "Marker Count", "Frequency", "marker_count_distribution_unfiltered.png"
    # )
    # plot_distribution(
    #     filtered_segments, "marker_count", "Distribution of Marker Count (Filtered)", 
    #     "Marker Count", "Frequency", "marker_count_distribution_filtered.png"
    # )

    # # Boxplot of genetic_length by chromosome
    # def plot_boxplot(data, x_col, y_col, title, xlabel, ylabel, filename):
    #     fig, ax = plt.subplots(figsize=(10, 6))
    #     sns.boxplot(x=x_col, y=y_col, data=data, ax=ax)
    #     ax.set_title(title)
    #     ax.set_xlabel(xlabel)
    #     ax.set_ylabel(ylabel)
    #     plt.xticks(rotation=45)
    #     plt.tight_layout()
    #     save_or_show_plot(fig, filename)

    # plot_boxplot(
    #     segments, "chromosome", "genetic_length", 
    #     "Distribution of Genetic Length by Chromosome", 
    #     "Chromosome", "Genetic Length (cM)", "genetic_length_by_chromosome_unfiltered.png"
    # )
    # plot_boxplot(
    #     filtered_segments, "chromosome", "genetic_length", 
    #     "Distribution of Genetic Length by Chromosome (Filtered)", 
    #     "Chromosome", "Genetic Length (cM)", "genetic_length_by_chromosome_filtered.png"
    # )

    print("\nAnalysis completed.")
    return

def run_hap_ibd(phased_samples_dir, results_directory, utils_directory, references_directory):
    """
    Runs hap-ibd IBD detection for chromosome-specific phased sample VCF files.
    
    Parameters:
        phased_samples_dir (str): Directory containing phased sample VCF files.
        results_directory (str): Directory to save the hap-ibd output files.
        utils_directory (str): Directory containing the hap-ibd tool.
        references_directory (str): Directory containing chromosome-specific genetic map files.
    """
    # Paths for the hap-ibd JAR
    hap_ibd_jar = os.path.join(utils_directory, "hap-ibd.jar")

    # Ensure the hap-ibd JAR exists
    if not os.path.isfile(hap_ibd_jar):
        raise FileNotFoundError(f"hap-ibd JAR not found: {hap_ibd_jar}")

    # Ensure the results directory exists or create it
    os.makedirs(results_directory, exist_ok=True)

    # Process each chromosome
    for chromosome in range(1, 23):
        print()
        # Paths for the genetic map and VCF file for the current chromosome
        map_file = os.path.join(references_directory, f"genetic_maps/beagle_genetic_maps/plink.chr{chromosome}.GRCh38.map")
        vcf_file = os.path.join(phased_samples_dir, f"opensnps_phased_chr{chromosome}.vcf.gz")
        output_prefix = os.path.join(results_directory, f"hap_ibd_chr{chromosome}")

        # Check if the required files exist
        if not os.path.isfile(map_file):
            print(f"Skipping chromosome {chromosome}: Genetic map file not found: {map_file}")
            continue
        if not os.path.isfile(vcf_file):
            print(f"Skipping chromosome {chromosome}: Phased VCF file not found: {vcf_file}")
            continue

        # Construct the hap-ibd command
        command = [
            "java", "-jar", hap_ibd_jar,
            f"gt={vcf_file}",
            f"out={output_prefix}",
            f"map={map_file}"
        ]

        try:
            # Execute the hap-ibd command
            subprocess.run(command, check=True)
            print(f"hap-ibd IBD detection completed successfully for chromosome {chromosome}.")
        except subprocess.CalledProcessError as e:
            print(f"Error running hap-ibd for chromosome {chromosome}: {e}")

def combine_and_sort_hap_ibd_outputs(results_dir):

    def process_files(file_list, output_path, file_type):

        if not file_list:
            print(f"No {file_type} files to process.")
            return False
        
        combined_data = []
        for seg_file in file_list:
            try:
                seg_data = pd.read_csv(seg_file, sep="\t", header=None)
                combined_data.append(seg_data)
            except Exception as e:
                print(f"Error reading {file_type} file {seg_file}: {e}")
        
        if combined_data:
            combined_df = pd.concat(combined_data, ignore_index=True)
            combined_df.columns = [
                "id1", "id1_haplotype_index", "id2", "id2_haplotype_index",
                "chromosome", 
                "physical_position_start", "physical_position_end",
                "genetic_length"
            ]
            sorted_df = combined_df.sort_values(
                by=["chromosome", "physical_position_start", "physical_position_end"],
                ascending=[True, True, True]
            )
            sorted_df.to_csv(output_path, sep="\t", index=False, header=False)
            print(f"Combined and sorted {file_type} file saved to: {output_path}")
            return True
        else:
            print(f"No valid {file_type} data to combine.")
            return False

    # Collect IBD and HBD files
    ibd_files = [
        os.path.join(results_dir, f"hap_ibd_chr{chrom}.ibd.gz") 
        for chrom in range(1, 23) if os.path.isfile(os.path.join(results_dir, f"hap_ibd_chr{chrom}.ibd.gz"))
    ]
    hbd_files = [
        os.path.join(results_dir, f"hap_ibd_chr{chrom}.hbd.gz") 
        for chrom in range(1, 23) if os.path.isfile(os.path.join(results_dir, f"hap_ibd_chr{chrom}.hbd.gz"))
    ]

    # print(f"ibd_files ++++ {ibd_files}, hbd_files ++++ {hbd_files}")

    if not ibd_files and not hbd_files:
        print("No IBD or HBD files found. Aborting.")
        return False

    # Process IBD and HBD files
    combined_ibd_filename = os.path.join(results_dir, "hap_ibd_MergedSamples.seg")
    # print(f"combined_ibd_path, {combined_ibd_filename}")
    ibd_success = process_files(ibd_files, combined_ibd_filename, "ibd")

    combined_hbd_filename = os.path.join(results_dir, "hap_hbd_MergedSamples.seg")
    # print(f"combined_hbd_path, {combined_hbd_filename}")
    hbd_success = process_files(hbd_files, combined_hbd_filename, "hbd")

    if ibd_success and hbd_success:
        return True
    else:
        return False

def explore_hap_ibd_results(
        results_directory,
        file_prefix="hap_ibd_MergedSamples",
        min_length=3, 
        save_filtered=True, 
        output_subdir="segments"
):
    """
    Explores and optionally filters hap-IBD results for IBD and HBD files.
    
    Parameters:
        results_directory (str): Directory containing hap-IBD files.
        file_prefix (str): Prefix for the hap-IBD files (e.g., "hap_ibd_MergedSamples").
        min_length (float): Minimum genetic length threshold for filtering.
        save_filtered (bool): If True, save filtered files.
        output_subdir (str): Subdirectory to save outputs.
    
    Returns:
        dict: DataFrames for IBD and HBD results (filtered and unfiltered).
    """
    # Ensure output directory exists
    output_dir = os.path.join(results_directory, output_subdir)
    os.makedirs(output_dir, exist_ok=True)

    print(f"output_directory: {output_dir}")

    def process_file(filename, file_type):
        """
        Process a single hap-IBD file.
        
        Parameters:
            file_path (str): Path to the hap-IBD file.
            file_type (str): Type of file ('ibd' or 'hbd').

        Returns:
            tuple: Unfiltered and filtered DataFrames.
        """
        if not os.path.isfile(filename):
            print(f"File not found: {filename}. Skipping {file_type} analysis.")
            return None, None
        
        print(f"loading: {filename}")
        
        # Load the file
        segments = pd.read_csv(filename, sep="\t", header=None)
        segments.columns = [
            "id1", "id1_haplotype_index", "id2", "id2_haplotype_index",
            "chromosome", 
            "physical_position_start", "physical_position_end",
            "genetic_length"
        ]

        # Ensure numeric columns are properly parsed
        numeric_columns = ["genetic_length", "chromosome", "physical_position_start", "physical_position_end"]
        for col in numeric_columns:
            segments[col] = pd.to_numeric(segments[col], errors='coerce')

        # Handle NaN values
        nan_rows = segments[segments[numeric_columns].isnull().any(axis=1)]
        if not nan_rows.empty:
            nan_file_path = os.path.join(output_dir, f"nan_segments_{file_type}.csv")
            nan_rows.to_csv(nan_file_path, sep="\t", index=False)
            print(f"Rows with NaN values in {file_type} saved to: {nan_file_path}")
        segments = segments.dropna(subset=numeric_columns).reset_index(drop=True)

        # Print basic info
        print(f"=== {file_type.upper()} Segments DataFrame Info ===")
        segments.info()
        print(f"\n=== Descriptive Statistics ({file_type.upper()}) ===")
        print(segments[['genetic_length']].describe())
        print("\n")

        # Save unfiltered data
        unfiltered_file_path = os.path.join(output_dir, f"unfiltered_segments_{file_type}.csv")
        segments.to_csv(unfiltered_file_path, sep="\t", index=False)
        print(f"Unfiltered {file_type} segments saved to: {unfiltered_file_path}")

        # Filter segments
        filtered_segments = segments[segments['genetic_length'] >= min_length].copy()
        print(f"=== Filtered {file_type.upper()} Segments Info ===")
        filtered_segments.info()
        print(f"\n=== Descriptive Statistics (Filtered {file_type.upper()}) ===")
        print(filtered_segments[['genetic_length']].describe())
        print("\n")

        # Save filtered segments
        if save_filtered:
            filtered_file_path = os.path.join(output_dir, f"filtered_segments_{file_type}.csv")
            filtered_segments.to_csv(filtered_file_path, sep="\t", index=False)
            print(f"Filtered {file_type} segments saved to: {filtered_file_path}")

        return segments, filtered_segments

    # Process IBD and HBD files
    ibd_file = os.path.join(results_directory, "hap_ibd_MergedSamples.seg")
    hbd_file = os.path.join(results_directory, "hap_hbd_MergedSamples.seg")

    # print()
    # print(ibd_file, hbd_file)
    # print()

    ibd_data = process_file(ibd_file, "ibd")
    hbd_data = process_file(hbd_file, "hbd")

    print("\nAnalysis completed.")

    return {
        "ibd": ibd_data,
        "hbd": hbd_data
    }

def main(results_directory, references_directory, utils_directory):
    """
    Main function to run IBD detection using the specified algorithm.
    """
    logging.info("Starting IBD detection.")
    logging.debug("Run using: poetry run python -m scripts_work.run_ibd_detection --algorithm IBIS")
    logging.debug("Run using: poetry run python -m scripts_work.run_ibd_detection --algorithm HAP-IBD")

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run IBD detection using the specified algorithm.")
    parser.add_argument(
        "--algorithm",
        type=str,
        required=True,
        help="The algorithm to use for IBD detection. Options: 'IBIS', 'HAP-IBD'."
    )

    args = parser.parse_args()

    phased_samples_dir = os.path.join(results_directory, "phased_samples")
    if args.algorithm.upper() == "IBIS":
        convert_all_vcfs_to_plink(phased_samples_dir, utils_directory)
        add_genetic_map_to_all_bim(phased_samples_dir, references_directory, utils_directory)
        run_ibis(phased_samples_dir, results_directory, utils_directory)
        ibis_completion = combine_and_sort_ibis_outputs(results_directory)
        # ibis_completion = True # Use only to bypass this section during testing or bebugging

        if ibis_completion == True:
            explore_coefficients(results_directory, filename="ibis_MergedSamples.coef", focus_on_related=True)
            
            explore_segments_ibis(
                results_directory, 
                filename="ibis_MergedSamples.seg",
                min_length=7, 
                min_markers=436, 
                max_error_density=0.004,
                save_plots=True, 
                output_subdir="segments"
            )
            # FIX: add IBD Type in descriptives
    elif args.algorithm.upper() == "HAP-IBD":
        # hap_ibd_completion = run_hap_ibd(phased_samples_dir, results_directory, utils_directory, references_directory)
        hap_ibd_completion = True # Use only to bypass this section during testing or bebugging

        combine_and_sort_hap_ibd_outputs(results_directory)

        if hap_ibd_completion == True:
            explore_hap_ibd_results(
                results_directory,
                file_prefix="hap_ibd_MergedSamples",
                min_length=3, 
                save_filtered=True, 
                output_subdir="segments"
            )
    else:
        raise ValueError("Unsupported algorithm. Choose 'IBIS' or 'HAP-IBD'")

if __name__ == "__main__":
    
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

    # Run the main function with the selected algorithm
    main(results_directory, references_directory, utils_directory)
