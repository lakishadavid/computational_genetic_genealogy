# Session 10: Up-Node Dictionary and Pedigree Representation

## Session Overview
This session provides a deeper exploration of the up-node dictionary, examining its implementation details, advantages, limitations, and advanced operations for pedigree manipulation.

## Key Topics

### 1. Up-Node Dictionary Design Principles
- Key design decisions and rationale
- Historical context and alternative approaches
- Graph theory foundations of the representation
- Directional nature: "up" to ancestors

### 2. Detailed Structure Analysis
- Key-value organization:
  ```python
  # Key: individual ID
  # Value: dictionary mapping parent IDs to weights (typically 1)
  individual_id: {parent_id1: 1, parent_id2: 1}
  ```
- ID system conventions:
  - Positive IDs for observed individuals
  - Negative IDs for inferred individuals
  - Consistent handling across the system
- Empty dictionaries for founder individuals

### 3. Querying Relationship Information
- Finding parents: Direct dictionary lookup
- Finding children: Reverse lookup implementation
- Finding siblings: Shared parent analysis
- Determining relationship paths between individuals
- Calculating genealogical distance

### 4. Advanced Dictionary Operations
- Adding new individuals and relationships
- Removing relationships and pruning
- Merging multiple dictionaries
- Splitting dictionaries at specific points
- Handling relationship weights and probabilities

### 5. Representing Complex Family Structures
- Half-sibling representation
- Multiple marriage/partnership handling
- Endogamous relationships (marriage between relatives)
- Adoption and non-biological relationships
- Generation skipping and unusual structures

### 6. Consistency and Validation
- Sex consistency checking for parents
- Temporal consistency for generations
- Graph property validation
- Detecting and handling contradictions

### 7. Efficient Access Patterns
- Common query optimizations
- Caching strategies for frequent operations
- Memory layout considerations
- Batch operations for performance

### 8. Serialization and External Representation
- Converting to/from JSON representation
- Database storage considerations
- Interface with visualization systems
- Compatibility with other genealogical formats

### 9. Implementation in Bonsai v3
- Integration with the pedigree building pipeline
- Key methods and functions operating on the structure
- Relationship to other data structures in the system
- Evolution and improvements over previous versions

## Practical Components
- Building complex family structures in up-node dictionaries
- Implementing relationship queries and traversals
- Converting between different pedigree representations
- Performance testing with various access patterns

## Recommended Reading
- Graph theory literature on directed acyclic graphs
- Papers on efficient genealogical data structures
- Algorithm design for relationship determination
- Performance analysis of dictionary-based structures

## Next Session
In our next meeting, we'll explore the connection logic that identifies optimal points to join individuals in the pedigree structure.