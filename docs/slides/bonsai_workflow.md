# Bonsai v3 Workflow: From IBD Segments to Pedigrees

This document provides a comprehensive workflow of the actual Bonsai v3 implementation, tracing the path from raw IBD segments to reconstructed pedigrees.

## 1. Main Entry Point: `bonsai.build_pedigree()`

The primary function that orchestrates the Bonsai v3 pedigree reconstruction process is `build_pedigree()` in `bonsai.py`. It takes the following key inputs:

- `bio_info`: Biological metadata for individuals (age, sex, etc.)
- `unphased_ibd_seg_list`: Unphased IBD segments from detectors like IBIS
- `phased_ibd_seg_list` (optional): Phased IBD segments if available

### Key Steps:

```
build_pedigree()
├── Initialize IBD data (convert between phased/unphased as needed)
├── Create PwLogLike instance for likelihood calculations
├── Initialize pedigree tracking data structures
└── Call combine_up_dicts() for the main pedigree building algorithm
```

## 2. Data Structures and Preprocessing

### 2.1 IBD Segment Formats

Bonsai v3 works with two IBD segment formats:

**Unphased Format**:
```
[id1, id2, chromosome, start_bp, end_bp, is_full_ibd, seg_cm]
```

**Phased Format**:
```
[id1, id2, hap1, hap2, chromosome, start_cm, end_cm, seg_cm]
```

### 2.2 IBD Data Processing Functions

- `get_phased_to_unphased()`: Converts phased segments to unphased format
- `get_unphased_to_phased()`: Creates pseudo-phased segments from unphased data
- `get_ibd_stats_unphased()`: Extracts statistics for each pair of individuals:
  - `total_half`: Total IBD1 sharing in cM
  - `total_full`: Total IBD2 sharing in cM
  - `num_half`: Number of IBD1 segments
  - `num_full`: Number of IBD2 segments
  - `max_seg_cm`: Length of largest segment

### 2.3 Pedigree Tracking Structures

The `initialize_input_dicts()` function creates three key data structures:

1. `idx_to_up_dict_ll_list`: Maps pedigree indices to lists of (pedigree, log-likelihood) pairs
2. `id_to_idx`: Maps individual IDs to their pedigree indices
3. `idx_to_id_set`: Maps pedigree indices to sets of contained individual IDs

## 3. Likelihood Calculation: The `PwLogLike` Class

The `PwLogLike` class from `likelihoods.py` is central to Bonsai's operation, computing relationship likelihoods between individuals.

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

### 3.4 Statistical Model

Unlike the simplified teaching version in the notebook, the real implementation:

1. Uses pre-calculated IBD moment distributions for different relationship types
2. Incorporates sophisticated background IBD modeling
3. Accounts for coverage effects on segment detection
4. Includes both IBD1 and IBD2 segments in likelihood calculations
5. Uses `get_log_seg_pdf()` to compute likelihoods from segment data

## 4. Pedigree Building: `combine_up_dicts()`

The core algorithm that iteratively builds pedigrees by connecting smaller pedigrees.

### 4.1 Main Flow

```
combine_up_dicts()
├── Filter pairwise stats for IDs in the same pedigree
├── Find closest pedigrees to merge using IBD sharing
├── Merge pedigree tracking structures
├── Combine pedigrees physically through connection points
└── Repeat until all pedigrees are connected or no more connections possible
```

### 4.2 Finding Connection Points

The `get_connecting_points_degs_and_log_likes()` function in `connections.py` finds optimal ways to connect pedigrees:

1. Gets potential connection points in each pedigree
2. Filters connection points based on various criteria
3. For each connection point pair:
   - Calculates connection likelihoods using `get_connection_degs_and_log_likes()`
   - Ranks connection points by likelihood
4. Returns ordered list of connection points and likelihoods

### 4.3 Advanced Filtering Strategies

Unlike the teaching version, the real implementation employs several sophisticated filtering strategies:

- `get_up_only_con_pt_set()`: Restricts connections to common ancestors
- `get_restricted_connection_point_sets()`: Limits connection points to subtrees with IBD sharing
- `get_max_con_pt_sets()`: Uses IBD correlation to identify most likely connection points

### 4.4 Connecting Pedigrees

The `connect_pedigrees_through_points()` function:

1. Takes connection points and relationship specification
2. Handles the actual creation of connections between pedigrees
3. Creates latent (inferred) ancestors as needed
4. Returns the connected pedigree

## 5. Adding Individuals Incrementally

For incremental pedigree building, Bonsai uses a different workflow:

### 5.1 Finding Next Individual

The `get_next_node()` function determines which unplaced individual to add next:

```python
def get_next_node(
    placed_id_set,  # Already placed individuals
    unphased_ibd_seg_list=None,
    phased_ibd_seg_list=None,
):
```

It selects the unplaced individual sharing the most IBD with any placed individual.

### 5.2 Finding Connection Points

`get_new_node_connections()` finds optimal ways to connect a new individual:

```python
def get_new_node_connections(
    node,  # New individual to connect
    up_node_dict,  # Existing pedigree
    bio_info,
    unphased_ibd_seg_list=None,
    # ... additional parameters
):
```

### 5.3 Making the Connection

Finally, `connect_new_node()` adds the individual to the pedigree:

```python
def connect_new_node(
    node,  # New individual
    up_node_dict,  # Existing pedigree
    con_pt,  # Connection point
    rel_tuple,  # Relationship specification
):
```

## 6. Mathematical Models

Unlike the teaching version, the real Bonsai v3 uses sophisticated statistical models:

### 6.1 IBD Length Distributions

- Models IBD segments using a two-component mixture model:
  - Foreground (relationship-based) segments
  - Background (population-based) segments
- Uses functions like `get_L_log_pdf_approx()` and `get_n_L_log_pdf_approx()` for calculation

### 6.2 Segment Length and Count Models

- Uses `get_lam_a_m()` to compute expected segment lengths by meiotic distance
- Uses `get_eta()` to calculate expected segment counts by relationship
- Adjusts for coverage effects on segment detection and length

### 6.3 Age-Based Modeling

- `get_age_mean_std_for_rel_tuple()`: Returns expected age difference and std dev for relationships
- `get_age_log_like()`: Computes likelihood based on age differences
- Calibrated using empirical data for different relationship types

## 7. Up-Node Dictionary Structure

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

## 8. Optimization and Performance Enhancements

The real Bonsai v3 includes several optimizations:

- Caching for repeated likelihood calculations
- Sparse representation of pedigrees for memory efficiency
- Community detection for breaking large problems into subproblems
- Priority-based processing of relationships by IBD amount
- Cycle detection to prevent invalid pedigree structures

## 9. Full Pedigree Construction Example

A complete workflow example:

```
1. Parse IBD data from IBIS or other detector
2. Convert to Bonsai format using ibd.py functions
3. Initialize pedigree structures with initialize_input_dicts()
4. Create PwLogLike instance for likelihood calculations
5. Find closest pairs of individuals using IBD statistics
6. Build initial small pedigrees for these closely related pairs
7. Iteratively combine pedigrees through optimal connection points
8. Return the final pedigree with log-likelihood score
```

## 10. Key Differences from Teaching Implementation

- Uses pre-computed moment-based statistical distributions rather than simple normal distributions
- Employs sophisticated filtering to prioritize the most promising connection points
- Includes advanced handling of background IBD and coverage effects
- Integrates both genetic and age-based likelihood components
- Handles both IBD1 and IBD2 segments, with proper modeling of their distributions
- Implements caching and optimization strategies for performance