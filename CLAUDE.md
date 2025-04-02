# Computational Genetic Genealogy Guidelines

## Build/Run Commands
- Poetry: `poetry config virtualenvs.in-project true` (configure), `poetry install --no-root` (install dependencies)
- Run scripts: `poetry run python -m scripts_work.<script_name> [arguments]`
- Run specific script: `poetry run python -m scripts_work.run_ibd_detection --algorithm IBIS`
- Run notebook: Navigate to instruction directory and execute Jupyter notebooks
- JupyterLite build: `cd docs/jupyterlite && ./build.sh`
- Test JupyterLite: `cd docs/jupyterlite/app && poetry run python -m http.server 8000`

## JupyterLite Configuration and Deployment

### Required Configuration Files
For proper JupyterLite functionality, ensure these configuration files exist:
1. `/docs/jupyterlite/jupyter_lite_config.json` - Main build configuration
2. `/docs/jupyterlite/jupyter-lite.json` - Application settings

### Critical HTML Configuration
JupyterLite requires proper configuration in HTML files, particularly:
- The configuration section in `app/lab/index.html` must contain a valid JSON object (not empty `{}`)
- The main `app/index.html` file should have correct redirection settings

### Common Issues and Solutions
1. **Blank screens on GitHub Pages**: Usually caused by:
   - Missing configuration in HTML files - The `jupyter-config-data` script section needs valid config
   - Missing or incorrectly named notebook files - Check for case sensitivity in filenames
   - Path reference errors - Ensure paths correctly reference the GitHub Pages URL structure

2. **Manual fixes (when needed)**: 
   - Edit `app/lab/index.html` to contain proper configuration in the `jupyter-config-data` script tag
   - Update app name in both HTML files and configuration files for consistent branding
   - Create lowercase symlinks if your JavaScript is looking for different filenames than actual files

3. **Debugging process**:
   - Check browser console for errors (F12)
   - Verify configuration objects are properly formatted JSON
   - Ensure all required extensions are properly listed in configuration
   - Test locally before deploying to GitHub Pages

### Build Process
The `build.sh` script handles proper setup by:
1. Building the JupyterLite application with configuration
2. Copying notebooks from the labs directory
3. Setting up class data access
4. Fixing HTML titles and configurations
5. Creating symlinks for more reliable notebook access

### Directory Structure
```
docs/jupyterlite/
├── app/               # Built JupyterLite application
│   ├── files/         # Notebook files directory
│   │   ├── Lab*.ipynb # Original notebook files
│   │   └── lab*.ipynb # Lowercase symlinks
│   └── lab/           # JupyterLab interface
├── build.sh           # Build script
├── jupyter_lite_config.json # Build configuration
└── jupyter-lite.json  # Application settings
```

## Code Style Guidelines
- **Imports**: Standard library → third-party → project-specific, with blank lines between
- **Formatting**: 4-space indentation, PEP 8 compliant
- **Documentation**: Numpy-style docstrings for functions/classes with parameters and returns
- **Naming**: Snake case for functions/variables (`filter_segments`), uppercase for constants (`LOGFILE`)
- **Error Handling**: Try/except blocks with descriptive messages, exit on critical errors
- **Environment**: Load variables from dotenv early in execution
- **Logging**: Configure file/console logging with appropriate levels (INFO/DEBUG)
- **Function Structure**: Modular functions with clear purposes and descriptive names

When working in this repo, ensure all scripts properly load environment variables from ~/.env file.