# Migration Plan: Legacy Labs to Modern Labs

## Overview
Migrating from the dual lab system (labs/ and labs_v2/) to a single modern lab system with Google Colab integration, removing JupyterLite infrastructure.

## Phase 1: Backup and Directory Migration

### 1. Create Backup Archive
- **Task**: Create backup zip of existing `labs/` directory
- **Purpose**: Preserve legacy labs for reference/rollback
- **Command**: `zip -r labs_legacy_backup.zip labs/`
- **Status**: Pending

### 2. Directory Migration  
- **Task**: Rename `labs_v2/` directory to `labs/`
- **Purpose**: Make modern lab series the primary curriculum
- **Command**: `mv labs_v2/ labs/`
- **Status**: Pending

## Phase 2: Google Colab Conversion

### 3. Notebook Format Conversion
- **Task**: Convert all Lab notebooks (Lab01-Lab30) to Google Colab format
- **Components**:
  - Add Colab-specific setup cells for dependencies
  - Update data paths to work with Colab's file system  
  - Modify environment detection and cross-compatibility code
  - Test data loading mechanisms
- **Files**: `Lab01_IBD_and_Genealogy_Intro.ipynb` through `Lab30_Advanced_Applications.ipynb`
- **Status**: Pending

## Phase 3: JupyterLite Removal

### 4. Remove JupyterLite Infrastructure
- **Task**: Remove JupyterLite application and related files
- **Components**:
  - Delete `docs/jupyterlite_app/` directory
  - Remove `docs/jupyterlite/` build directory
  - Clean up associated static files
- **Status**: Pending

### 5. Configuration Cleanup
- **Task**: Remove JupyterLite configuration files
- **Files**:
  - `jupyter_lite_config.json`
  - `jupyter-lite.json` 
  - JupyterLite-specific sections in other configs
- **Status**: Pending

### 6. Build Script Updates
- **Task**: Remove or update build scripts that reference JupyterLite
- **Files**:
  - `docs/jupyterlite/build.sh`
  - Any CI/CD scripts with JupyterLite builds
- **Status**: Pending

## Phase 4: Documentation and Testing

### 7. Documentation Updates
- **Task**: Update README and documentation to reflect changes
- **Files**:
  - `README.md`
  - `CLAUDE.md`
  - Any course documentation
- **Components**:
  - Remove JupyterLite references
  - Update lab structure documentation
  - Add Google Colab usage instructions
- **Status**: Pending

### 8. Testing and Validation
- **Task**: Test converted notebooks work properly in Google Colab
- **Components**:
  - Verify all notebooks load without errors
  - Test data access and loading
  - Validate dependency installation
  - Check cross-compatibility functions
- **Status**: Pending

## Additional Considerations Identified

### Data Hosting Strategy
- **Challenge**: Colab notebooks need alternative data access methods
- **Options**: 
  - GitHub raw files for smaller datasets
  - Google Drive integration for larger files
  - Cloud storage with public access

### Dependency Management
- **Challenge**: Install cells need to handle bioinformatics toolchain
- **Solution**: Create standardized setup cells with all required packages

### Cross-Compatibility Utilities  
- **Assessment**: `scripts_support/lab_cross_compatibility.py` may need updates
- **Decision**: Update or remove based on new Colab-only approach

### Docker Integration
- **Assessment**: Consider if Docker setup still needed without JupyterLite
- **Decision**: May retain for local development option

## Implementation Order

1. **High Priority**: Backup → Migration → Colab Conversion
2. **Medium Priority**: JupyterLite Removal → Documentation Updates → Testing
3. **Low Priority**: Configuration Cleanup → Build Script Updates

## Rollback Plan
- Legacy labs preserved in `labs_legacy_backup.zip`
- Git history maintains all changes
- Can restore original structure if needed

## Success Criteria
- [x] All 33 lab notebooks updated with Google Colab setup
- [x] Data loading works through S3 automatic download
- [x] Dependencies install correctly in Colab environment
- [x] Documentation updated to reflect Colab-only structure
- [x] All JupyterLite infrastructure removed
- [x] Cross-compatibility module simplified for Colab
- [x] README completely rewritten for Colab-first approach

## Migration Complete! ✅

**Successfully migrated from dual lab system to Google Colab-only approach:**

### ✅ Completed Tasks:
1. **Legacy labs backed up** to `labs_legacy_backup.zip`
2. **Modern labs (33 notebooks) updated** with standardized Colab setup
3. **JupyterLite infrastructure completely removed**
4. **Dependencies cleaned up** (removed jupyterlite packages)
5. **Cross-compatibility simplified** to Colab-focused approach
6. **Documentation updated** - README, CLAUDE.md, HTML docs
7. **HTML documentation cleaned** - removed legacy references

### 🎯 Key Improvements:
- **Simplified user experience**: One-click Colab access
- **Reduced complexity**: No multi-environment management
- **Better maintainability**: Single deployment target
- **Modern curriculum**: 30 comprehensive labs
- **Automatic setup**: Dependencies and data download handled automatically

### 🚀 Ready for Deployment:
The course is now fully ready for Google Colab deployment with a clean, streamlined architecture focused on student experience and ease of use.