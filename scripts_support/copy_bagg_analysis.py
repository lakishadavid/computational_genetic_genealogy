import os
import shutil

# Define the source and destination directories
source_dir = "/home/ubuntu/bagg_analysis"
dest_dir = "/home/ubuntu/computational_genetic_genealogy"

# List of files or directories to exclude
exclusions = {
    "cloudformation",
    "codepipeline",
    "data",
    "etc",
    "processors",
    "references",
    "results",
    "utils",
    ".env",
    ".gitignore",
    ".Rhistory",
    "appspec.yml",
    "Dockerfile",
    "README.md",
    "Rplots.pdf",
    "run_genotype_workflow.sh",
}

def copy_directory(src, dest, exclude_set):
    if not os.path.exists(dest):
        os.makedirs(dest)

    for item in os.listdir(src):
        item_path = os.path.join(src, item)
        dest_path = os.path.join(dest, item)

        if item in exclude_set:
            print(f"Skipping excluded item: {item}")
            continue

        if os.path.isdir(item_path):
            copy_directory(item_path, dest_path, exclude_set)
        else:
            shutil.copy2(item_path, dest_path)

if __name__ == "__main__":
    copy_directory(source_dir, dest_dir, exclusions)
    print("Copy completed.")