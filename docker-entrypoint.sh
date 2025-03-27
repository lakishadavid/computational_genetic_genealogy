#!/bin/bash
set -e

# Constants
USERNAME="ubuntu"
WORKSPACE_DIR="/home/ubuntu"
PROJECT_DIR="${WORKSPACE_DIR}/computational_genetic_genealogy"

echo "==============================================="
echo "🚀 Starting container initialization..."
echo "==============================================="

# Function to print section headers
section_header() {
    echo ""
    echo "==============================================="
    echo "🔷 $1"
    echo "==============================================="
}

# Check environment
section_header "Checking environment"
echo "Running as user: $(whoami)"
echo "Working directory: $PWD"
echo "Project directory: $PROJECT_DIR"

# Verify directory structure exists
section_header "Verifying directory structure"
for dir in "data" "results" "references" "utils"; do
    if [ -d "${PROJECT_DIR}/${dir}" ]; then
        echo "✅ Directory ${PROJECT_DIR}/${dir} exists"
    else
        echo "⚠️ Creating missing directory: ${PROJECT_DIR}/${dir}"
        mkdir -p "${PROJECT_DIR}/${dir}"
        chown -R ${USERNAME}:${USERNAME} "${PROJECT_DIR}/${dir}"
    fi
done

# Update environment variables if needed
section_header "Setting up environment variables"
# Load from .env if it exists
if [ -f "${WORKSPACE_DIR}/.env" ]; then
    echo "📄 Loading environment variables from ${WORKSPACE_DIR}/.env"
    set -a
    source "${WORKSPACE_DIR}/.env"
    set +a
else
    echo "⚠️ No .env file found, using default settings"
fi

# Verify critical tools are available
section_header "Verifying installed tools"
command -v python3 >/dev/null 2>&1 && echo "✅ Python3 is installed: $(python3 --version)"
command -v java >/dev/null 2>&1 && echo "✅ Java is installed: $(java -version 2>&1 | head -1)"
command -v R >/dev/null 2>&1 && echo "✅ R is installed: $(R --version | head -1)"
command -v bcftools >/dev/null 2>&1 && echo "✅ bcftools is installed: $(bcftools --version | head -1)"
command -v samtools >/dev/null 2>&1 && echo "✅ samtools is installed: $(samtools --version | head -1)"
command -v tabix >/dev/null 2>&1 && echo "✅ tabix is installed: $(tabix --version 2>&1 | head -1)"

# Verify custom genomic tools
section_header "Verifying genomic analysis tools"
UTILS_DIR="${PROJECT_DIR}/utils"

# Check JAR files
for jar in "beagle.27Feb25.75f.jar" "hap-ibd.jar" "refined-ibd.17Jan20.102.jar" "merge-ibd-segments.17Jan20.102.jar"; do
    if [ -f "${UTILS_DIR}/${jar}" ]; then
        echo "✅ ${jar} exists"
    else
        echo "❌ Missing JAR file: ${jar}"
    fi
done

# Check executables
for tool_dir in "${UTILS_DIR}/rfmix2" "${UTILS_DIR}/ibis" "${UTILS_DIR}/ped-sim"; do
    tool_name=$(basename "$tool_dir")
    if [ -d "${tool_dir}" ]; then
        echo "✅ ${tool_name} directory exists"
        
        # Check for the expected executable
        executable=""
        case "$tool_name" in
            "rfmix2") executable="${tool_dir}/rfmix" ;;
            "ibis") executable="${tool_dir}/ibis" ;;
            "ped-sim") executable="${tool_dir}/ped-sim" ;;
        esac
        
        if [ -n "$executable" ] && [ -x "$executable" ]; then
            echo "  ✅ ${tool_name} executable is available"
        else
            echo "  ❌ ${tool_name} executable is missing or not executable"
        fi
    else
        echo "❌ Missing tool directory: ${tool_name}"
    fi
done

# Check for PLINK2
if [ -x "${UTILS_DIR}/plink2" ]; then
    echo "✅ PLINK2 is available"
else
    echo "❌ PLINK2 is missing or not executable"
fi

# Check BonsaiTree
if [ -d "${UTILS_DIR}/bonsaitree" ]; then
    echo "✅ BonsaiTree repository exists"
else
    echo "❌ BonsaiTree repository is missing"
fi

section_header "Initialization complete!"
echo "Your development container is ready!"
echo "Run your commands or use the provided scripts in the computational_genetic_genealogy directory."
echo ""
echo "📄 Project structure:"
echo "- Data directory: ${PROJECT_DIR}/data"
echo "- Results directory: ${PROJECT_DIR}/results"
echo "- References directory: ${PROJECT_DIR}/references"
echo "- Utils directory: ${UTILS_DIR}"
echo ""

# Execute the command passed to docker run, or fall back to bash
if [ $# -eq 0 ]; then
    echo "📢 No command specified, starting bash..."
    exec bash
else
    echo "📢 Executing provided command: $@"
    exec "$@"
fi