#!/usr/bin/env python3
"""
MSprime Simulation Script

This script simulates genetic data using msprime, incorporating a defined pedigree
structure and demographic model. It can generate multiple replicates of tree sequences
with mutations and save them for further analysis.

Usage:
    python msprime_simulation.py [OPTIONS]

Options:
    --results-dir PATH        Directory to store results
    --num-replicates INT      Number of simulation replicates [default: 10]
    --min-span FLOAT          Minimum IBD segment length [default: 3e6]
    --max-time INT            Maximum time to look back for IBD segments [default: 25]
    --mutation-rate FLOAT     Mutation rate [default: 1.29e-8]
    --log-level STRING        Logging level (DEBUG, INFO, WARNING, ERROR) [default: INFO]
    --analyze                 Run analysis on simulated data
    --pedigree-file PATH      Path to pedigree file [default: pedigree.fam]
    --which-chromosomes LIST  Comma-separated list of chromosomes to simulate [default: 1-22]
    --genetic-map STRING      Genetic map to use [default: HapMapII_GRCh38]
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path
from time import process_time
import math
from collections import Counter, defaultdict
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import msprime
import stdpopsim
import tskit
import pysam


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="MSprime genetic data simulation")
    parser.add_argument("--results-dir", type=str, default=None,
                        help="Directory to store results")
    parser.add_argument("--num-replicates", type=int, default=10,
                        help="Number of simulation replicates")
    parser.add_argument("--min-span", type=float, default=3e6,
                        help="Minimum IBD segment length")
    parser.add_argument("--max-time", type=int, default=25,
                        help="Maximum time to look back for IBD segments")
    parser.add_argument("--mutation-rate", type=float, default=1.29e-8,
                        help="Mutation rate")
    parser.add_argument("--log-level", type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Logging level")
    parser.add_argument("--analyze", action="store_true",
                        help="Run analysis on simulated data")
    parser.add_argument("--pedigree-file", type=str, default="pedigree.fam",
                        help="Path to pedigree file")
    parser.add_argument("--which-chromosomes", type=str, default="1-22",
                        help="Comma-separated list of chromosomes to simulate")
    parser.add_argument("--genetic-map", type=str, default="HapMapII_GRCh38",
                        help="Genetic map to use")
    
    return parser.parse_args()


def find_comp_gen_dir():
    """Find the computational_genetic_genealogy directory by searching up from current directory."""
    current = Path.cwd()
    # Search up through parent directories
    while current != current.parent:
        # Check if target directory exists in current path
        target = current / 'computational_genetic_genealogy'
        if target.is_dir():
            return target
        # Move up one directory
        current = current.parent
    raise FileNotFoundError("Could not find computational_genetic_genealogy directory")


def load_env_file():
    """Find and load the .env file from the computational_genetic_genealogy directory."""
    try:
        # Find the computational_genetic_genealogy directory
        comp_gen_dir = find_comp_gen_dir()
        
        # Look for .env file
        env_path = comp_gen_dir / '.env'
        if not env_path.exists():
            print(f"Warning: No .env file found in {comp_gen_dir}")
            return None
        
        # Load environment variables directly (without dotenv dependency)
        env_vars = {}
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key] = value
                    os.environ[key] = value
        
        print(f"Loaded environment variables from: {env_path}")
        
        # Set directory variables
        directories = {
            "WORKING_DIRECTORY": os.environ.get('PROJECT_WORKING_DIR'),
            "DATA_DIRECTORY": os.environ.get('PROJECT_DATA_DIR'),
            "REFERENCES_DIRECTORY": os.environ.get('PROJECT_REFERENCES_DIR'),
            "RESULTS_DIRECTORY": os.environ.get('PROJECT_RESULTS_DIR'),
            "UTILS_DIRECTORY": os.environ.get('PROJECT_UTILS_DIR')
        }
        
        # Set these in environment variables
        for key, value in directories.items():
            if value:
                os.environ[key] = value
                print(f"{key.replace('_', ' ').title()}: {value}")
        
        return env_path
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None


def configure_logging(log_filename, log_file_debug_level="INFO", console_debug_level="INFO"):
    """
    Configure logging for both file and console handlers.
    Args:
        log_filename (str): Path to the log file where logs will be written.
        log_file_debug_level (str): Logging level for the file handler.
        console_debug_level (str): Logging level for the console handler.
    """
    # Create a root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Capture all messages at the root level
    
    # Convert level names to numeric levels
    file_level = getattr(logging, log_file_debug_level.upper(), logging.INFO)
    console_level = getattr(logging, console_debug_level.upper(), logging.INFO)
    
    # File handler: Logs messages at file_level and above to the file
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(file_level)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Console handler: Logs messages at console_level and above to the console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to the root logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def clear_logger():
    """Remove all handlers from the root logger."""
    logger = logging.getLogger()
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)


def parse_chromosome_range(chromosome_str):
    """Parse a string like '1-22' or '1,3,5,21-22' into a list of chromosome numbers."""
    chromosomes = []
    
    # Split by comma
    parts = chromosome_str.split(',')
    
    for part in parts:
        if '-' in part:
            # Handle range like '1-22'
            start, end = part.split('-')
            chromosomes.extend(range(int(start), int(end) + 1))
        else:
            # Handle single chromosome
            chromosomes.append(int(part))
    
    return chromosomes


def setup_demography_model():
    """Set up and return the demographic model."""
    species = stdpopsim.get_species("HomSap")
    # Demographic model for American admixture, from Browning et al. 2011
    # populations: ADMIX, AFR, ASIA, EUR
    demography_model = species.get_demographic_model("AmericanAdmixture_4B11").model
    return species, demography_model


def build_rate_map(species, genetic_map_name, which_chromosome):
    """
    Build a rate map that takes into account multiple chromosomes.
    
    Args:
        species: The species object from stdpopsim
        genetic_map_name: Name of the genetic map to use
        which_chromosome: List of chromosome numbers to include
        
    Returns:
        rate_map: The constructed rate map
        assembly_len_maps: The total sequence length
        conversion_dict: Dictionary mapping positions to chromosomes
    """
    genetic_map = species.get_genetic_map(genetic_map_name)
    
    # Set the recombination rate in the base pair segments separating chromosomes to log(2)
    r_break = math.log(2)
    
    map_positions = []
    map_rates = []
    chrom_positions = [0]
    
    # Dictionary to keep track of chromosome positions
    genetic_map_positions = {}
    
    # Dictionary to convert positions to original chromosomes
    conversion_dict = {}
    
    assembly_len = 0
    
    for chromosome in which_chromosome:
        # Get chromosome map
        rate_map = genetic_map.get_chromosome_map(f"chr{chromosome}")
        
        # Record the chromosome position
        genetic_map_positions[chromosome] = int(rate_map.sequence_length)
        assembly_len += rate_map.sequence_length
        
        if chromosome != which_chromosome[0]:
            # For chromosomes after the first one, adjust positions
            positions = [x + last_position + 1 for x in rate_map.position]
            map_positions.extend(positions)
            
            # Record the mapping between new positions and original chromosome
            conversion_dict[(int(last_position + 1), 
                           int(last_position + 1 + int(rate_map.sequence_length)))] = chromosome
            
            # Update the last position
            last_position = map_positions[-1]
            chrom_positions.append(int(last_position))
            
            # Handle rates - set first rate to mean rate
            shape = rate_map.rate.shape
            rates = rate_map.rate.tolist()
            rates[0] = rate_map.mean_rate
            rates = np.array(rates)
            rates.reshape(shape)
            map_rates.extend(rates)
        else:
            # For the first chromosome, use positions as-is
            map_positions.extend(rate_map.position)
            last_position = map_positions[-1]
            chrom_positions.append(int(last_position))
            map_rates.extend(rate_map.rate)
            
            # Record mapping for first chromosome
            conversion_dict[(int(0), int(last_position))] = chromosome
        
        # Add a high recombination rate between chromosomes except for the last one
        if chromosome != which_chromosome[-1]:
            map_rates.append(r_break)
    
    # Create the final rate map
    rate_map = msprime.RateMap(position=map_positions, rate=map_rates)
    assembly_len_maps = int(rate_map.sequence_length)
    
    print(f"The assembly length is {assembly_len_maps:,} bp.")
    print(f"Chromosome lengths: {genetic_map_positions}")
    
    return rate_map, assembly_len_maps, conversion_dict


def assign_generations(ped_df):
    """
    Assign generation numbers to individuals in a pedigree.
    
    Args:
        ped_df: DataFrame containing the pedigree
        
    Returns:
        ped_df: DataFrame with 'generation' column added
    """
    # Initialize generations for founders
    ped_df['generation'] = np.where((ped_df['parent0'] == -1) & (ped_df['parent1'] == -1), 0, -1)
    
    # Function to recursively get generation
    def get_generation(ind):
        row = ped_df.loc[ped_df['ind'] == ind]
        if row['generation'].values[0] != -1:
            return row['generation'].values[0]
        
        parent0_gen = get_generation(row['parent0'].values[0]) if row['parent0'].values[0] != -1 else 0
        parent1_gen = get_generation(row['parent1'].values[0]) if row['parent1'].values[0] != -1 else 0
        
        gen = max(parent0_gen, parent1_gen) + 1
        ped_df.loc[ped_df['ind'] == ind, 'generation'] = gen
        return gen
    
    # Assign generations to all individuals
    for ind in ped_df['ind']:
        get_generation(ind)
    
    # Update spouse generations
    for _, row in ped_df.iterrows():
        if row['parent0'] == -1 and row['parent1'] == -1:
            children = ped_df[(ped_df['parent0'] == row['ind']) | (ped_df['parent1'] == row['ind'])]
            if not children.empty:
                child_gen = children['generation'].min()
                ped_df.loc[ped_df['ind'] == row['ind'], 'generation'] = child_gen - 1
    
    # Reverse generations (make 0 the youngest generation)
    max_gen = ped_df['generation'].max()
    ped_df['generation'] = max_gen - ped_df['generation']
    
    return ped_df


def add_individuals_to_pedigree(pb, text_pedigree):
    """
    msprime pedigree builder.
    Loops through each individual in text pedigree and adds the individual to msprime pedigree with:
    parents, time, population, and metadata of individual_name from text pedigree.
    
    Args:
        pb: Pedigree builder object
        text_pedigree: DataFrame containing the pedigree
        
    Returns:
        pb: Updated pedigree builder
        txt_ped_to_tskit_key: Dictionary mapping text pedigree IDs to msprime IDs
    """
    # Dictionary linking text_pedigree ids to msprime ids
    txt_ped_to_tskit_key = {}
    
    # For each individual in the genealogy
    for i in text_pedigree.index:
        ind_id = text_pedigree["ind"][i]
        parent0_id = text_pedigree["parent0"][i]
        parent1_id = text_pedigree["parent1"][i]
        ind_time = text_pedigree["generation"][i]
        pop = "AFR"  # Default population
        
        # Include only generation 0 in the sample
        include_sample = ind_time == 0
        
        # Add individual to pedigree
        if parent0_id == -1 and parent1_id == -1:
            # Add founders without parents
            parent = pb.add_individual(
                time=ind_time,
                population=pop,
                is_sample=include_sample,
                metadata={
                    "individual_name": str(ind_id),
                    "parent0_name": int(parent0_id),
                    "parent1_name": int(parent1_id),
                    "generation": int(ind_time),
                    "population": str(pop)
                }
            )
            txt_ped_to_tskit_key[ind_id] = parent
        else:
            # Add non-founders with parents
            parent0 = txt_ped_to_tskit_key[parent0_id] if parent0_id != -1 else tskit.NULL
            parent1 = txt_ped_to_tskit_key[parent1_id] if parent1_id != -1 else tskit.NULL
            
            child = pb.add_individual(
                time=ind_time,
                population=pop,
                parents=[parent0, parent1],
                is_sample=include_sample,
                metadata={
                    "individual_name": str(ind_id),
                    "parent0_name": int(parent0_id),
                    "parent1_name": int(parent1_id),
                    "generation": int(ind_time),
                    "population": str(pop)
                }
            )
            txt_ped_to_tskit_key[ind_id] = child
    
    return pb, txt_ped_to_tskit_key


def draw_pedigree(pedigree, output_file):
    """
    Draw the pedigree as a network graph and save to file.
    
    Args:
        pedigree: tskit TableCollection containing the pedigree
        output_file: Path to save the visualization to
    
    Returns:
        G: NetworkX graph of the pedigree
    """
    fig = plt.figure(figsize=(25, 10), dpi=100)
    G = nx.DiGraph()
    
    for ind_id, table_row in enumerate(pedigree.individuals):
        # Get info from the first node of two nodes for each individual
        node_info = pedigree.nodes[pedigree.nodes.individual == ind_id]
        time = int(node_info.time[0])
        pop = node_info.population[0]
        
        # Add the individual as the graph node
        G.add_node(ind_id, time=time, population=pop)
        
        for p in table_row.parents:
            if p != tskit.NULL:
                G.add_edge(ind_id, p)
    
    # Create multipartite layout based on generation/time
    pos = nx.multipartite_layout(G, subset_key="time", align="horizontal")
    
    # Use color cycle from matplotlib
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    node_colors = [colors[node_attr["population"]] for node_attr in G.nodes.values()]
    
    # Draw the graph
    nx.draw_networkx(
        G, pos, 
        node_size=3000, 
        with_labels=True, 
        node_color=node_colors,
        bbox=dict(facecolor="none", edgecolor='black', boxstyle='round, pad=0.2')
    )
    
    plt.title("msprime Pedigree")
    plt.savefig(output_file, bbox_inches='tight', pad_inches=0)
    
    return G

def convert_ts_to_vcf(ts, output_filename, conversion_dict, txt_ped_to_tskit_key, replicate_index):
    """
    Convert a tree sequence to a VCF file with adjusted chromosome and local base positions.
    
    Args:
        ts: The tree sequence object.
        output_filename: Path to the output VCF file.
        conversion_dict: Dictionary mapping global position intervals (tuples) to chromosome numbers.
        txt_ped_to_tskit_key: Dictionary mapping text pedigree IDs (names) to msprime individual IDs.
        replicate_index: Integer replicate index to append to sample names.
        
    Sample names will be formatted as: "indXX_repY"
    """
    # Invert the mapping so that msprime individual IDs map back to original names
    ind_mapping = {v: k for k, v in txt_ped_to_tskit_key.items()}

    # Determine sample names from the tree sequence, appending replicate index
    sample_names = []
    for sample in ts.samples():
        node = ts.node(sample)
        ind_id = node.individual
        sample_name = ind_mapping.get(ind_id, f"ind{ind_id}")  # Default name if not found
        sample_name = f"{sample_name}_rep{replicate_index}"  # Append replicate index
        sample_names.append(sample_name)

    with open(output_filename, "w") as vcf:
        # Write VCF header lines
        vcf.write("##fileformat=VCFv4.2\n")
        vcf.write("##source=msprime_simulation\n")
        vcf.write("##INFO=<ID=TMRC,Number=1,Type=Float,Description=\"TMRCA at variant site (if computed)\">\n")
        header_cols = ["#CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO", "FORMAT"] + sample_names
        vcf.write("\t".join(header_cols) + "\n")
        
        # Process each variant in the tree sequence
        for variant in ts.variants():
            pos = variant.position
            chrom, chrom_start = None, None
            for (start, end), chrom_num in conversion_dict.items():
                if start <= pos < end:
                    chrom = chrom_num
                    chrom_start = start
                    break
            if chrom is None:
                continue
            
            # Calculate the local position (VCF is 1-indexed)
            local_pos = int(pos - chrom_start + 1)

            # Set VCF fields
            var_id = "."
            ref = variant.alleles[0]
            alt = ",".join(variant.alleles[1:]) if len(variant.alleles) > 1 else "."
            qual = "."
            filt = "PASS"
            info = "."
            fmt = "GT"

            # Convert genotype data
            genotypes = [str(gt) for gt in variant.genotypes]

            # Write VCF record
            record = [str(chrom), str(local_pos), var_id, ref, alt, qual, filt, info, fmt] + genotypes
            vcf.write("\t".join(record) + "\n")

    print(f"VCF file written to {output_filename}")


def main():
    """Main function."""
    args = parse_arguments()
    
    # Start timing
    t1_start = process_time()
    
    # Set up current time for logging
    now_est = datetime.now()
    print(f"Starting simulation at {now_est.strftime('%B %d, %-I:%M:%S %p')}")
    
    # Load environment or use provided results directory
    if args.results_dir:
        results_directory = args.results_dir
        os.makedirs(results_directory, exist_ok=True)
    else:
        load_env_file()
        results_directory = os.environ.get("RESULTS_DIRECTORY")
        if not results_directory:
            results_directory = "results"
            os.makedirs(results_directory, exist_ok=True)
    
    # Set up logging
    log_filename = os.path.join(results_directory, "simulation_log.txt")
    print(f"Log file is located at {log_filename}")
    
    # Ensure the results_directory exists
    if not os.path.exists(results_directory):
        os.makedirs(results_directory)
    
    # Check if the file exists; if not, create it
    if not os.path.exists(log_filename):
        with open(log_filename, 'w') as file:
            pass  # Create empty file
    
    clear_logger()  # Clear the logger before reconfiguring it
    configure_logging(log_filename, log_file_debug_level=args.log_level, console_debug_level=args.log_level)
    
    # Setup demographic model and parse chromosomes
    species, demography_model = setup_demography_model()
    which_chromosome = parse_chromosome_range(args.which_chromosomes)
    
    print(f"Simulating chromosomes: {which_chromosome}")
    
    # Build the rate map
    rate_map, assembly_len_maps, conversion_dict = build_rate_map(
        species, args.genetic_map, which_chromosome
    )
    
    # Load and process pedigree
    pedigree_path = os.path.join(results_directory, args.pedigree_file)
    if os.path.exists(pedigree_path):
        ped_sim_fam = pd.read_csv(pedigree_path, header=None, sep="\t")
        ped_sim_fam.columns = ["famid", "ind", "parent0", "parent1", "sex", "phenotype"]
        ped_sim_fam['ind'] = ped_sim_fam['ind'].astype(int)
        ped_sim_fam["parent0"] = ped_sim_fam["parent0"].replace(0, -1)
        ped_sim_fam["parent1"] = ped_sim_fam["parent1"].replace(0, -1)
        
        # Assign generations
        ped_sim_fam = assign_generations(ped_sim_fam)
        
        # Create pedigree for msprime
        text_pedigree = ped_sim_fam.copy()
        pb = msprime.PedigreeBuilder(
            demography_model,
            individuals_metadata_schema=tskit.MetadataSchema.permissive_json()
        )
        
        # Build out the pedigree using input text pedigree
        pb, txt_ped_to_tskit_key = add_individuals_to_pedigree(pb, text_pedigree)
        txt_ped_to_tskit_key_conv = {int(k): v for k, v in txt_ped_to_tskit_key.items()}
        output_path_tskit_key = os.path.join(results_directory, "pedigree_key.json")
        with open(output_path_tskit_key, "w") as f:
            json.dump(txt_ped_to_tskit_key_conv, f, indent=4)
        logging.info(f"Pedigree key saved to {output_path_tskit_key}")
        
        # Set the initial state of tree sequence
        pedigree = pb.finalise(sequence_length=assembly_len_maps)
        
        # Optionally visualize the pedigree
        pedigree_viz_path = os.path.join(results_directory, "diagram_msprime_pedigree.svg")
        try:
            G = draw_pedigree(pedigree, pedigree_viz_path)
            print(f"Pedigree diagram saved to {pedigree_viz_path}")
        except Exception as e:
            logging.warning(f"Could not generate pedigree visualization: {e}")
        
        # Run simulations
        print(f"Checkpoint 1: Starting simulation with the Fixed Pedigree")
        
        # This tells the sim_ancestry function to generate a certain number of
        # separate, independent simulation replicates.
        ped_ts_replicates = msprime.sim_ancestry(
            initial_state=pedigree,
            recombination_rate=rate_map,
            model="fixed_pedigree",
            record_provenance=False,
            discrete_genome=True,
            num_replicates=args.num_replicates
        )
        
        ts_filenames = []
        for replicate_index, ts in enumerate(ped_ts_replicates):
            print(f"Checkpoint 2: Processing replicate {replicate_index}")
            
            completed_ts = msprime.sim_ancestry(
                initial_state=ts,
                recombination_rate=rate_map,
                demography=demography_model,
                model=[
                    msprime.DiscreteTimeWrightFisher(duration=25),
                    msprime.StandardCoalescent(),
                ],
                record_provenance=False
            )
            
            mutated_ts = msprime.sim_mutations(
                completed_ts,
                rate=args.mutation_rate
            )
            
            # Save the tree sequence
            ts_filename = f"{results_directory}/msprime_tree_replicate_{replicate_index}.trees"
            mutated_ts.dump(ts_filename)
            ts_filenames.append(ts_filename)
            
            print(f"Checkpoint 3: Saved replicate {replicate_index}")
        
            output_filename_vcf = os.path.join(results_directory, f"msprime_replicate_{replicate_index}.vcf")
            convert_ts_to_vcf(ts, output_filename_vcf, conversion_dict, txt_ped_to_tskit_key, replicate_index)
            
    else:
        logging.error(f"Pedigree file not found at {pedigree_path}")
        print(f"Error: Pedigree file not found at {pedigree_path}")
        sys.exit(1)
    
    # Calculate and print runtime
    t1_stop = process_time()
    runtime = t1_stop - t1_start
    hours = runtime // 3600
    minutes = (runtime % 3600) // 60
    seconds = (runtime % 3600) % 60
    print(f"Runtime: {hours:.0f}:{minutes:.0f}:{seconds:.0f}")
    
    vcf_files = [f"{results_directory}/msprime_replicate_{i}.vcf" for i in range(args.num_replicates)]
    output_vcf = os.path.join(results_directory, "merged_replicates.vcf")

    with pysam.VariantFile(output_vcf, "w") as outfile:
        for vcf_file in vcf_files:
            with pysam.VariantFile(vcf_file) as infile:
                for rec in infile:
                    outfile.write(rec)

    print(f"Merged VCF file saved to {output_vcf}")


if __name__ == "__main__":
    main()