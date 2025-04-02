# JupyterLite Integration for Computational Genetic Genealogy

This directory contains the JupyterLite integration for the Computational Genetic Genealogy course. JupyterLite is a lightweight, browser-based version of Jupyter notebooks that allows students to run Python code directly in their browsers without the need for installation or server setup.

## Directory Structure

- `css/` - CSS stylesheets for JupyterLite integration
- `js/` - JavaScript files for JupyterLite integration
- `lab/` - Container page for JupyterLite iframe
- `notebooks/` - Jupyter notebooks for each lab
  - `lab1/` - Lab 1: Exploring Genomic Data
  - `lab2/` - Lab 2: Processing Raw DNA Profiles
  - `lab3/` - Lab 3: Quality Control

## Implementation Notes

This implementation uses a CDN-based approach, embedding a JupyterLite instance from a public CDN rather than building and hosting JupyterLite locally. This approach has several advantages:

1. No build process required
2. Always up-to-date with the latest JupyterLite version
3. Reduced server storage requirements
4. Faster loading times

## Local Development

If you need to modify the notebooks, you can:

1. Edit the notebook files directly in the `notebooks/` directory
2. Test them by loading them from the course pages
3. Or test locally using a standard Jupyter Notebook installation

## Browser Support

JupyterLite works best in modern browsers:
- Chrome/Chromium-based browsers
- Firefox
- Safari 14 or newer
- Edge (Chromium-based)

## Data Persistence

JupyterLite uses browser-based storage (IndexedDB and localStorage) to maintain notebook state and user data between sessions. This allows students to:

1. Save their progress between lab sessions
2. Download their completed notebooks
3. Transfer data between sequential labs

## Limitations

Note that browser-based JupyterLite has some limitations compared to full Jupyter:

1. Limited memory and processing power
2. Cannot install arbitrary Python packages (only pre-built Pyodide packages)
3. No access to local file system beyond what the browser allows
4. Cannot run system commands

For more complex labs requiring full computational resources, students should still use the Docker environment or local installation.

## Future Improvements

Planned enhancements:
- Add more labs beyond the initial three
- Create specialized extensions for genetic data visualization
- Improve cross-notebook data persistence
- Add automated testing functionality