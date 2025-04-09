# Session 15: The combine_up_dicts() Algorithm

## Session Overview
This session examines the `combine_up_dicts()` algorithm, a core component of Bonsai v3 that merges smaller pedigrees into larger structures through an iterative process.

## Key Topics

### 1. The Pedigree Merging Challenge
- Why pedigree merging is a difficult problem
- Combinatorial complexity of merge operations
- Coherence requirements for merged structures
- Goals of the merging process in Bonsai v3

### 2. The `combine_up_dicts()` Function Signature
- Implementation in the Bonsai v3 codebase:
  ```python
  def combine_up_dicts(
      unphased_ibd_seg_list=None,
      phased_ibd_seg_list=None,
      bio_info=None,
      pw_ll_cls=None,
      # ... additional parameters
  ):
  ```
- Key parameters and their significance
- Return values and their structure
- Integration with the broader workflow

### 3. Main Algorithm Flow
- High-level steps in the pedigree merging process:
  ```
  combine_up_dicts()
  ├── Filter pairwise stats for IDs in the same pedigree
  ├── Find closest pedigrees to merge using IBD sharing
  ├── Merge pedigree tracking structures
  ├── Combine pedigrees physically through connection points
  └── Repeat until all pedigrees are connected or no more connections possible
  ```
- Loop termination conditions
- Progress tracking and reporting

### 4. Finding Closest Pedigrees to Merge
- Identifying which pedigrees share the most IBD:
  ```python
  # Find the two pedigrees that share the most IBD
  idx1, idx2 = find_closest_pedigrees(idx_to_id_set, ibd_seg_list)
  ```
- Cross-pedigree IBD calculation
- Prioritization strategies
- Handling ties and ambiguous cases

### 5. Pedigree Tracking Data Structure Updates
- Manipulating key tracking dictionaries during merges:
  - `idx_to_up_dict_ll_list`: Pedigrees with likelihoods
  - `id_to_idx`: Individual to pedigree mapping
  - `idx_to_id_set`: Pedigree to individual set mapping
- Ensuring consistency during updates
- Handling merge conflicts

### 6. The Physical Merging Process
- Identifying optimal connection points between pedigrees
- Evaluating alternative connection configurations
- Creating the actual connections in the up-node dictionary
- Computing likelihood of the combined structure

### 7. Iterative Merging Strategy
- Bottom-up vs. greedy merging approaches
- Benefits of the iterative strategy
- When to stop the merging process
- Handling remaining unconnected pedigrees

### 8. Performance Considerations
- Computational complexity analysis
- Memory requirements during merging
- Optimization techniques employed
- Scaling behavior with pedigree size

### 9. Validation and Quality Control
- Consistency checking during and after merges
- Likelihood thresholds for accepting merges
- Detecting problematic merge operations
- Recovery strategies for failed merges

## Practical Components
- Implementing a simplified version of `combine_up_dicts()`
- Tracing the merging process on sample data
- Visualizing pedigree merging steps
- Debugging common issues in pedigree merging

## Recommended Reading
- Graph merging algorithms
- Optimization literature on constrained merging problems
- Papers on genealogical network construction
- Algorithm design for hierarchical structure building

## Next Session
In our next meeting, we'll explore how Bonsai v3 identifies and utilizes optimal connection points for merging pedigrees, ensuring biologically and statistically sound reconstructions.