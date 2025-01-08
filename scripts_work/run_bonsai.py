import subprocess
import os
import argparse
import logging
import sys
from utils.bonsaitree.bonsaitree.v3 import bonsai
import pandas as pd
import json
import random
import networkx as nx
from tqdm import tqdm
from collections import Counter
import numpy as np
import math
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle
from cdlib import algorithms, NodeClustering
import cdlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from scipy.spatial import ConvexHull
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from decouple import config


# https://github.com/23andMe/bonsaitree/tree/main/bonsaitree/v3

# def import_bonsai():
#     try:
#         from utils.bonsaitree.bonsaitree.v3 import bonsai  # Then try utils-prefixed import
#         return bonsai
#     except ImportError:
#         pass

#     # Try various path configurations
#     possible_paths = [
#         Path("utils/bonsaitree"),
#         Path("utils/bonsaitree/bonsaitree"),
#         Path("../utils/bonsaitree"),
#         Path(os.path.dirname(__file__)) / "utils/bonsaitree",
#         Path(os.path.dirname(__file__)).parent / "utils/bonsaitree"  # One level up
#     ]

#     for path in possible_paths:
#         abs_path = path.resolve()
#         if abs_path.exists():
#             sys.path.insert(0, str(abs_path))
#             try:
#                 from utils.bonsaitree.bonsaitree.v3 import bonsai
#                 return bonsai
#             except ImportError:
#                 sys.path.pop(0)

#     raise ImportError("Could not import bonsai module")

# Usage
# bonsai = import_bonsai()

def configure_logging(log_filename, log_file_debug_level="INFO", console_debug_level="INFO"):
    """
    Configure logging for both file and console handlers.

    Args:
        log_file_path (str): Path to the log file where logs will be written.
    """
    # Create a root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Set the root logger to DEBUG to allow all levels

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

def read_ibis_seg(file_path):
    """
    Reads an IBIS .seg file and returns a DataFrame.

    Parameters:
        file_path (str): Path to the IBIS .seg file.

    Returns:
        pd.DataFrame: DataFrame containing the IBIS segments.
    """
    columns = [
        "id1", "id2", "chromosome", "physical_position_start", 
        "physical_position_end", "IBD_type", "genetic_position_start", 
        "genetic_position_end", "genetic_length", "marker_count", 
        "error_count", "error_density"
    ]

    try:
        df = pd.read_csv(file_path, sep="\t", header=None, names=columns)
        return df
    except Exception as e:
        print(f"Error reading IBIS .seg file: {e}")
        return pd.DataFrame()

def read_ibd_hbd_seg(file_path):
    """
    Reads a hap-IBD .ibd.gz file and returns a DataFrame.

    Parameters:
        file_path (str): Path to the hap-IBD .ibd.gz file.

    Returns:
        pd.DataFrame: DataFrame containing the hap-IBD segments.
    """
    columns = [
        "id1", "id1_haplotype_index", "id2", "id2_haplotype_index", 
        "chromosome", "physical_position_start", "physical_position_end", 
        "genetic_length"
    ]

    try:
        df = pd.read_csv(file_path, sep="\t", header=None, names=columns)
        return df
    except Exception as e:
        print(f"Error reading hap-IBD .ibd.gz file: {e}")
        return pd.DataFrame()
    
def filter_segments(segments, min_genetic_length = 7):
    """
    Filters the segments DataFrame based on the minimum genetic length.

    Parameters:
        segments (pd.DataFrame): The segments DataFrame (IBIS, IBD, or HBD).
        segment_type (str): The type of segments ("ibis", "ibd", or "hbd").
        min_genetic_length_ibis (float): Minimum genetic length threshold for IBIS segments.
        min_genetic_length_ibd_hbd (float): Minimum genetic length threshold for IBD/HBD segments.

    Returns:
        pd.DataFrame: Filtered DataFrame containing only rows meeting the genetic length criteria.
    """

    # Filter the DataFrame
    filtered_segments = segments[segments['genetic_length'] >= min_genetic_length].copy()

    print(f"Filtered segments: {len(filtered_segments)} rows (min_genetic_length >= {min_genetic_length}).")
    return filtered_segments

def extract_samples(segments):
    """
    Extracts unique samples from the 'id1' and 'id2' columns of the segments DataFrame.

    Parameters:
        segments (pd.DataFrame): DataFrame containing 'id1' and 'id2' columns.

    Returns:
        list: List of unique samples.
    """
    return list(set(segments["id1"].tolist() + segments["id2"].tolist()))

def generate_numeric_ids(samples):
    numeric_ids = {}
    used_ids = set()
    for sample in samples:
        while True:
            random_id = random.randint(1000, 9999)  # Generate a 4-digit random number
            if random_id not in used_ids:  # Ensure the ID is unique
                numeric_ids[sample] = random_id
                used_ids.add(random_id)
                break
    return numeric_ids


def create_sex_json(sex_data_filename, sex_json_filename):
    """
    Creates a JSON file from the provided sex data file.

    Parameters:
        sex_data_filename (str): Path to the sex data file (text format).
        sex_json_filename (str): Path to save the sex data as a JSON file.

    Returns:
        None
    """
    if os.path.exists(sex_data_filename):
        sex_dict = {}
        sex_map = {"Female": "F", "Male": "M"}  # Explicit mapping
        with open(sex_data_filename, 'r') as f:
            for line_number, line in enumerate(f, start=1):
                stripped_line = line.strip()
                if not stripped_line:  # Skip empty lines
                    continue
                try:
                    user_id, sex = stripped_line.split("\t")
                    if sex in sex_map:
                        sex_dict[user_id] = sex_map[sex]
                    else:
                        print(f"Skipping invalid sex value on line {line_number}: {sex}")
                except ValueError:
                    print(f"Skipping invalid line {line_number}: {line.strip()}")
                    print(line)
        if sex_dict:  # Save only if there is valid data
            with open(sex_json_filename, 'w') as json_file:
                json.dump(sex_dict, json_file, indent=4)
            print(f"Sex data saved to: {sex_json_filename}")
        else:
            print(f"No valid data found in {sex_data_filename}. JSON file not created.")
    else:
        print(f"Sex data file {sex_data_filename} not found.")

def create_age_json(age_data_filename, age_json_filename, samples):
    """
    Creates a JSON file for ages. If `age_data_filename` is None, it generates random ages
    for the provided samples. If `age_data_filename` is provided, it uses the age data file.

    Parameters:
        age_data_filename (str): Path to the age data file (optional, text format).
        age_json_filename (str): Path to save the age data as a JSON file.
        samples (list): List of sample IDs for which to generate ages.

    Returns:
        None
    """
    age_dict = {}

    if age_data_filename and os.path.exists(age_data_filename):
        with open(age_data_filename, 'r') as f:
            for line in f:
                user_id, age = line.strip().split("\t")
                age_dict[user_id] = int(age)
    else:
        # Generate random ages between 18 and 80 for the provided samples
        for sample in samples:
            age_dict[sample] = random.randint(18, 80)

    with open(age_json_filename, 'w') as json_file:
        json.dump(age_dict, json_file, indent=4)
        print(f"Age data saved to: {age_json_filename}")

def load_age_dict(age_json_filename):
    """
    Loads the age dictionary from a JSON file.

    Parameters:
        age_json_filename (str): Path to the JSON file containing age data.

    Returns:
        dict: Dictionary mapping sample IDs to ages.
    """
    with open(age_json_filename, 'r') as file:
        return json.load(file)

def load_sex_dict(sex_json_filename):
    """
    Loads the sex dictionary from a JSON file.

    Parameters:
        sex_json_filename (str): Path to the JSON file containing sex data.

    Returns:
        dict: Dictionary mapping sample IDs to sexes.
    """
    with open(sex_json_filename, 'r') as file:
        return json.load(file)

def select_communities_by_size(communities, target_size, tolerance=0, selection=None, random_selection=False):
    """
    Select communities based on size criteria
    
    Parameters:
    communities (list): List of communities, where each community is a set of member IDs
    target_size (int): Desired size of the community to select
    tolerance (int): Allow communities within +/- tolerance of target size
    selection (int/list): Specific index(es) to select. Can be single index or list of indices
    random_selection (bool): Whether to select communities randomly
    
    Returns:
    list: Selected communities (list of sets of member IDs)
    """
    # Filter communities by target size with tolerance
    filtered_communities = [
        comm for comm in communities 
        if target_size - tolerance <= len(comm) <= target_size + tolerance
    ]
    
    if not filtered_communities:
        print(f"No communities of size {target_size} (±{tolerance}) found.")
        return None
    
    print(f"Found {len(filtered_communities)} communities matching size criteria")
    for i, comm in enumerate(filtered_communities):
        print(f"Community {i}: {len(comm)} members")
    
    # Handle selection
    if selection is not None:
        if isinstance(selection, (list, tuple)):
            selected = [filtered_communities[i] for i in selection]
            print(f"Selected communities at positions {selection}")
        else:
            selected = [filtered_communities[selection]]
            print(f"Selected community at position {selection}")
    elif random_selection:
        selected = [random.choice(filtered_communities)]
        print("Randomly selected one community")
    else:
        selected = filtered_communities
        print("Returning all matching communities")
    
    return selected

def create_bioinfo(samples, numeric_ids, sex_dict, age_dict, output_filename=None):
    """
    Creates a BioInfo object containing genotype IDs, ages, and sexes for the given samples.

    Parameters:
        samples (list): List of sample IDs (e.g., ['user1001', 'user1002']).
        numeric_ids (dict): Dictionary mapping sample IDs to numeric IDs (e.g., {'user1001': 1, 'user1002': 2}).
        age_dict (dict): Dictionary containing ages for each sample ID (e.g., {'user1001': 25, 'user1002': 30}).
        sex_dict (dict): Dictionary containing sexes for each sample ID (e.g., {'user1001': 'M', 'user1002': 'F'}).

    Returns:
        list: List of dictionaries, where each dictionary represents a BioInfo object.
    """
    bioinfo = []
    for sample in samples:
        individual = {
            "genotype_id": numeric_ids[sample],
            "age": age_dict[sample],
            "sex": sex_dict.get(sample, "Unknown"),
            "coverage": float('inf')
        }
        bioinfo.append(individual)

    # Save to a JSON file if output_filename is provided
    if output_filename:
        try:
            with open(output_filename, 'w') as outfile:
                json.dump(bioinfo, outfile, indent=4)
            print(f"BioInfo object saved to {output_filename}")
        except Exception as e:
            print(f"Error saving BioInfo object: {e}")

    return bioinfo

def create_phased_ibd_seg_list(segments_ibd, numeric_ids):
    """
    Creates a phased IBD segment list from the given DataFrame.

    Parameters:
        segments_ibd (pd.DataFrame): DataFrame containing the IBD segments with columns:
                                     ['id1', 'id1_haplotype_index', 'id2', 'id2_haplotype_index',
                                      'chromosome', 'physical_position_start', 'physical_position_end',
                                      'genetic_length'].
        numeric_ids (dict): Mapping of sample IDs (str) to numeric IDs (int).

    Returns:
        list: A list of IBD segments in the specified format:
              [[id1, id2, hap1, hap2, chrom, start_cm, end_cm, len_cm], ...].
    """
    phased_ibd_seg_list = []

    for _, row in segments_ibd.iterrows():
        try:
            id1 = numeric_ids[row['id1']]
            id2 = numeric_ids[row['id2']]
            hap1 = int(row['id1_haplotype_index'])
            hap2 = int(row['id2_haplotype_index'])
            chrom = int(row['chromosome'])
            start_cm = float(row['physical_position_start'])  # Assuming cM info is here
            end_cm = float(row['physical_position_end'])      # Assuming cM info is here
            len_cm = float(row['genetic_length'])

            phased_ibd_seg_list.append([id1, id2, hap1, hap2, chrom, start_cm, end_cm, len_cm])
        except KeyError as e:
            print(f"Error mapping ID: {e}")
        except ValueError as e:
            print(f"Error converting row data: {e}")

    return phased_ibd_seg_list

def create_unphased_ibd_seg_list(segments_ibd, numeric_ids):
    """
    Creates an unphased IBD segment list from the given DataFrame.

    Parameters:
        segments_ibd (pd.DataFrame): DataFrame containing the IBD segments with columns:
                                     ['id1', 'id2', 'chromosome', 'physical_position_start',
                                      'physical_position_end', 'IBD_type', 'genetic_length'].
        numeric_ids (dict): Mapping of sample IDs (str) to numeric IDs (int).

    Returns:
        list: A list of unphased IBD segments in the specified format:
              [[id1, id2, chrom, start_bp, end_bp, is_full, len_cm], ...].
    """
    unphased_ibd_seg_list = []

    for _, row in segments_ibd.iterrows():
        try:
            id1 = numeric_ids[row['id1']]
            id2 = numeric_ids[row['id2']]
            chrom = str(row['chromosome'])  # Convert chromosome to string if necessary
            start_bp = float(row['physical_position_start'])
            end_bp = float(row['physical_position_end'])
            is_full = row['IBD_type'] == 2  # Assuming IBD2 indicates "full"
            len_cm = float(row['genetic_length'])

            unphased_ibd_seg_list.append([id1, id2, chrom, start_bp, end_bp, is_full, len_cm])
        except KeyError as e:
            print(f"Error mapping ID: {e}")
        except ValueError as e:
            print(f"Error converting row data: {e}")

    return unphased_ibd_seg_list

# def create_ibd_network(segments):
#     G = nx.Graph()
#     with tqdm(total=len(segments), desc="Adding edges to the graph") as pbar:
#         for _, row in segments.iterrows():
#             first_sample = row["id1"]
#             second_sample = row["id2"]
#             genetic_length = row["genetic_length"]
#             G.add_edge(first_sample, second_sample, weight=genetic_length)
#             pbar.update(1)
#     return G

# """
# Find overlapping communities using graph-tool

# # Install graph-tool
# wget https://downloads.skewed.de/skewed-keyring/skewed-keyring_1.1_all_$(lsb_release -s -c).deb
# sudo dpkg -i skewed-keyring_1.1_all_$(lsb_release -s -c).deb
# echo "deb [signed-by=/usr/share/keyrings/skewed-keyring.gpg] https://downloads.skewed.de/apt $(lsb_release -s -c) main" | sudo tee /etc/apt/sources.list.d/skewed.list
# sudo apt-get update
# sudo apt install -y python3-graph-tool

# poetry add git+https://git.skewed.de/count0/graph-tool.git
# """

def graph_ibd_segments(segments_ibd, segments_hbd=None, 
                            min_segment_cm=3,
                            min_total_cm=3):
    """
    Find overlapping communities based on IBD segments, accounting for HBD
    
    Parameters:
    segments_ibd: pandas DataFrame with IBD segments
                 Expected columns: [id1, id2, chromosome, physical_position_start, 
                                  physical_position_end, genetic_length]
    segments_hbd: pandas DataFrame with HBD segments (optional)
                 Expected columns: [id1, chromosome, physical_position_start, 
                                  physical_position_end, genetic_length]
    """
    # Verify required columns exist
    required_ibd_cols = ['id1', 'id2', 'chromosome', 'physical_position_start', 
                        'physical_position_end', 'genetic_length']
    if not all(col in segments_ibd.columns for col in required_ibd_cols):
        raise ValueError(f"IBD DataFrame missing required columns. Required: {required_ibd_cols}")

    print("Building graph...")
    # Create graph
    G = nx.Graph()
    
    # Create HBD lookup if provided
    hbd_regions = defaultdict(list)
    if segments_hbd is not None:
        required_hbd_cols = ['id1', 'chromosome', 'physical_position_start', 
                           'physical_position_end', 'genetic_length']
        if not all(col in segments_hbd.columns for col in required_hbd_cols):
            raise ValueError(f"HBD DataFrame missing required columns. Required: {required_hbd_cols}")
            
        for _, row in segments_hbd.iterrows():
            hbd_regions[row['id1']].append({
                'chrom': row['chromosome'],
                'start': row['physical_position_start'],
                'end': row['physical_position_end']
            })
    
    # Process IBD segments and build graph
    pair_segments = defaultdict(list)
    
    print("Processing segments...")
    for _, row in tqdm(segments_ibd.iterrows(), desc="Adding edges to the graph"):
        if row['genetic_length'] >= min_segment_cm:
            pair = tuple(sorted([row['id1'], row['id2']]))
            
            # Check for HBD overlap
            segment_overlaps_hbd = False
            if segments_hbd is not None:
                for id_check in pair:
                    for hbd_seg in hbd_regions[id_check]:
                        if (row['chromosome'] == hbd_seg['chrom'] and 
                            row['physical_position_start'] < hbd_seg['end'] and 
                            row['physical_position_end'] > hbd_seg['start']):
                            segment_overlaps_hbd = True
                            break
                    if segment_overlaps_hbd:
                        break
            
            # Store segment information
            pair_segments[pair].append({
                'chrom': row['chromosome'],
                'start': row['physical_position_start'],
                'end': row['physical_position_end'],
                'cm': row['genetic_length'],
                'overlaps_hbd': segment_overlaps_hbd
            })
    
    # Add edges to graph
    print("Building network...")
    for pair, segments in tqdm(pair_segments.items(), desc="Creating graph edges"):
        # Calculate total IBD, potentially adjusting for HBD overlap
        total_ibd = sum(seg['cm'] for seg in segments 
                       if not seg['overlaps_hbd'])  # Exclude HBD overlapping segments
        
        if total_ibd >= min_total_cm:
            G.add_edge(pair[0], pair[1], 
                      weight=total_ibd,
                      segments=segments)

    print(f"Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    return G

def get_cliques(G, min_size=2):
    """Analyze clique structure as baseline"""
    """
    A maximal clique is a set of nodes that forms a complete subgraph, 
    and it cannot be extended by including any adjacent node without 
    breaking its completeness. A node can belong to multiple maximal 
    cliques if it forms complete subgraphs with different subsets of 
    nodes.
    """
    print("Analyzing clique structure...")
    cliques = list(nx.find_cliques(G))
    clique_sizes = {}  # Dictionary instead of list
    for clique in cliques:
        size = len(clique)
        if size >= min_size:
            clique_sizes[size] = clique_sizes.get(size, 0) + 1
    
    # Print and return clique distribution
    for size in sorted(clique_sizes.keys(), reverse=True):
        print(f"Size: {size}, Quantity: {clique_sizes[size]}")
    return cliques, clique_sizes

def flexible_genetic_clusters_hybrid(G, cliques, threshold, min_connection_size):
    print("Detecting communities with iterative clique merging...")

    groups = [set(clique) for clique in cliques]
    round_counter = 0
    continue_merging = True
    previous_group_counts = []

    while continue_merging:
        round_counter += 1
        current_group_count = len(groups)
        print(f"\nRound {round_counter}: Starting with {current_group_count} groups...")

        merged = False
        new_groups = []
        skip_indices = set()

        # Add progress bar for outer loop
        for i in tqdm(range(len(groups)), desc="Processing groups", unit="group"):
            group_a = groups[i]
            if i in skip_indices:
                continue

            # Add progress bar for inner loop
            for j in range(i + 1, len(groups)):
                if j in skip_indices:
                    continue

                group_b = groups[j]
                matched_b_nodes = set()
                nodes_with_unique_connection = 0

                for node_a in group_a:
                    for node_b in group_b:
                        if (node_b != node_a and 
                            node_b not in matched_b_nodes and 
                            G.has_edge(node_a, node_b) and
                            G.edges[node_a, node_b]['weight'] >= min_connection_size):
                            matched_b_nodes.add(node_b)
                            nodes_with_unique_connection += 1
                            break

                required_connections = int(len(group_a) * threshold)

                if nodes_with_unique_connection >= required_connections:
                    merged_group = group_a | group_b
                    new_groups.append(merged_group)
                    skip_indices.add(i)
                    skip_indices.add(j)
                    merged = True
                    break
            else:
                if i not in skip_indices:
                    new_groups.append(group_a)

        # Add progress bar for remaining groups
        print("\nAdding remaining unmerged groups...")
        for i in tqdm(range(len(groups)), desc="Processing remaining groups", unit="group"):
            if i not in skip_indices:
                new_groups.append(groups[i])

        new_group_count = len(new_groups)
        print(f"\nRound {round_counter}: {new_group_count} groups after merging.")

        if new_group_count in previous_group_counts:
            print(f"Cycle detected. Successfully terminating after round {round_counter} with {new_group_count} groups.")
            continue_merging = False
        else:
            previous_group_counts.append(new_group_count)

        if len(previous_group_counts) > 3:
            previous_group_counts.pop(0)

        print(f"Group counts history: {previous_group_counts}")

        if not merged:
            print(f"No substantial changes detected. Stopping after round {round_counter}.")
            break

        groups = new_groups

    print("\nCreating NodeClustering object...")
    communities_obj = NodeClustering(
        communities=[list(comm) for comm in groups],
        graph=G,
        method_name="iterative_clique_merging"
    )

    return groups, communities_obj

def analyze_communities_vs_cliques(communities, clique_sizes, G, original_cliques):
    """Compare community structure with original clique distribution."""
    print("\nComparing Communities with Clique Structure:")

    print("\nMerging Analysis:")
    contained_cliques = defaultdict(list)
    for i, comm in enumerate(communities):
        for clique in original_cliques:
            if set(clique).issubset(comm):
                contained_cliques[i].append(len(clique))
    
    print("Cliques contained within communities:")
    for comm_idx, contained_sizes in list(contained_cliques.items())[:10]:  # Renamed from clique_sizes
        print(f"Community {comm_idx} (size {len(communities[comm_idx])}):")
        print(f"  Contains {len(contained_sizes)} cliques")
        print(f"  Largest contained clique: {max(contained_sizes)}")
        print(f"  Average clique size: {sum(contained_sizes)/len(contained_sizes):.1f}")

    # Community size distribution
    comm_sizes = {}
    for comm in communities:
        size = len(comm)
        comm_sizes[size] = comm_sizes.get(size, 0) + 1

    print("\nCommunity size distribution:")
    total_communities = sum(comm_sizes.values())
    for size in sorted(comm_sizes.keys(), reverse=True):
        print(f"Size: {size}, Quantity: {comm_sizes[size]} ({(comm_sizes[size]/total_communities)*100:.1f}%)")

    print("\nComparison with original clique distribution:")
    overlap_sizes = set(comm_sizes.keys()) & set(clique_sizes.keys()) 
    if overlap_sizes:
        print("Sizes present in both distributions:")
        for size in sorted(overlap_sizes, reverse=True):
            print(f"Size {size}: Communities={comm_sizes[size]}, Cliques={clique_sizes[size]}")

    print("\nAnalyzing overlap with original cliques:")
    for i, comm in enumerate(communities[:10]):  # Limit to 10 communities for analysis
        max_overlap = 0
        best_clique = None
        for clique in original_cliques:
            overlap = len(set(comm) & set(clique))
            if overlap > max_overlap:
                max_overlap = overlap
                best_clique = clique

        if best_clique:
            print(f"\nCommunity {i+1}:")
            print(f"Size: {len(comm)}")
            # print(f"Best matching clique: {best_clique}")
            print(f"Clique size: {len(best_clique)}")
            print(f"Overlap: {max_overlap} nodes ({(max_overlap / len(best_clique)) * 100:.1f}%)")

    # Analyze sample of communities
    print("\nAnalyzing sample of communities (max 10):")
    sample_size = min(10, len(communities))
    sorted_communities = sorted(communities, key=len, reverse=True)

    for i, comm in enumerate(sorted_communities[:sample_size]):
        subg = G.subgraph(comm)
        density = nx.density(subg)
        edge_weights = [d['weight'] for _, _, d in subg.edges(data=True)]
        avg_weight = sum(edge_weights) / len(edge_weights) if edge_weights else 0

        print(f"\nCommunity {i+1}:")
        print(f"Size: {len(comm)}")
        print(f"Density: {density:.3f}")
        print(f"Average IBD weight: {avg_weight:.1f}")
        print(f"Edge count: {len(edge_weights)}")

        if edge_weights:
            print(f"IBD weight range: {min(edge_weights):.1f} - {max(edge_weights):.1f}")

    # Overall statistics
    print("\nOverall Statistics:")
    print(f"Total communities: {len(communities)}")
    print(f"Average community size: {sum(len(c) for c in communities)/len(communities):.1f}")
    print(f"Size range: {min(len(c) for c in communities)} - {max(len(c) for c in communities)}")

    # Add IBD pattern analysis
    print("\nIBD Patterns in Communities:")
    for i, comm in enumerate(list(communities)[:5]):  # Analyze first 5 communities
        subg = G.subgraph(comm)
        ibd_weights = [d['weight'] for _, _, d in subg.edges(data=True)]
        print(f"\nCommunity {i} IBD Statistics:")
        print(f"Total IBD: {sum(ibd_weights):.1f}")
        print(f"Average IBD: {np.mean(ibd_weights):.1f}")
        print(f"IBD quartiles: {np.percentile(ibd_weights, [25, 50, 75])}")

def graph_pedigree_networkx(pedigree, community_members, numeric_ids, output_filename, 
                           figsize=(12, 8), dpi=300):
    """
    Visualizes a pedigree structure using NetworkX.

    Args:
        pedigree (dict): Pedigree structure {child: {parent: degree}}
        community_members (set/list): Members of the community being analyzed
        numeric_ids (dict): Mapping between user IDs and numeric IDs
        output_filename (str): Path to save the output graph
        figsize (tuple): Figure size
        dpi (int): DPI for output file
    """
    G = nx.DiGraph()

    # Add edges based on the pedigree structure
    for child, parents in pedigree.items():
        for parent, degree in parents.items():
            G.add_edge(parent, child, degree=degree)

    # Define the hierarchical layout
    pos = nx.nx_agraph.graphviz_layout(G, prog="dot")

    # Reverse the numeric_ids dictionary
    id_to_name = {v: k for k, v in numeric_ids.items()}

    # Generate node colors (yellow for community members, skyblue for inferred ancestors)
    node_colors = [
        "yellow" if id_to_name.get(node) in community_members else "skyblue"
        for node in G.nodes()
    ]

    # Create the plot
    plt.figure(figsize=figsize)

    # Draw the graph
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=700)
    nx.draw_networkx_edges(G, pos, edge_color="gray", arrows=True)
    nx.draw_networkx_labels(G, pos, font_size=10, font_color="black")

    # Add degree labels to edges
    edge_labels = {(u, v): f"d:{d['degree']}" for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8)

    # Add title and metadata
    plt.title(f"Pedigree Structure (Community Size: {len(community_members)})", 
              fontsize=16, pad=20)
    
    # Add metadata text
    info_text = f"Community Members: {len(community_members)}\n"
    info_text += f"Total Individuals: {len(G.nodes())}\n"
    info_text += f"Inferred Relations: {len(G.edges())}"
    plt.text(0.02, 0.98, info_text, 
             transform=plt.gca().transAxes,
             verticalalignment='top',
             bbox=dict(facecolor='white', alpha=0.8))

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_filename, dpi=dpi, bbox_inches='tight')
    print(f"Pedigree graph saved to {output_filename}")
    plt.close()

def rgb2hex(rgb_color):
    """Convert RGB tuple to hex color code"""
    return '#{:02x}{:02x}{:02x}'.format(
        int(rgb_color[0] * 255),
        int(rgb_color[1] * 255),
        int(rgb_color[2] * 255)
    )

def plot_cliques(cliques, G, figsize=(30, 30), min_ibd=3):
    """Plot network with nodes grouped by clique boundaries"""
    plt.figure(figsize=figsize)
    
    # Position nodes using force-directed layout
    pos = nx.spring_layout(G, k=1 / np.sqrt(G.number_of_nodes()), iterations=50)
    
    # Draw edges with width based on IBD weight
    edge_weights = [d['weight'] for _, _, d in G.edges(data=True)]
    max_weight = max(edge_weights)
    
    for u, v, d in G.edges(data=True):
        if d['weight'] >= min_ibd:
            width = 0.5 + 3 * (d['weight'] / max_weight)
            alpha = min(1, d['weight'] / 100)
            plt.plot([pos[u][0], pos[v][0]], 
                     [pos[u][1], pos[v][1]], 
                     color='gray',
                     alpha=alpha,
                     linewidth=width)
    
    # # Draw cliques with boundaries
    # colors = plt.cm.rainbow(np.linspace(0, 1, len(cliques)))  # Unique color per clique
    # for i, clique in enumerate(cliques):
    #     clique_pos = np.array([pos[node] for node in clique])
    #     if len(clique_pos) > 2:  # ConvexHull requires at least 3 points
    #         hull = ConvexHull(clique_pos)
    #         for simplex in hull.simplices:
    #             plt.plot(clique_pos[simplex, 0], clique_pos[simplex, 1], color=colors[i], alpha=0.4, linewidth=2)
            # plt.fill(clique_pos[hull.vertices, 0], clique_pos[hull.vertices, 1], color=colors[i], alpha=0.2)
    
    # Draw nodes
    nx.draw_networkx_nodes(
        G,
        pos,
        node_color='lightblue',  # Uniform node color for simplicity
        node_size=100,
        edgecolors='black',
        linewidths=0.5
    )
    
    # Title and axis off
    plt.title(f"IBD Network with {len(cliques)} Cliques (Boundaries)")
    plt.axis('off')
    
    return plt

def plot_merged_communities(merged_communities, G, figsize=(30, 30), min_ibd=3):
    """Plot network with nodes colored by merged community membership"""
    plt.figure(figsize=figsize)
    
    # Create color map for communities
    n_communities = len(merged_communities)
    community_colors = plt.cm.rainbow(np.linspace(0, 1, n_communities))
    
    # Create node color mapping
    node_colors = {}
    for i, comm in enumerate(merged_communities):
        for node in comm:
            if node in node_colors:
                # Node in multiple communities - mark as special
                node_colors[node] = 'yellow'
            else:
                node_colors[node] = community_colors[i]
    
    # Position nodes using force-directed layout
    pos = nx.spring_layout(G, k=1/np.sqrt(G.number_of_nodes()), iterations=50)
    
    # Draw edges with width based on IBD weight
    edge_weights = [d['weight'] for _, _, d in G.edges(data=True)]
    max_weight = max(edge_weights)
    
    # Draw edges first
    for u, v, d in G.edges(data=True):
        if d['weight'] >= min_ibd:
            width = 0.5 + 3 * (d['weight'] / max_weight)
            alpha = min(1, d['weight'] / 100)
            plt.plot([pos[u][0], pos[v][0]], 
                    [pos[u][1], pos[v][1]], 
                    color='gray',
                    alpha=alpha,
                    linewidth=width)
    
    # Draw individual nodes
    for node in G.nodes():
        color = node_colors.get(node, 'lightgray')  # Default color for nodes not in any community
        plt.scatter(pos[node][0], pos[node][1], 
                   c=[color], 
                   s=100,
                   edgecolors='black',
                   linewidth=0.5)
    
    # Add labels for larger communities
    comm_sizes = [len(c) for c in merged_communities]
    mean_size = np.mean(comm_sizes)
    for i, comm in enumerate(merged_communities):
        if len(comm) > mean_size:
            center = np.mean([pos[node] for node in comm], axis=0)
            plt.annotate(f"Community {i}\n({len(comm)})", 
                        center,
                        bbox=dict(facecolor='white', alpha=0.7))
    
    plt.title(f"IBD Network with {len(merged_communities)} Merged Communities")
    plt.axis('off')
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], color='gray', linewidth=2, label='IBD Connection'),
        plt.scatter([0], [0], c='yellow', label='Multi-Community Node'),
        plt.scatter([0], [0], c='lightgray', label='No Community')
    ]
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))
    
    return plt

def plot_ibd_network(merged_communities, G, figsize=(30, 30), min_ibd=3, show_hbd=False):
    """Enhanced network visualization"""
    plt.figure(figsize=figsize)
    
    # Create color map for communities
    n_communities = len(merged_communities)
    community_colors = plt.cm.rainbow(np.linspace(0, 1, n_communities))
    
    # Create node color mapping
    node_colors = {}
    for i, comm in enumerate(merged_communities):
        for node in comm:
            if node in node_colors:
                # Node in multiple communities - mark as special
                node_colors[node] = 'yellow'
            else:
                node_colors[node] = community_colors[i]
    
    # Position nodes using force-directed layout
    pos = nx.spring_layout(G, k=1/np.sqrt(G.number_of_nodes()), iterations=50)
    
    # Draw edges with width based on IBD weight
    edge_weights = [d['weight'] for _, _, d in G.edges(data=True)]
    max_weight = max(edge_weights)
    
    # Draw edges
    for u, v, d in G.edges(data=True):
        if d['weight'] >= min_ibd:
            width = 0.5 + 3 * (d['weight'] / max_weight)
            alpha = min(1, d['weight'] / 100)
            color = 'red' if show_hbd and any(s.get('overlaps_hbd', False) 
                                            for s in d['segments']) else 'gray'
            plt.plot([pos[u][0], pos[v][0]], 
                    [pos[u][1], pos[v][1]], 
                    color=color,
                    alpha=alpha,
                    linewidth=width)
    
    # Draw nodes
    node_size = 100
    nx.draw_networkx_nodes(G, pos,
                          node_color=[node_colors[node] for node in G.nodes()],
                          node_size=node_size)
    
    # Add labels for larger communities
    comm_sizes = [len(c) for c in merged_communities]
    for i, comm in enumerate(merged_communities):
        if len(comm) > np.mean(comm_sizes):
            center = np.mean([pos[node] for node in comm], axis=0)
            plt.annotate(f"C{i}\n({len(comm)})", 
                        center,
                        bbox=dict(facecolor='white', alpha=0.7))
    
    plt.title(f"IBD Network with {len(merged_communities)} Communities")
    plt.axis('off')
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], color='gray', linewidth=2, label='IBD Connection'),
        plt.Line2D([0], [0], color='red', linewidth=2, label='HBD Overlap'),
        plt.scatter([0], [0], c='yellow', label='Multi-Community Node')
    ]
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))
    
    return plt

def plot_community_matrix(merged_communities, G, figsize=(20, 30), show_hbd=False):
    """Enhanced community matrix visualization"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    
    # Create adjacency matrix for communities
    n_communities = len(merged_communities)
    overlap_matrix = np.zeros((n_communities, n_communities))
    ibd_matrix = np.zeros((n_communities, n_communities))
    
    for i, comm1 in enumerate(merged_communities):
        for j, comm2 in enumerate(merged_communities):
            if i != j:
                overlap = len(comm1 & comm2)
                overlap_matrix[i,j] = overlap
                
                # Calculate total IBD between communities
                ibd_sum = 0
                for node1 in comm1:
                    for node2 in comm2:
                        if G.has_edge(node1, node2):
                            ibd_sum += G[node1][node2]['weight']  # Access edge weight this way
                ibd_matrix[i,j] = ibd_sum
    
    # Plot overlap matrix
    im1 = ax1.imshow(overlap_matrix, cmap='viridis')
    ax1.set_title('Community Overlap')
    plt.colorbar(im1, ax=ax1, label='Number of shared nodes')
    
    # Plot IBD matrix
    im2 = ax2.imshow(ibd_matrix, cmap='magma')
    ax2.set_title('Inter-Community IBD')
    plt.colorbar(im2, ax=ax2, label='Total IBD (cM)')
    
    # Add community sizes to axis labels
    comm_sizes = [len(c) for c in merged_communities]
    ax1.set_xticks(range(n_communities))
    ax1.set_yticks(range(n_communities))
    ax1.set_xticklabels([f'C{i}\n({s})' for i, s in enumerate(comm_sizes)], rotation=45)
    ax1.set_yticklabels([f'C{i}\n({s})' for i, s in enumerate(comm_sizes)])
    
    ax2.set_xticks(range(n_communities))
    ax2.set_yticks(range(n_communities))
    ax2.set_xticklabels([f'C{i}\n({s})' for i, s in enumerate(comm_sizes)], rotation=45)
    ax2.set_yticklabels([f'C{i}\n({s})' for i, s in enumerate(comm_sizes)])
    
    plt.tight_layout()
    return plt

def plot_ibd_distribution(G, merged_communities, figsize=(15, 10), bins=50, show_hbd=False):
    """Enhanced IBD distribution visualization"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    
    # Collect IBD values within and between communities
    within_ibd = []
    between_ibd = []
    hbd_overlap_ibd = []
    
    for u, v, d in G.edges(data=True):
        is_within = False
        for comm in merged_communities:
            if u in comm and v in comm:
                within_ibd.append(d['weight'])
                is_within = True
                break
        if not is_within:
            between_ibd.append(d['weight'])
            
        if show_hbd and any(s.get('overlaps_hbd', False) for s in d['segments']):
            hbd_overlap_ibd.append(d['weight'])
    
    # Plot IBD distributions
    ax1.hist([within_ibd, between_ibd], 
             label=['Within Communities', 'Between Communities'],
             bins=bins, alpha=0.6)
    ax1.set_xlabel('IBD (cM)')
    ax1.set_ylabel('Count')
    ax1.set_title('IBD Distribution')
    ax1.legend()
    
    # Add statistical summary
    ax1.text(0.95, 0.95, 
             f"Within: mean={np.mean(within_ibd):.1f}\n"
             f"Between: mean={np.mean(between_ibd):.1f}",
             transform=ax1.transAxes,
             verticalalignment='top',
             horizontalalignment='right',
             bbox=dict(facecolor='white', alpha=0.7))
    
    # Plot community size vs average IBD
    comm_sizes = []
    comm_avg_ibd = []
    for comm in merged_communities:
        subg = G.subgraph(comm)
        if subg.number_of_edges() > 0:
            avg_ibd = np.mean([d['weight'] for _, _, d in subg.edges(data=True)])
            comm_sizes.append(len(comm))
            comm_avg_ibd.append(avg_ibd)
    
    ax2.scatter(comm_sizes, comm_avg_ibd, alpha=0.6)
    ax2.set_xlabel('Community Size')
    ax2.set_ylabel('Average IBD (cM)')
    ax2.set_title('Community Size vs Average IBD')
    
    # Add trend line
    z = np.polyfit(comm_sizes, comm_avg_ibd, 1)
    p = np.poly1d(z)
    ax2.plot(comm_sizes, p(comm_sizes), "r--", alpha=0.8)
    
    plt.tight_layout()
    return plt

def plot_community_overlap(G, communities_obj, figsize=(15, 10)):
    """
    Create visualization of community overlaps using merged communities
    """
    plt.figure(figsize=figsize)
    
    # Calculate node membership count
    node_membership = defaultdict(int)
    for comm in communities_obj.communities:  # using the communities list from NodeClustering
        for node in comm:
            node_membership[node] += 1
    
    # Create node colors based on number of communities
    max_memberships = max(node_membership.values())
    node_colors = [plt.cm.viridis(node_membership[node]/max_memberships)
                  for node in G.nodes()]
    
    # Position nodes using spring layout
    pos = nx.spring_layout(G, k=1/np.sqrt(G.number_of_nodes()), iterations=50)
    
    # Draw network
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, 
                          node_size=100, alpha=0.6)
    
    # Draw edges with weight-based transparency
    edge_weights = [d['weight'] for _, _, d in G.edges(data=True)]
    max_weight = max(edge_weights)
    for u, v, d in G.edges(data=True):
        alpha = min(1, d['weight'] / max_weight)
        plt.plot([pos[u][0], pos[v][0]], 
                [pos[u][1], pos[v][1]], 
                color='gray',
                alpha=alpha * 0.2,  # make edges more transparent
                linewidth=0.5)
    
    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, 
                              norm=plt.Normalize(vmin=1, 
                                               vmax=max_memberships))
    plt.colorbar(sm, label='Number of community memberships')
    
    # Add statistics
    stats_text = f"Nodes in multiple communities: {sum(1 for v in node_membership.values() if v > 1)}\n"
    stats_text += f"Max memberships per node: {max_memberships}\n"
    stats_text += f"Average memberships: {np.mean(list(node_membership.values())):.2f}"
    
    plt.text(0.95, 0.95, stats_text,
             transform=plt.gca().transAxes,
             verticalalignment='top',
             horizontalalignment='right',
             bbox=dict(facecolor='white', alpha=0.7))
    
    plt.title("Community Overlap Network")
    plt.axis('off')
    plt.tight_layout()
    return plt

def plot_merge_history(communities, original_cliques, figsize=(15, 10)):
    """Visualize how original cliques were merged into communities"""
    plt.figure(figsize=figsize)
    
    # Create size distributions
    orig_sizes = [len(c) for c in original_cliques]
    merged_sizes = [len(c) for c in communities]
    
    plt.hist([orig_sizes, merged_sizes], label=['Original Cliques', 'Merged Communities'],
             alpha=0.6, bins=30)
    plt.xlabel('Size')
    plt.ylabel('Count')
    plt.title('Size Distribution: Original Cliques vs Merged Communities')
    plt.legend()
    
    return plt

def save_community_membership(communities, output_filename):
    """
    Save community memberships to JSON file
    Each community is a list of members
    """
    # Convert sets to lists for JSON serialization
    community_list = [list(comm) for comm in communities]
    
    # Create metadata
    community_data = {
        "date_created": datetime.now().isoformat(),
        "total_communities": len(communities),
        "community_sizes": [len(c) for c in communities],
        "communities": community_list
    }
    
    with open(output_filename, 'w') as f:
        json.dump(community_data, f, indent=4)
    
    print(f"Community membership saved to {output_filename}")
    return community_data

def load_community_membership(input_filename):
    """
    Load community memberships from JSON file
    Returns list of sets for compatibility with existing code
    """
    with open(input_filename, 'r') as f:
        community_data = json.load(f)
    
    # Convert lists back to sets
    communities = [set(comm) for comm in community_data["communities"]]
    
    print(f"Loaded {len(communities)} communities")
    print(f"Created on: {community_data['date_created']}")
    print(f"Community size range: {min(community_data['community_sizes'])} - {max(community_data['community_sizes'])}")
    
    return communities

# Function to filter segments based on community membership
def filter_segments_by_community(segments_df, community_members, numeric_ids=None):
    """
    Filter IBD segments to only those within a community
    
    Parameters:
    segments_df: DataFrame with IBD segments
    community_members: Set of member IDs
    numeric_ids: Optional dict to convert between string and numeric IDs
    """
    if numeric_ids:
        # Convert community members to numeric IDs if needed
        numeric_community = {numeric_ids[member] for member in community_members}
        filtered = segments_df[
            (segments_df["id1"].isin(numeric_community)) & 
            (segments_df["id2"].isin(numeric_community))
        ]
    else:
        filtered = segments_df[
            (segments_df["id1"].isin(community_members)) & 
            (segments_df["id2"].isin(community_members))
        ]
    
    return filtered

def prepare_bonsai_input(numeric_ids, sex_dict, age_dict, 
                        segments_ibis, segments_ibd,
                        output_directory, selected_communities=None, prefix="bonsai_format"):
    """
    Prepare input data structures for Bonsai
    
    Parameters:
    numeric_ids: dict mapping sample IDs to numeric IDs
    sex_dict: dict mapping sample IDs to sex
    age_dict: dict mapping sample IDs to age
    segments_ibis: DataFrame with unphased IBD segments
    segments_ibd: DataFrame with phased IBD segments
    output_directory: str, where to save files
    selected_communities: list of sets of member IDs (optional)
    prefix: str, prefix for output files
    
    Returns:
    dict: Contains bioinfo, unphased and phased segment lists, and metadata for each community
    """
    results = {}
    
    if selected_communities:
        print("Processing selected communities...")
        for i, community in enumerate(selected_communities):
            community_prefix = f"{prefix}_{i}"
            
            # Create bioinfo for community
            bio_filename = os.path.join(output_directory, f"{community_prefix}_bioinfo.json")
            community_bioinfo = create_bioinfo(list(community), numeric_ids, sex_dict, age_dict, 
                                             output_filename=bio_filename)
            
            # Filter unphased segments (IBIS)
            community_segments_ibis = segments_ibis[
                (segments_ibis["id1"].isin(community)) & 
                (segments_ibis["id2"].isin(community))
            ]
            
            # Filter phased segments (IBD)
            community_segments_ibd = segments_ibd[
                (segments_ibd["id1"].isin(community)) & 
                (segments_ibd["id2"].isin(community))
            ]
            
            # Create segment lists
            unphased_list = create_unphased_ibd_seg_list(community_segments_ibis, numeric_ids)
            phased_list = create_phased_ibd_seg_list(community_segments_ibd, numeric_ids)
            
            # Save data (optional)
            unphased_filename = os.path.join(output_directory, f"{community_prefix}_unphased_segments.json")
            phased_filename = os.path.join(output_directory, f"{community_prefix}_phased_segments.json")
            
            with open(unphased_filename, 'w') as f:
                json.dump(unphased_list, f, indent=4)
            with open(phased_filename, 'w') as f:
                json.dump(phased_list, f, indent=4)
            
            results[i] = {
                'bioinfo': community_bioinfo,
                'unphased_segment_list': unphased_list,
                'phased_segment_list': phased_list,
                'metadata': {
                    'community_size': len(community),
                    'bioinfo_file': bio_filename,
                    'unphased_segments_file': unphased_filename,
                    'phased_segments_file': phased_filename,
                    'member_ids': list(community),
                    'n_unphased_segments': len(unphased_list),
                    'n_phased_segments': len(phased_list)
                }
            }
            
            print(f"\nPrepared data for community {i}:")
            print(f"Size: {len(community)} members")
            print(f"Unphased segments: {len(unphased_list)}")
            print(f"Phased segments: {len(phased_list)}")
    
    else:
        print("Processing complete dataset...")
        all_samples = list(numeric_ids.keys())
        
        # Create bioinfo for all samples
        bio_filename = os.path.join(output_directory, f"{prefix}_all_bioinfo.json")
        all_bioinfo = create_bioinfo(all_samples, numeric_ids, sex_dict, age_dict, 
                                   output_filename=bio_filename)
        
        # Create segment lists for all samples
        unphased_list = create_unphased_ibd_seg_list(segments_ibis, numeric_ids)
        phased_list = create_phased_ibd_seg_list(segments_ibd, numeric_ids)
        
        # Save data (optional)
        unphased_filename = os.path.join(output_directory, f"{prefix}_all_unphased_segments.json")
        phased_filename = os.path.join(output_directory, f"{prefix}_all_phased_segments.json")
        
        with open(unphased_filename, 'w') as f:
            json.dump(unphased_list, f, indent=4)
        with open(phased_filename, 'w') as f:
            json.dump(phased_list, f, indent=4)
        
        results['full_dataset'] = {
            'bioinfo': all_bioinfo,
            'unphased_segment_list': unphased_list,
            'phased_segment_list': phased_list,
            'metadata': {
                'dataset_size': len(all_samples),
                'bioinfo_file': bio_filename,
                'unphased_segments_file': unphased_filename,
                'phased_segments_file': phased_filename,
                'member_ids': all_samples,
                'n_unphased_segments': len(unphased_list),
                'n_phased_segments': len(phased_list)
            }
        }
        
        print("\nPrepared data for complete dataset:")
        print(f"Size: {len(all_samples)} samples")
        print(f"Unphased segments: {len(unphased_list)}")
        print(f"Phased segments: {len(phased_list)}")

    return results

def print_results_summary(results):
    """Print a summary of the Bonsai input preparation results"""
    print("\nProcessing complete. Results summary:")
    
    if 'full_dataset' in results:
        # Single dataset case
        meta = results['full_dataset']['metadata']
        print("\nFull Dataset Summary:")
        print(f"Total samples: {meta['dataset_size']}")
        print(f"Total unphased segments: {meta['n_unphased_segments']}")
        print(f"Total phased segments: {meta['n_phased_segments']}")
        print("\nOutput files:")
        print(f"BioInfo: {meta['bioinfo_file']}")
        print(f"Unphased segments: {meta['unphased_segments_file']}")
        print(f"Phased segments: {meta['phased_segments_file']}")
    
    else:
        # Multiple communities case
        print(f"\nProcessed {len(results)} communities:")
        for i, data in results.items():
            meta = data['metadata']
            print(f"\nCommunity {i}:")
            print(f"Members: {meta['community_size']}")
            print(f"Unphased segments: {meta['n_unphased_segments']}")
            print(f"Phased segments: {meta['n_phased_segments']}")

def bonsai_post_process(up_dict_log_like_list, i, community_data, numeric_ids):
    print(f"Number of pedigrees: {len(up_dict_log_like_list)}")
    community_members = set(community_data['metadata']['member_ids'])
    
    print(f"\nProcessing pedigrees for community {i}")
    for i, (up_node_dict, log_like) in enumerate(up_dict_log_like_list):
        # print(f"Pedigree {i} structure: {up_node_dict}")
        # print(f"Composite log likelihood: {log_like}")
        
        output_filename = os.path.join(
            results_directory, 
            f"bonsai_pedigree_community_{i}.svg"
        )
        graph_pedigree_networkx(
            up_node_dict, 
            community_members, 
            numeric_ids, 
            output_filename
        )

def main(results_directory):
    """
    Reads IBIS, IBD, and HBD segment files if they exist in the results directory.

    Parameters:
        results_directory (str): Directory containing the segment files.

    Returns:
        tuple: DataFrames for IBIS, IBD, and HBD segments.
    """
    ibis_file = os.path.join(results_directory, "ibis_MergedSamples.seg")
    ibd_file = os.path.join(results_directory, "hap_ibd_MergedSamples.seg")
    hbd_file = os.path.join(results_directory, "hap_hbd_MergedSamples.seg")

    segments_ibis_temp = read_ibis_seg(ibis_file) if os.path.isfile(ibis_file) else pd.DataFrame()
    segments_ibd_temp = read_ibd_hbd_seg(ibd_file) if os.path.isfile(ibd_file) else pd.DataFrame()
    segments_hbd_temp = read_ibd_hbd_seg(hbd_file) if os.path.isfile(hbd_file) else pd.DataFrame()

    segments_ibis_temp = segments_ibis_temp.drop(['marker_count', 'error_count', 'error_density'], axis=1)

    min_segment_size_ibd = 3
    min_segment_size_ibis = 7
    segments_ibis = filter_segments(segments_ibis_temp, min_genetic_length = min_segment_size_ibis)
    print(segments_ibis.head())
    segments_ibd = filter_segments(segments_ibd_temp, min_genetic_length = min_segment_size_ibd)
    print(segments_ibd.head())
    segments_hbd = filter_segments(segments_hbd_temp, min_genetic_length = min_segment_size_ibd)
    print(segments_hbd.head())

    # Ask for target size only if user wants to select communities
    process_all = input("Process all samples? (y/n): ").lower().strip()

    if process_all == "n":
        G = graph_ibd_segments(segments_ibd, segments_hbd=None, min_segment_cm=min_segment_size_ibd, min_total_cm=min_segment_size_ibd)

        print("Running comprehensive community analysis...")
        print()
        # First analyze cliques
        print("Finding the cliques")
        min_nodes = 2
        original_cliques, clique_sizes = get_cliques(G, min_size=min_nodes)
        print()

        # Run hybrid approach
        print("Starting Hybrid Algorithm...")
        threshold = 1 # how many unique intergroup connections
        min_connection_size = 7
        merged_communities, communities_obj = flexible_genetic_clusters_hybrid(G, original_cliques, threshold, min_connection_size)
        print()
        print("Hybrid Algorithm Results:")
        analyze_communities_vs_cliques(merged_communities, clique_sizes, G, original_cliques)

        # # Save Merged Communities
        merged_communities_filename = os.path.join(results_directory, "merged_communities")
        save_community_membership(merged_communities, merged_communities_filename)

        plt0 = plot_cliques(original_cliques, G, figsize=(30, 30), min_ibd=min_segment_size_ibd)
        output_filename0 = os.path.join(results_directory, "plot_cliques.svg")
        plt0.savefig(output_filename0, dpi=300, bbox_inches='tight', format='svg', pad_inches=0.5)
        plt0.close()
        print(f"Pedigree graph saved to {output_filename0}")

        # Basic network plots - these use merged_communities
        plt1 = plot_merged_communities(merged_communities, G, figsize=(30, 30), min_ibd=min_segment_size_ibd)
        output_filename1 = os.path.join(results_directory, "plot_merged_communities_network.svg")
        plt1.savefig(output_filename1, dpi=300, bbox_inches='tight', format='svg', pad_inches=0.5)
        plt1.close()
        print(f"Pedigree graph saved to {output_filename1}")

        # plot_ibd_network(merged_communities, G, figsize=(30, 30), min_ibd=3)

        # # HBD network plot
        # plt2 = plot_ibd_network(merged_communities, G, figsize=(30, 30), min_ibd=3, show_hbd=True)
        # output_filename2 = os.path.join(results_directory, "plot_merged_communities_network_hbd.svg")
        # plt2.savefig(output_filename2, dpi=300, bbox_inches='tight', format='svg', pad_inches=0.5)
        # plt2.close()
        # print(f"Pedigree graph saved to {output_filename2}")

        # # Matrix plot with HBD
        # plt4 = plot_community_matrix(merged_communities, G, figsize=(20, 30), show_hbd=True)
        # output_filename4 = os.path.join(results_directory, "plot_merged_communities_matrix_hbd.svg")
        # plt4.savefig(output_filename4, dpi=300, bbox_inches='tight', format='svg', pad_inches=0.5)
        # plt4.close()
        # print(f"Pedigree graph saved to {output_filename4}")

        # # Distribution plot
        # plt5 = plot_ibd_distribution(G, merged_communities, figsize=(15, 10), bins=50, show_hbd=True)
        # output_filename5 = os.path.join(results_directory, "plot_merged_communities_ibd_distributions.svg")
        # plt5.savefig(output_filename5, dpi=300, bbox_inches='tight', format='svg', pad_inches=0.5)
        # plt5.close()
        # print(f"Pedigree graph saved to {output_filename5}")

        # # Overlap plot - this one needs the communities object
        # plt6 = plot_community_overlap(G, communities_obj, figsize=(15, 10))
        # output_filename6 = os.path.join(results_directory, "plot_merged_communities_overlap.svg")
        # plt6.savefig(output_filename6, dpi=300, bbox_inches='tight', format='svg', pad_inches=0.5)
        # plt6.close()
        # print(f"Pedigree graph saved to {output_filename6}")

        # plt7 = plot_merge_history(merged_communities, original_cliques, figsize=(15, 10))
        # output_filename7 = os.path.join(results_directory, "plot_merge_history.svg")
        # plt7.savefig(output_filename7, dpi=300, bbox_inches='tight', format='svg', pad_inches=0.5)
        # plt7.close()
        # print(f"Pedigree graph saved to {output_filename6}")

    # Main Bonsai preprocessing ################################################
    samples = extract_samples(segments_ibd)
    numeric_ids = generate_numeric_ids(samples)
    print(f"Number of samples: {len(samples)}")

    sex_json_filename = os.path.join(data_directory, 'open_snps_data/demographic_data_sex.json')
    sex_data_filename = os.path.join(data_directory, "open_snps_data/determined_sex.txt")
    if not os.path.exists(sex_json_filename):
        create_sex_json(sex_data_filename, sex_json_filename)
    
    age_data_filename = None
    age_json_filename = os.path.join(data_directory, 'open_snps_data/demographic_data_age.json')
    if not os.path.exists(age_json_filename):
        create_age_json(age_data_filename, age_json_filename, samples)

    sex_dict = load_sex_dict(sex_json_filename)
    age_dict = load_age_dict(age_json_filename)


    if process_all == "n":
        communities = load_community_membership(merged_communities_filename)
        target_size = int(input("Please enter the target community size: "))
        selected_communities = select_communities_by_size(
            communities, 
            target_size=target_size,
            tolerance=2,
            selection=None,
            random_selection=False
        )
    else:
        selected_communities = None

    # Prepare Bonsai input files
    results = prepare_bonsai_input(
        numeric_ids,
        sex_dict,
        age_dict,
        segments_ibis,
        segments_ibd,
        output_directory=results_directory,
        selected_communities=selected_communities
    )

    print_results_summary(results)

    ##### Run Bonsai ##############################
    if selected_communities:
        # Run Bonsai for each selected community
        for i, community_data in results.items():
            print(f"\nRunning Bonsai for community {i}...")
            up_dict_log_like_list = bonsai.build_pedigree(
                bio_info=community_data['bioinfo'],
                unphased_ibd_seg_list=community_data['unphased_segment_list'],
                phased_ibd_seg_list=community_data['phased_segment_list'],
                min_seg_len=3
            )
            bonsai_post_process(up_dict_log_like_list, i, community_data, numeric_ids)
    else:
        # Run Bonsai on full dataset
        print(f"\nRunning Bonsai...")
        up_dict_log_like_list = bonsai.build_pedigree(
            bio_info=results['full_dataset']['bioinfo'],
            unphased_ibd_seg_list=results['full_dataset']['unphased_segment_list'],
            phased_ibd_seg_list=results['full_dataset']['phased_segment_list'],
            min_seg_len=3
        )
        bonsai_post_process(up_dict_log_like_list, "all", results['full_dataset'], numeric_ids)
 

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="")

    args = parser.parse_args()

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

    log_filename = os.path.join(results_directory, "log.txt")
    configure_logging(log_filename, log_file_debug_level="INFO", console_debug_level="INFO")

    # Run the main function with the selected algorithm
    main(results_directory)
