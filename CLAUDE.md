# Computational Genetic Genealogy Guidelines

## Build/Run Commands
- Poetry: `poetry config virtualenvs.in-project true` (configure), `poetry install --no-root` (install dependencies)
- Run scripts: `poetry run python -m scripts_work.<script_name> [arguments]`
- Run specific script: `poetry run python -m scripts_work.run_ibd_detection --algorithm IBIS`
- Run notebook: Navigate to instruction directory and execute Jupyter notebooks
- JupyterLite build: `cd docs/jupyterlite && poetry run jupyter lite build --output-dir=app`
- Test JupyterLite: `cd docs/jupyterlite/app && python -m http.server 8000`

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