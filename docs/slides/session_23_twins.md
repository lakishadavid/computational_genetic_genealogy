# Session 23: Handling Twins and Close Relatives (twins.py)

## Session Overview
This session explores the specialized algorithms in Bonsai v3's `twins.py` module for handling twins and other very close relatives, which present unique challenges for pedigree reconstruction.

## Key Topics

### 1. The Twin Challenge in Genetic Genealogy
- Types of twins and their genetic signatures:
  - Monozygotic (identical) twins
  - Dizygotic (fraternal) twins
- Why twins create special cases:
  - Identical or nearly identical genetic profiles
  - IBD patterns that violate standard assumptions
  - Age-based inference complications
- Impact on pedigree reconstruction

### 2. The `twins.py` Module Structure
- Design philosophy and implementation approach
- Key components and functions
- Integration with other system modules
- Configuration options and thresholds
- Use cases and triggering conditions

### 3. Twin Detection Algorithms
- Identifying potential twin relationships:
  - Extremely high IBD sharing (>90%)
  - Identical or nearly identical age
  - Identical sex (for identical twins)
- Statistical models for twin vs. non-twin discrimination
- Implementation in detection functions
- Confidence scoring for twin identification

### 4. Specialized IBD Modeling for Twins
- Adjusted IBD expectations for twin relationships
- Handling identical genetic profiles
- Distinguishing twins from parent-child relationships
- Custom likelihood functions for twin cases
- Implementation in twin-specific IBD models

### 5. Twin Placement in Pedigrees
- Specialized connection logic for twin pairs
- Ensuring consistent parent relationships
- Handling twin-specific constraints
- Implementation in twin placement functions
- Validation of twin connections

### 6. Other Very Close Relatives
- Double first cousins (shares ~25% DNA, like half-siblings)
- Parent-child incest cases
- Compound relationships
- Endogamous populations with elevated IBD sharing
- Implementation of special handling for these cases

### 7. The Identical Twin Problem
- Fundamental limits of genetic differentiation
- Strategies for distinguishing identical twins:
  - Epigenetic markers
  - Somatic mutations
  - Non-genetic information
- Implementation of twin differentiation approaches
- Fallback strategies when differentiation fails

### 8. Age and Sex Modeling for Twins
- Using age and birth order information
- Sex-specific twin constraints
- Demographic patterns in twin births
- Implementation in twin-specific age models
- Integration with genetic evidence

### 9. Handling Twin Children
- Modeling children of twins
- Avuncular relationships through twin parents
- Cousin relationships through twin parents
- Complex relationship structures
- Implementation in specialized relationship functions

### 10. Twin-Specific Visualization and Reporting
- Visual representation of twin relationships
- Reporting twin confidence
- Communicating twin-specific uncertainty
- Annotation of twin relationships
- Implementation in twin-aware visualization

## Practical Components
- Implementing twin detection algorithms
- Adjusting IBD models for twin relationships
- Placing twins correctly in pedigree structures
- Handling edge cases with very close relatives

## Recommended Reading
- Twin studies in genetics
- Statistical models for identical vs. fraternal twins
- Papers on twin differentiation methods
- Literature on compound relationships in genetics
- Visualization standards for twin relationships

## Next Session
In our next meeting, we'll explore how Bonsai v3 handles complex relationship patterns through specialized logic in the `relationships.py` module.