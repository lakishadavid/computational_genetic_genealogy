# Session 28: Integration with Other Genealogical Tools (druid.py)

## Session Overview
This session explores how Bonsai v3 integrates with other genealogical tools and systems through the `druid.py` module and related interfaces, enabling comprehensive workflow integration in the genetic genealogy ecosystem.

## Key Topics

### 1. The Genetic Genealogy Ecosystem
- Overview of key tools and systems:
  - IBD detection tools (IBIS, RefinedIBD, HapIBD)
  - Phasing software (SHAPEIT, Eagle)
  - Traditional genealogy platforms
  - Visualization systems
  - Analysis frameworks
- Integration challenges and opportunities
- Bonsai v3's position in the ecosystem

### 2. The `druid.py` Module Structure
- Purpose and design philosophy
- Key components and functions
- Integration patterns implemented
- Configuration options
- Extension points for additional tools

### 3. IBD Detector Integration
- Input format conversion for different detectors:
  - IBIS format handling
  - RefinedIBD integration
  - HapIBD compatibility
  - Custom detector support
- Normalization and standardization
- Configuration for detector-specific parameters
- Implementation in IBD adapter functions

### 4. Phasing Tool Integration
- Working with phased vs. unphased data
- Integrating with phasing software:
  - SHAPEIT output processing
  - Eagle format compatibility
  - Beagle integration
- Handling phasing uncertainty
- Implementation in phasing adapters

### 5. Traditional Genealogy Platform Integration
- GEDCOM import and export
- Family tree software compatibility
- Commercial platform APIs:
  - Ancestry integration
  - FamilySearch connection
  - MyHeritage compatibility
- Implementation in genealogy platform adapters

### 6. Visualization System Integration
- Output formats for visualization tools
- Interactive visualization connections
- Embedding in web applications
- Custom visualization pipelines
- Implementation in visualization adapters

### 7. Analysis Framework Integration
- Statistical analysis tool connections
- R and Python integration
- Jupyter notebook compatibility
- Custom analysis pipeline support
- Implementation in analysis adapters

### 8. Data Format Conversion Utilities
- Standard format converters
- Custom format handling
- Lossy vs. lossless conversion
- Validation during conversion
- Implementation in format converters

### 9. API Design for Integration
- RESTful API implementation
- Command-line interface design
- Library integration patterns
- Configuration and extensibility
- Implementation in API modules

### 10. End-to-End Workflow Integration
- Complete pipeline examples:
  - Raw data to pedigree visualization
  - Integration with existing trees
  - Multi-tool analysis workflows
  - Large-scale processing pipelines
- Implementation in workflow examples

## Practical Components
- Implementing format converters for IBD data
- Creating integration adapters for visualization tools
- Building end-to-end processing pipelines
- Developing extension points for third-party tools

## Recommended Reading
- Systems integration literature
- API design principles
- Data transformation patterns
- Workflow orchestration approaches
- Standards in genealogical software

## Next Session
In our next meeting, we'll begin our capstone project with an end-to-end pedigree reconstruction implementation using Bonsai v3.