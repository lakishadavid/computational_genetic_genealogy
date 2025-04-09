# Session 7: The PwLogLike Class and Likelihood Computation

## Session Overview
This session delves into the `PwLogLike` class from `likelihoods.py`, a core component of Bonsai v3 that handles the computation of relationship likelihoods based on IBD data.

## Key Topics

### 1. The PwLogLike Class Architecture
- Class design and purpose in the Bonsai v3 system
- Initialization and required parameters:
  ```python
  pw_ll_cls = PwLogLike(
      bio_info=bio_info,
      unphased_ibd_seg_list=unphased_ibd_seg_list,
      condition_pair_set=condition_pair_set,
      mean_bgd_num=mean_bgd_num,
      mean_bgd_len=mean_bgd_len,
  )
  ```
- Key properties and data structures maintained
- Integration with other system components

### 2. Initialization and Data Preparation
- Processing IBD data during initialization
- Building internal data structures:
  - `ibd_stat_dict`: IBD statistics for all pairs
  - `sex_dict`, `age_dict`, `cov_dict`: Metadata dictionaries
  - `cond_dict`, `uncond_dict`: Pre-calculated IBD relationship moments
- Validation and error handling

### 3. Likelihood Component Methods
- `get_pw_gen_ll()`: Genetic likelihood computation
  - Implementation details and parameters
  - Statistical models and approximations used
  - Performance optimizations
  
- `get_pw_age_ll()`: Age-based likelihood computation
  - Age difference modeling for relationships
  - Integration with genetic likelihoods
  - Handling missing age information
  
- `get_pw_ll()`: Combined likelihood calculation
  - Weighting genetic and age components
  - Configuration parameters for likelihood balance
  - Log-likelihood scaling and normalization

### 4. Core Likelihood Algorithms
- Mathematical foundations of likelihood computation
- Converting IBD statistics to relationship probabilities
- Handling of background IBD and false positive segments
- Implementation of likelihood ratio tests

### 5. Relationship Space Navigation
- Testing multiple relationship hypotheses
- Ranking relationships by likelihood
- Finding maximum likelihood relationship types
- Confidence measures for relationship determinations

### 6. Performance Considerations
- Computational complexity analysis
- Caching strategies for repeated calculations
- Memory efficiency in large-scale applications
- Optimization techniques for real-time performance

### 7. Edge Cases and Special Handling
- Dealing with low-coverage samples
- Managing close relationships with unusual IBD patterns
- Handling relationships not well-modeled by standard patterns
- Controls for false positive and false negative rates

## Practical Components
- Implementing a simplified version of `PwLogLike`
- Computing likelihoods for sample relationship cases
- Visualizing likelihood distributions across relationship space
- Testing with edge cases and unusual IBD patterns

## Recommended Reading
- Statistical methods for likelihood calculation
- Papers on relationship inference from genetic data
- Documentation on likelihood ratio testing
- Background on combining multiple evidence sources in inference

## Next Session
In our next meeting, we'll explore age-based relationship modeling, which complements genetic data to improve inference accuracy.