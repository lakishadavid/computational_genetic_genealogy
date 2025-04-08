# Data Structures and Algorithmic Design in Bonsai v3

## Slide 1: Introduction to Bonsai v3 Data Structures
- Bonsai v3: Modular algorithmic framework for pedigree reconstruction
- Core innovation: Enhanced support for both phased and unphased genetic data
- Efficient data structures enable handling large genealogical datasets
- Building on mathematical foundations with improved implementation

## Slide 2: The Up-Node Dictionary in v3
- Core data structure for representing pedigree relationships
- Format: `{individual_id: {parent1_id: 1, parent2_id: 1}, ...}`
- Genotyped individuals have positive IDs, inferred ancestors have negative IDs

```python
# Example v3 up-node dictionary
up_node_dict = {
    1000: {1001: 1, 1002: 1},  # Individual 1000 has parents 1001 and 1002
    1003: {1001: 1, 1002: 1},  # Sibling of 1000
    1004: {-1: 1, -2: 1},      # Individual 1004 has inferred parents -1 and -2
    -1: {1005: 1, 1006: 1},    # Inferred individual -1 has parents 1005 and 1006
}
```

## Slide 3: IBD Segment Representation in v3
- Dual representation for phased and unphased genetic data:
  - **Unphased format**: `[id1, id2, chromosome, start_bp, end_bp, is_full_ibd, seg_cm]`
  - **Phased format**: `[id1, id2, hap1, hap2, chromosome, start_cm, end_cm, seg_cm]`
- Conversion functions enable seamless switching between formats

```python
def get_unphased_to_phased(unphased_ibd_seg_list):
    """Convert unphased IBD segments to phased IBD segments."""
    # Implementation for format conversion
    # ...
```

## Slide 4: From IBD Detection Output to Bonsai Format
- IBD detection tools (IBIS, hap-IBD, refined-IBD) output segments in tool-specific formats
- IBIS output format: 
  ```
  sample1 sample2 chrom phys_start_pos phys_end_pos IBD_type genetic_start_pos genetic_end_pos genetic_seg_length marker_count error_count error_density
  ```
- Transformation pipeline handled by `ibis_to_ibd_seg_list` in Bonsai:
  1. Parse raw IBIS output into fields
  2. Extract values and convert IDs to integers
  3. Map IBD_type ('IBD1' or 'IBD2') to boolean is_full_ibd (False or True)
  4. Create segments in Bonsai unphased format: `[id1, id2, chromosome, start_bp, end_bp, is_full_ibd, seg_cm]`
  5. Pass to IBDIndex for efficient access

```python
# Actual Bonsai v3 IBIS conversion (simplified)
def ibis_to_ibd_seg_list(raw_ibis_segs):
    """Convert IBIS output to Bonsai format"""
    ibd_seg_list = []
    
    for seg in raw_ibis_segs:
        # Unpack IBIS segment fields
        (id1, id2, chrom, phys_start, phys_end, ibd_type, 
         gen_start, gen_end, gen_seg_len, num_snps, 
         err_ct, err_density) = seg.split()
        
        # Convert types
        id1 = int(id1.split(':')[1])
        id2 = int(id2.split(':')[1])
        phys_start = float(phys_start)
        phys_end = float(phys_end)
        gen_seg_len = float(gen_seg_len)
        
        # Convert IBD type to boolean
        is_full = ibd_type == 'IBD2'
        
        # Create Bonsai segment format
        segment = (id1, id2, chrom, phys_start, phys_end, is_full, gen_seg_len)
        ibd_seg_list.append(segment)
    
    return ibd_seg_list
```

## Slide 5: Segment Organization and Indexing
- Efficient indexing for fast access patterns
- Primary indexing by pairs: `pair_index = {frozenset({id1, id2}): [segment_list]}`
- Multiple indexing dimensions:
  - By individual: `id_index = {id: [segment_list]}`
  - By chromosome: `chrom_index = {chrom: [segment_list]}`
  - By haplotype: `haplotype_index = {(id, hap): [segment_list]}`

```python
class IBDIndex:
    """Efficient indexing structure for IBD segments with v3 compatibility."""
    def __init__(self, min_cm=7.0):
        self.pair_index = {}           # {frozenset({id1, id2}): [segment_list]}
        self.id_index = {}             # {id: [segment_list]}
        self.chrom_index = {}          # {chrom: [segment_list]}
        self.id_to_chrom_index = {}    # {id: {chrom: [segment_list]}}
        self.haplotype_index = {}      # {(id, hap): [segment_list]}
```

## Slide 6: Computing IBD Statistics
- IBD statistics transform raw segments into relationship evidence
- Key function in Bonsai v3: `get_ibd_stats_unphased(unphased_ibd_seg_list)`
- Calculates key metrics for each pair:
  - Total IBD1 (half-identical) segments length in cM
  - Total IBD2 (fully-identical) segments length in cM
  - Number of IBD1 and IBD2 segments
  - Maximum segment length (critical for relationship inference)

```python
# Actual Bonsai v3 implementation
def get_ibd_stats_unphased(unphased_ibd_segs):
    """
    Get ibd_stats from ibd segments data
    
    Args:
        ibd_segs:
            [[id1, id2, chromosome, start, end, is_full_ibd, seg_cm]]
            
    Returns:
        ibd_stats:
            {frozenset({id1,id2}): {'total_half': in cm,
                                   'total_full': in cm,
                                   'num_half': int(total # of half segments),
                                   'num_full': int(total # of full segments),
                                   'max_seg_cm': largest segment in cm}}
    """
    ibd_stats = defaultdict(lambda: {
        'total_half': 0,
        'total_full': 0,
        'num_half': 0,
        'num_full': 0,
        'max_seg_cm': 0})

    for s in unphased_ibd_segs:
        id1, id2, chromosome, start, end, is_full_ibd, seg_cm = s
        key = frozenset([id1, id2])
        ibd_stats[key]['total_half'] += (seg_cm if not is_full_ibd else 0)
        ibd_stats[key]['total_full'] += (seg_cm if is_full_ibd else 0)
        ibd_stats[key]['num_half'] += int(not is_full_ibd)
        ibd_stats[key]['num_full'] += int(is_full_ibd)
        ibd_stats[key]['max_seg_cm'] = max(ibd_stats[key]['max_seg_cm'], seg_cm)

    return ibd_stats
```

## Slide 7: Pairwise Likelihood Calculation (PwLogLike)
- New v3 class for computing relationship likelihoods
- Encapsulates all likelihood computation logic in one place
- Supports conditional/unconditional probability calculations
- Handles background IBD modeling
- Uses IBD statistics to compute likelihoods for different relationships

```python
class PwLogLike:
    """Class for computing pairwise likelihoods between individuals."""
    
    def __init__(self, bio_info, unphased_ibd_seg_list, condition_pair_set=None,
                 mean_bgd_num=MEAN_BGD_NUM, mean_bgd_len=MEAN_BGD_LEN):
        """Initialize with biological info and IBD segments."""
        self.bio_info = bio_info
        self.id_to_info = {info['genotype_id']: info for info in bio_info}
        # Convert segments to IBD statistics
        self.ibd_stat_dict = get_ibd_stats_unphased(unphased_ibd_seg_list)
        self.condition_pair_set = condition_pair_set or set()
        self.mean_bgd_num = mean_bgd_num
        self.mean_bgd_len = mean_bgd_len
```

## Slide 8: Connection Point Architecture
- Modular approach to finding connection points between pedigrees
- Configuration parameters control connection behavior
- Returns ranked list of potential connections with likelihoods

```python
def get_connecting_points_degs_and_log_likes(
    up_dct1, up_dct2, pw_ll_cls, ibd_seg_list,
    condition=False, min_seg_len=MIN_SEG_LEN,
    max_con_pts=MAX_CON_PTS, restrict_connection_points=RESTRICT_CON_PTS,
    connect_up_only=CONNECT_UP_ONLY):
    """Find potential connection points between two pedigrees."""
    # Implementation for finding optimal connections
    # ...
```

## Slide 9: Graph-Theoretical Pedigree Operations
- Pedigree validation using cycle detection
- Temporal consistency checking
- Generation assignment for visualization
- Efficient traversal algorithms

```python
def would_create_cycle(up_node_dict, child_id, proposed_parent_id):
    """Check if adding a parent-child relationship would create a cycle."""
    # Start with the proposed parent
    current_ids = [proposed_parent_id]
    visited = set(current_ids)
    
    # Traverse up the pedigree
    while current_ids:
        # Implementation of cycle detection algorithm
        # ...
```

## Slide 10: Community Detection and Graph Partitioning
- Divides large problems into manageable components
- Uses weighted IBD sharing graph
- Applies Louvain community detection algorithm
- Enables parallel pedigree reconstruction

```python
def partition_with_community_detection(segments):
    """Partition individuals into communities based on IBD sharing."""
    # Create a graph where nodes are individuals and edges represent IBD sharing
    G = nx.Graph()
    
    # Add edges with weights based on IBD sharing
    for seg in segments:
        # Implementation of community detection
        # ...
```

## Slide 11: Extended Metadata Handling
- Biological metadata integration through BioInfo
- Demographic constrained relationship inference
- Extended up-node dictionary for rich relationship metadata
- Support for different relationship types (biological, adoptive, etc.)

```python
class ExtendedUpNodeDict:
    """Enhanced up-node dictionary with relationship metadata."""
    def __init__(self):
        self.up_dict = {}  # Main relationship storage
        self.metadata = {}  # Metadata storage
        
    def add_relationship(self, child_id, parent_id, relationship_type='biological', 
                         confidence=1.0, year=None, source=None):
        # Implementation for storing rich relationship metadata
        # ...
```

## Slide 12: Pedigree Building Algorithms
- Step-by-step modular approach in v3
- Prioritization based on IBD sharing confidence
- Integration of multiple evidence sources
- Connects subpedigrees through optimal connection points

```python
def build_pedigree_step_by_step(unphased_ibd_segs, bio_info):
    """Build a pedigree step by step using the v3 approach."""
    # Convert to phased format for compatibility
    phased_ibd_segs = get_unphased_to_phased(unphased_ibd_segs)
    
    # Create likelihood calculator
    pw_ll_cls = PwLogLike(bio_info, unphased_ibd_segs)
    
    # Implementation of incremental pedigree building
    # ...
```

## Slide 13: Memory-Efficient Computation Strategies
- Sparse matrix representations for large pedigrees
- Strategic caching and memoization
- On-demand computation for relationship coefficients
- Optimized data structures for large-scale inference

```python
class SparseRelationshipCalculator:
    """Memory-efficient relationship calculator using sparse matrices."""
    def __init__(self, up_node_dict, max_individuals=None):
        # Map IDs to matrix indices
        self.id_to_index = {}
        self.index_to_id = {}
        
        # Build sparse parent matrix
        # Using scipy.sparse for memory efficiency
        # ...
```

## Slide 14: Visualization Techniques
- Enhanced visualization for complex pedigrees
- Support for different relationship types
- Generational layout algorithms
- Interactive exploration capabilities

```python
class PedigreeVisualizer:
    """Enhanced visualization tool for pedigrees."""
    def __init__(self, up_node_dict, bio_info=None, extended_relationships=None):
        self.up_node_dict = up_node_dict
        self.bio_info = bio_info or []
        self.id_to_info = {info['genotype_id']: info for info in self.bio_info} if bio_info else {}
        self.extended_relationships = extended_relationships or {}
        
    def visualize(self, figsize=(14, 10), title='Pedigree Structure', 
                 show_labels=True, show_sex=True, edge_style_field='type',
                 node_size_field=None, node_color_field='sex',
                 generation_layout=True):
        # Implementation of flexible pedigree visualization
        # ...
```

## Slide 15: Time and Space Complexity Analysis
- Key operations performance characteristics:
  
  | Operation | Time Complexity | Space Complexity |
  |-----------|-----------------|------------------|
  | Segment access by pair | O(1) | O(S) |
  | Relationship computation | O(d) where d is depth | O(d) |
  | Cycle detection | O(n) where n is nodes | O(n) |
  | Community detection | O(m log n) for m edges, n nodes | O(m + n) |
  | Pedigree merging | O(p) where p is size of smaller pedigree | O(1) |
  
- Optimizations enable handling thousands of individuals and millions of segments

## Slide 16: Validation and Quality Control
- Comprehensive validation framework
- Checks for biological consistency:
  - Temporal consistency (parent older than child)
  - Gender consistency in parent pairs
  - Maximum number of parents constraint
  - Detection of relationship cycles
- Isolation of disconnected components

```python
def validate(pedigree, bio_info, verbose=True):
    """Run comprehensive validation on a pedigree structure."""
    validator = PedigreeValidator(pedigree, bio_info)
    
    # Run all validation checks
    result = validator.validate(verbose=verbose)
    
    # Report validation results
    # ...
```

## Slide 17: Practical Applications and Extensions
- Real-world performance on thousands of individuals
- Extensions for different relationship types:
  - Half-siblings, complex cousin relationships
  - Adoptive relationships
  - Multiple spouse scenarios
- Integration with external demographic data
- Application to large-scale population studies