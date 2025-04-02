/**
 * JupyterLite Integration
 * This script handles the integration of JupyterLite within the Computational Genetic Genealogy course.
 */

class JupyterLiteIntegration {
    constructor(options = {}) {
        // Default options
        this.options = Object.assign({
            coursePageSelector: '.course-content',
            jupyterButtonClass: 'open-jupyterlite',
            jupyterContainerClass: 'jupyterlite-container',
            labPath: '/computational_genetic_genealogy/jupyterlite/app/',
            storageKeyPrefix: 'genetic_genealogy_',
            notebookPath: 'files/notebooks',
            notebookURLs: {
                'lab1': 'lab1/lab1_exploring.ipynb',
                'lab2': 'lab2/lab2_processing.ipynb',
                'lab3': 'lab3/lab3_quality.ipynb'
            }
        }, options);

        // Initialize integration
        this.init();
    }

    init() {
        // Look for integration buttons
        const buttons = document.querySelectorAll(`.${this.options.jupyterButtonClass}`);
        
        if (buttons.length === 0) {
            console.log('No JupyterLite integration buttons found on this page.');
            return;
        }
        
        // Add click event to each button
        buttons.forEach(button => {
            const labId = button.dataset.lab || 'lab1';
            
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.openJupyterLite(labId);
            });
        });

        // Check for progress data
        this.checkProgress();
    }

    openJupyterLite(labId) {
        // Get the unique notebook path for this specific lab
        const notebookPath = this.options.notebookURLs[labId];
        
        // OPTION 1: Try to open the notebook with a direct path
        // This approach may fail in some environments, which is why we have fallbacks
        const directUrl = `${this.options.labPath}lab/index.html?path=${this.options.notebookPath}/${notebookPath}`;
        
        // OPTION 2: Fallback approach - just open the lab interface
        // This will always work, but requires manual navigation to the notebook
        const fallbackUrl = `${this.options.labPath}lab/`;
        
        // Use the fallback URL which has proven more reliable
        const labUrl = fallbackUrl;
        
        console.log(`Opening JupyterLite for ${labId} at URL: ${labUrl}`);
        
        // Show navigation instructions in an alert
        const navPath = notebookPath.split('/')[1];
        const message = `Opening JupyterLite for ${labId}.\n\nPlease navigate to:\nFiles > notebooks > ${labId} > ${navPath}\n\nOr look for ${navPath} in the root files directory.`;
        alert(message);
        
        // Open in new window
        window.open(labUrl, 'jupyterlite', 'width=1200,height=800');
    }

    checkProgress() {
        // Look for progress indicators on the page
        const progressIndicators = document.querySelectorAll('.lab-progress');
        
        if (progressIndicators.length === 0) {
            return;
        }
        
        // Update progress for each lab
        progressIndicators.forEach(indicator => {
            const labId = indicator.dataset.lab;
            const progressKey = `${this.options.storageKeyPrefix}progress_${labId}`;
            
            // Get progress from localStorage
            let progress = localStorage.getItem(progressKey);
            
            if (progress) {
                try {
                    progress = JSON.parse(progress);
                    
                    // Update indicator
                    const percentComplete = progress.percent || 0;
                    const lastUpdated = progress.lastUpdated ? new Date(progress.lastUpdated).toLocaleDateString() : 'Never';
                    
                    // Create or update progress display
                    let progressBar = indicator.querySelector('.progress-bar');
                    let progressInfo = indicator.querySelector('.progress-info');
                    
                    if (!progressBar) {
                        progressBar = document.createElement('div');
                        progressBar.className = 'progress-bar';
                        indicator.appendChild(progressBar);
                    }
                    
                    if (!progressInfo) {
                        progressInfo = document.createElement('div');
                        progressInfo.className = 'progress-info';
                        indicator.appendChild(progressInfo);
                    }
                    
                    // Update elements
                    progressBar.style.width = `${percentComplete}%`;
                    progressBar.setAttribute('aria-valuenow', percentComplete);
                    progressInfo.textContent = `${percentComplete}% complete (Last worked on: ${lastUpdated})`;
                    
                    // Add class if completed
                    if (percentComplete >= 100) {
                        indicator.classList.add('completed');
                    } else {
                        indicator.classList.remove('completed');
                    }
                } catch (e) {
                    console.error('Error parsing progress data:', e);
                }
            } else {
                // No progress yet
                indicator.innerHTML = '<div class="no-progress">Not started yet</div>';
            }
        });
    }

    // Helper to estimate storage usage
    static getStorageUsage() {
        let total = 0;
        
        // Count localStorage usage
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key.startsWith('genetic_genealogy_')) {
                const value = localStorage.getItem(key);
                total += (key.length + value.length) * 2; // Approx bytes for UTF-16
            }
        }
        
        // Return in KB
        return Math.round(total / 1024);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.jupyterLiteIntegration = new JupyterLiteIntegration();
});