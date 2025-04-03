# Mathematical Foundations of Bonsai Genetic Genealogy Algorithm 

## Slide 1: Introduction to Bonsai
- Bonsai: A probabilistic algorithm for pedigree reconstruction
- Uses identity-by-descent (IBD) segments to infer genealogical relationships
- Developed and used at 23andMe for relationship inference
- Core innovation: statistical likelihood models for IBD patterns

## Slide 2: The Probabilistic Framework
- **Maximum Likelihood Estimation (MLE)**
- Finds the pedigree structure that best explains observed genetic data
- $\mathcal{P}^* = \arg\max_{\mathcal{P}} P(\text{IBD data} | \mathcal{P})$
- Combines both genetic evidence and demographic constraints

## Slide 3: Up-Node Dictionary Structure
- Efficient representation of pedigree relationships
- Format: `{individual_id: {parent1_id: degree1, parent2_id: degree2}, ...}`
- Genotyped IDs are positive integers, inferred IDs are negative
- Facilitates easy traversal and manipulation of pedigree structure

```python
# Example of an up-node dictionary
up_node_dict = {
    101: {201: 1, 202: 1},  # Individual 101 has parents 201 and 202
    102: {201: 1, 202: 1},  # Full sibling of 101
    103: {201: 1, 203: 1},  # Half-sibling to 101/102
    # ...
}
```

## Slide 4: IBD Segment Modeling
- IBD segments are stretches of identical genetic material
- Key IBD statistics: count, total length, segment distribution
- Different relationships have characteristic IBD patterns
- Bonsai models:
  - Expected number of segments
  - Expected distribution of segment lengths

## Slide 5: Relationship Representation
- Relationships encoded as tuples: `(up, down, num_ancestors)`
  - `up` = generations from individual 1 up to common ancestor
  - `down` = generations from common ancestor down to individual 2
  - `num_ancestors` = number of common ancestors (1 or 2)
- Examples:
  - Parent-child: `(0, 1, 1)` or `(1, 0, 1)`
  - Full siblings: `(1, 1, 2)`
  - Half-siblings: `(1, 1, 1)`
  - First cousins: `(2, 2, 2)`

## Slide 6: Core Likelihood Functions
- IBD segment count follows a Poisson distribution
- IBD segment lengths follow an Exponential distribution
- Total IBD length modeled with Gamma distribution (sum of exponentials)
- Conditional probability key for unrelated pairs: P(IBD | relationship)

```python
# From the production code:
def get_log_seg_pdf(n1, n2, L1, L2, rel_tuple, ...):
    """Calculate log pdf of IBD statistics given relationship"""
    # Getting expected values for the proposed relationship
    mean_n1 = moments[rel_tuple]['mean_n1']  # Expected segment count
    mean_l1 = moments[rel_tuple]['mean_l1']  # Expected segment length
    
    # Calculate likelihood using segment count and length
    # ...
```

## Slide 7: Expected IBD Segments Calculation

```python
# From the production code:
def get_eta(a_lst, m_lst, covs1=None, covs2=None, ...):
    """
    Get the expected number of segments for a relationship with
    m meioses, a common ancestors, and minimum segment length.
    """
    # Formula from Jewett et al. (2021)
    eta = (2**(1-m_lst)) * a_lst * (r*m_lst+c)
    
    # Correct for coverage and minimum segment length
    # ...
```

## Slide 8: IBD Moments
- Store precomputed expected moments for different relationship types
- Moments calibrated from empirical data and theoretical models
- First moment: number of segments (count)
- Second moment: total IBD length 
- Used for fast likelihood calculation

```python
# From the production code:
def load_ibd_moments():
    """Load precomputed IBD distribution moments"""
    str_ibd_moments = json.loads(open(IBD_MOMENT_FP, 'r').read())
    return unstringify_keys(str_ibd_moments)
```

## Slide 9: Age Constraint Modeling
- Age differences follow predictable patterns in pedigrees
- Modeled as Gaussian distributions with relationship-specific parameters
- Parent-child: mean ≈ 30 years, σ ≈ 7 years
- Siblings: mean ≈ 0 years, σ ≈ 7 years
- Incorporates demographic evidence into likelihood

```python
# From the production code:
def get_age_log_like(age1, age2, rel_tuple):
    """Find the age component of the pairwise log likelihood"""
    mean, std = get_age_mean_std_for_rel_tuple(rel_tuple, age1, age2)
    age_diff = age1 - age2
    return scipy.stats.norm.logpdf(age_diff, loc=mean, scale=std)
```

## Slide 10: Composite Likelihood Framework
- Overall likelihood = sum of pairwise log-likelihoods
- Each pair contributes genetic and age components
- Genetic component: IBD segment patterns
- Age component: plausibility of age differences
- Final score guides optimization algorithms

```python
# From the production code:
def get_ped_like(ped, pw_ll_cls):
    """
    Get the composite likelihood of a pedigree
    as the sum of pairwise log likelihoods
    between each pair of genotyped IDs.
    """
    gt_id_set = get_gt_id_set(ped)
    log_like = 0
    for i1, i2 in combinations(gt_id_set, r=2):
        rel_tuple = get_simple_rel_tuple(ped, i1, i2)
        ll = pw_ll_cls.get_pw_ll(node1=i1, node2=i2, rel_tuple=rel_tuple)
        log_like += ll
    return log_like
```

## Slide 11: Handling Low Coverage Data
- Adjusts for incomplete genetic data
- Scaling factors (P, Q) for segment detection probability
- Corrects expected segment count and length
- Enables robust inference even with varying data quality

```python
# From the production code:
def get_lam_a_m(m_lst, covs1=None, covs2=None, p=P):
    """
    Get the inverse mean segment length adjusting for coverage
    """
    # Basic meiosis-dependent calculation
    lam_a_m = m_lst/100
    
    # Coverage adjustment factors
    cov_factor1 = 1 - np.exp(-p*covs1)
    cov_factor2 = 1 - np.exp(-p*covs2)
    cov_factor = cov_factor1 * cov_factor2
    
    # Apply coverage correction
    lam_a_m = np.outer(cov_factor, lam_a_m)
```

## Slide 12: Optimization Strategies
- Search for maximum likelihood pedigree is NP-hard
- Bonsai uses several optimization strategies:
  - Greedy approach: build from most confident relationships
  - Simulated annealing: avoid local optima
  - Integer Linear Programming (ILP) for final refinement
- Memoization and pruning for computational efficiency

## Slide 13: Handling Background IBD
- Small chance of IBD sharing between truly unrelated people
- Models "background noise" in IBD detection
- Parameters:
  - `MEAN_BGD_NUM`: Expected number of background segments
  - `MEAN_BGD_LEN`: Expected length of background segments
- Critical for distinguishing distant relationships from noise

```python
# From the production code:
# Background IBD parameters
MEAN_BGD_NUM = 0.01  # expected number of background segments  
MEAN_BGD_LEN = 5     # expected length of background segments
```

## Slide 14: Advanced Likelihood Models
- Bessel function approximation for segment length distributions
- Conditional vs. unconditional likelihood formulations
- Joint modeling of segment count and total length
- Handles edge cases (zero segments, tiny segments)

```python
# From the production code:
def total_conditional_ibd_pdf_bessel(L, m, a, ...):
    """
    Bessel function approximation of IBD length PDF
    """
    # Get lambda and eta parameters
    lam = get_lam_a_m(m_lst=np.array([m]), ...)[0][0]
    eta = get_eta(a_lst=np.array([a]), m_lst=np.array([m]), ...)[0][0]
    
    # Approximation using modified Bessel function of first kind
    pdf = (
        np.exp(-lam*(L-min_seg_len)) *
        np.sqrt(eta*lam) *
        iv(1, 2*np.sqrt((L-min_seg_len)*eta*lam)) /
        (np.sqrt(L-min_seg_len) *
        (np.exp(eta) - 1))
    )
```

## Slide 15: Integrating Theory and Practice
- Mathematical foundations mapped to production code
- Calibration using real and simulated data
- Performance guarantees and validation
- Balances statistical rigor with computational efficiency
- Enables real-world relationship inference at scale