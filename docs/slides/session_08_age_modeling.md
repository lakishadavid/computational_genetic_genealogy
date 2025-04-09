# Session 8: Age-Based Relationship Modeling

## Session Overview
This session explores how Bonsai v3 incorporates age information to enhance relationship inference, focusing on the statistical models and methods used to leverage demographic data alongside genetic evidence.

## Key Topics

### 1. The Role of Age in Relationship Inference
- Why age data improves genealogical accuracy
- Complementary nature of genetic and age information
- Types of relationships uniquely constrained by age
- Limitations of purely genetic approaches

### 2. Age Difference Models in Bonsai v3
- Statistical distributions of age differences by relationship type
- Implementation in the `PwLogLike` class:
  - `get_age_mean_std_for_rel_tuple()`: Expected age differences
  - `get_age_log_like()`: Computing likelihood from age
- Empirical calibration of age models

### 3. Age-Based Constraints for Different Relationships
- Parent-child: Typical age differences and constraints
- Siblings and half-siblings: Age clustering patterns
- Grandparent-grandchild: Multi-generational age gaps
- Cousin relationships: Variable age differences
- Avuncular (aunt/uncle-niece/nephew): Mixed-generation modeling

### 4. Implementing `get_age_log_like()`
- Mathematical foundation for age likelihood calculation
- Gaussian approximation for age difference distributions
- Handling missing or uncertain age information
- Parameter estimation and confidence levels

### 5. Integration with Genetic Likelihoods
- Weighting age and genetic evidence appropriately
- Configuration parameters for evidence balance
- Implementation in `get_pw_ll()` method
- Adaptive weighting based on data quality

### 6. Age Priors and Population Demographics
- Cultural and historical factors in age distributions
- Population-specific calibration of age models
- Temporal changes in generation lengths
- Incorporating external demographic information

### 7. Age Data Quality and Preprocessing
- Handling approximate or uncertain birth years
- Age imputation for missing data
- Confidence measures for age information
- Validation and consistency checking

### 8. Advanced Age-Based Modeling
- Multi-generational constraints
- Age-ordered sibling groups
- Temporal impossibility detection
- Age-based anomaly detection in pedigrees

## Practical Components
- Computing age-based likelihoods for sample relationships
- Calibrating age difference models with empirical data
- Combining age and genetic likelihoods for improved accuracy
- Testing with incomplete and uncertain age information

## Recommended Reading
- Demographic research on generation lengths
- Statistical methods for age-based inference
- Papers on integrating multiple evidence types
- Historical trends in generation intervals

## Next Session
In our next meeting, we'll examine the core algorithms and data structures used to implement pedigrees in Bonsai v3.