#!/bin/bash

# Define directories and Beagle jar path
RESULTS_DIR=$1
REFERENCES_DIR=$2
UTILS_DIR=$3
BEAGLE_JAR=$4

PHASED_DIR="${RESULTS_DIR}/phased_samples"
mkdir -p "$PHASED_DIR"

# Start logging
LOG_FILE="${RESULTS_DIR}/phasing_pipeline.log"
exec > >(tee -a "$LOG_FILE") 2>&1

# Phase chromosomes using Beagle
for CHR in {1..22}; do
    echo "Processing chromosome $CHR"

    INPUT_VCF="${RESULTS_DIR}/opensnps_qcfinished_chr${CHR}.vcf.gz"
    REF_VCF="${REFERENCES_DIR}/onethousandgenomes_genotype/onethousandgenomes_genotyped_phased.chr${CHR}.vcf.gz"
    MAP_FILE="${REFERENCES_DIR}/genetic_maps/beagle_genetic_maps/plink.chr${CHR}.GRCh38.map"
    OUTPUT_PREFIX="${PHASED_DIR}/opensnps_phased_chr${CHR}"
    PHASED_VCF="${OUTPUT_PREFIX}.vcf.gz"

    # Check if input VCF exists
    if [ ! -f "$INPUT_VCF" ]; then
        echo "Input VCF file not found for chromosome $CHR. Skipping."
        continue
    fi

    # Run Beagle
    java -jar "$BEAGLE_JAR" \
        gt="$INPUT_VCF" \
        ref="$REF_VCF" \
        map="$MAP_FILE" \
        out="$OUTPUT_PREFIX"

    if [ $? -ne 0 ]; then
        echo "Beagle failed for chromosome $CHR. Skipping."
        continue
    fi

    if [ ! -f "$PHASED_VCF" ]; then
        echo "Phasing failed for chromosome $CHR. Skipping."
        continue
    fi

    # Sort and index the phased VCF
    echo "Sorting and indexing phased VCF for chromosome $CHR"
    SORTED_VCF="${PHASED_DIR}/opensnps_phased_chr${CHR}_sorted.vcf.gz"
    bcftools sort -Oz -o "$SORTED_VCF" "$PHASED_VCF"
    bcftools index --tbi "$SORTED_VCF"

    # Replace original VCF with sorted version
    mv "$SORTED_VCF" "$PHASED_VCF"
    mv "${SORTED_VCF}.tbi" "${PHASED_VCF}.tbi"
done

# Generate stats for each chromosome
for CHR in {1..22}; do
    PHASED_VCF="${PHASED_DIR}/opensnps_phased_chr${CHR}.vcf.gz"
    if [ -f "$PHASED_VCF" ]; then
        STATS_OUTPUT="${PHASED_DIR}/opensnps_phased_chr${CHR}_stats.vchk"
        echo "Generating stats for chromosome $CHR"
        bcftools stats -s - "$PHASED_VCF" > "$STATS_OUTPUT"
    else
        echo "Phased VCF not found for chromosome $CHR. Skipping stats generation."
    fi
done

# Final cleanup of QC files
echo "Cleaning up intermediate QC files"
for CHR in {1..22}; do
    rm -f "${RESULTS_DIR}/opensnps_qcfinished_chr${CHR}.vcf.gz"
    rm -f "${RESULTS_DIR}/opensnps_qcfinished_chr${CHR}.log"
    rm -f "${RESULTS_DIR}/opensnps_qcfinished_chr${CHR}.vcf.gz.csi"
done

rm -f "${RESULTS_DIR}/opensnps_autosomes_step1*"
rm -f "${RESULTS_DIR}/opensnps_autosomes_step2*"

echo "Phasing, sorting, and cleanup completed successfully."


# # Concatenate phased VCF files
# echo "Creating list of phased VCF files..."
# PHASED_FILE_LIST="${PHASED_DIR}/phased_file_list_sample.txt"
# > "$PHASED_FILE_LIST"

# for CHR in {1..22}; do
#     PHASED_VCF="${PHASED_DIR}/opensnps_phased_chr${CHR}.vcf.gz"
#     if [ -f "$PHASED_VCF" ]; then
#         echo "$PHASED_VCF" >> "$PHASED_FILE_LIST"
#     else
#         echo "Phased VCF missing for chromosome $CHR"
#     fi
# done

# CONCATENATED_VCF="${PHASED_DIR}/opensnps_multichrom_autosomes_samples.vcf"
# SORTED_VCF="${PHASED_DIR}/opensnps_multichrom_autosomes_samples_sorted.vcf.gz"
# STATS_OUTPUT="${PHASED_DIR}/opensnps_multichrom_autosomes_samples_sorted_stats.vchk"

# # Concatenate VCF files
# bcftools concat -o "$CONCATENATED_VCF" --file-list "$PHASED_FILE_LIST"

# if [ -f "$CONCATENATED_VCF" ]; then
#     # Sort and compress the concatenated VCF
#     bcftools sort -Oz -o "$SORTED_VCF" "$CONCATENATED_VCF"

#     # Index the sorted VCF
#     bcftools index --tbi -f "$SORTED_VCF"

#     # Generate stats
#     bcftools stats -s - "$SORTED_VCF" > "$STATS_OUTPUT"

#     rm -f "${RESULTS_DIR}/opensnps_autosomes_step1*"
#     rm -f "${RESULTS_DIR}/opensnps_autosomes_step2*"

#     echo "Phasing, cleanup, and concatenation completed successfully."

#     # Remove individual phased VCF files
#     echo "Removing individual phased VCF files..."
#     for CHR in {1..22}; do
#         PHASED_VCF="${PHASED_DIR}/opensnps_phased_chr${CHR}.vcf.gz"
#         if [ -f "$PHASED_VCF" ]; then
#             rm -f "$PHASED_VCF"
#             rm -f "${PHASED_VCF}.tbi"  # Also remove the index file if it exists
#             echo "Removed $PHASED_VCF and its index."
#         fi
#     done
# else
#     echo "Concatenated VCF file missing. Pipeline aborted."
#     exit 1
# fi