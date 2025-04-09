# Session 6: Probabilistic Relationship Inference (moments.py)

## Session Overview
This session focuses on the probabilistic methods used in Bonsai v3 to infer relationships from IBD data, with particular emphasis on the moment-based approaches implemented in `moments.py`.

## Key Topics

### 1. Foundations of Probabilistic Relationship Inference
- From deterministic to probabilistic relationship models
- The likelihood-based framework in Bonsai v3
- Inherent uncertainty in genetic inheritance
- Confidence levels in relationship inference

### 2. Moment-Based Inference in `moments.py`
- Definition of statistical moments and their relevance
- Moments for IBD length and count distributions
- Implementation of moment-based estimators:
  - Conditional moments for known relationships
  - Unconditional moments for relationship inference
- Computational efficiency of moment-based methods

### 3. Conditional vs. Unconditional Moments
- `cond_dict`: Moments conditioned on relationship type
- `uncond_dict`: Moments across the relationship space
- Loading pre-computed moment distributions
- Application in relationship likelihood calculation

### 4. From Moments to Likelihoods
- Converting distribution moments to likelihood functions
- Computing log-likelihoods from distribution parameters
- Implementation of `get_log_seg_pdf()` function
- Handling edge cases and detection thresholds

### 5. Relationship Tuple Representation
- Structure of relationship tuples in Bonsai v3:
  ```python
  # (degree1, removal1, degree2, removal2, half)
  (1, 0, 1, 0, 0)  # Full siblings
  (1, 0, 0, 0, 1)  # Parent-child
  (2, 0, 2, 0, 0)  # First cousins
  ```
- Mapping relationship tuples to moment expectations
- Complete relationship space representation
- Common relationship types and their tuple encoding

### 6. Moment Calibration with Real Data
- Fitting theoretical models to empirical IBD data
- Calibration datasets and their characteristics
- Cross-validation and verification of moment estimates
- Handling population-specific variations

### 7. Performance Optimization in Moment-Based Inference
- Caching strategies for moment calculations
- Approximation methods for computational efficiency
- Vectorized implementations for speed
- Memory-computation tradeoffs

## Practical Components
- Computing relationship moments from IBD data
- Implementing key functions from `moments.py`
- Relationship inference exercises with sample data
- Calibrating moment parameters with empirical data

## Recommended Reading
- Statistical literature on moment-based inference
- Papers on probabilistic relationship determination
- Documentation for IBD-based relationship inference tools
- Background on Bayesian inference in genetics

## Next Session
In our next session, we'll examine the `PwLogLike` class and dive into the details of likelihood computation for relationship inference.