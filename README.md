# Computational Genetic Genealogy Course

This repository contains the complete **Computational Genetic Genealogy** course materials, featuring 30 comprehensive lab notebooks designed to teach genetic genealogy analysis using the Bonsai v3 pedigree reconstruction system.

## 🚀 Quick Start with Google Colab

**No installation required!** All labs run directly in Google Colab with one-click setup.

### How to Use the Labs

1. **Visit the course website**: [Computational Genetic Genealogy Labs](https://lakishadavid.github.io/computational_genetic_genealogy/)

2. **Click "Open in Colab"** for any lab you want to explore

3. **Run the first cell** in the notebook - it will automatically:
   - Install all required dependencies (bioinformatics tools, Python packages)
   - Set up the analysis environment
   - Download essential class data from cloud storage
   - Configure utility functions for saving results

4. **Start learning!** Each lab is self-contained with explanations, code, and exercises.

## 📚 Course Structure

The course consists of **30 progressive labs** organized into 5 modules:

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

## 🔬 What You'll Learn

- **Genetic Genealogy Fundamentals**: DNA inheritance, IBD detection, relationship patterns
- **Bonsai v3 System**: Advanced pedigree reconstruction algorithms and data structures
- **Statistical Modeling**: Likelihood-based relationship inference with demographic data
- **Practical Applications**: Working with real genetic datasets and building analysis pipelines
- **Performance Optimization**: Scaling algorithms for large datasets

## 🛠 Technology Stack

- **Platform**: Google Colab (browser-based, no setup required)
- **Language**: Python 3.12 with scientific computing libraries
- **Core Libraries**: NumPy, Pandas, SciPy, Matplotlib, Seaborn, NetworkX
- **Specialized Tools**: Bonsai v3, IBD detection algorithms, genetic analysis utilities

## 📖 Course Materials

- **Interactive Labs**: 30 Jupyter notebooks with executable code and explanations
- **Datasets**: Real and simulated genetic data for hands-on analysis
- **Documentation**: Comprehensive course materials and reference guides
- **Visualizations**: Interactive plots and network diagrams

## 🎯 Target Audience

- **Researchers** in computational genetics and genealogy
- **Students** in bioinformatics, anthropology, or related fields
- **Data Scientists** interested in genetic analysis applications
- **Genealogists** wanting to understand computational methods

## 🏗 Local Development (Optional)

While the course is designed for Google Colab, you can also run it locally:

### Prerequisites
- Ubuntu 24.04 (or WSL2 with Ubuntu 24.04)
- Python 3.12
- Poetry for dependency management

### Setup
```bash
# Clone the repository
git clone https://github.com/lakishadavid/computational_genetic_genealogy.git
cd computational_genetic_genealogy

# Install dependencies
poetry config virtualenvs.in-project true
poetry install --no-root

# Run notebooks locally
poetry run jupyter lab
```

For detailed local setup instructions including bioinformatics tools, see the [Local Setup Guide](docs/local_setup.md).

## 📊 Course Data

The course uses a combination of:
- **Simulated genetic data** generated with ped-sim and msprime
- **Real genetic profiles** from the OpenSNP public dataset
- **Reference data** from the 1000 Genomes Project
- **Pedigree examples** demonstrating various relationship structures

All data is automatically downloaded when you run the labs in Google Colab.

## 👥 Contributing

We welcome contributions to improve the course materials:

1. **Report Issues**: Use GitHub Issues for bugs or suggestions
2. **Submit Pull Requests**: For fixes or enhancements
3. **Share Feedback**: Help us improve the learning experience

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Bonsai v3 System**: Developed by 23andMe Research Team
- **Course Development**: Dr. LaKisha David, University of Illinois Urbana-Champaign
- **Data Sources**: OpenSNP, 1000 Genomes Project
- **Tools Integration**: Various open-source genetic analysis tools

## 📞 Contact

- **Instructor**: Dr. LaKisha David
- **Institution**: Department of Anthropology, University of Illinois Urbana-Champaign
- **Course Website**: https://lakishadavid.github.io/computational_genetic_genealogy/
- **Repository**: https://github.com/lakishadavid/computational_genetic_genealogy

---

**Start your computational genetic genealogy journey today!** 
[Open the first lab in Google Colab →](https://colab.research.google.com/github/lakishadavid/computational_genetic_genealogy/blob/main/labs/Lab01_IBD_and_Genealogy_Intro.ipynb)