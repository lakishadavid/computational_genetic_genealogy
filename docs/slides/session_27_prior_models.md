# Session 27: Custom Prior Probability Models (prior.py)

## Session Overview
This session explores custom prior probability models in Bonsai v3, implemented in the `prior.py` module, which allow incorporating prior knowledge and population-specific information into the pedigree reconstruction process.

## Key Topics

### 1. The Role of Prior Probabilities
- Bayesian inference framework in Bonsai v3
- Why priors matter in pedigree reconstruction
- Balancing prior knowledge and genetic evidence
- Impact on reconstruction accuracy
- Use cases for custom priors

### 2. The `prior.py` Module Structure
- Design philosophy and implementation approach
- Key components and functions
- Integration with likelihood computation
- Configuration options and customization
- Default prior models

### 3. Types of Prior Information
- Demographic priors:
  - Age distributions
  - Generation length patterns
  - Sex ratios and fertility patterns
- Geographic priors:
  - Distance-based relationship probability
  - Migration patterns and constraints
- Temporal priors:
  - Historical population size
  - Birth rate variations over time
- Implementation in different prior classes

### 4. Relationship Prior Probability Model
- Base relationship probability distributions
- Modeling relationship frequency in populations:
  ```python
  # Example prior probability structure
  relationship_prior = {
      (1, 0, 1, 0, 0): 0.01,  # Full siblings
      (1, 0, 0, 0, 1): 0.02,  # Parent-child
      (2, 0, 2, 0, 0): 0.005,  # First cousins
      # ... additional relationships
  }
  ```
- Calibration with empirical data
- Implementation in relationship prior functions

### 5. Age-Based Prior Models
- Prior probabilities for age differences
- Generation length distributions
- Age constraint implementation
- Integration with relationship priors
- Implementation in age prior functions

### 6. Population-Specific Customization
- Adjusting priors for different populations
- Endogamous population considerations
- Cultural family structure variations
- Historical demographic differences
- Configuration for population-specific priors

### 7. Incorporating External Knowledge
- Using documentary evidence in priors
- Historical records integration
- Expert knowledge encoding
- Confidence-weighted external information
- Implementation in external knowledge adapters

### 8. Mathematical Framework
- From prior probabilities to log-likelihoods
- Combining priors with genetic evidence
- Weighting schemes for different evidence types
- Statistical validity considerations
- Implementation in mathematical functions

### 9. Dynamic and Adaptive Priors
- Context-dependent prior adjustment
- Feedback loops with preliminary results
- Adaptive prior weight adjustment
- Implementation in adaptive prior systems
- Self-calibrating prior models

### 10. Prior Model Validation
- Testing prior accuracy with known relationships
- Calibration methodologies
- Sensitivity analysis for prior parameters
- Measuring impact on reconstruction results
- Implementation in validation frameworks

## Practical Components
- Implementing custom relationship priors
- Calibrating prior models with empirical data
- Integrating priors into the likelihood framework
- Evaluating the impact of different prior models

## Recommended Reading
- Bayesian statistics literature
- Papers on demographic prior modeling
- Historical demography studies
- Cultural anthropology of family structures
- Statistical methods for prior calibration

## Next Session
In our next meeting, we'll explore integration with other genealogical tools through the `druid.py` module and related interfaces.