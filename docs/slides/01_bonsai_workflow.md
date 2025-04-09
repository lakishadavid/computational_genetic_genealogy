# Bonsai v3 Workflow: From IBD Segments to Pedigrees

This document outlines the Bonsai v3 workflow, following the implementation path from raw IBD segments to reconstructed pedigrees.

## Workflow Overview

The complete Bonsai v3 workflow follows these steps:

1. Process raw IBD segments from detectors like IBIS
2. Extract IBD statistics (counts, lengths) for all individual pairs
3. Compute pairwise relationship likelihoods using genetic and age data
4. Build small, highly confident pedigrees for closely related individuals
5. Iteratively combine smaller pedigrees into larger ones
6. Add individuals incrementally when building large pedigrees
7. Return the final pedigree with log-likelihood scores

## 1. Main Entry Point: `build_pedigree()`

The primary function orchestrating the Bonsai v3 process is `build_pedigree()` in `bonsai.py`. It takes these key inputs:

- `bio_info`: Biological metadata (age, sex, coverage)
- `unphased_ibd_seg_list`: Unphased IBD segments (from detectors like IBIS)
- `phased_ibd_seg_list`: Phased IBD segments (optional)

## 2. IBD Data Management and Processing

### 2.1 IBD Data Formats

Bonsai v3 works with two IBD segment formats:

**Unphased Format**:
```
[id1, id2, chromosome, start_bp, end_bp, is_full_ibd, seg_cm]
```

**Phased Format**:
```
[id1, id2, hap1, hap2, chromosome, start_cm, end_cm, seg_cm]
```

### 2.2 IBD Conversion Functions

- `get_phased_to_unphased()`: Converts phased segments to unphased format
- `get_unphased_to_phased()`: Creates pseudo-phased segments from unphased data

### 2.3 IBD Statistics Extraction

`get_ibd_stats_unphased()` extracts key statistics:
- `total_half`: Total IBD1 sharing (cM)
- `total_full`: Total IBD2 sharing (cM)
- `num_half`: Number of IBD1 segments
- `num_full`: Number of IBD2 segments
- `max_seg_cm`: Length of largest segment

### 2.4 The Up-Node Dictionary Structure

The central data structure in Bonsai v3 is the up-node dictionary:

```python
up_node_dict = {
    1000: {1001: 1, 1002: 1},  # Individual 1000 has parents 1001 and 1002
    1003: {1001: 1, 1002: 1},  # Individual 1003 has the same parents (siblings)
    1004: {-1: 1, -2: 1},      # Individual 1004 has inferred parents -1 and -2
    -1: {1005: 1, 1006: 1},    # Inferred individual -1 has parents 1005 and 1006
    # ... additional relationships
}
```

- Positive IDs represent observed individuals
- Negative IDs represent inferred (latent) ancestors
- Empty dictionaries represent individuals with no recorded parents

## 3. Pairwise Relatedness Analysis: The `PwLogLike` Class

The `PwLogLike` class (in `likelihoods.py`) computes relationship likelihoods between individuals.

### 3.1 Initialization

```python
pw_ll_cls = PwLogLike(
    bio_info=bio_info,
    unphased_ibd_seg_list=unphased_ibd_seg_list,
    condition_pair_set=condition_pair_set,
    mean_bgd_num=mean_bgd_num,
    mean_bgd_len=mean_bgd_len,
)
```

### 3.2 Key Properties

- `ibd_stat_dict`: IBD statistics for all pairs
- `sex_dict`, `age_dict`, `cov_dict`: Metadata dictionaries
- `cond_dict`, `uncond_dict`: Pre-calculated IBD relationship moment distributions

### 3.3 Likelihood Methods

- `get_pw_gen_ll()`: Calculates genetic component of likelihood
- `get_pw_age_ll()`: Calculates age-based component of likelihood
- `get_pw_ll()`: Combines genetic and age components for total likelihood

### 3.4 Statistical IBD Models

The implementation uses sophisticated statistical models:

- `get_lam_a_m()`: Computes expected segment lengths by meiotic distance
- `get_eta()`: Calculates expected segment counts by relationship
- `get_log_seg_pdf()`: Computes likelihoods from segment data
- Coverage adjustments for segment detection and length

### 3.5 Age-Based Modeling

Bonsai v3 includes sophisticated age-based relationship modeling:

- `get_age_mean_std_for_rel_tuple()`: Returns expected age difference and std dev for relationships
- `get_age_log_like()`: Computes likelihood based on age differences
- Calibrated using empirical data for different relationship types

## 4. Building Small Pedigrees

### 4.1 Pedigree Tracking Structures

The `initialize_input_dicts()` function creates three key data structures:

1. `idx_to_up_dict_ll_list`: Maps pedigree indices to lists of (pedigree, log-likelihood) pairs
2. `id_to_idx`: Maps individual IDs to their pedigree indices
3. `idx_to_id_set`: Maps pedigree indices to sets of contained individual IDs

### 4.2 Finding Closest Individuals

Bonsai begins by identifying individuals who share the most IBD:

```python
# From combine_up_dicts() in connections.py
# Get the closest pair of IDs that are not already in the same pedigree
c1, c2 = get_closest_pair(ibd_stats)
```

### 4.3 Finding Connection Points

`get_connecting_points_degs_and_log_likes()` in `connections.py` finds optimal ways to connect individuals:

1. Gets potential connection points for each individual
2. Filters connection points based on various criteria
3. For each connection point pair:
   - Calculates connection likelihoods 
   - Ranks connection points by likelihood
4. Returns ordered list of connection points and likelihoods

### 4.4 Advanced Filtering Strategies

- `get_up_only_con_pt_set()`: Restricts connections to common ancestors
- `get_restricted_connection_point_sets()`: Limits connection points to subtrees with IBD sharing
- `get_max_con_pt_sets()`: Uses IBD correlation to identify most likely connection points

### 4.5 Connecting Small Pedigrees

`connect_pedigrees_through_points()` function handles:

1. Taking connection points and relationship specification
2. Handling the actual creation of connections between individuals
3. Creating latent (inferred) ancestors as needed
4. Returning the connected small pedigree

## 5. Building Large Pedigrees: `combine_up_dicts()`

The core algorithm iteratively builds larger pedigrees by connecting smaller ones.

### 5.1 Main Flow

```
combine_up_dicts()
├── Filter pairwise stats for IDs in the same pedigree
├── Find closest pedigrees to merge using IBD sharing
├── Merge pedigree tracking structures
├── Combine pedigrees physically through connection points
└── Repeat until all pedigrees are connected or no more connections possible
```

### 5.2 Finding Closest Pedigrees

The algorithm identifies which pedigrees share the most IBD with each other:

```python
# Find the two pedigrees that share the most IBD
idx1, idx2 = find_closest_pedigrees(idx_to_id_set, ibd_seg_list)
```

### 5.3 Merging Pedigrees

For each pair of candidate pedigrees, Bonsai:

1. Identifies optimal connection points
2. Connects them using specific relationship configurations
3. Evaluates likelihood of the combined pedigree
4. Keeps the most likely configurations

## 6. Adding Individuals Incrementally

For incremental pedigree building, Bonsai provides an alternative flow:

### 6.1 Finding Next Individual

`get_next_node()` selects the unplaced individual who shares the most IBD with any placed individual:

```python
def get_next_node(
    placed_id_set,  # Already placed individuals
    unphased_ibd_seg_list=None,
    phased_ibd_seg_list=None,
):
```

### 6.2 Finding Connection Points

`get_new_node_connections()` finds optimal ways to connect a new individual to the existing pedigree:

```python
def get_new_node_connections(
    node,  # New individual to connect
    up_node_dict,  # Existing pedigree
    bio_info,
    unphased_ibd_seg_list=None,
    # ... additional parameters
):
```

### 6.3 Making the Connection

`connect_new_node()` adds the individual to the pedigree:

```python
def connect_new_node(
    node,  # New individual
    up_node_dict,  # Existing pedigree
    con_pt,  # Connection point
    rel_tuple,  # Relationship specification
):
```

## 7. Optimization and Performance Enhancements

Bonsai v3 includes several optimizations:

- Caching for repeated likelihood calculations
- Sparse representation of pedigrees for memory efficiency
- Community detection for breaking large problems into subproblems
- Priority-based processing of relationships by IBD amount
- Cycle detection to prevent invalid pedigree structures

## 8. Complete Pedigree Construction Example

A complete workflow example from IBD detector output to final pedigree:

```
1. Parse IBD data from IBIS or other detector
   • Load unphased IBD segments
   • Convert to phased format if needed (get_unphased_to_phased)
   • Extract IBD statistics (get_ibd_stats_unphased)

2. Initialize relationship likelihood computation
   • Create PwLogLike instance with IBD data and bio info
   • Set up background IBD model parameters

3. Initialize pedigree data structures
   • Create empty pedigrees for each individual (initialize_input_dicts)
   • Set up tracking dictionaries for individuals and pedigrees

4. Build pedigrees iteratively
   • Find closest pairs of individuals or pedigrees using IBD
   • Identify optimal connection points for merging
   • Connect using most likely relationship configurations
   • Repeat until all connected or no more valid connections

5. Evaluate final pedigree
   • Calculate composite log-likelihood
   • Remove dangling founders if needed
   • Return the final pedigree structure
```