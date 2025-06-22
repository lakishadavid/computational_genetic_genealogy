# Computational Genetic Genealogy Guidelines

## Development Principles
**NEVER use "Perfect!" to describe work**: Do not use the word "Perfect!" to describe your work unless the fix has been verified and tested by the user.

## Build/Run Commands
- Poetry: `poetry config virtualenvs.in-project true` (configure), `poetry install --no-root` (install dependencies)
- Run scripts: `poetry run python -m scripts_work.<script_name> [arguments]`
- Run specific script: `poetry run python -m scripts_work.run_ibd_detection --algorithm IBIS`
- Run notebook locally: `poetry run jupyter lab`
- Google Colab: All labs are designed to run directly in Google Colab with one-click setup

## Course Architecture

This repository contains a complete **Computational Genetic Genealogy** course with 30 progressive lab notebooks designed for Google Colab deployment.

### Google Colab Integration
- **Primary Platform**: All labs run in Google Colab with automatic setup
- **No Installation Required**: Students click "Open in Colab" links to access labs
- **Automatic Environment Setup**: First cell in each notebook handles dependency installation and data download
- **Cross-Compatibility Module**: `scripts_support/lab_cross_compatibility.py` handles environment detection and setup

### Lab Structure
- **30 Progressive Labs**: Lab01 through Lab30 covering comprehensive curriculum
- **Modular Design**: Each lab is self-contained with explanations, code, and exercises
- **Standardized Setup**: All labs use the same Colab setup pattern for consistency
- **Data Integration**: Automatic download of class data from S3 storage

## Documentation
For genomic analysis pipeline documentation, refer to the consolidated documentation in the bagg_website repository:

- **Documentation Hub**: `/home/lakishadavid/bagg_website/documentation/README.md`
- **Batch Processing**: `/home/lakishadavid/bagg_website/documentation/user_guides/batch_processing_workflow.md`
- **Genetic Similarity Implementation**: `/home/lakishadavid/bagg_website/documentation/developer/genetic_similarity_implementation.md`
- **Status Tracking Reference**: `/home/lakishadavid/bagg_website/documentation/developer/status_tracking_reference.md`

## Course Content Structure

### Module 1: Foundations (Labs 1-6)
- Introduction to genetic genealogy and IBD concepts
- Bonsai v3 architecture and data structures
- IBD file formats and statistics extraction
- Statistical models for relationship inference

### Module 2: Core Algorithms (Labs 7-12)
- PwLogLike class for likelihood calculations
- Age-based relationship modeling
- Pedigree data structures and up-node dictionaries
- Finding connection points in pedigrees

### Module 3: Pedigree Construction (Labs 13-18)
- Small pedigree structures and optimization
- Combining up-node dictionaries
- Merging pedigrees and incremental addition
- Advanced optimization techniques

### Module 4: System Integration (Labs 19-24)
- Caching mechanisms and error handling
- Pedigree rendering and result interpretation
- Handling special cases (twins, complex relationships)
- Real-world dataset processing

### Module 5: Advanced Applications (Labs 25-30)
- Performance tuning and scalability
- Custom prior probability models
- Integration with external tools
- End-to-end implementation projects

## Code Style Guidelines
- **Imports**: Standard library → third-party → project-specific, with blank lines between
- **Formatting**: 4-space indentation, PEP 8 compliant
- **Documentation**: Numpy-style docstrings for functions/classes with parameters and returns
- **Naming**: Snake case for functions/variables (`filter_segments`), uppercase for constants (`LOGFILE`)
- **Error Handling**: Try/except blocks with descriptive messages, exit on critical errors
- **Environment**: Load variables from dotenv early in execution
- **Logging**: Configure file/console logging with appropriate levels (INFO/DEBUG)
- **Function Structure**: Modular functions with clear purposes and descriptive names

## Local Development (Optional)

While designed for Google Colab, the repository supports local development:

### Prerequisites
- Ubuntu 24.04 (or WSL2 with Ubuntu 24.04)
- Python 3.12
- Poetry for dependency management

### Setup Commands
```bash
# Clone and setup
git clone https://github.com/lakishadavid/computational_genetic_genealogy.git
cd computational_genetic_genealogy
poetry config virtualenvs.in-project true
poetry install --no-root

# Run notebooks locally
poetry run jupyter lab
```

When working locally, ensure all scripts properly load environment variables from ~/.env file.

## Deployment

- **GitHub Pages**: Course website at https://lakishadavid.github.io/computational_genetic_genealogy/
- **Google Colab Integration**: Direct links from website to Colab notebooks
- **Automatic Setup**: No manual configuration required for students
- **Data Delivery**: Class data automatically downloaded from S3 storage during lab setup