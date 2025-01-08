import pandas as pd
import msprime
import tskit

# Define the file path for the pedigree definition
pedigree_file = "pedigree_definition.csv"

# Load the pedigree data from the CSV file
pedigree_df = pd.read_csv(pedigree_file)

# Ensure columns are named correctly
pedigree_df.columns = ["individual", "father", "mother", "sex"]

# Replace missing parent values (e.g., 0) with -1 for msprime
pedigree_df["father"] = pedigree_df["father"].replace(0, -1).astype(int)
pedigree_df["mother"] = pedigree_df["mother"].replace(0, -1).astype(int)

# Assign generation times for msprime simulation
def assign_generations(pedigree):
    """
    Assigns generation times based on parent-child relationships in the pedigree.
    Assumes individuals without parents are in generation 0.
    """
    pedigree["generation"] = -1  # Initialize with -1
    pedigree.loc[(pedigree["father"] == -1) & (pedigree["mother"] == -1), "generation"] = 0

    while (pedigree["generation"] == -1).any():
        for _, row in pedigree.iterrows():
            if row["generation"] == -1:
                father_gen = pedigree.loc[pedigree["individual"] == row["father"], "generation"]
                mother_gen = pedigree.loc[pedigree["individual"] == row["mother"], "generation"]
                if not father_gen.empty and not mother_gen.empty:
                    pedigree.loc[pedigree["individual"] == row["individual"], "generation"] = max(father_gen.values[0], mother_gen.values[0]) + 1
    return pedigree

# Apply generation assignment
pedigree_df = assign_generations(pedigree_df)

# Initialize msprime PedigreeBuilder
pb = msprime.PedigreeBuilder()

# Add individuals to the pedigree
individual_map = {}  # Mapping of individual IDs to msprime IDs
for _, row in pedigree_df.iterrows():
    individual_id = pb.add_individual(
        time=row["generation"],
        parents=[
            individual_map.get(row["father"], tskit.NULL),
            individual_map.get(row["mother"], tskit.NULL)
        ],
        metadata={
            "individual": row["individual"],
            "sex": row["sex"]
        }
    )
    individual_map[row["individual"]] = individual_id

# Finalize the pedigree
sequence_length = 1e6  # Example sequence length (can be adjusted)
pedigree = pb.finalise(sequence_length=sequence_length)

# Simulate tree sequence
tree_sequence = msprime.sim_ancestry(
    initial_state=pedigree,
    sequence_length=sequence_length,
    recombination_rate=1e-8,
    population_size=1000
)

# Simulate mutations
mutated_ts = msprime.sim_mutations(tree_sequence, rate=1e-8)

# Save the tree sequence
output_file = "simulated_pedigree.trees"
mutated_ts.dump(output_file)

print(f"Simulation completed. Tree sequence saved to {output_file}.")
