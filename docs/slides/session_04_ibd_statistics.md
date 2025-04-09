# Session 4: IBD Statistics Extraction and Analysis

## Session Overview
This session explores how Bonsai v3 extracts and utilizes statistical information from IBD segments to inform relationship inference and pedigree construction.

## Key Topics

### 1. IBD Statistics Fundamentals
- Key statistics for relationship inference:
  - Total shared IBD (in cM)
  - Number of distinct IBD segments
  - Distribution of segment lengths
  - IBD1 vs IBD2 patterns
- Statistical properties and their genealogical significance
- How statistics vary by relationship type

### 2. The `get_ibd_stats_unphased()` Function
- Implementation details and algorithm walkthrough
- Input requirements and output format
- Key statistics computed:
  - `total_half`: Total IBD1 sharing (cM)
  - `total_full`: Total IBD2 sharing (cM)
  - `num_half`: Number of IBD1 segments
  - `num_full`: Number of IBD2 segments
  - `max_seg_cm`: Length of largest segment
- Edge cases and special handling

### 3. IBD Statistic Dictionaries
- Structure and organization:
  ```python
  ibd_stat_dict = {
      (id1, id2): {
          'total_half': 75.3,
          'total_full': 12.1,
          'num_half': 8,
          'num_full': 1,
          'max_seg_cm': 23.4
      }
  }
  ```
- Efficient lookup and storage techniques
- Memory optimization for large datasets

### 4. Coverage Adjustment for IBD Statistics
- Accounting for incomplete genomic coverage
- Effects of missing data on IBD detection
- Statistical adjustment methods:
  - Scaling factors for total IBD
  - Correction for segment count expectations
  - Confidence intervals with coverage information

### 5. Using IBD Statistics for Triage
- Prioritizing relationship analysis based on statistics
- Thresholds for different relationship categories
- Fast-path vs. detailed analysis decisions
- Implementation of efficient triage workflows

### 6. Background IBD and False Positives
- Sources of background IBD in populations
- Modeling and accounting for population-specific sharing
- False positive detection and filtering
- Parameters controlling background assumptions:
  - `mean_bgd_num`: Expected background segments
  - `mean_bgd_len`: Expected background segment length

## Practical Components
- Computing IBD statistics from sample segment data
- Visualizing statistics across different relationship types
- Implementing and testing statistical adjustments
- Comparing raw and adjusted statistics for accuracy

## Recommended Reading
- Papers on expected IBD sharing in different relationships
- Statistical methods for genealogical inference
- Background IBD models for various populations

## Next Session
In our next meeting, we'll examine the statistical models of genetic inheritance that form the mathematical foundation of Bonsai v3's relationship inference.