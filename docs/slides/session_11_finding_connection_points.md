# Session 11: Finding Connection Points Between Individuals

## Session Overview
This session focuses on the algorithms used in Bonsai v3 to identify optimal connection points between individuals in pedigree structures, a critical step in the pedigree building process.

## Key Topics

### 1. The Connection Point Concept
- Definition of connection points in pedigrees
- Role in pedigree construction workflow
- Types of connection points:
  - Direct connections (parent-child)
  - Common ancestor connections
  - Lateral connections (marriage/partnership)
- Genealogical implications of different connections

### 2. The `get_connecting_points_degs_and_log_likes()` Function
- Implementation details from `connections.py`
- Function signature and parameters:
  ```python
  connection_info = get_connecting_points_degs_and_log_likes(
      up_dict1, up_dict2, id_set1, id_set2, 
      pw_ll_cls, max_rel_deg=3
  )
  ```
- Algorithm walkthrough and complexity analysis
- Return value structure and interpretation

### 3. Finding Potential Connection Points
- For each individual in pedigree:
  - Identifying ancestors as potential connection points
  - Building sets of available connection points
  - Filtering based on biological constraints
  - Prioritizing based on IBD evidence

### 4. Connection Point Filtering Strategies
- `get_up_only_con_pt_set()`: Restricting to common ancestors
- `get_restricted_connection_point_sets()`: Limiting to subtrees with IBD
- `get_max_con_pt_sets()`: Using IBD correlation for point selection
- Tradeoffs in different filtering approaches

### 5. Connection Point Pair Evaluation
- For each connection point pair:
  - Calculating connection likelihoods
  - Determining optimal relationship configuration
  - Ranking connection options by likelihood
  - Pruning unlikely connection candidates

### 6. Mathematical Models for Connection Evaluation
- Likelihood computation for different connection types
- Genetic evidence integration for connection points
- Age-based constraints on connection feasibility
- Joint probability models for connection assessment

### 7. Prioritization and Ranking
- Sorting connection options by likelihood
- Confidence scoring for connection candidates
- Handling multiple equally likely connections
- Breaking ties with additional evidence

### 8. Edge Cases and Special Handling
- Connecting individuals with limited or no IBD sharing
- Handling potential endogamous relationships
- Managing contradictory evidence
- Fallback strategies when optimal connections fail

## Practical Components
- Implementing simplified connection point algorithms
- Evaluating connection points in sample pedigrees
- Visualizing connection options and their likelihoods
- Debugging challenging connection scenarios

## Recommended Reading
- Graph theory literature on connectivity problems
- Papers on genealogical network construction
- Statistical methods for evaluating connection hypotheses
- Algorithm design for graph connection problems

## Next Session
In our next meeting, we'll examine how Bonsai v3 assesses and validates relationships between connection points, ensuring biological and statistical consistency.