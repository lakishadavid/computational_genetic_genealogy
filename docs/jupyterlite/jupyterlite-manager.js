/**
 * JupyterLite Manager for Computational Genetic Genealogy
 * Handles integration of JupyterLite with the course pages
 */

class JupyterLiteManager {
  constructor(options = {}) {
    this.options = Object.assign({
      iframe: '#jupyterlite-frame',
      labSelector: '.load-notebook', 
      saveSelector: '.save-progress',
      downloadSelector: '.download-notebook',
      statusSelector: '.jupyterlite-status',
      notebooksPath: '../jupyterlite/notebooks',
      datasetsPath: '../jupyterlite/datasets'
    }, options);
    
    this.iframe = document.querySelector(this.options.iframe);
    this.currentLabId = null;
    this.currentNotebook = null;
    this.isReady = false;
    
    this.initEventListeners();
    this.setupMessageHandling();
  }
  
  /**
   * Initialize event listeners for UI controls
   */
  initEventListeners() {
    // Lab notebook loading buttons
    document.querySelectorAll(this.options.labSelector).forEach(button => {
      button.addEventListener('click', (event) => {
        const notebookPath = event.target.dataset.notebook;
        if (notebookPath) {
          this.loadNotebook(notebookPath);
          this.currentNotebook = notebookPath;
          this.currentLabId = notebookPath.split('/')[0]; // Extract lab ID from path
        }
      });
    });
    
    // Save progress button
    document.querySelectorAll(this.options.saveSelector).forEach(button => {
      button.addEventListener('click', () => {
        this.saveProgress();
      });
    });
    
    // Download notebook button
    document.querySelectorAll(this.options.downloadSelector).forEach(button => {
      button.addEventListener('click', () => {
        this.downloadNotebook();
      });
    });
  }
  
  /**
   * Set up message handling for communication with JupyterLite iframe
   */
  setupMessageHandling() {
    window.addEventListener('message', (event) => {
      // Make sure message is from our JupyterLite iframe
      if (event.source !== this.iframe.contentWindow) return;
      
      const message = event.data;
      
      if (message.type === 'jupyterlite-ready') {
        this.isReady = true;
        this.updateStatus('JupyterLite is ready');
        this.restoreProgress();
      } else if (message.type === 'notebook-saved') {
        this.updateStatus('Notebook saved');
        this.storeProgressData(message.data);
      } else if (message.type === 'error') {
        this.updateStatus(`Error: ${message.error}`, 'error');
      }
    });
  }
  
  /**
   * Load a notebook into JupyterLite
   * @param {string} notebookPath - Path to the notebook file
   */
  loadNotebook(notebookPath) {
    if (!this.isReady) {
      this.updateStatus('JupyterLite is still loading...', 'warning');
      return;
    }
    
    const fullPath = `${this.options.notebooksPath}/${notebookPath}`;
    this.updateStatus(`Loading notebook: ${notebookPath}...`);
    
    this.iframe.contentWindow.postMessage({
      type: 'open-notebook',
      path: fullPath
    }, '*');
  }
  
  /**
   * Save the current notebook progress
   */
  saveProgress() {
    if (!this.currentNotebook) {
      this.updateStatus('No notebook is currently loaded', 'warning');
      return;
    }
    
    this.updateStatus('Saving progress...');
    this.iframe.contentWindow.postMessage({
      type: 'save-notebook'
    }, '*');
  }
  
  /**
   * Download the current notebook
   */
  downloadNotebook() {
    if (!this.currentNotebook) {
      this.updateStatus('No notebook is currently loaded', 'warning');
      return;
    }
    
    this.updateStatus('Preparing download...');
    this.iframe.contentWindow.postMessage({
      type: 'download-notebook'
    }, '*');
  }
  
  /**
   * Store progress data in localStorage
   * @param {Object} data - Notebook data to store
   */
  storeProgressData(data) {
    if (!this.currentLabId) return;
    
    try {
      // Get existing progress data
      const progressKey = `geneticGenealogy_progress_${this.currentLabId}`;
      const progressData = JSON.parse(localStorage.getItem(progressKey) || '{}');
      
      // Update with new data
      progressData.lastModified = new Date().toISOString();
      progressData.notebook = data;
      
      // Store updated data
      localStorage.setItem(progressKey, JSON.stringify(progressData));
      
      // Update course progress tracker
      this.updateCourseProgress(this.currentLabId, true);
      
    } catch (error) {
      console.error('Error storing progress:', error);
      this.updateStatus('Failed to store progress', 'error');
    }
  }
  
  /**
   * Restore previous progress if available
   */
  restoreProgress() {
    if (!this.currentLabId) return;
    
    try {
      const progressKey = `geneticGenealogy_progress_${this.currentLabId}`;
      const progressData = JSON.parse(localStorage.getItem(progressKey) || '{}');
      
      if (progressData.notebook) {
        this.updateStatus('Restoring previous progress...');
        this.iframe.contentWindow.postMessage({
          type: 'restore-notebook',
          data: progressData.notebook
        }, '*');
      }
    } catch (error) {
      console.error('Error restoring progress:', error);
      this.updateStatus('Failed to restore progress', 'error');
    }
  }
  
  /**
   * Update the course progress tracker
   * @param {string} labId - ID of the completed lab
   * @param {boolean} completed - Whether the lab was completed
   */
  updateCourseProgress(labId, completed) {
    try {
      const progressKey = 'geneticGenealogy_courseProgress';
      const courseProgress = JSON.parse(localStorage.getItem(progressKey) || '{}');
      
      courseProgress[labId] = {
        completed: completed,
        timestamp: new Date().toISOString()
      };
      
      localStorage.setItem(progressKey, JSON.stringify(courseProgress));
      
      // Trigger event for progress update
      window.dispatchEvent(new CustomEvent('course-progress-updated', {
        detail: { labId, completed }
      }));
      
    } catch (error) {
      console.error('Error updating course progress:', error);
    }
  }
  
  /**
   * Update status display
   * @param {string} message - Status message to display
   * @param {string} type - Message type (info, warning, error)
   */
  updateStatus(message, type = 'info') {
    const statusElement = document.querySelector(this.options.statusSelector);
    if (!statusElement) return;
    
    statusElement.textContent = message;
    statusElement.className = `jupyterlite-status status-${type}`;
    
    // Clear status after 5 seconds for info messages
    if (type === 'info') {
      setTimeout(() => {
        statusElement.textContent = '';
        statusElement.className = 'jupyterlite-status';
      }, 5000);
    }
  }
  
  /**
   * Check if browser supports required features
   * @returns {boolean} True if browser is compatible
   */
  static checkBrowserCompatibility() {
    const requiredFeatures = [
      'localStorage' in window,
      'indexedDB' in window,
      'Blob' in window,
      'Worker' in window,
      'WebAssembly' in window,
      'postMessage' in window
    ];
    
    return requiredFeatures.every(feature => feature === true);
  }
}

// Initialize on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  // Check browser compatibility
  if (!JupyterLiteManager.checkBrowserCompatibility()) {
    const containers = document.querySelectorAll('.jupyter-integration');
    containers.forEach(container => {
      container.innerHTML = `
        <div class="compatibility-warning">
          <h3>Browser Compatibility Issue</h3>
          <p>Your browser doesn't support all features required for JupyterLite.</p>
          <p>Please try using a modern browser like Chrome, Firefox, or Edge.</p>
        </div>
      `;
    });
    return;
  }
  
  // Initialize the manager
  window.jupyterliteManager = new JupyterLiteManager();
  
  // Add progress indicators to the sidebar
  updateProgressIndicators();
});

/**
 * Update progress indicators in the sidebar
 */
function updateProgressIndicators() {
  try {
    const progressKey = 'geneticGenealogy_courseProgress';
    const courseProgress = JSON.parse(localStorage.getItem(progressKey) || '{}');
    
    // Update sidebar lab items with progress indicators
    for (const labId in courseProgress) {
      if (courseProgress[labId].completed) {
        const labItems = document.querySelectorAll(`.sidebar-item[data-lab="${labId}"]`);
        labItems.forEach(item => {
          item.classList.add('completed');
          const indicator = document.createElement('span');
          indicator.className = 'completion-indicator';
          indicator.innerHTML = '✓';
          item.appendChild(indicator);
        });
      }
    }
  } catch (error) {
    console.error('Error updating progress indicators:', error);
  }
}