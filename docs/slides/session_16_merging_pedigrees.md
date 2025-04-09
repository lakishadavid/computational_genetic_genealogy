# Session 16: Merging Pedigrees with Optimal Connection Points

## Session Overview
This session examines the specific techniques used in Bonsai v3 to identify optimal connection points between pedigrees and create biologically and statistically sound merged structures.

## Key Topics

### 1. Connection Point Selection for Pedigree Merging
- Distinction from individual-level connection points
- Criteria for good inter-pedigree connections:
  - Strong IBD evidence between pedigrees
  - Biological compatibility
  - Temporal/age consistency
  - Statistical likelihood
- Implementation in Bonsai v3 algorithms

### 2. Pedigree-Level Connection Functions
- Key functions involved in pedigree connection:
  - `find_connection_points()`: Identifying candidate points
  - `evaluate_connection()`: Assessing connection quality
  - `merge_pedigrees()`: Implementing the actual merge
- Function signatures and interactions
- Return values and error handling

### 3. Cross-Pedigree IBD Analysis
- Computing IBD statistics between members of different pedigrees
- Building the inter-pedigree IBD graph
- Identifying IBD hotspots between pedigrees
- Using IBD patterns to guide connection point selection

### 4. Finding Optimal Points for Each Pedigree Pair
- For each candidate pedigree pair:
  1. Identify individuals with highest cross-pedigree IBD sharing
  2. Generate potential connection points around these individuals
  3. Evaluate multiple connection configurations
  4. Rank connections by composite likelihood
  5. Select optimal connection strategy

### 5. Connection Configuration Generation
- Types of connections considered:
  - Direct ancestral/descendant connections
  - Marriage/partnership connections
  - Common ancestor connections
  - Complex relationship connections
- Constraints on configuration search space
- Prioritization of high-likelihood configurations

### 6. Physical Pedigree Merging Process
- The `connect_pedigrees_through_points()` function:
  - Taking connection points and relationship specification
  - Creating the necessary links between pedigrees
  - Handling the creation of inferred individuals
  - Returning the connected pedigree structure
- Implementation details and edge cases

### 7. Handling Merge Conflicts
- Detecting contradictions during merging
- Resolution strategies for conflicts:
  - Likelihood-based selection
  - Conservatism principle (avoid questionable merges)
  - User intervention points
  - Recording alternatives for later resolution
- Implementation in conflict detection functions

### 8. Updating Pedigree Tracking Structures
- Maintaining consistent tracking dictionaries during merges
- Efficient updates to large tracking structures
- Preserving information for future merge operations
- Memory management considerations

### 9. Merge Validation and Quality Control
- Post-merge validation checks
- Likelihood computation for merged structures
- Confidence scoring for merged pedigrees
- Identifying weak points in merged structures

## Practical Components
- Implementing key pedigree merging functions
- Tracing the connection point selection process
- Visualizing before and after states of merged pedigrees
- Testing with challenging merge scenarios

## Recommended Reading
- Graph theory literature on graph merging
- Papers on genealogical network construction
- Statistical methods for evaluating network merges
- Algorithm design for constrained merging problems

## Next Session
In our next meeting, we'll explore incremental individual addition strategies, an alternative approach to building pedigrees by adding one individual at a time.