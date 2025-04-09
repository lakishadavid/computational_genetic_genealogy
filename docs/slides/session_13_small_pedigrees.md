# Session 13: Connecting Individuals into Small Structures

## Session Overview
This session examines how Bonsai v3 connects individuals into small pedigree structures, focusing on the algorithms that identify and link closely related individuals as the foundation for larger pedigree reconstruction.

## Key Topics

### 1. The Small Pedigree Construction Workflow
- Bottom-up approach in Bonsai v3:
  1. Start with individual-level pedigrees
  2. Identify closely related pairs
  3. Connect them with optimal relationship structures
  4. Build small, highly confident pedigrees
  5. Use these as building blocks for larger structures
- Rationale and advantages of this approach

### 2. Initializing the Pedigree Building Process
- The `initialize_input_dicts()` function:
  - Creating initial pedigree structures
  - Setting up tracking dictionaries
  - Preparing for iterative construction
- Data structures created:
  - `idx_to_up_dict_ll_list`: Pedigrees with likelihoods
  - `id_to_idx`: Individual to pedigree mapping
  - `idx_to_id_set`: Pedigree to individual set mapping

### 3. Finding Closest Individuals: The Starting Point
- Implementation in Bonsai v3:
  ```python
  # From combine_up_dicts() in connections.py
  # Get the closest pair of IDs that are not already in the same pedigree
  c1, c2 = get_closest_pair(ibd_stats)
  ```
- Prioritization strategies based on IBD sharing
- Handling ties and ambiguous relationships
- Sequential vs. parallel processing approaches

### 4. Connecting Close Relatives
- Direct connection creation:
  - Parent-child connections
  - Sibling connections
  - Grandparent connections
- Using the `connect_pedigrees_through_points()` function
- Handling of sex and age constraints
- Creating minimal valid structures

### 5. Special Relationship Structures
- Nuclear family formation
- Extended family units
- Half-sibling groups
- Multiple generation structures
- Implementation of specific connection patterns

### 6. Small Pedigree Validation
- Consistency checking for small structures
- Likelihood thresholds for acceptance
- Detecting anomalies and contradictions
- Reporting confidence levels

### 7. Optimizing Small Pedigree Configurations
- Testing alternative relationship configurations
- Scoring and ranking different structures
- Selecting optimal small pedigrees
- Preparing for later merging operations

### 8. Implementation in Bonsai v3 Codebase
- Key functions involved in small pedigree building
- Algorithm complexity and performance considerations
- Memory management for numerous small structures
- Parallelization potential and implementation

## Practical Components
- Building small pedigrees from sample IBD data
- Implementing core connection algorithms
- Testing with various relationship patterns
- Visualizing and validating small structures

## Recommended Reading
- Papers on family structure reconstruction
- Algorithm design for small graph construction
- Statistical methods for relationship grouping
- Computational efficiency in pedigree building

## Next Session
In our next meeting, we'll focus on optimizing small pedigree configurations to ensure they provide the most accurate foundation for larger pedigree construction.