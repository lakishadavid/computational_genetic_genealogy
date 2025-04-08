import time
import random
from numba import jit

class IBDIndex:
    """
    An efficient indexing structure for IBD segments that supports both
    phased and unphased data with optimized access patterns aligned with v3.
    """
    def __init__(self, min_cm=7.0):
        self.min_cm = min_cm
        self.pair_index = {}           # {frozenset({id1, id2}): [segment_list]}
        self.id_index = {}             # {id: [segment_list]}
        self.pair_stats = {}           # {frozenset({id1, id2}): stats_dict}
        self.chrom_index = {}          # {chrom: [segment_list]}
        self.id_to_chrom_index = {}    # {id: {chrom: [segment_list]}}
        self.haplotype_index = {}      # {(id, hap): [segment_list]} (for phased data)
        
    def add_segment(self, segment, segment_type="unphased"):
        """Add a segment to all relevant indexes."""
        if segment_type == "unphased":
            # [id1, id2, chromosome, start_bp, end_bp, is_full_ibd, seg_cm]
            id1, id2, chrom, start, end, is_full, seg_cm = segment
            
            # Filter by minimum length
            if seg_cm < self.min_cm:
                return
                
            # Create keys
            pair_key = frozenset({id1, id2})
            
            # Update pair index
            if pair_key not in self.pair_index:
                self.pair_index[pair_key] = []
            self.pair_index[pair_key].append(segment)
            
            # Update individual index
            for id_val in [id1, id2]:
                if id_val not in self.id_index:
                    self.id_index[id_val] = []
                self.id_index[id_val].append(segment)
                
                # Update id-to-chrom index
                if id_val not in self.id_to_chrom_index:
                    self.id_to_chrom_index[id_val] = {}
                if chrom not in self.id_to_chrom_index[id_val]:
                    self.id_to_chrom_index[id_val][chrom] = []
                self.id_to_chrom_index[id_val][chrom].append(segment)
            
            # Update chromosome index
            if chrom not in self.chrom_index:
                self.chrom_index[chrom] = []
            self.chrom_index[chrom].append(segment)
            
            # Update stats
            if pair_key not in self.pair_stats:
                self.pair_stats[pair_key] = {
                    'total_half': 0,
                    'total_full': 0,
                    'num_half': 0,
                    'num_full': 0,
                    'max_seg_cm': 0
                }
            
            if is_full:
                self.pair_stats[pair_key]['total_full'] += seg_cm
                self.pair_stats[pair_key]['num_full'] += 1
            else:
                self.pair_stats[pair_key]['total_half'] += seg_cm
                self.pair_stats[pair_key]['num_half'] += 1
            
            self.pair_stats[pair_key]['max_seg_cm'] = max(
                self.pair_stats[pair_key]['max_seg_cm'], seg_cm
            )
            
        elif segment_type == "phased":
            # [id1, id2, hap1, hap2, chromosome, start_cm, end_cm, seg_cm]
            id1, id2, hap1, hap2, chrom, start, end, seg_cm = segment
            
            # Filter by minimum length
            if seg_cm < self.min_cm:
                return
                
            # Create keys
            pair_key = frozenset({id1, id2})
            hap1_key = (id1, hap1)
            hap2_key = (id2, hap2)
            
            # Update pair index
            if pair_key not in self.pair_index:
                self.pair_index[pair_key] = []
            self.pair_index[pair_key].append(segment)
            
            # Update individual index
            for id_val in [id1, id2]:
                if id_val not in self.id_index:
                    self.id_index[id_val] = []
                self.id_index[id_val].append(segment)
            
            # Update haplotype index
            for hap_key in [hap1_key, hap2_key]:
                if hap_key not in self.haplotype_index:
                    self.haplotype_index[hap_key] = []
                self.haplotype_index[hap_key].append(segment)
            
            # Update chromosome index
            if chrom not in self.chrom_index:
                self.chrom_index[chrom] = []
            self.chrom_index[chrom].append(segment)
    
    def add_segments(self, segments, segment_type="unphased"):
        """Add multiple segments at once."""
        for segment in segments:
            self.add_segment(segment, segment_type)
    
    # Removed the @jit decorator to avoid Numba errors with frozenset
    def get_segments_for_pair(self, id1, id2):
        """Get all segments shared between a pair of individuals."""
        pair_key = frozenset({id1, id2})
        return self.pair_index.get(pair_key, [])
    
    def get_stats_for_pair(self, id1, id2):
        """Get IBD statistics for a pair of individuals."""
        pair_key = frozenset({id1, id2})
        return self.pair_stats.get(pair_key, {
            'total_half': 0,
            'total_full': 0,
            'num_half': 0,
            'num_full': 0,
            'max_seg_cm': 0
        })
    
    def get_segments_by_chromosome(self, chrom):
        """Get all segments on a particular chromosome."""
        return self.chrom_index.get(chrom, [])
    
    def get_segments_for_individual(self, individual_id):
        """Get all segments involving a particular individual."""
        return self.id_index.get(individual_id, [])
    
    def get_segments_for_haplotype(self, individual_id, haplotype):
        """Get all segments on a specific haplotype (for phased data)."""
        key = (individual_id, haplotype)
        return self.haplotype_index.get(key, [])
    
    def get_total_ibd_between_id_sets(self, id_set1, id_set2):
        """Calculate total IBD shared between two sets of IDs."""
        total_ibd = 0
        
        for id1 in id_set1:
            for id2 in id_set2:
                if id1 == id2:
                    continue
                    
                pair_key = frozenset({id1, id2})
                if pair_key in self.pair_stats:
                    stats = self.pair_stats[pair_key]
                    total_ibd += stats['total_half'] + stats['total_full']
        
        return total_ibd

def generate_random_segments(num_individuals, num_segments, phased=False):
    """Generate random IBD segments for benchmarking."""
    segments = []
    
    for _ in range(num_segments):
        # Choose random individuals
        id1, id2 = random.sample(range(1, num_individuals + 1), 2)
        
        # Generate random segment attributes
        chrom = random.randint(1, 22)
        start_pos = random.randint(1, 200_000_000)
        end_pos = start_pos + random.randint(1_000_000, 50_000_000)
        is_ibd2 = random.random() < 0.2  # 20% chance of IBD2
        length_cm = random.uniform(7.0, 100.0)  # Random length between 7 and 100 cM
        
        if not phased:
            # Unphased format
            segments.append([id1, id2, chrom, start_pos, end_pos, is_ibd2, length_cm])
        else:
            # Phased format (add haplotype info)
            hap1 = random.randint(0, 1)
            hap2 = random.randint(0, 1)
            segments.append([id1, id2, hap1, hap2, chrom, start_pos/1_000_000, end_pos/1_000_000, length_cm])
    
    return segments

# Benchmark the IBD index
def benchmark_ibd_index():
    # Reduced dataset size for faster execution in the notebook environment
    num_individuals = 50  # Reduced from 500
    num_segments = 1000   # Reduced from 10000
    
    print(f"Generating {num_segments} random segments for {num_individuals} individuals...")
    unphased_segments = generate_random_segments(num_individuals, num_segments)
    phased_segments = generate_random_segments(num_individuals, num_segments, phased=True)
    
    # Time index creation
    print("\nBenchmarking index creation...")
    start_time = time.time()
    index = IBDIndex()
    index.add_segments(unphased_segments, "unphased")
    index.add_segments(phased_segments, "phased")
    end_time = time.time()
    print(f"Time to build index: {end_time - start_time:.4f} seconds")
    
    # Time pair lookup
    print("\nBenchmarking pair lookup (100 random pairs)...")
    start_time = time.time()
    lookup_count = 0
    for _ in range(100):  # Reduced from 1000
        id1, id2 = random.sample(range(1, num_individuals + 1), 2)
        segments = index.get_segments_for_pair(id1, id2)
        if segments:
            lookup_count += 1
    end_time = time.time()
    print(f"Time for 100 pair lookups: {end_time - start_time:.4f} seconds")
    print(f"Average time per lookup: {(end_time - start_time) / 100:.6f} seconds")
    print(f"Found segments for {lookup_count}/100 pairs")
    
    # Time individual lookup
    print("\nBenchmarking individual lookup (100 random individuals)...")
    start_time = time.time()
    ind_count = 0
    for _ in range(100):  # Reduced from 1000
        id1 = random.randint(1, num_individuals)
        segments = index.get_segments_for_individual(id1)
        if segments:
            ind_count += 1
    end_time = time.time()
    print(f"Time for 100 individual lookups: {end_time - start_time:.4f} seconds")
    print(f"Average time per lookup: {(end_time - start_time) / 100:.6f} seconds")
    print(f"Found segments for {ind_count}/100 individuals")
    
    # Time ID set calculations
    print("\nBenchmarking ID set calculations (10 random set pairs)...")
    start_time = time.time()
    set_count = 0
    for _ in range(10):  # Reduced from 100
        set1 = set(random.sample(range(1, num_individuals + 1), 5))  # Reduced size
        set2 = set(random.sample(range(1, num_individuals + 1), 5))  # Reduced size
        total_ibd = index.get_total_ibd_between_id_sets(set1, set2)
        if total_ibd > 0:
            set_count += 1
    end_time = time.time()
    print(f"Time for 10 ID set calculations: {end_time - start_time:.4f} seconds")
    print(f"Average time per calculation: {(end_time - start_time) / 10:.6f} seconds")
    print(f"Found IBD between {set_count}/10 set pairs")
    
    return index

if __name__ == "__main__":
    print("Testing IBDIndex class with frozenset...")
    index = benchmark_ibd_index()
    print("Benchmark completed successfully!")