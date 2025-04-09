# Session 17: Incremental Individual Addition Strategies

## Session Overview
This session explores the incremental individual addition approach in Bonsai v3, an alternative strategy for building pedigrees by adding one individual at a time to an existing structure.

## Key Topics

### 1. The Incremental Pedigree Building Paradigm
- Contrast with pedigree merging approach
- Advantages of incremental building:
  - Fine-grained control over additions
  - Potentially better handling of complex cases
  - More deterministic behavior
  - Easier to understand and debug
- Use cases in Bonsai v3 workflow

### 2. The `get_next_node()` Function
- Purpose: Selecting the next unplaced individual to add
- Implementation details:
  ```python
  def get_next_node(
      placed_id_set,  # Already placed individuals
      unphased_ibd_seg_list=None,
      phased_ibd_seg_list=None,
  ):
  ```
- Selection criteria:
  - IBD sharing with placed individuals
  - Confidence in relationship determination
  - Strategic considerations for pedigree growth
- Return value and interpretation

### 3. Finding Connection Points for New Individuals
- The `get_new_node_connections()` function:
  ```python
  def get_new_node_connections(
      node,  # New individual to connect
      up_node_dict,  # Existing pedigree
      bio_info,
      unphased_ibd_seg_list=None,
      # ... additional parameters
  ):
  ```
- Process for identifying optimal connection points
- Evaluation of alternative connection strategies
- Return value structure and usage

### 4. Making the Connection
- The `connect_new_node()` function:
  ```python
  def connect_new_node(
      node,  # New individual
      up_node_dict,  # Existing pedigree
      con_pt,  # Connection point
      rel_tuple,  # Relationship specification
  ):
  ```
- Adding the individual to the pedigree
- Creating necessary relationships
- Handling special cases and edge conditions
- Return value and post-connection validation

### 5. Incremental Building Algorithm Flow
- Overall process for incremental pedigree construction:
  1. Start with a small, high-confidence pedigree core
  2. Identify the next best individual to add
  3. Find optimal connection points
  4. Connect the individual
  5. Update the pedigree and tracking structures
  6. Repeat until all individuals are placed or no more connections possible
- Implementation details and control flow

### 6. Strategic Considerations in Individual Selection
- Breadth-first vs. depth-first addition strategies
- Impact of selection order on final pedigree
- Handling difficult-to-place individuals
- Tradeoffs in different selection approaches

### 7. Handling Uncertain Connections
- Confidence thresholds for additions
- Deferring low-confidence connections
- Tentative placements and validation
- Fallback strategies when connections fail

### 8. Performance and Scaling Considerations
- Computational complexity of incremental addition
- Memory efficiency compared to other approaches
- Scaling behavior with pedigree size
- Optimization opportunities

### 9. Integration with the Main Bonsai v3 Workflow
- When to use incremental vs. merging approaches
- Hybrid strategies combining both methods
- Implementation in the overall system
- Configuration parameters controlling the approach

## Practical Components
- Implementing incremental addition algorithms
- Testing with various pedigree scenarios
- Visualizing the incremental building process
- Comparing results with merging-based approaches

## Recommended Reading
- Graph theory literature on incremental graph construction
- Papers on sequential genealogical network building
- Decision theory for sequential addition problems
- Algorithm design for incremental structure building

## Next Session
In our next meeting, we'll explore optimization techniques and performance enhancements employed in Bonsai v3 to handle large and complex pedigree reconstruction challenges.