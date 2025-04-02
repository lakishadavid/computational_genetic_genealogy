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
            labPath: '/jupyterlite/lab/index.html',
            storageKeyPrefix: 'genetic_genealogy_',
            notebookURLs: {
                'lab1': 'lab1/starter.ipynb',
                'lab2': 'lab2/starter.ipynb',
                'lab3': 'lab3/starter.ipynb'
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
        // Save lab to open in session storage
        sessionStorage.setItem('current_lab', labId);
        
        // Open JupyterLite in a new window or redirect
        const labUrl = `${this.options.labPath}?lab=${labId}`;
        
        // Check if we should open in new window or same window
        const openInNewWindow = true; // Could be an option
        
        if (openInNewWindow) {
            window.open(labUrl, 'jupyterlite', 'width=1200,height=800');
        } else {
            window.location.href = labUrl;
        }
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

    // Helper to clear progress data
    static clearProgressData(labId = null) {
        if (labId) {
            // Clear specific lab
            localStorage.removeItem(`genetic_genealogy_progress_${labId}`);
            localStorage.removeItem(`genetic_genealogy_notebook_${labId}`);
        } else {
            // Clear all labs
            for (let i = localStorage.length - 1; i >= 0; i--) {
                const key = localStorage.key(i);
                if (key.startsWith('genetic_genealogy_')) {
                    localStorage.removeItem(key);
                }
            }
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.jupyterLiteIntegration = new JupyterLiteIntegration();
});