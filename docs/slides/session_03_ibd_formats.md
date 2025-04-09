# Session 3: IBD Data Formats and Preprocessing (ibd.py)

## Session Overview
This session focuses on the IBD data formats used in Bonsai v3 and the preprocessing steps that transform raw IBD detector output into usable data structures.

## Key Topics

### 1. IBD Data Format Specifications
- **Unphased Format** (primary input from IBD detectors):
  ```
  [id1, id2, chromosome, start_bp, end_bp, is_full_ibd, seg_cm]
  ```
  - `id1`, `id2`: Individual identifiers
  - `chromosome`: Chromosome number (1-22)
  - `start_bp`, `end_bp`: Segment boundaries in base pairs
  - `is_full_ibd`: Boolean indicating IBD1 (0) or IBD2 (1)
  - `seg_cm`: Segment length in centiMorgans

- **Phased Format** (haplotype-specific information):
  ```
  [id1, id2, hap1, hap2, chromosome, start_cm, end_cm, seg_cm]
  ```
  - `hap1`, `hap2`: Specific haplotypes that match (0 or 1)
  - Start/end positions directly in centiMorgans

### 2. Deep Dive into `ibd.py`
- Module structure and key functions
- Integration points with other system components
- Error handling and validation of IBD data

### 3. IBD Format Conversion Functions
- `get_phased_to_unphased()`: Converting phased data to unphased format
  - Grouping overlapping segments
  - Identifying fully identical regions
  - Calculating merged segment properties

- `get_unphased_to_phased()`: Creating pseudo-phased data from unphased
  - Approximation techniques
  - Limitations and accuracy considerations
  - Implementation details

### 4. IBD Filtering and Normalization
- Quality control steps for IBD segments
  - Minimum length thresholds
  - Chromosome boundary validation
  - Handling of centromere regions
- Standardizing segment data across detectors
- Dealing with missing or inconsistent information

### 5. Genetic Map Integration
- Purpose of genetic maps in IBD analysis
- Converting between base pairs and centiMorgans
- Handling different genetic map formats
- Interpolation methods for precise position conversion

### 6. Common IBD Detector Outputs
- IBIS output format and processing
- RefinedIBD data preparation
- HapIBD and other detector integration
- Standardization across different detection methods

## Practical Components
- Hands-on examination of IBD detector outputs
- Implementation of format conversion functions
- Validating and debugging IBD data quality issues
- Working with sample IBD data files

## Recommended Reading
- Documentation for popular IBD detection tools
- Papers on IBD filtering and quality control
- Genetic map resources and documentation

## Next Session
In our next meeting, we'll focus on extracting meaningful statistics from IBD segments, a critical step for relationship inference.