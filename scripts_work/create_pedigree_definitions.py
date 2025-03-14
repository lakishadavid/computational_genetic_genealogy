import os
import sys
import subprocess
import pandas as pd
import logging
import networkx as nx
import argparse
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from decouple import config

def configure_logging(log_filename, log_file_debug_level="INFO", console_debug_level="INFO"):
    """
    Configure logging for both file and console handlers.

    Args:
        log_file_path (str): Path to the log file where logs will be written.
    """
    # Create a root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Set the root logger to DEBUG to allow all levels

    # File handler: Logs INFO and above to the file
    LOGFILE = log_filename
    file_handler = logging.FileHandler(LOGFILE)
    file_handler.setLevel(log_file_debug_level)  # File captures only INFO and above
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Console handler: Logs DEBUG and above to the console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_debug_level)  # Console shows DEBUG and above
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # Add handlers to the root logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def generate_pedigree(num_generations=5, num_children=3, num_mates=1):

    if num_generations <= 1:
        raise ValueError("Number of generations must be greater than 1.")

    logging.debug(f"Number of generations to generate: {num_generations}")

    # Initialize list to store pedigree records
    pedigree = []

    # Initialize ID counter
    next_id = 1

    # Founder generation (generation 1)
    founders = [
        {"ID": next_id, "Father": 0, "Mother": 0, "Sex": 1, "Generation": 1, "Type": "Founder"},  # Father
        {"ID": next_id + 1, "Father": 0, "Mother": 0, "Sex": 2, "Generation": 1, "Type": "Founder"}  # Mother
    ]
    pedigree.extend(founders)
    logging.debug(f"Founder generation: {founders}")
    next_id += 2

    # Second generation (generation 2)
    second_generation = []
    father = founders[0]
    mother = founders[1]

    for _ in range(num_children):
        child = {
            "ID": next_id,
            "Father": father["ID"],
            "Mother": mother["ID"],
            "Sex": 1 if next_id % 2 == 0 else 2,  # Alternate sexes
            "Generation": 2,
            "Type": "Descendant"
        }
        second_generation.append(child)
        next_id += 1

    pedigree.extend(second_generation)
    logging.debug(f"Second generation: {second_generation}")

    # Subsequent generations (generation > 2)
    for gen in range(3, num_generations + 1):
        logging.debug(f"Generating generation {gen}...")
        current_generation = []

        # Iterate over descendants from the previous generation
        descendants = [ind for ind in pedigree if ind["Generation"] == gen - 1 and ind["Type"] == "Descendant"]

        for descendant in descendants:
            for _ in range(num_mates):
                mate = {
                    "ID": next_id,
                    "Father": 0,
                    "Mother": 0,
                    "Sex": 2 if descendant["Sex"] == 1 else 1,  # Opposite sex
                    "Generation": gen,
                    "Type": "NotDescendant"
                }
                pedigree.append(mate)
                next_id += 1

                # Add children for the descendant and their mate
                for _ in range(num_children):
                    child = {
                        "ID": next_id,
                        "Father": descendant["ID"],
                        "Mother": mate["ID"],
                        "Sex": 1 if next_id % 2 == 0 else 2,  # Alternate sexes
                        "Generation": gen,
                        "Type": "Descendant"
                    }
                    current_generation.append(child)
                    next_id += 1

        pedigree.extend(current_generation)
        logging.debug(f"Generation {gen} added: {current_generation}")
    
    return pd.DataFrame(pedigree)

def graph_pedigree_networkx(pedigree, output_file):
    """
    Visualizes a pedigree using networkx and matplotlib.

    Args:
        pedigree (list[dict]): The pedigree list generated by `generate_pedigree`.
        output_file (str): Path to save the output graph.
    """
    # Convert the pedigree list into a DataFrame for easier handling
    pedigree_df = pd.DataFrame(pedigree)

    # Create a directed graph
    G = nx.DiGraph()

    # Add nodes with attributes (ID, Generation, Type)
    for _, row in pedigree_df.iterrows():
        G.add_node(
            row["ID"],
            Generation=row["Generation"],
            Sex=row["Sex"],
            Type=row["Type"]
        )

    # Add edges for parent-child relationships
    for _, row in pedigree_df.iterrows():
        if row["Father"] != 0:
            G.add_edge(row["Father"], row["ID"])
        if row["Mother"] != 0:
            G.add_edge(row["Mother"], row["ID"])

    # Define node colors based on Type (Descendants and NotDescendants)
    node_colors = {
        node: "blue" if G.nodes[node]["Type"] != "NotDescendant" else "yellow"
        for node in G.nodes
    }

    # Separate nodes by Sex
    male_nodes = [node for node in G.nodes if G.nodes[node]["Sex"] == 1]
    female_nodes = [node for node in G.nodes if G.nodes[node]["Sex"] == 2]

    # Position nodes based on a hierarchical layout
    pos = nx.nx_agraph.graphviz_layout(G, prog="dot")

    # Plot the graph
    plt.figure(figsize=(30, 8))

    # Draw male nodes (squares)
    nx.draw_networkx_nodes(
        G, pos,
        nodelist=male_nodes,
        node_color=[node_colors[node] for node in male_nodes],  # Corrected
        node_shape='s',  # Square shape for males
        node_size=800
    )

    # Draw female nodes (circles)
    nx.draw_networkx_nodes(
        G, pos,
        nodelist=female_nodes,
        node_color=[node_colors[node] for node in female_nodes],  # Corrected
        node_shape='o',  # Circle shape for females
        node_size=800
    )

    # Draw edges
    nx.draw_networkx_edges(
        G, pos,
        edge_color="gray",
        arrows=True
    )

    # # Define node labels as Generation and Type
    # labels = {
    #     node: f'{G.nodes[node]["Generation"]}\n{G.nodes[node]["Type"]}' for node in G.nodes
    # }

    # # Draw labels
    # nx.draw_networkx_labels(
    #     G, pos,
    #     labels=labels,
    #     font_size=8,
    #     font_color="black"
    # )

    plt.title("Pedigree Visualization")
    plt.savefig(output_file, dpi=300)
    print(f"Graph saved to {output_file}")


# # interactivity
# # or Use D3.js: Export the graph to JSON and use D3.js for interactive visualization in a web browser.

def main(results_directory):

    parser = argparse.ArgumentParser(
        description="Generate a pedigree definition with the specified number of generations."
    )

    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Generate pedigree")
    parser.add_argument("--num_generations", type=int, default=5, help="Number of generations")
    parser.add_argument("--num_children", type=int, default=3, help="Number of children per pairing")
    parser.add_argument("--num_mates", type=int, default=1, help="Number of mates per descendant")
    
    # Parse the arguments
    args = parser.parse_args()

    print(f"Generating pedigree with {args.num_generations} generations...")
    print(f"Number of mates: {args.num_mates}")
    # print(f"Each descendant will have {args.num_mates}.")
    # poetry run python -m scripts_work.create_pedigree_definitions --num_generations 5
    # Generate the pedigree
    pedigree_df = generate_pedigree(
        num_generations=args.num_generations,
        num_children=args.num_children,
        num_mates=args.num_mates
    )

    if len(pedigree_df) > 0:
        ped_filename = os.path.join(results_directory, f"generated_pedigree_numgen_{args.num_generations}_nummate_{args.num_mates}.ped")
        pedigree_df.to_csv(ped_filename, sep="\t", header=False, index=False)
        # pedigree_df = pd.read_csv("generated_pedigree.ped", sep="\t", header=None, names=["ID", "Father", "Mother", "Sex", "Generation", "Type"])
    else:
        return False
    

    # Preview the data
    print(pedigree_df)

    # output_file = os.path.join(results_directory, "Pedigree Visualization")
    # graph_pedigree_networkx(pedigree_df, output_file + ".png")
    # graph_pedigree_plotly(pedigree_df, output_file + ".html")



if __name__ == "__main__":
    try:
        subprocess.run(['poetry', 'run', 'python', '-m', 'scripts_support.directory_setup'], check=True)
        working_directory = config('PROJECT_WORKING_DIR', default=None)
        data_directory = config('PROJECT_DATA_DIR', default=None)
        references_directory = config('PROJECT_REFERENCES_DIR', default=None)
        results_directory = config('PROJECT_RESULTS_DIR', default=None)
        utils_directory = config('PROJECT_UTILS_DIR', default=None)

        if not all([working_directory, data_directory, references_directory, 
                   results_directory, utils_directory]):
            raise ValueError("Not all required directories were configured")
            
    except Exception as e:
        print(f"Error verifying directories: {e}")
        sys.exit(1)

    log_filename = os.path.join(results_directory, "log.txt")
    configure_logging(log_filename, log_file_debug_level="INFO", console_debug_level="INFO")

    main(results_directory)