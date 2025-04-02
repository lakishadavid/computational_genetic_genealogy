# JupyterLite Integration: Three-Phase Implementation

This document summarizes the implementation of the three-phase approach for JupyterLite integration in the Computational Genetic Genealogy course.

## Phase 1: Basic JupyterLite Functionality with Notebook Access

The first phase focused on establishing the basic JupyterLite environment and ensuring reliable access to notebook files.

### Key Components:

1. **File Organization**:
   - Renamed notebook files from generic "starter.ipynb" to more specific names (e.g., lab1_exploring.ipynb)
   - Structured files in both root files/ directory and nested notebooks/lab*/ directories for flexibility

2. **URL Construction**:
   - Implemented multiple approaches to URL construction in `jupyterlite-integration.js`
   - Settled on direct links to files in the root files/ directory
   - Added fallback mechanism to just open the lab interface if direct links fail

3. **User Instructions**:
   - Added alert messages with navigation instructions
   - Updated HTML pages with clear directions for accessing notebooks

4. **Progress Tracking**:
   - Implemented localStorage-based progress tracking
   - Added visual progress indicators on course pages

### Implementation Details:

```javascript
// Direct file URL approach
const directFileUrl = `${this.options.labPath}lab/index.html?path=files/${filename}`;

// Fallback approach
const fallbackUrl = `${this.options.labPath}lab/`;
```

## Phase 2: Browser-Based Notebooks

The second phase focused on creating simplified, browser-friendly versions of the full notebooks that demonstrate key concepts.

### Key Components:

1. **Simplified Notebooks**:
   - Created browser-optimized versions of lab notebooks
   - Lab 1: Population genomic data exploration with visualizations
   - Lab 2: Processing raw DNA profiles with standardization and format conversion
   - Lab 3: Quality control and phasing with metrics and examples

2. **Integration with HTML Pages**:
   - Added buttons for launching JupyterLite notebooks
   - Included conceptual foundations to provide context
   - Added learning pathway navigation

3. **Styling and UX**:
   - Created dedicated CSS for JupyterLite integration
   - Implemented responsive design with dark mode support
   - Added status indicators for notebook progress

### Implementation Details:

The notebooks were placed in both the root files directory and nested directories:
```
/app/files/
  ├── lab1_exploring.ipynb
  ├── lab2_processing.ipynb
  ├── lab3_quality.ipynb
  └── notebooks/
      ├── lab1/
      │   └── lab1_exploring.ipynb
      ├── lab2/
      │   └── lab2_processing.ipynb
      └── lab3/
          └── lab3_quality.ipynb
```

## Phase 3: Seamless Integration between Online and Local Environments

The third phase implemented advanced features for data transfer between browser-based notebooks and local environment.

### Key Components:

1. **Data Export Functionality**:
   - Added ability to export notebooks from JupyterLite
   - Implemented export of analysis results
   - Used localStorage to persist exported data

2. **Data Import Capabilities**:
   - Created import interface for notebooks and data
   - Implemented file selection dialog
   - Added browser-to-local file transfer

3. **Transition Documentation**:
   - Added detailed instructions for transitioning to local environment
   - Included paths to corresponding full notebooks
   - Provided context about differences between environments

4. **State Persistence**:
   - Implemented localStorage for saving notebook state
   - Added progress tracking across sessions
   - Created storage usage monitoring

5. **Enhanced Browser-Local Workflow**:
   - Added workflow guidance in the UI
   - Implemented expandable controls section
   - Created consistent design language across environments

### Implementation Details:

```javascript
// Lab-specific configuration
labConfigs: {
    'lab1': {
        title: 'Exploring Genomic Data',
        filename: 'lab1_exploring.ipynb',
        dataSources: ['sample_data.csv'],
        localNotebook: '../../instructions/Lab1_Exploring_onekgenomes.ipynb'
    },
    'lab2': {
        title: 'Processing Raw DNA',
        filename: 'lab2_processing.ipynb',
        dataSources: ['raw_dna.txt'],
        localNotebook: '../../instructions/Lab2_Process_Raw_DNA_profile.ipynb'
    },
    'lab3': {
        title: 'Quality Control',
        filename: 'lab3_quality.ipynb',
        dataSources: ['qc_data.vcf'],
        localNotebook: '../../instructions/Lab3_Quality_Control.ipynb'
    }
}
```

## Technical Notes

### File Naming Convention

- Standardized naming: `lab{number}_{description}.ipynb`
- Examples: lab1_exploring.ipynb, lab2_processing.ipynb, lab3_quality.ipynb

### URL Structure

The integration supports multiple URL formats:
1. Direct file reference: `app/lab/index.html?path=files/lab1_exploring.ipynb`
2. Nested path reference: `app/lab/index.html?path=files/notebooks/lab1/lab1_exploring.ipynb`
3. Lab-only reference: `app/lab/` (requires manual navigation)

### Integration Functions

Key JavaScript functions for integration:
- `openJupyterLite(labId)`: Opens the notebook for the specified lab
- `exportData(dataType)`: Handles data export functionality
- `importData(dataType)`: Manages data import process
- `transitionToLocal(labId)`: Provides guidance for transitioning to local environment
- `checkProgress()`: Updates progress indicators
- `addIntegrationInfo()`: Adds Phase 3 integration controls to the page

## Troubleshooting

1. **404 Errors for Notebooks**:
   - Check that notebook files exist in both the root files/ directory and the nested directories
   - Verify JS is using the correct file paths that match actual filenames
   - Ensure the build.sh script correctly copies notebooks to the built app directory

2. **Integration Controls Not Appearing**:
   - Check that the JS and CSS files are properly loaded on the page
   - Verify that containers with the jupyterlite-container class exist
   - Check browser console for any JavaScript errors

3. **Data Export/Import Issues**:
   - Ensure localStorage is available in the browser
   - Check for size limitations (typically 5MB per origin)
   - Verify CORS settings if importing from external sources

## Future Enhancements

1. **Advanced Data Synchronization**:
   - Implement automatic synchronization between local and browser environments
   - Add cloud storage integration options
   
2. **Enhanced Progress Tracking**:
   - Add cell-level progress tracking
   - Implement achievement badges for completing specific exercises
   
3. **Collaborative Features**:
   - Add shared notebooks functionality
   - Implement comment/feedback mechanisms

4. **Offline Support**:
   - Enhance offline capabilities
   - Add service worker for better caching

## Resources

- [JupyterLite Documentation](https://jupyterlite.readthedocs.io/)
- [JupyterLab Documentation](https://jupyterlab.readthedocs.io/)
- [LocalStorage Documentation](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage)