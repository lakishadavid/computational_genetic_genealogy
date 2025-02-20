#!/usr/bin/env python3
"""
Script to add genetic map positions to a PLINK BIM file.
Usage: python add_genetic_map.py input.bim map_dir output.bim
"""

import sys
import os
import glob
from collections import defaultdict
import bisect

def load_genetic_maps(map_directory):
    """
    Load all genetic maps from the specified directory.
    Expects files named like plink.chr1.GRCh38.map, plink.chr2.GRCh38.map, etc.
    """
    genetic_maps = defaultdict(list)
    
    # Get all map files
    map_files = glob.glob(f"{map_directory}/plink.chr*.GRCh38.map")
    
    for map_file in sorted(map_files):
        print(f"Loading map file: {map_file}")
        chr_num = None
        positions = []
        genetic_positions = []
        
        with open(map_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 3:
                    continue
                    
                chrom, pos, gen_pos = parts[0], int(parts[1]), float(parts[2])
                
                # Set chromosome if not already set
                if chr_num is None:
                    chr_num = chrom
                
                positions.append(pos)
                genetic_positions.append(gen_pos)
        
        if chr_num is not None and positions:
            genetic_maps[chr_num] = (positions, genetic_positions)
            print(f"  Loaded {len(positions)} markers for chromosome {chr_num}")
    
    return genetic_maps

def interpolate_genetic_position(physical_pos, positions, genetic_positions):
    """
    Interpolate genetic position based on physical position.
    """
    if physical_pos <= positions[0]:
        return genetic_positions[0]
    if physical_pos >= positions[-1]:
        return genetic_positions[-1]
    
    # Find the insertion point
    idx = bisect.bisect_left(positions, physical_pos)
    
    if positions[idx] == physical_pos:
        return genetic_positions[idx]
    
    # Interpolate between the two nearest positions
    left_pos, right_pos = positions[idx-1], positions[idx]
    left_gen, right_gen = genetic_positions[idx-1], genetic_positions[idx]
    
    # Linear interpolation
    fraction = (physical_pos - left_pos) / (right_pos - left_pos)
    gen_pos = left_gen + fraction * (right_gen - left_gen)
    
    return gen_pos

def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} input.bim map_directory output.bim")
        sys.exit(1)
    
    input_bim = sys.argv[1]
    map_directory = sys.argv[2]
    output_bim = sys.argv[3]
    
    # Load all genetic maps
    print("Loading genetic maps...")
    genetic_maps = load_genetic_maps(map_directory)
    print(f"Loaded genetic maps for {len(genetic_maps)} chromosomes")
    
    # Process BIM file
    print(f"Processing BIM file: {input_bim}")
    updated_count = 0
    interpolated_count = 0
    missing_map_count = 0
    zero_physical_count = 0
    
    with open(input_bim, 'r') as infile, open(output_bim, 'w') as outfile:
        for line_num, line in enumerate(infile, 1):
            if line_num % 100000 == 0:
                print(f"Processed {line_num} lines...")
                
            parts = line.strip().split()
            if len(parts) < 6:
                print(f"Warning: Invalid BIM line at {line_num}: {line}")
                outfile.write(line)
                continue
            
            chrom, snp_id, gen_pos, phys_pos, allele1, allele2 = parts
            
            try:
                phys_pos_int = int(phys_pos)
            except ValueError:
                print(f"Warning: Invalid physical position at line {line_num}: {phys_pos}")
                outfile.write(line)
                continue
                
            if phys_pos_int <= 0:
                zero_physical_count += 1
                outfile.write(line)
                continue
                
            if chrom in genetic_maps:
                positions, genetic_positions = genetic_maps[chrom]
                
                # Interpolate genetic position
                new_gen_pos = interpolate_genetic_position(
                    phys_pos_int, positions, genetic_positions
                )
                
                if new_gen_pos is not None:
                    # Update genetic position in the line
                    updated_count += 1
                    outfile.write(f"{chrom}\t{snp_id}\t{new_gen_pos:.6f}\t{phys_pos}\t{allele1}\t{allele2}\n")
                else:
                    interpolated_count += 1
                    outfile.write(line)
            else:
                missing_map_count += 1
                outfile.write(line)
    
    print(f"Done! Updated {updated_count} positions.")
    print(f"Interpolated {interpolated_count} positions.")
    print(f"Skipped {missing_map_count} positions due to missing map.")
    print(f"Skipped {zero_physical_count} positions due to invalid physical position.")
    print(f"Output written to: {output_bim}")

if __name__ == "__main__":
    main()