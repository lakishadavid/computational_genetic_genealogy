import os
import subprocess
import sys

def run_command(command):
    """Runs a shell command and checks for errors."""
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result.stdout.decode('utf-8'))
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr.decode('utf-8')}")
        sys.exit(1)

def convert_fam_to_def(input_fam_file, output_def_file):
    """Converts a .fam file to a .def file using fam2def.py."""
    print(f"Converting {input_fam_file} to {output_def_file}...")
    command = f"./fam2def.py -i {input_fam_file} -o {output_def_file}"
    run_command(command)

def run_ped_sim(def_file, map_file, output_prefix, interference_file, seed):
    """Runs ped-sim with specified parameters."""
    print("Running ped-sim with the following parameters:")
    print(f" - Pedigree definition file: {def_file}")
    print(f" - Genetic map file: {map_file}")
    print(f" - Interference model file: {interference_file}")
    print(f" - Output prefix: {output_prefix}")

    command = (
        f"./pedsim/ped-sim "
        f"-d {def_file} "
        f"-m {map_file} "
        f"-o {output_prefix} "
        f"--intf {interference_file} "
        f"--seed {seed} "
        f"--fam "
        f"--mrca"
    )
    run_command(command)

def main(references_directory, use_directory, results_directory, input_fam_file):
    pedigree_definition_file = os.path.join(use_directory, "ped_simulation.def")
    ped_sim_output_prefix = os.path.join(results_directory, "ped_simulation_output")
    genetic_map_file = os.path.join(references_directory, "refined_mf_b37.simmap")
    interference_model_file = os.path.join(use_directory, "pedsim/interfere/nu_p_campbell.tsv")

    # Step 1: Convert .fam to .def
    convert_fam_to_def(input_fam_file, pedigree_definition_file)

    # Step 2: Run ped-sim
    run_ped_sim(
        def_file=pedigree_definition_file,
        map_file=genetic_map_file,
        output_prefix=ped_sim_output_prefix,
        interference_file=interference_model_file,
        seed=1234
    )
    print(f"ped-sim completed successfully. Results are in {results_directory}.")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python run_ped_sim.py <references_directory> <use_directory> <results_directory> <input_fam_file>")
        sys.exit(1)

    references_directory = sys.argv[1]
    use_directory = sys.argv[2]
    results_directory = sys.argv[3]
    input_fam_file = sys.argv[4]

    main(references_directory, use_directory, results_directory, input_fam_file)
