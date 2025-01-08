#!/bin/bash

# Define directories and Beagle jar path
RESULTS_DIR=$1
REFERENCES_DIR=$2
UTILS_DIR=$3

# Prepare the necessary input files:
bpm_manifest_file="..."
csv_manifest_file="..."
egt_cluster_file="..."
path_to_gtc_folder="..."
ref="$HOME/GRCh38/GCA_000001405.15_GRCh38_no_alt_analysis_set.fna" # or ref="$HOME/GRCh37/human_g1k_v37.fasta"
out_prefix="..."

# Convert from Illumina's IDAT to GTC
# Array Analysis CLI (latest and recommended for Linux environments).

# Convert from GTC format to VCF
# https://github.com/freeseek/gtc2vcf
# Alternative to https://github.com/Illumina/GTCtoVCF
bcftools +gtc2vcf \
  --no-version -Ou \
  --bpm $bpm_manifest_file \
  --csv $csv_manifest_file \
  --egt $egt_cluster_file \
  --gtcs $path_to_gtc_folder \
  --fasta-ref $ref \
  --extra $out_prefix.tsv | \
  bcftools sort -Ou -T ./bcftools. | \
  bcftools norm --no-version -o $out_prefix.bcf -Ob -c x -f $ref --write-index

# Apply quality filters to the VCF file to remove low-quality variants
# Retains variants with a quality score above 20 and depth greater than 10.
# QUAL > 20, the variant has a 99% probability of being correct.
# May need QUAL > 30 for publications
# The DP field indicates how many reads support the call for a given variant.
# Genotype Quality (GQ): GQ > 20 ensures confidence in individual genotypes.
# Allele Frequency (AF): The proportion of reads supporting the alternate allele.
# Minimum: AF > 0.2 ensures a sufficient proportion of reads support the alternate allele.
# Mapping Quality (MQ): MQ > 40 ensures that reads are uniquely and confidently aligned.
# Base Quality (BQ): The average quality score of bases supporting the variant.
# BQ > 30 ensures high confidence in base calls.
bcftools filter \
  -i 'QUAL>20 && DP>10 && MQ>40 && AF>0.2 && AF<0.8' \
  -o high_quality_variants.vcf \
  input.vcf


# NOTES: # Perform further analysis or as alternative to bcftools

# import cyvcf2
# import pandas as pd

# vcf_reader = cyvcf2.VCF('filtered_output.vcf')
# records = [variant for variant in vcf_reader]

# # Convert from VCF to DataFrame for analysis
# df = pd.DataFrame({
#     'CHROM': [variant.CHROM for variant in records],
#     'POS': [variant.POS for variant in records],
#     'REF': [variant.REF for variant in records],
#     'ALT': [variant.ALT[0] for variant in records],
#     'QUAL': [variant.QUAL for variant in records]
# })

# 
# print(df.head())
