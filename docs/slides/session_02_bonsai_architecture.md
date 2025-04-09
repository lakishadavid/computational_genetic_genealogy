# Session 2: Bonsai v3 Architecture Overview and Core Data Structures

## Session Overview
This session introduces the Bonsai v3 architecture and core data structures, providing a high-level understanding of the system before diving into specific components.

## Key Topics

### 1. Bonsai v3 Architectural Overview
- Design philosophy and goals of Bonsai v3
- End-to-end workflow from raw IBD to pedigrees
- Key improvements over previous versions
- Module organization and dependencies

### 2. The Up-Node Dictionary: Bonsai's Central Data Structure
- Definition and purpose of the up-node dictionary
- Structure and interpretation:
  ```python
  up_node_dict = {
      1000: {1001: 1, 1002: 1},  # Individual 1000 has parents 1001 and 1002
      1003: {1001: 1, 1002: 1},  # Individual 1003 has the same parents (siblings)
      1004: {-1: 1, -2: 1},      # Individual 1004 has inferred parents -1 and -2
      -1: {1005: 1, 1006: 1},    # Inferred individual -1 has parents 1005 and 1006
  }
  ```
- Interpretation of IDs: positive (observed) vs. negative (inferred)
- Representing complex family relationships in the dictionary

### 3. Core Library Components
- Overview of the main modules:
  - `bonsai.py`: Main entry point and orchestration
  - `ibd.py`: IBD data management
  - `likelihoods.py`: Relationship assessment
  - `connections.py`: Pedigree connection logic
  - `pedigrees.py`: Pedigree construction and manipulation
  - Supporting modules (utilities, rendering, etc.)

### 4. Data Flow in Bonsai v3
- Input data requirements and formats
- Transformation of IBD segments into statistics
- Conversion between phased and unphased formats
- Information flow through the system components

### 5. Key Data Structures
- IBD segment formats (phased and unphased)
- Pedigree tracking structures:
  - `idx_to_up_dict_ll_list`: Pedigrees and their likelihoods
  - `id_to_idx`: Individual to pedigree mappings
  - `idx_to_id_set`: Pedigree to individual set mappings
- Relationship representation and connection points

### 6. System Integration Points
- How Bonsai v3 integrates with:
  - IBD detection algorithms
  - Visualization systems
  - External datasets (genetic maps, age distributions)

## Practical Components
- Walkthrough of a simple pedigree in the up-node dictionary format
- Tracing data flow through main function calls
- Examining key configuration parameters and their effects

## Recommended Reading
- Bonsai v3 documentation and README
- Key data structure papers and relevant algorithm design patterns
- Background on probabilistic graphical models for genealogy

## Next Session
In our next meeting, we'll examine the IBD data formats and preprocessing steps that form the foundation of the Bonsai v3 workflow.