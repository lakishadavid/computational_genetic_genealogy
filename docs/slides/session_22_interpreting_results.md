# Session 22: Interpreting Results and Confidence Measures

## Session Overview
This session focuses on methods for interpreting pedigree reconstruction results in Bonsai v3, examining how to evaluate relationship confidence, assess overall pedigree quality, and make informed decisions based on the output.

## Key Topics

### 1. Understanding Bonsai v3 Output
- Structure of the result objects
- Key components of the output:
  - The final pedigree structure
  - Likelihood scores for relationships
  - Confidence measures and statistics
  - Alternative configurations
- Interpretation framework and approach

### 2. Relationship Confidence Scoring
- From likelihoods to confidence measures
- Likelihood ratio interpretation
- Confidence calculation methods:
  - Absolute confidence scores
  - Relative confidence between alternatives
  - Statistical significance measures
- Implementation in confidence scoring functions

### 3. Assessing Overall Pedigree Quality
- Composite likelihood interpretation
- Structure-level confidence measures
- Identifying weak points in reconstructed pedigrees
- Consistency and coherence metrics
- Implementation in pedigree assessment functions

### 4. Understanding Likelihood Values
- Interpreting log-likelihood magnitudes
- Comparing relationships using likelihood values
- Common likelihood patterns for relationships
- Warning signs in likelihood distributions
- Practical interpretation guidelines

### 5. Confidence Threshold Guidelines
- Recommended confidence thresholds for different applications
- Relationship-specific threshold considerations
- Context-dependent threshold adjustment
- Conservative vs. exploratory threshold settings
- Implementation in configuration parameters

### 6. Disambiguating Similar Relationships
- Common confusion cases:
  - Half-siblings vs. first cousins
  - Grandparent vs. avuncular
  - Second cousins vs. first cousins once removed
- Disambiguation strategies
- Using additional evidence
- Implementation in relationship comparison functions

### 7. Handling Alternative Reconstructions
- When to consider multiple hypotheses
- Representing alternative pedigree configurations
- Ranking alternatives by plausibility
- Making decisions with uncertainty
- Implementation in alternative tracking

### 8. Incorporating External Knowledge
- Integrating documentary evidence
- Using demographic knowledge
- Cultural and historical context
- Domain-specific constraints
- Implementation in prior probability models

### 9. Communicating Results and Uncertainty
- Visualization of confidence measures
- Uncertainty representation in reports
- Language for describing probabilistic relationships
- Appropriate caveats and limitations
- Implementation in reporting functions

### 10. From Results to Action
- Decision-making framework for different applications
- Confirmation strategies for uncertain results
- Follow-up analysis recommendations
- When to seek additional evidence
- Implementation in recommendation functions

## Practical Components
- Interpreting likelihood values from sample data
- Calculating confidence measures for relationships
- Evaluating overall pedigree quality
- Communicating results with appropriate uncertainty

## Recommended Reading
- Statistical interpretation literature
- Confidence interval and hypothesis testing theory
- Papers on genetic relationship inference evaluation
- Communication of scientific uncertainty
- Decision theory for probabilistic results

## Next Session
In our next meeting, we'll explore how Bonsai v3 handles twins and close relatives through specialized algorithms in the `twins.py` module.