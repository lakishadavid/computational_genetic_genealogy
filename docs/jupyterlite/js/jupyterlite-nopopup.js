/**
 * JupyterLite Integration (No Popup Version)
 * This script handles the integration of JupyterLite within the Computational Genetic Genealogy course.
 * 
 * IMPORTANT: This version has NO POPUPS as explicitly requested.
 */

class JupyterLiteIntegration {
    constructor(options = {}) {
        // Default options
        this.options = Object.assign({
            coursePageSelector: '.course-content',
            jupyterButtonClass: 'open-jupyterlite',
            jupyterContainerClass: 'jupyterlite-container',
            labPath: '../jupyterlite/app/',  // Relative path from the textbook directory
            storageKeyPrefix: 'genetic_genealogy_',
            // Lab-specific configuration
            labConfigs: {
                'lab1': {
                    title: 'Exploring Genomic Data',
                    filename: 'lab1_exploring.ipynb'
                },
                'lab2': {
                    title: 'Processing Raw DNA',
                    filename: 'lab2_processing.ipynb'
                },
                'lab3': {
                    title: 'Quality Control',
                    filename: 'lab3_quality.ipynb'
                }
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
        // Get lab configuration
        const labConfig = this.options.labConfigs[labId] || {};
        const filename = labConfig.filename || `${labId}_exploring.ipynb`;
        
        // OPTION 1: Direct link to file in root files directory (most reliable)
        const directFileUrl = `${this.options.labPath}lab/index.html?path=files/${filename}`;
        
        // OPTION 2: Direct link to file in nested notebooks directory
        const nestedFileUrl = `${this.options.labPath}lab/index.html?path=files/notebooks/${labId}/${filename}`;
        
        // OPTION 3: Just open the lab interface (fallback)
        const fallbackUrl = `${this.options.labPath}lab/`;
        
        // Use the direct URL as our primary approach - NO POPUPS
        const labUrl = directFileUrl;
        
        console.log(`Opening JupyterLite for ${labId} at URL: ${labUrl}`);
        
        // Open in new window - NO POPUPS
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