# Session 5: Statistical Models of Genetic Inheritance

## Session Overview
This session explores the statistical models that describe genetic inheritance patterns, providing the theoretical foundation for relationship inference in Bonsai v3.

## Key Topics

### 1. Genetic Inheritance Fundamentals
- Mendelian inheritance and recombination
- The stochastic nature of genetic transmission
- Mathematical representation of inheritance processes
- Random vs. non-random patterns in genetic sharing

### 2. IBD Segment Length Distributions
- Theoretical models for segment length distributions
- The exponential length distribution approximation
- Factors affecting segment length:
  - Relationship degree
  - Population history
  - Chromosome-specific recombination rates
- Implementation in Bonsai v3's statistical framework

### 3. IBD Segment Count Distributions
- Poisson approximations for segment counts
- Relationship between meiotic distance and expected counts
- Implementation of `get_eta()` for expected segment counts
- Adjustments for detection thresholds and genomic coverage

### 4. The Coefficient of Relatedness
- Definition and calculation for different relationships
- Connection to expected total IBD sharing
- Implementation in relationship likelihood calculations
- Limitations and edge cases

### 5. Parameter Estimation from Empirical Data
- Calibration of theoretical models with real data
- Extracting relationship-specific parameters
- Bootstrapping techniques for parameter confidence
- Implementation in Bonsai v3's model fitting routines

### 6. The Three-Parameter Model
- Lambda (λ): IBD segment length parameter
- Eta (η): Expected segment count
- Probability of sharing: Background vs. relationship-based
- Integration of parameters into likelihood functions

### 7. Mathematical Framework in `moments.py`
- Implementation of key mathematical functions:
  - `get_lam_a_m()`: Computing expected segment lengths
  - Parameter computation for different relationship types
  - Moment calculations for IBD distributions
- Connection to likelihood computation

## Practical Components
- Working with IBD distribution models
- Calculating expected statistics for sample relationships
- Fitting distribution parameters to empirical data
- Implementing key mathematical functions

## Recommended Reading
- Papers on IBD segment distribution modeling
- Statistical theory for genetic inheritance
- Background on moment-based inference methods
- Documentation for relationship inference algorithms

## Next Session
In our next meeting, we'll explore probabilistic relationship inference methods, building on the mathematical foundations covered today.