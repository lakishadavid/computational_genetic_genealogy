"""
Legacy cross-compatibility module - now simplified since all labs are self-contained.
This module is kept for backward compatibility but is no longer required.
All new labs use self-contained setup cells.
"""

import os
import pandas as pd
from IPython.display import display, HTML

def is_colab():
    """Check if running in Google Colab (legacy function)"""
    try:
        import google.colab
        return True
    except ImportError:
        return False

def setup_environment():
    """Simple environment setup (legacy function)"""
    if is_colab():
        return "/content/class_data", "/content/results"
    else:
        return "class_data", "results"

def save_results(dataframe, filename, description="results"):
    """Save results with download option (legacy function)"""
    DATA_DIR, RESULTS_DIR = setup_environment()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    full_path = os.path.join(RESULTS_DIR, filename)
    dataframe.to_csv(full_path, index=False)
    
    if is_colab():
        display(HTML(f"""
        <div style="padding: 10px; background-color: #e3f2fd; border-left: 4px solid #2196f3; margin: 10px 0;">
            <p><strong>💾 Results saved!</strong> To download: 
            <code>from google.colab import files; files.download('{full_path}')</code></p>
        </div>
        """))
    
    return full_path

def save_plot(plt, filename, description="plot"):
    """Save a plot with download option (legacy function)"""
    DATA_DIR, RESULTS_DIR = setup_environment()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    full_path = os.path.join(RESULTS_DIR, filename)
    plt.savefig(full_path, dpi=300, bbox_inches='tight')
    plt.show()
    
    if is_colab():
        display(HTML(f"""
        <div style="padding: 10px; background-color: #e8f5e8; border-left: 4px solid #4caf50; margin: 10px 0;">
            <p><strong>📊 Plot saved!</strong> To download: 
            <code>from google.colab import files; files.download('{full_path}')</code></p>
        </div>
        """))
    
    return full_path

# Legacy functions - no longer used in new self-contained notebooks
def install_dependencies():
    """Legacy function - dependencies now handled in notebook setup cells"""
    pass

def download_class_data():
    """Legacy function - data download now handled in notebook setup cells"""
    pass

def colab_setup():
    """Legacy function - setup now handled in notebook setup cells"""
    pass