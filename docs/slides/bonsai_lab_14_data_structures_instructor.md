# Data Structures and Algorithmic Design in Bonsai v3 - Instructor Guide

## Introduction

This lecture explores the data structures and algorithmic design in Bonsai v3, focusing on the conceptual foundations of how we computationally represent and manipulate genealogical relationships. While the student lab provides hands-on implementation experience, this lecture aims to connect those technical implementations to broader theoretical concepts in computational genealogy.

The core questions we're addressing:
1. How do we represent complex family relationships in a way that's both computationally efficient and biologically meaningful?
2. What data structures enable us to bridge the gap between abstract genetic patterns and concrete family relationships?
3. How do algorithmic design choices reflect underlying assumptions about kinship and relationship?

## The Representation Problem in Computational Genealogy

When we talk about "data structures" in Bonsai, we're really discussing how we model human relationships computationally. This is more than a technical choice—it's a conceptual framework that determines what kinds of relationships we can represent, how efficiently we can work with them, and what cultural assumptions we embed in our code.

The fundamental challenge: translating the fluid, multidimensional nature of human kinship into discrete computational structures.

Traditional family trees are hierarchical structures optimized for a single perspective—tracing ancestry from one individual upward. But real human kinship networks are multidirectional webs. Bonsai v3's data structures represent a particular solution to this representation challenge.

## The Up-Node Dictionary: From Tree to Forest

The central data structure in Bonsai—the "up-node dictionary"—represents a significant conceptual innovation in representing family relationships. 

```python
# Example of an up-node dictionary in Bonsai v3
up_node_dict = {
    1000: {1001: 1, 1002: 1},  # Individual 1000 has parents 1001 and 1002
    1003: {1001: 1, 1002: 1},  # Sibling relationship through shared parents
    1004: {-1: 1, -2: 1},      # Individual with inferred/latent parents
    -1: {1005: 1, 1006: 1},    # An inferred ancestor with known parents
}
```

This structure embodies several key insights about human kinship:

1. **Multidirectional Perspective**: Unlike traditional trees, it allows traversal in multiple directions (up to ancestors, down to descendants, laterally to relatives)
2. **Network Rather Than Hierarchy**: It represents family structures as interconnected webs rather than strict trees
3. **Focus on Immediate Connections**: It uses direct parent-child relationships as building blocks, from which all other relationships emerge
4. **Latent Ancestor Representation**: It allows for missing individuals to be inferred (with negative IDs), acknowledging the incomplete nature of most genealogical data

In Bonsai v3, we've extended this structure to support additional metadata about relationships, enabling representation of different relationship types (biological, adoptive), confidence scores, and temporal information. This moves us closer to representing the social complexity of kinship, not just its genetic components.

## Beyond Trees: Graph Theory and Kinship Systems

The graph-theoretical foundation of Bonsai connects to a rich tradition of representing kinship through network structures. By modeling pedigrees as directed acyclic graphs (DAGs), we gain powerful mathematical tools while making specific assumptions:

- **Directionality** encodes the asymmetry of genetic inheritance and generational flow
- **Acyclicity** enforces the biological reality that no one can be their own ancestor
- **Biparental structure** reflects sexual reproduction but also encodes a particular cultural model of family

These properties create a flexible framework but also embed cultural assumptions that shape how relationships can be conceptualized. Some kinship systems (like those with complex marriage patterns or non-genealogical kinship) may be challenging to represent in this framework.

In Bonsai v3, we provide validation tools that enforce these constraints while allowing for different relationship types:

```python
def would_create_cycle(up_node_dict, child_id, proposed_parent_id):
    """Check if adding this parent would create a cycle in the pedigree."""
    # Implementation details...
```

This cycle detection is more than a technical check—it's enforcing a linear conception of time and ancestry that is fundamental to our mathematical model.

## Phased vs. Unphased: Representing Genetic Material

Bonsai v3 introduces a key conceptual advance: dual representation of genetic data to support both phased and unphased IBD segments.

**Unphased format**: `[id1, id2, chromosome, start_bp, end_bp, is_full_ibd, seg_cm]`
**Phased format**: `[id1, id2, hap1, hap2, chromosome, start_cm, end_cm, seg_cm]`

This distinction matters because it represents different levels of certainty about genetic inheritance. Phased data tells us not just *that* two people share DNA, but *which* parental chromosome it came from—allowing more precise relationship inference.

The ability to convert between these formats and work with both efficiently is critical because different detection algorithms produce different data types. This flexibility lets Bonsai bridge between various upstream tools and create a unified analytical framework.

## From Local to Global: Building Pedigrees from Fragments

A central challenge in pedigree reconstruction is moving from local relationship evidence (pairwise IBD sharing) to global structure (complete pedigrees). This is analogous to assembling a puzzle where:
- The pieces are relationships between pairs of individuals
- The picture is the complete family structure
- Some pieces are missing, and others might not belong in the picture at all

In Bonsai v3, we approach this challenge through modular algorithms for connection point finding:

```python
def get_connecting_points_degs_and_log_likes(up_dct1, up_dct2, ...):
    """Find optimal ways to connect two separate pedigree fragments."""
    # Implementation details...
```

This function does more than just connect pedigrees—it evaluates multiple possible relationships between fragments and ranks them by likelihood. This reflects a key insight: pedigree reconstruction is inherently probabilistic and should consider multiple hypotheses.

The connection process raises fascinating questions about identity and relationship across sub-pedigrees:
- When are two separate family trees actually part of the same larger family?
- How do we determine the most likely points of connection?
- How do we balance genetic evidence against demographic plausibility?

## The Statistical Backbone: PwLogLike

The PwLogLike class is the statistical heart of Bonsai v3, encapsulating how we translate genetic observations into relationship probabilities.

```python
class PwLogLike:
    """Class for computing pairwise likelihoods between individuals."""
    
    def get_log_like(self, id1, id2, relationship_tuple, condition=False):
        """Calculate log likelihood of a specific relationship."""
        # Implementation details...
```

This class implements a crucial conceptual framework:
1. Different relationship types create characteristic patterns of genetic sharing
2. These patterns can be modeled mathematically using statistical distributions
3. By comparing observed patterns to expected ones, we can infer likely relationships

The PwLogLike class abstracts away the mathematical complexity, providing a clean interface for relationship likelihood calculation. This encapsulation is more than a coding practice—it represents a clear separation between the statistical model and the algorithmic process of pedigree building.

## Memory and Efficiency: Computational Considerations

When dealing with large-scale genetic datasets, computational efficiency isn't just a practical concern—it shapes what analyses are possible and which relationships we can detect.

Bonsai v3 introduces several advanced data structures optimized for different access patterns:

```python
class IBDIndex:
    """Efficient indexing structure for IBD segments."""
    def __init__(self):
        self.pair_index = {}           # {frozenset({id1, id2}): [segment_list]}
        self.id_index = {}             # {id: [segment_list]}
        self.chrom_index = {}          # {chrom: [segment_list]}
        self.haplotype_index = {}      # {(id, hap): [segment_list]}
```

This multi-dimensional indexing strategy reflects a key insight: different analytical questions require different ways of accessing the same underlying data. The structure is shaped by the questions we anticipate researchers asking.

For large pedigrees, memory usage becomes critical. Our SparseRelationshipCalculator uses sparse matrix representations to efficiently compute relationship coefficients for pedigrees with thousands of individuals:

```python
class SparseRelationshipCalculator:
    """Memory-efficient relationship calculator using sparse matrices."""
    # Implementation details...
```

This isn't just a performance optimization—it's what makes analysis of large communities and populations feasible, extending the scale at which we can reconstruct relationships.

## Visualization and Interpretation

Data structures shape not only computation but also how we visualize and interpret pedigrees. Bonsai v3's visualization tools transform abstract data structures into human-readable representations:

```python
class PedigreeVisualizer:
    """Enhanced visualization tool for pedigrees."""
    def visualize(self, figsize=(14, 10), title='Pedigree Structure', 
                 show_labels=True, show_sex=True, edge_style_field='type',
                 node_size_field=None, node_color_field='sex',
                 generation_layout=True):
        # Implementation details...
```

This is where computational representation meets human understanding. The visualization process involves important choices:
- How to represent inferred/latent ancestors visually
- How to show different relationship types (biological, adoptive)
- How to organize individuals spatially (by generation, by family cluster)
- Which attributes to emphasize through visual cues (sex, age, data quality)

These choices are not neutral—they reflect assumptions about which aspects of kinship are most important and how relationships should be understood.

## Community Structure and Network Analysis

As we scale to larger datasets, community detection becomes essential. This connects computational genealogy to broader network science:

```python
def partition_with_community_detection(segments):
    """Partition individuals into communities based on IBD sharing."""
    # Implementation details using graph algorithms...
```

This approach raises interesting questions about how genetic communities relate to cultural or social ones:
- Do genetically detected communities align with self-identified families?
- How do isolated genetic communities reflect historical patterns of marriage and migration?
- What constitutes a meaningful "community" in genetic terms?

These questions bridge computational methods with anthropological and sociological perspectives on kinship and community formation.

## Validation: Ensuring Biological and Logical Consistency

Pedigree validation is more than error checking—it's about ensuring that computational representations respect biological and logical constraints:

```python
class PedigreeValidator:
    """Validate pedigree structures for consistency."""
    def validate(self):
        """Run all validation checks."""
        self.detect_cycles()
        self.check_temporal_consistency()
        self.check_gender_consistency()
        self.check_max_parents()
        self.check_disconnected_components()
        # Implementation details...
```

Each validation type enforces a different conceptual constraint:
- **Cycle detection**: Enforces linear time and generational progression
- **Temporal consistency**: Ensures biologically plausible age relationships
- **Gender consistency**: Checks reproductive compatibility (though with cultural assumptions)
- **Maximum parents**: Enforces biological constraints on parentage

Validation isn't just technical—it's where computational models interact with biological reality and cultural understanding of kinship.

## Cultural Implications and Limitations

Any computational representation of kinship necessarily makes simplifying assumptions. Bonsai's data structures work well for certain family models but may less naturally represent:

- **Unilineal systems**: Societies with matrilineal or patrilineal descent
- **Non-genealogical kinship**: Systems where significant kinship is established through means other than biological descent
- **Complex marriage patterns**: Polygynous, polyandrous, or other non-monogamous family structures

While Bonsai v3 extends support for different relationship types, it still operates within certain conceptual boundaries. Being aware of these limitations is essential when applying the algorithm across different cultural contexts.

The ExtendedUpNodeDict class represents our attempt to broaden support for diverse kinship models:

```python
class ExtendedUpNodeDict:
    """Enhanced dictionary supporting various relationship types."""
    def add_relationship(self, child_id, parent_id, relationship_type='biological', 
                       confidence=1.0, year=None, source=None):
        # Implementation details...
```

This allows representation of adoptive, step, and other culturally recognized relationships—a step toward more inclusive kinship modeling.

## Ethical Dimensions

Data structures for representing family relationships raise important ethical considerations:

1. **Privacy and interconnectedness**: Including one individual necessarily reveals information about their relatives
2. **Representation of uncertainty**: How probabilistic inferences are communicated matters for individuals whose family connections may be questioned
3. **Cultural appropriateness**: The assumptions embedded in data structures may conflict with cultural understandings of kinship
4. **Accessibility and control**: Technical complexity can create barriers to understanding one's own family information

These ethical dimensions should inform how we design, implement, and apply pedigree reconstruction algorithms.

## Conclusion: From Structure to Understanding

The data structures in Bonsai v3 represent more than technical implementations—they embody a particular approach to understanding human relationships through genetic data. By examining these structures critically, we gain insight into both the capabilities and limitations of computational approaches to kinship.

As we continue developing these algorithms, we should strive for data structures that:
- Accommodate diverse cultural understandings of kinship
- Support transparent and interpretable relationship inference
- Balance computational efficiency with representational flexibility
- Respect the ethical dimensions of family information

In bridging computation and genealogy, we're not just solving technical problems—we're creating frameworks for understanding human connection.