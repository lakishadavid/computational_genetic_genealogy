/**
 * JupyterLite Integration
 * This script handles the integration of JupyterLite within the Computational Genetic Genealogy course.
 * 
 * This version includes Phase 3 features:
 * - Data export functionality from JupyterLite
 * - Data import capabilities
 * - State persistence between sessions
 * - Enhanced browser-local workflow
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
                    filename: 'Lab1_Exploring_onekgenomes.ipynb',
                    dataSources: ['sample_data.csv'],
                    localNotebook: '../../instructions/Lab1_Exploring_onekgenomes.ipynb'
                },
                'lab2': {
                    title: 'Processing Raw DNA',
                    filename: 'Lab2_Process_Raw_DNA_profile.ipynb',
                    dataSources: ['raw_dna.txt'],
                    localNotebook: '../../instructions/Lab2_Process_Raw_DNA_profile.ipynb'
                },
                'lab3': {
                    title: 'Quality Control',
                    filename: 'Lab3_Quality_Control.ipynb',
                    dataSources: ['qc_data.vcf'],
                    localNotebook: '../../instructions/Lab3_Quality_Control.ipynb'
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

        // Add data export/import buttons if they exist
        this.setupDataTransferButtons();
        
        // Check for progress data
        this.checkProgress();
        
        // Add integration info to the page if container exists
        this.addIntegrationInfo();
    }

    openJupyterLite(labId) {
        // Get lab configuration
        const labConfig = this.options.labConfigs[labId] || {};
        const filename = labConfig.filename || `${labId}_exploring.ipynb`;
        
        // Direct path to the file in the root files directory
        const directFileUrl = `${this.options.labPath}lab/index.html?path=files/${filename}`;
        
        // Use the direct file URL
        const labUrl = directFileUrl;
        
        console.log(`Opening JupyterLite for ${labId} at URL: ${labUrl}`);
        
        // Save the last accessed lab for persistence
        localStorage.setItem(`${this.options.storageKeyPrefix}last_lab`, labId);
        
        // Open in new window
        const jupyterWindow = window.open(labUrl, 'jupyterlite', 'width=1200,height=800');
        
        // Store reference to the window for communication
        this.jupyterWindow = jupyterWindow;
    }

    setupDataTransferButtons() {
        // Set up export buttons
        const exportButtons = document.querySelectorAll('.export-jupyter-data');
        exportButtons.forEach(button => {
            const dataType = button.dataset.type || 'notebook';
            button.addEventListener('click', () => this.exportData(dataType));
        });
        
        // Set up import buttons
        const importButtons = document.querySelectorAll('.import-jupyter-data');
        importButtons.forEach(button => {
            const dataType = button.dataset.type || 'notebook';
            button.addEventListener('click', () => this.importData(dataType));
        });
        
        // Set up transition to local environment buttons
        const transitionButtons = document.querySelectorAll('.transition-to-local');
        transitionButtons.forEach(button => {
            const labId = button.dataset.lab || 'lab1';
            button.addEventListener('click', () => this.transitionToLocal(labId));
        });
    }

    exportData(dataType = 'notebook') {
        // Create an invisible file input element
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = dataType === 'notebook' ? '.ipynb' : '.csv,.txt,.json';
        fileInput.style.display = 'none';
        document.body.appendChild(fileInput);
        
        // Handle file selection
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = (event) => {
                const content = event.target.result;
                
                // Store in localStorage for later access
                const key = `${this.options.storageKeyPrefix}${dataType}_${file.name}`;
                localStorage.setItem(key, content);
                
                alert(`Successfully exported ${file.name}. This data will be available when you return to JupyterLite.`);
            };
            reader.readAsText(file);
            
            // Clean up
            document.body.removeChild(fileInput);
        });
        
        // Trigger file selection
        fileInput.click();
    }

    importData(dataType = 'notebook') {
        // Get last accessed lab
        const lastLab = localStorage.getItem(`${this.options.storageKeyPrefix}last_lab`) || 'lab1';
        const labConfig = this.options.labConfigs[lastLab] || {};
        
        // List available exports
        const availableData = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key.startsWith(`${this.options.storageKeyPrefix}${dataType}_`)) {
                availableData.push(key.replace(`${this.options.storageKeyPrefix}${dataType}_`, ''));
            }
        }
        
        if (availableData.length === 0) {
            alert(`No ${dataType} data available for import. Please export some data first.`);
            return;
        }
        
        // Create simple selection dialog
        const dataOptions = availableData.map(name => 
            `<option value="${name}">${name}</option>`
        ).join('');
        
        const selectHtml = `
            <div style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:9999;">
                <div style="background:white;padding:20px;border-radius:5px;max-width:500px;">
                    <h3>Import ${dataType}</h3>
                    <p>Select data to import:</p>
                    <select id="data-import-select" style="width:100%;margin-bottom:15px;padding:5px;">
                        ${dataOptions}
                    </select>
                    <div style="display:flex;justify-content:space-between;">
                        <button id="data-import-cancel" style="padding:5px 15px;">Cancel</button>
                        <button id="data-import-confirm" style="padding:5px 15px;background:#4CAF50;color:white;border:none;">Import</button>
                    </div>
                </div>
            </div>
        `;
        
        // Add dialog to page
        const dialogContainer = document.createElement('div');
        dialogContainer.innerHTML = selectHtml;
        document.body.appendChild(dialogContainer);
        
        // Handle dialog actions
        document.getElementById('data-import-cancel').addEventListener('click', () => {
            document.body.removeChild(dialogContainer);
        });
        
        document.getElementById('data-import-confirm').addEventListener('click', () => {
            const selectedName = document.getElementById('data-import-select').value;
            const key = `${this.options.storageKeyPrefix}${dataType}_${selectedName}`;
            const content = localStorage.getItem(key);
            
            // Trigger download of the file
            const blob = new Blob([content], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = selectedName;
            a.click();
            
            // Clean up
            URL.revokeObjectURL(url);
            document.body.removeChild(dialogContainer);
            
            alert(`${selectedName} has been imported. Save this file to your local environment.`);
        });
    }

    transitionToLocal(labId) {
        const labConfig = this.options.labConfigs[labId] || {};
        const localNotebookPath = labConfig.localNotebook;
        
        if (!localNotebookPath) {
            console.log('No local notebook path configured for this lab.');
            return;
        }
        
        // Log transition information
        console.log(`Transitioning to local environment: ${localNotebookPath}`);
        
        // Open the local notebook path in a new tab if possible
        window.open(localNotebookPath, '_blank');
    }

    addIntegrationInfo() {
        const containers = document.querySelectorAll(`.${this.options.jupyterContainerClass}`);
        
        containers.forEach(container => {
            // Find or create integration info section
            let infoSection = container.querySelector('.jupyterlite-integration-info');
            
            if (!infoSection) {
                infoSection = document.createElement('div');
                infoSection.className = 'jupyterlite-integration-info';
                
                // Create Phase 3 interface
                infoSection.innerHTML = `
                    <div class="integration-controls">
                        <details>
                            <summary>Data Transfer & Environment Integration</summary>
                            <div class="data-transfer-section">
                                <h4>Notebook Data</h4>
                                <div class="button-group">
                                    <button class="export-jupyter-data" data-type="notebook">Export Notebook</button>
                                    <button class="import-jupyter-data" data-type="notebook">Import Notebook</button>
                                </div>
                                
                                <h4>Analysis Results</h4>
                                <div class="button-group">
                                    <button class="export-jupyter-data" data-type="data">Export Data</button>
                                    <button class="import-jupyter-data" data-type="data">Import Data</button>
                                </div>
                                
                                <h4>Transition to Local Environment</h4>
                                <p>When you're ready to move to the full-featured local environment:</p>
                                <button class="transition-to-local" data-lab="${container.closest('[data-lab]')?.dataset.lab || 'lab1'}">
                                    Transition to Local Environment
                                </button>
                                
                                <div class="integration-storage">
                                    <p>Browser storage usage: ${JupyterLiteIntegration.getStorageUsage()} KB</p>
                                </div>
                            </div>
                        </details>
                    </div>
                `;
                
                // Add to container
                container.appendChild(infoSection);
                
                // Set up event listeners for the new buttons
                this.setupDataTransferButtons();
            }
        });
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