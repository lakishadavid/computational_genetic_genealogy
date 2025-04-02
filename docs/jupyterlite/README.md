# JupyterLite for Computational Genetic Genealogy

This directory contains the JupyterLite integration for the Computational Genetic Genealogy course. JupyterLite provides a browser-based execution environment for Jupyter notebooks, eliminating the need for local installations or Docker.

## Implementation Details

### Structure

- `/jupyterlite/` - Main directory for JupyterLite implementation
  - `/jupyterlite/notebooks/` - Pre-configured notebooks for each lab
  - `/jupyterlite/datasets/` - Lightweight datasets for browser use
  - `/jupyterlite/lab/` - JupyterLite application files (to be added)
  - `/jupyterlite/jupyterlite-integration.css` - Styling for the integration
  - `/jupyterlite/jupyterlite-manager.js` - JavaScript for managing JupyterLite in the course

### Setup Instructions

To deploy JupyterLite for the course:

1. Install JupyterLite CLI tool:
   ```bash
   pip install jupyterlite-core
   pip install jupyterlite-pyodide-kernel
   pip install jupyterlite-javascript-kernel
   ```

2. Build the JupyterLite environment:
   ```bash
   cd /path/to/computational_genetic_genealogy/docs
   jupyter lite build
   ```

3. This will create the necessary files in the `jupyterlite/lab` directory.

4. Customize the configuration in `jupyter-lite.json` as needed.

### Integration with Course Pages

The JupyterLite environment is integrated into the course pages using:

1. CSS and JavaScript additions in the HTML header:
   ```html
   <link rel="stylesheet" href="../jupyterlite/jupyterlite-integration.css">
   <script src="../jupyterlite/jupyterlite-manager.js" defer></script>
   ```

2. JupyterLite iframe and control buttons:
   ```html
   <div class="jupyter-integration">
     <div class="jupyter-buttons">
       <button class="load-notebook" data-notebook="lab1/starter.ipynb">Load Notebook</button>
       <button class="save-progress">Save Progress</button>
       <button class="download-notebook">Download Notebook</button>
     </div>
     <iframe id="jupyterlite-frame" src="../jupyterlite/lab/index.html" width="100%" height="600px"></iframe>
   </div>
   ```

### Data Persistence

The JupyterLite integration uses browser storage for data persistence:

- IndexedDB for notebook content and execution results
- LocalStorage for progress tracking and metadata

Users can download their work at any time using the Download button.

## Adapting Notebooks

When adapting notebooks for JupyterLite:

1. Replace filesystem operations with browser-compatible alternatives
2. Use `pyodide.http` for fetching remote data instead of direct downloads
3. Simplify heavy computational tasks for browser execution
4. Add proper error handling for browser environment limitations

Example adaptation:
```python
# Original code (filesystem-based)
import os
sample_df = pd.read_csv(os.path.join(data_directory, "sample_file.csv"))

# JupyterLite adaptation
from pyodide.http import open_url
url = "../datasets/sample_file.csv"
with open_url(url) as f:
    sample_df = pd.read_csv(f)
```

## Known Limitations

- Maximum storage limit of 2-5GB depending on browser
- Limited support for C-based Python extensions
- Computational performance constraints compared to native execution
- No access to local filesystem or command-line tools
- Not all Python packages are available in Pyodide

## Resources

- [JupyterLite Documentation](https://jupyterlite.readthedocs.io/)
- [Pyodide Documentation](https://pyodide.org/en/stable/)
- [IndexedDB API](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API)