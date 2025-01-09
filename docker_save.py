# container_backup.py
import subprocess
import os
from datetime import datetime
import argparse

def backup_container(container_id, backup_path):
    """Backup both container data and image"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(backup_path, f'container_backup_{timestamp}')
    os.makedirs(backup_dir, exist_ok=True)
    
    # Directories to backup
    dirs_to_backup = [
        '/home/ubuntu/results',
        '/home/ubuntu/data',
        '/home/ubuntu/references',
        '/home/ubuntu/utils'
    ]
    
    # Backup container directories
    print("Backing up container directories...")
    for dir_path in dirs_to_backup:
        dir_name = os.path.basename(dir_path)
        target_path = os.path.join(backup_dir, dir_name)
        try:
            subprocess.run([
                'docker', 'cp',
                f'{container_id}:{dir_path}',
                target_path
            ], check=True)
            print(f"Backed up {dir_path}")
        except subprocess.CalledProcessError:
            print(f"Warning: Could not backup {dir_path}")
    
    # Save the image
    print("\nSaving Docker image...")
    image_path = os.path.join(backup_dir, 'devcontainer-image.tar')
    subprocess.run([
        'docker', 'save',
        '-o', image_path,
        'devcontainer-image'
    ], check=True)
    
    print(f"\nBackup completed to: {backup_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backup Docker container data and image")
    parser.add_argument('container_id', help="Container ID or name")
    parser.add_argument('--backup-path', default='./backups',
                       help="Path to store backup (default: ./backups)")
    
    args = parser.parse_args()
    backup_container(args.container_id, args.backup_path)