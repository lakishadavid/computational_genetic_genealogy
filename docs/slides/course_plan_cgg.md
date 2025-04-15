# Computational Pedigree Reconstruction: Deep Dive into Bonsai v3

A 15-week course (30 sessions) on mastering the Bonsai v3 codebase for genetic genealogy applications:

## Week 1: Foundations
- **Session 1**: Introduction to Genetic Genealogy and IBD Concepts  
  Explore the fundamental concepts of Identity By Descent (IBD) segments, genetic inheritance patterns, and recombination. Learn how Bonsai v3 leverages these principles to infer relationships from genetic data, with an overview of its probabilistic approach to pedigree reconstruction.

- **Session 2**: Bonsai v3 Architecture Overview and Core Data Structures  
  Dive into Bonsai v3's modular architecture, examining how the codebase is structured into specialized components (ibd.py, likelihoods.py, pedigrees.py, etc.). Understand the flow of data through the system and how core constants (GENOME_LENGTH, MIN_SEG_LEN, etc.) underpin the mathematical models.

## Week 2: IBD Processing Framework
- **Session 3**: IBD Data Formats and Preprocessing (ibd.py)  
  Master the IBDSegment class implementation and learn how Bonsai processes raw IBD data. Explore conversion functions between phased and unphased segment formats, segment merging algorithms, and genetic-to-physical position mapping used in ibd.py.

- **Session 4**: IBD Statistics Extraction and Analysis  
  Analyze how Bonsai extracts meaningful statistics from IBD data using functions like get_ibd_stats_unphased() and get_total_ibd_between_id_sets(). Learn to calculate key metrics that serve as inputs to the likelihood models for relationship inference.

## Week 3: Mathematical Foundations
- **Session 5**: Statistical Models of Genetic Inheritance  
  Examine the mathematical models that describe expected IBD sharing patterns between relatives. Study the probability distributions implemented in Bonsai v3 for segment lengths and counts, including the specialized adaptations for close relatives.

- **Session 6**: Probabilistic Relationship Inference (moments.py)  
  Discover how Bonsai uses moment-based methods to model relationship probabilities. Explore the empirical and theoretical moments of IBD sharing distributions and how they're used to calibrate the likelihood functions that power relationship inference.

## Week 4: Relationship Analysis
- **Session 7**: The PwLogLike Class and Likelihood Computation  
  Deep dive into the PwLogLike class from likelihoods.py, which calculates pairwise log-likelihoods for different relationship hypotheses. Learn how genetic and age-based evidence are combined using principled Bayesian approaches to rank potential relationships.

- **Session 8**: Age-Based Relationship Modeling  
  Explore Bonsai's age-based constraints system using get_age_mean_std_for_rel_tuple() and get_age_log_like() functions. Understand how empirically-derived age difference distributions are integrated with genetic evidence to improve relationship predictions.

## Week 5: Core Algorithms
- **Session 9**: Pedigree Data Structures Implementation  
  Master Bonsai's core pedigree representation using up-node and down-node dictionaries. Learn how these flexible data structures efficiently encode parent-child relationships while supporting arbitrary pedigree complexity and efficient traversal operations.

- **Session 10**: Up-Node Dictionary and Pedigree Representation  
  Explore advanced up-node dictionary operations including re_root_up_node_dict(), get_subdict(), and trim_to_proximal(). Understand how these functions enable powerful pedigree manipulations that form the foundation for merging and optimization algorithms.

## Week 6: Connection Logic
- **Session 11**: Finding Connection Points Between Individuals  
  Learn how Bonsai identifies optimal connection points between individuals using genetic evidence. Analyze the algorithms that evaluate different possible relationship configurations and select the most likely connection based on combined likelihoods.

- **Session 12**: Relationship Assessment and Validation (connections.py)  
  Study Bonsai's approach to validating inferred relationships through the connections.py module. Examine methods for assessing relationship compatibility, detecting contradictions, and ensuring pedigree consistency across multiple relationship hypotheses.

## Week 7: Building Small Pedigrees
- **Session 13**: Connecting Individuals into Small Structures  
  Explore algorithms for constructing small pedigree structures from pairwise relationships. Learn how Bonsai builds trio and quartet structures while maintaining consistency with the genetic evidence and resolving ambiguous connection patterns.

- **Session 14**: Optimizing Small Pedigree Configurations  
  Master techniques for optimizing small pedigree structures by evaluating alternative configurations. Understand how Bonsai calculates the overall likelihood of a pedigree and applies optimization strategies to find the maximum likelihood configuration.

## Week 8: Scaling to Larger Pedigrees
- **Session 15**: The combine_up_dicts() Algorithm  
  Analyze the combine_up_dicts() algorithm that enables merging of separate pedigree structures. Learn how Bonsai determines the optimal connection points between pedigrees, handles overlapping individuals, and maintains consistency during merges.

- **Session 16**: Merging Pedigrees with Optimal Connection Points  
  Build on combine_up_dicts() to understand the complete pedigree merging workflow. Explore strategies for prioritizing connections, resolving conflicts during merges, and validation procedures that ensure the resulting pedigree remains genetically consistent.

## Week 9: Advanced Algorithms
- **Session 17**: Incremental Individual Addition Strategies  
  Learn how Bonsai efficiently adds new individuals to existing pedigrees using incremental strategies. Understand the optimization techniques that evaluate multiple potential connection points and select the maximum likelihood placement.

- **Session 18**: Optimization Techniques and Performance Enhancements  
  Explore the computational optimizations implemented in Bonsai v3 including dynamic programming approaches, pruning strategies, and early termination conditions that enable efficient processing of large pedigrees and complex relationship networks.

## Week 10: System Integration
- **Session 19**: Caching Mechanisms for Computational Efficiency (caching.py)  
  Examine Bonsai's sophisticated caching framework that significantly improves performance for repeated operations. Learn about the memoization decorators, strategic caching points, and cache invalidation strategies that balance memory usage with computational savings.

- **Session 20**: Error Handling and Edge Cases (exceptions.py)  
  Master Bonsai's approach to error handling and edge case management through exceptions.py. Study the custom exception hierarchy, coding practices for robust error handling, and strategies for graceful degradation when faced with unexpected data patterns.

## Week 11: Visualization and Interpretation
- **Session 21**: Pedigree Rendering and Visualization (rendering.py)  
  Learn how Bonsai visualizes complex pedigree structures using the rendering.py module. Explore the render_ped() function that leverages Graphviz for pedigree visualization, including customization options for node colors, labels, and highlighting focal individuals.

- **Session 22**: Interpreting Results and Confidence Measures  
  Discover how Bonsai quantifies and communicates confidence in relationship predictions. Study the likelihood ratio approach, confidence interval calculations via get_total_ibd_deg_lbd_pt_ubd(), and methods for interpreting competing relationship hypotheses.

## Week 12: Special Cases
- **Session 23**: Handling Twins and Close Relatives (twins.py)  
  Explore Bonsai's specialized handling of identical twins and other close relatives that present unique genetic signatures. Learn about the twins.py module's algorithms for detecting twin-like patterns and ensuring appropriate treatment in pedigree construction.

- **Session 24**: Complex Relationship Patterns (relationships.py)  
  Master Bonsai's approach to complex relationship patterns through the relationships.py module. Study functions like get_deg() and reverse_rel() that support interpretation and manipulation of unusual relationship configurations and endogamous patterns.

## Week 13: Practical Applications
- **Session 25**: Real-World Datasets and Challenges  
  Apply Bonsai to real-world genetic datasets, addressing challenges like missing data, endogamy, and population-specific patterns. Learn strategies for data preparation, parameter tuning, and result validation in practical genetic genealogy applications.

- **Session 26**: Performance Tuning for Large-Scale Applications  
  Explore advanced performance optimization for applying Bonsai to large datasets. Learn profiling techniques to identify bottlenecks, memory management strategies, parallel processing approaches, and configuration optimizations for different dataset characteristics.

## Week 14: Advanced Topics
- **Session 27**: Custom Prior Probability Models (prior.py)  
  Dive into Bonsai's prior probability framework through prior.py. Learn how to develop and integrate custom prior models that incorporate demographic information, historical records, or domain-specific knowledge to enhance the accuracy of relationship predictions.

- **Session 28**: Integration with Other Genealogical Tools (druid.py)  
  Study Bonsai's integration capabilities, particularly through the DRUID algorithm in druid.py. Understand how infer_degree_generalized_druid() works with external data sources and tools to create a comprehensive genetic genealogy workflow.

## Week 15: Capstone Project
- **Session 29**: End-to-End Pedigree Reconstruction Implementation  
  Develop a complete pedigree reconstruction pipeline using Bonsai v3, integrating all components from data preparation through visualization. Create a solution that handles real data challenges while producing interpretable, confidence-scored results.

- **Session 30**: Advanced Applications and Future Directions  
  Explore cutting-edge applications of Bonsai v3 and emerging research directions in computational genetic genealogy. Discuss potential improvements to the algorithms, integration with machine learning approaches, and extensions to handle additional data types.