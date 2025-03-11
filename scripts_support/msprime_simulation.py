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
import subprocess


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
            logging.info(f"Warning: No .env file found in {comp_gen_dir}")
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
        
        logging.info(f"Loaded environment variables from: {env_path}")
        
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
                logging.info(f"{key.replace('_', ' ').title()}: {value}")
        
        return env_path
    
    except FileNotFoundError as e:
        logging.error(f"Error: {e}")
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
    
    logging.info(f"The assembly length is {assembly_len_maps:,} bp.")
    logging.info(f"Chromosome lengths: {genetic_map_positions}")
    
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

def extract_ibd_segments(ts, min_segment_length_cm, max_time, conversion_dict, genetic_map_name, replicate_index):
    """
    Extract IBD segments from a tree sequence with proper chromosome coordinates.
    
    Args:
        ts: Tree sequence object
        min_segment_length_cm: Minimum segment length in centiMorgans
        max_time: Maximum time to look back (None for unlimited)
        conversion_dict: Dictionary mapping positions to chromosomes
        genetic_map_name: Name of genetic map to use
        
    Returns:
        DataFrame with IBD segments in the requested format
    """
    # Convert min_segment_length from cM to bp (approximate)
    min_segment_length_bp = min_segment_length_cm * 1e6
    
    # Get IBD segments with no time limitation if max_time is None
    ibd_segments = ts.ibd_segments(
        min_span=min_segment_length_bp,
        max_time=max_time,
        store_pairs=True,
        store_segments=True
    )
    
    # Create node-to-individual mapping
    node_to_ind = {}
    
    # Map each node to its individual
    for ind in ts.individuals():
        for node in ind.nodes:
            node_to_ind[node] = ind.id
    
    # Function to identify chromosome and start position
    def identify_chromosome(position, conversion_dict):
        """Identify which chromosome a position belongs to."""
        for (start, end), chrom in conversion_dict.items():
            if start <= position < end:
                return chrom, start
        return None, None
    
    # Function to convert bp to cM
    def bp_to_cm(bp_length, chrom_num, genetic_map_name):
        """Convert base pair length to centiMorgans using a genetic map."""
        # Get average recombination rate from stdpopsim
        species = stdpopsim.get_species("HomSap")
        genetic_map = species.get_genetic_map(genetic_map_name)
        
        try:
            # Get chromosome-specific rate map
            rate_map = genetic_map.get_chromosome_map(f"chr{chrom_num}")
            # Use mean recombination rate (Morgan/bp) for conversion
            mean_rate = rate_map.mean_rate
            # Convert to centiMorgans (1 Morgan = 100 cM)
            cm_length = bp_length * mean_rate * 100
            return cm_length
        except Exception as e:
            logging.info(f"Error getting recombination rate for chromosome {chrom_num}: {e}")
            # Fallback to standard approximation: 1cM ≈ 1Mb
            return bp_length / 1e6
    
    # Process IBD segments
    segment_data = []
    for pair, segments in ibd_segments.items():
        node1, node2 = pair
        
        # Get individual IDs
        ind1_id = node_to_ind.get(node1, -1)
        ind2_id = node_to_ind.get(node2, -1)
        
        for segment in segments:
            # Determine chromosome and position within chromosome
            chrom, chrom_start = identify_chromosome(segment.left, conversion_dict)
            if chrom is None:
                continue
                
            # Calculate local positions
            local_left = segment.left - chrom_start
            local_right = segment.right - chrom_start
            local_span = segment.right - segment.left  # Use actual segment span
            
            # Convert span to cM
            span_cm = bp_to_cm(local_span, chrom, genetic_map_name)
            
            # Get MRCA for this segment
            tree = ts.at(segment.left)
            mrca_node = tree.mrca(node1, node2)
            tmrca = tree.time(mrca_node) if mrca_node != tskit.NULL else np.nan
            
            # Get MRCA individual if available
            mrca_individual_id = -1
            if mrca_node != tskit.NULL:
                mrca_ind = ts.node(mrca_node).individual
                if mrca_ind != tskit.NULL:
                    mrca_individual_id = mrca_ind
            
            # Add to results
            segment_data.append({
                'individual1_id': f"{int(ind1_id)}_rep{replicate_index}",  # Add replicate suffix
                'node1': int(node1),
                'individual2_id': f"{int(ind2_id)}_rep{replicate_index}",  # Add replicate suffix
                'node2': int(node2),
                'chromosome': chrom,
                'start_bp': int(local_left),
                'end_bp': int(local_right),
                'length_bp': int(local_span),
                'length_cm': float(span_cm),
                'mrca_individual_id': f"{int(mrca_individual_id)}_rep{replicate_index}",
                'mrca_node': int(mrca_node) if mrca_node != tskit.NULL else -1,
                'tmrca': float(tmrca) if not np.isnan(tmrca) else -1
            })
    
    # Create DataFrame
    if segment_data:
        df = pd.DataFrame(segment_data)
        # Filter by actual cM length now that we have proper conversions
        df = df[df['length_cm'] >= min_segment_length_cm]
        # Ensure specific column order
        columns = ['individual1_id', 'node1', 'individual2_id', 'node2', 
                  'chromosome', 'start_bp', 'end_bp', 'length_bp', 'length_cm', 
                  'mrca_individual_id', 'mrca_node', 'tmrca']
        return df[columns]
    else:
        return pd.DataFrame(columns=[
            'individual1_id', 'node1', 'individual2_id', 'node2',
            'chromosome', 'start_bp', 'end_bp', 'length_bp', 'length_cm',
            'mrca_individual_id', 'mrca_node', 'tmrca'
        ])

def write_multi_chrom_vcf(ts, vcf_file, conversion_dict, replicate_index, txt_ped_to_tskit_key, node_to_individual):
    """
    Write a tree sequence to a multi-chromosome VCF file with proper sample naming.
    
    Args:
        ts: The tree sequence object
        vcf_file: Path to output VCF file
        conversion_dict: Dictionary mapping position ranges to chromosome numbers
        replicate_index: Index of the replicate to append to sample names
        txt_ped_to_tskit_key: Dictionary mapping original IDs to tskit IDs
    
    Returns:
        vcf_file: Path to the created VCF file
        sample_names: List of sample names used in the VCF
    """
    
    # Add at the beginning of write_multi_chrom_vcf
    logging.info(f"Tree sequence stats: {ts.num_samples} samples, {ts.num_trees} trees, {ts.num_mutations} mutations")

    # Test direct variant access
    variant_count = 0
    for variant in ts.variants():
        variant_count += 1
        if variant_count <= 5:
            logging.info(f"Direct variant access - Variant {variant_count}: pos={variant.position}, alleles={variant.alleles}")
    logging.info(f"Total variants accessed directly: {variant_count}")
    
    # Add this debugging section near the beginning of write_multi_chrom_vcf
    logging.info(f"Conversion dictionary contains {len(conversion_dict)} chromosome mappings:")
    for (start, end), chrom in conversion_dict.items():
        logging.info(f"  Range {start}-{end} maps to chromosome {chrom}")

    # Track chromosome assignments during variant processing
    assigned_chroms = {}
    unassigned_count = 0
    for variant in ts.variants():
        pos = int(variant.position)
        
        # Find which chromosome this position belongs to
        chrom = None
        for (start, end), chromosome in conversion_dict.items():
            if start <= pos < end:
                chrom = chromosome
                if chrom not in assigned_chroms:
                    assigned_chroms[chrom] = 0
                assigned_chroms[chrom] += 1
                break
        
        if chrom is None:
            unassigned_count += 1

    logging.info(f"Variant chromosome assignments: {assigned_chroms}")
    logging.info(f"Unassigned variants: {unassigned_count}")
    
    # Add this near the beginning of write_multi_chrom_vcf
    logging.info("Examining the first 5 variants from the tree sequence:")
    for i, variant in enumerate(ts.variants()):
        if i >= 5:
            break
        pos = int(variant.position)
        logging.info(f"Variant {i}: position={pos}, alleles={variant.alleles}")
        # Check which chromosome this belongs to
        assigned_chrom = None
        for (start, end), chrom in conversion_dict.items():
            if start <= pos < end:
                assigned_chrom = chrom
                local_pos = pos - start
                logging.info(f"  Assigned to chromosome {chrom} at local position {local_pos}")
                break
        if assigned_chrom is None:
            logging.info("  Not assigned to any chromosome!")
            
    ##################################################################
    
    # Create a reverse mapping from tskit IDs to text pedigree IDs
    tskit_to_txt_ped = {v: k for k, v in txt_ped_to_tskit_key.items()}
    
    # Use the provided mapping for tracking nodes per individual
    if node_to_individual is None:
        node_to_individual = {}
        for ind in ts.individuals():
            for node in ind.nodes:
                node_to_individual[node] = ind.id

    # Create a collection of nodes per individual
    individual_nodes = defaultdict(list)
    for node, ind_id in node_to_individual.items():
        individual_nodes[ind_id].append(node)
    
    # Extract sample individuals and their metadata
    sample_nodes = ts.samples()
    sample_individuals = {}  # Individual ID -> list of sample nodes
    sample_names = []  # Final list of sample names for the VCF
    node_idx = {}  # Map node ID to sample index in the VCF
    
    # For each sample node, get the corresponding individual
    for node_id in sample_nodes:
        if node_id in node_to_individual:
            ind_id = node_to_individual[node_id]
            if ind_id not in sample_individuals:
                sample_individuals[ind_id] = []
            sample_individuals[ind_id].append(node_id)
    
    # Generate unique sample names
    sample_idx = 0
    for ind_id, nodes in sample_individuals.items():
        ind = ts.individual(ind_id)
        
        # Use the reverse mapping to get the original ID
        if ind_id in tskit_to_txt_ped:
            original_id = tskit_to_txt_ped[ind_id]
            base_name = f"{original_id}_rep{replicate_index}"
        else:
            # Fallback to metadata if mapping doesn't exist
            metadata = ind.metadata
            individual_name = metadata.get('individual_name', f"ind_{ind_id}")
            base_name = f"{individual_name}_rep{replicate_index}"
        
        # Sort nodes to ensure consistent haplotype naming
        sorted_nodes = sorted(nodes)
        
        # Create names for each haplotype of this individual
        for i, node_id in enumerate(sorted_nodes):
            haplotype_name = f"{base_name}_{i}"
            sample_names.append(haplotype_name)
            node_idx[node_id] = sample_idx
            sample_idx += 1
    
    # Create a dictionary to organize variants by chromosome
    variants_by_chrom = {}
    
    # Process all variants and assign to chromosomes
    variant_count = 0
    for variant in ts.variants():
        pos = int(variant.position)
        
        # Find which chromosome this position belongs to
        chrom = None
        chrom_pos = None
        
        for (start, end), chromosome in conversion_dict.items():
            if start <= pos < end:
                # Calculate the position within the original chromosome
                chrom_pos = pos - start
                chrom = chromosome
                break
        
        if chrom is not None:
            # Initialize chromosome entry if not exists
            if chrom not in variants_by_chrom:
                variants_by_chrom[chrom] = []
            
            # Store variant data: position, alleles, genotypes
            variants_by_chrom[chrom].append({
                'position': chrom_pos,
                'alleles': variant.alleles,
                'genotypes': variant.genotypes  # This is a numpy array
            })
            variant_count += 1
    
    logging.info(f"Found {variant_count} variants across {len(variants_by_chrom)} chromosomes")
    
    # Create VCF file
    with open(vcf_file, 'w') as f:
        # Write VCF header
        f.write('##fileformat=VCFv4.2\n')
        f.write('##source=custom_tree_sequence_converter\n')
        
        # Add chromosome information to header
        for chrom in sorted(variants_by_chrom.keys()):
            f.write(f'##contig=<ID=chr{chrom}>\n')
        
        # Add format field
        f.write('##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n')
        
        # Write the column header line
        f.write('#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT')
        for sample in sample_names:
            f.write(f'\t{sample}')
        f.write('\n')
        
        # Write variants for each chromosome
        for chrom in sorted(variants_by_chrom.keys()):
            # Sort variants by position
            variants = sorted(variants_by_chrom[chrom], key=lambda x: x['position'])
            
            for var in variants:
                pos = var['position']
                alleles = var['alleles']
                genotypes = var['genotypes']  # This is a numpy array
                
                # Format genotypes differently based on the array structure
                gt_str = []
                
                # Determine the shape of genotypes to handle correctly
                if len(genotypes.shape) == 1:
                    # 1D array - one entry per sample
                    for i, sample_node in enumerate(sample_nodes):
                        if sample_node in node_idx:
                            sample_index = node_idx[sample_node]
                            # Ensure we have a valid array index
                            if i < len(genotypes):
                                g = genotypes[i]
                                phased = str(g)  # Simple scalar value
                                
                                # Ensure the genotypes are in the same order as sample_names
                                while len(gt_str) <= sample_index:
                                    gt_str.append(".")  # Placeholder for missing samples
                                
                                gt_str[sample_index] = phased
                
                elif len(genotypes.shape) == 2:
                    # 2D array - ploidy is represented in second dimension
                    for i, sample_node in enumerate(sample_nodes):
                        if sample_node in node_idx:
                            sample_index = node_idx[sample_node]
                            # Ensure we have a valid array index
                            if i < len(genotypes):
                                g = genotypes[i]
                                phased = '|'.join([str(x) for x in g])
                                
                                # Ensure the genotypes are in the same order as sample_names
                                while len(gt_str) <= sample_index:
                                    gt_str.append(".|.")  # Placeholder for missing samples
                                
                                gt_str[sample_index] = phased
                
                # Write variant line
                f.write(f'chr{chrom}\t{pos+1}\t.\t{alleles[0]}\t')
                
                # Handle multiple alternate alleles
                if len(alleles) > 2:
                    f.write(','.join(alleles[1:]))
                else:
                    f.write(f'{alleles[1]}')
                    
                f.write('\t.\t.\t.\tGT\t')
                f.write('\t'.join(gt_str))
                f.write('\n')
    
    return vcf_file, sample_names

def calculate_comprehensive_pairwise_mrca(ts, ibd_segments_file=None, ibd_segments_df=None, node_to_individual=None, replicate_index=None):
    """
    Calculate all distinct MRCAs for each pair of samples from IBD segments.
    
    Args:
        ts: Tree sequence object
        ibd_segments_file: Path to CSV file with IBD segments (optional)
        ibd_segments_df: DataFrame with IBD segments (optional)
        node_to_individual: Mapping from node IDs to individual IDs (optional)
        replicate_index: Index of the current replicate for ID suffixing
        
    Returns:
        DataFrame with comprehensive pairwise MRCA information
    """
    from collections import defaultdict
    from intervaltree import IntervalTree
    import pandas as pd
    import numpy as np
    
    try:
        # Load IBD segments if file provided
        if ibd_segments_df is None and ibd_segments_file is not None:
            ibd_segments_df = pd.read_csv(ibd_segments_file)
        elif ibd_segments_df is None:
            logging.info("Either ibd_segments_df or ibd_segments_file must be provided")
            return pd.DataFrame(columns=[
                'individual1_id', 'node1', 'individual2_id', 'node2',
                'mrca_individual_id', 'mrca_node', 'tmrca', 
                'total_length_bp', 'covered_regions'
            ])
        
        # Return empty dataframe if no segments
        if len(ibd_segments_df) == 0:
            return pd.DataFrame(columns=[
                'individual1_id', 'node1', 'individual2_id', 'node2',
                'mrca_individual_id', 'mrca_node', 'tmrca', 
                'total_length_bp', 'covered_regions'
            ])
        
        # Ensure node IDs are integers
        ibd_segments_df['node1'] = ibd_segments_df['node1'].astype(int)
        ibd_segments_df['node2'] = ibd_segments_df['node2'].astype(int)
        
        # Create a mapping from nodes to individuals if not provided
        if node_to_individual is None:
            node_to_individual = {}
            for ind in ts.individuals():
                for node in ind.nodes:
                    node_to_individual[node] = ind.id
        
        # For each pair, we'll track the genomic intervals where each MRCA applies
        pair_mrca_intervals = defaultdict(lambda: defaultdict(list))
        
        # Store individual info for each pair
        pair_info = {}
        
        # Process each IBD segment
        for _, segment in ibd_segments_df.iterrows():
            node1 = int(segment['node1'])
            node2 = int(segment['node2'])
            pair = (min(node1, node2), max(node1, node2))  # Ensure consistent ordering
            
            # Store individual information
            if pair not in pair_info:
                if 'individual1_id' in segment:
                    # Use the IDs from the segment, which might already have replicate suffix
                    ind1_id = segment['individual1_id']
                    ind2_id = segment['individual2_id']
                else:
                    # Get IDs from node_to_individual mapping
                    ind1_id = node_to_individual.get(node1, -1)
                    ind2_id = node_to_individual.get(node2, -1)
                    
                    # Add replicate suffix if provided and if IDs don't already have it
                    if replicate_index is not None:
                        if isinstance(ind1_id, (int, float)):
                            ind1_id = f"{int(ind1_id)}_rep{replicate_index}"
                        if isinstance(ind2_id, (int, float)):
                            ind2_id = f"{int(ind2_id)}_rep{replicate_index}"
                
                pair_info[pair] = {
                    'individual1_id': ind1_id,
                    'node1': node1,
                    'individual2_id': ind2_id,
                    'node2': node2
                }
            
            # Get the tree at this segment
            tree = ts.at(segment['start_bp'])
            mrca_node = tree.mrca(node1, node2)
            
            if mrca_node != tskit.NULL:
                start = segment['start_bp']
                end = segment['end_bp']
                # Add this interval to the MRCA's list for this pair
                pair_mrca_intervals[pair][mrca_node].append((start, end))
        
        # Now process the intervals to find the non-redundant MRCAs
        results = []
        
        for pair, mrca_intervals in pair_mrca_intervals.items():
            # Get the pair information
            pair_data = pair_info[pair]
            
            # Create interval trees for each MRCA
            mrca_trees = {}
            for mrca, intervals in mrca_intervals.items():
                tree = IntervalTree()
                for start, end in intervals:
                    tree[start:end] = mrca
                mrca_trees[mrca] = tree
            
            # Find all time points (MRCAs)
            mrca_times = {}
            for mrca in mrca_intervals.keys():
                # Sample a tree where this MRCA exists
                sample_interval = mrca_intervals[mrca][0]
                sample_point = (sample_interval[0] + sample_interval[1]) / 2
                tree = ts.at(sample_point)
                mrca_times[mrca] = tree.time(mrca)
            
            # For each MRCA, calculate the total region it covers exclusively
            for mrca, intervals in mrca_intervals.items():
                # Convert intervals to a set for easier operations
                mrca_regions = IntervalTree()
                for start, end in intervals:
                    mrca_regions[start:end] = mrca
                
                # Remove regions covered by more recent MRCAs
                for other_mrca, other_time in mrca_times.items():
                    if other_mrca != mrca and other_time < mrca_times[mrca]:
                        # This is a more recent MRCA, remove its regions
                        other_regions = mrca_trees[other_mrca]
                        
                        # We need to work with copies to avoid modifying during iteration
                        to_remove = []
                        to_add = []
                        
                        for interval in mrca_regions:
                            overlaps = other_regions.overlap(interval.begin, interval.end)
                            for overlap in overlaps:
                                # Mark this interval for removal
                                to_remove.append(interval)
                                
                                # Create new intervals for non-overlapping parts
                                if interval.begin < overlap.begin:
                                    to_add.append((interval.begin, overlap.begin, interval.data))
                                if interval.end > overlap.end:
                                    to_add.append((overlap.end, interval.end, interval.data))
                        
                        # Apply the changes
                        for interval in to_remove:
                            mrca_regions.remove(interval)
                        for begin, end, data in to_add:
                            mrca_regions[begin:end] = data
                
                # Calculate total bp covered by this MRCA exclusively
                total_bp = sum(interval.end - interval.begin for interval in mrca_regions)
                
                # Create a string representation of the covered regions
                covered_regions = ';'.join([f"{int(interval.begin)}-{int(interval.end)}" 
                                          for interval in sorted(mrca_regions)])
                
                # Get MRCA individual if available
                mrca_individual_id = -1
                if mrca != tskit.NULL:
                    mrca_ind = ts.node(mrca).individual
                    if mrca_ind != tskit.NULL:
                        mrca_individual_id = mrca_ind
                
                # Add replicate suffix to mrca_individual_id if it's not -1
                if replicate_index is not None and mrca_individual_id != -1:
                    mrca_individual_id = f"{int(mrca_individual_id)}_rep{replicate_index}"
                
                # Add to results if there's any exclusive coverage
                if total_bp > 0:
                    result_row = {
                        **pair_data,  # Include individual and node IDs
                        'mrca_individual_id': mrca_individual_id,
                        'mrca_node': mrca,
                        'tmrca': mrca_times[mrca],
                        'total_length_bp': total_bp,
                        'covered_regions': covered_regions
                    }
                    
                    results.append(result_row)
        
        # Create DataFrame and ensure column order
        if results:
            mrca_df = pd.DataFrame(results)
            columns = [
                'individual1_id', 'node1', 'individual2_id', 'node2',
                'mrca_individual_id', 'mrca_node', 'tmrca', 
                'total_length_bp', 'covered_regions'
            ]
            return mrca_df[columns]
        else:
            return pd.DataFrame(columns=[
                'individual1_id', 'node1', 'individual2_id', 'node2',
                'mrca_individual_id', 'mrca_node', 'tmrca', 
                'total_length_bp', 'covered_regions'
            ])

    except Exception as e:
        logging.info(f"Error in calculate_comprehensive_pairwise_mrca: {e}")
        return pd.DataFrame(columns=[
            'individual1_id', 'node1', 'individual2_id', 'node2',
            'mrca_individual_id', 'mrca_node', 'tmrca', 
            'total_length_bp', 'covered_regions'
        ])

def process_tree_sequence(ts, conversion_dict, replicate_index, txt_ped_to_tskit_key, 
                        results_directory, min_segment_length_cm=3.0, max_time=None, 
                        genetic_map_name="HapMapII_GRCh38"):
    """
    Integrated function that:
    1. Writes the tree sequence to a VCF file (adds mutations if none present)
    2. Extracts IBD segments with proper chromosome coordinates
    3. Calculates comprehensive pairwise MRCA information
    
    Args:
        ts: The tree sequence object
        conversion_dict: Dictionary mapping position ranges to chromosomes
        replicate_index: Index of the replicate
        txt_ped_to_tskit_key: Dictionary mapping original IDs to tskit IDs
        results_directory: Directory to save results
        min_segment_length_cm: Minimum segment length in centiMorgans
        max_time: Maximum time to look back (None for unlimited)
        genetic_map_name: Name of genetic map to use
    
    Returns:
        Dictionary with paths to generated files
    """
    
    # Create node to individual mapping that will be used by multiple functions
    node_to_individual = {}
    for ind in ts.individuals():
        for node in ind.nodes:
            node_to_individual[node] = ind.id
            
    files_info = {
        'vcf_file': None,
        'compressed_vcf': None,
        'index_file': None,
        'stats_file': None,
        'ibd_file': None
    }
    
    # # Part 1: VCF conversion
    # vcf_file = os.path.join(results_directory, f"msprime_replicate_{replicate_index}.vcf")
    # vcf_file, sample_names = write_multi_chrom_vcf(
    #     ts, vcf_file, conversion_dict, replicate_index, txt_ped_to_tskit_key,
    #     node_to_individual=node_to_individual
    # )
    
    # # Compress and index the VCF file
    # compressed_vcf = f"{vcf_file}.gz"

    
    # try:
    #     # Use bgzip to compress
    #     bgzip_cmd = ["bgzip", "-c", vcf_file]
    #     with open(compressed_vcf, 'wb') as f:
    #         subprocess.run(bgzip_cmd, stdout=f, check=True)
    #     files_info['compressed_vcf'] = compressed_vcf
        
    #     # Index the compressed VCF file with tabix
    #     tabix_cmd = ["tabix", "-p", "vcf", compressed_vcf]
    #     subprocess.run(tabix_cmd, check=True)
    #     files_info['index_file'] = f"{compressed_vcf}.tbi"
        
    #     # Run a quick stats check
    #     stats_output = os.path.join(results_directory, f"vcf_stats_rep{replicate_index}.txt")
    #     stat_cmd = ["bcftools", "stats", compressed_vcf]
    #     with open(stats_output, 'w') as f:
    #         subprocess.run(stat_cmd, stdout=f, check=True)
    #     files_info['stats_file'] = stats_output
        
    #     logging.info(f"Generated VCF files for replicate {replicate_index}")
    # except subprocess.CalledProcessError as e:
    #     logging.info(f"Error processing VCF for replicate {replicate_index}: {e}")
    
    # Part 2: Extract IBD segments
    ibd_output = os.path.join(results_directory, f"ibd_segments_rep_{replicate_index}.csv")
    
    try:
        # Extract IBD segments
        ibd_df = extract_ibd_segments(
            ts, 
            min_segment_length_cm, 
            max_time, 
            conversion_dict, 
            genetic_map_name,
            replicate_index
        )
        
        # Save IBD segments
        ibd_df.to_csv(ibd_output, index=False)
        files_info['ibd_file'] = ibd_output
        logging.info(f"Extracted {len(ibd_df)} IBD segments for replicate {replicate_index}")
    except Exception as e:
        logging.info(f"Error extracting IBD segments for replicate {replicate_index}: {e}")
        
    # Part 3: Calculate comprehensive pairwise MRCA
    mrca_output = os.path.join(results_directory, f"pairwise_mrca_rep_{replicate_index}.csv")
    files_info['mrca_file'] = None

    try:
        # Only calculate MRCA if we have IBD segments
        if 'ibd_file' in files_info and files_info['ibd_file'] is not None:
            # Call the MRCA calculation function
            mrca_df = calculate_comprehensive_pairwise_mrca(
                ts=ts,
                ibd_segments_file=files_info['ibd_file'],
                node_to_individual=node_to_individual,
                replicate_index=replicate_index
            )
            
            if len(mrca_df) > 0:
                # Save MRCA results
                mrca_df.to_csv(mrca_output, index=False)
                files_info['mrca_file'] = mrca_output
                logging.info(f"Calculated MRCA for {len(mrca_df)} sample pairs")
            else:
                logging.info("No valid MRCA results found")
    except Exception as e:
        logging.info(f"Error calculating MRCA for replicate {replicate_index}: {e}")
    
    return files_info


def main():
    """Main function."""
    args = parse_arguments()
    
    # Start timing
    t1_start = process_time()
    
    # Set up current time for logging
    now_est = datetime.now()
    logging.info(f"Starting simulation at {now_est.strftime('%B %d, %-I:%M:%S %p')}")
    
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
    logging.info(f"Log file is located at {log_filename}")
    
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
    
    logging.info(f"Simulating chromosomes: {which_chromosome}")
    
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
            logging.info(f"Pedigree diagram saved to {pedigree_viz_path}")
        except Exception as e:
            logging.warning(f"Could not generate pedigree visualization: {e}")
        
        # # Create reference sequences for all requested chromosomes
        # reference_seed = 42  # Fixed seed for consistency
        # rng = np.random.RandomState(reference_seed)
        # reference_sequence = {}  # Will hold a reference sequence for each chromosome

        # # For each chromosome in the simulation, create a reference sequence
        # # We'll create sequences for all chromosomes in which_chromosome
        # for chrom in which_chromosome:
        #     # Find the chromosome length from conversion_dict
        #     chrom_length = None
        #     for (start, end), chromosome in conversion_dict.items():
        #         if chromosome == chrom:
        #             chrom_length = end - start
        #             break
            
        #     if chrom_length is not None:
        #         # Generate a reference sequence for this chromosome
        #         reference_sequence[chrom] = "".join(np.random.choice(
        #             ["A", "C", "G", "T"], 
        #             size=chrom_length, 
        #             p=[0.3, 0.2, 0.2, 0.3]
        #         ))
        #     else:
        #         logging.warning(f"Could not find length for chromosome {chrom}")

        # Run simulations
        logging.info("")
        logging.info(f"Checkpoint 1: Starting simulation with the Fixed Pedigree")
        
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
        all_files_info = []
        for replicate_index, ts in enumerate(ped_ts_replicates):
            logging.info("")
            logging.info(f"Checkpoint 2: Processing replicate {replicate_index}")
            
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
            
            # mutation_seed = rng.randint(1, 2**32 - 1)
            
            # # For multiple chromosomes, use a different approach
            # # We need to mutate the sequence according to position
            # if len(which_chromosome) == 1:
            #     # Simple case - just one chromosome
            #     chrom = which_chromosome[0]
            #     mutation_model = msprime.SLiMMutationModel(
            #         type=0,
            #         next_id=0,
            #         rate=args.mutation_rate,
            #         nucleotides=True,
            #         slim_generation=1,
            #         sequence=reference_sequence[chrom]
            #     )
                
            #     # Apply mutations
            #     mutated_ts = msprime.sim_mutations(
            #         completed_ts,
            #         rate=None,  # Rate is specified in the model
            #         model=mutation_model,
            #         random_seed=mutation_seed
            #     )
            # else:
            #     # Multiple chromosomes - use position-specific ancestral states
            #     mutated_ts = completed_ts
                
            #     # Create a position-specific ancestral state map
            #     ancestral_states = {}
                
            #     for position in range(int(assembly_len_maps)):
            #         # Find which chromosome this position belongs to
            #         for (start, end), chrom in conversion_dict.items():
            #             if start <= position < end:
            #                 # Get the base from the appropriate reference sequence
            #                 local_pos = position - start
            #                 if chrom in reference_sequence and local_pos < len(reference_sequence[chrom]):
            #                     ancestral_states[position] = reference_sequence[chrom][local_pos]
            #                 break
                
            #     # Apply mutations with consistent ancestral states
            #     mutated_ts = msprime.sim_mutations(
            #         completed_ts,
            #         rate=args.mutation_rate,
            #         random_seed=mutation_seed,
            #         discrete_genome=True,
            #         ancestral_state_map=ancestral_states
            #     )
                
            mutated_ts = msprime.sim_mutations(
                completed_ts,
                rate=args.mutation_rate
            )
            
            # Save the tree sequence
            ts_filename = f"{results_directory}/msprime_tree_replicate_{replicate_index}.trees"
            mutated_ts.dump(ts_filename)
            ts_filenames.append(ts_filename)
            
            logging.info(f"Checkpoint 3: Saved replicate {replicate_index}")
        
            files_info = process_tree_sequence(mutated_ts, conversion_dict, replicate_index, txt_ped_to_tskit_key, 
                        results_directory, min_segment_length_cm=3.0, max_time=None, 
                        genetic_map_name="HapMapII_GRCh38")
            all_files_info.append(files_info)
            
    else:
        logging.error(f"Pedigree file not found at {pedigree_path}")
        logging.error(f"Error: Pedigree file not found at {pedigree_path}")
        sys.exit(1)
    
    # Calculate and print runtime
    t1_stop = process_time()
    runtime = t1_stop - t1_start
    hours = runtime // 3600
    minutes = (runtime % 3600) // 60
    seconds = (runtime % 3600) % 60
    logging.info(f"Runtime: {hours:.0f}:{minutes:.0f}:{seconds:.0f}")
    
    # Merge IBD segment files
    ibd_files = [info['ibd_file'] for info in all_files_info if info['ibd_file'] is not None]
    if ibd_files:
        # Read and concatenate all IBD segment files
        merged_ibd = pd.concat([pd.read_csv(f) for f in ibd_files if os.path.exists(f)], ignore_index=True)
        merged_ibd_file = os.path.join(results_directory, "merged_ibd_segments.csv")
        merged_ibd.to_csv(merged_ibd_file, index=False)
        logging.info(f"Merged IBD segments saved to {merged_ibd_file}")
            
    # Merge MRCA files
    mrca_files = [info['mrca_file'] for info in all_files_info if info['mrca_file'] is not None]
    if mrca_files:
        # Read and concatenate all MRCA files
        merged_mrca = pd.concat([pd.read_csv(f) for f in mrca_files if os.path.exists(f)], ignore_index=True)
        merged_mrca_file = os.path.join(results_directory, "merged_pairwise_mrca.csv")
        merged_mrca.to_csv(merged_mrca_file, index=False)
        logging.info(f"Merged MRCA information saved to {merged_mrca_file}")
    
    # Merge VCF files if needed
    compressed_vcf_files = [info['compressed_vcf'] for info in all_files_info if info['compressed_vcf']]

    if compressed_vcf_files:
        output_vcf = os.path.join(results_directory, "merged_replicates.vcf.gz")
        
        merge_cmd = ["bcftools", "merge", "-o", output_vcf, "-O", "z"] + compressed_vcf_files
        
        try:
            subprocess.run(merge_cmd, check=True)
            logging.info(f"Merged VCF file saved to {output_vcf}")
            
            # Index the merged file
            merged_index_cmd = ["tabix", "-p", "vcf", output_vcf]
            subprocess.run(merged_index_cmd, check=True)
            logging.info(f"Indexed merged VCF file")
            
        except subprocess.CalledProcessError as e:
            logging.info(f"Error merging VCF files: {e}")
    else:
        logging.info("No valid VCF files to merge")


if __name__ == "__main__":
    main()