# Running the Course Container

## Understanding Configuration Files

Before we start, let's understand the key files that make up our container environment:

1. **Dockerfile**
   - The recipe for building our container image
   - Specifies the base Ubuntu image
   - Installs required system packages
   - Sets up Python and Poetry
   - Creates necessary directories within the container

2. **docker-compose.yml**
   - Configures how our container runs
   - Maps directories between your computer and the container
   - Uses environment variables for flexible directory mapping
   - Sets up the working environment

3. **scripts_support/directory_setup.py**
   - Helps set up and verify your local directories
   - Creates environment variables for directory locations
   - Ensures proper directory structure exists
   - Creates/updates the .env file with your paths

## Understanding Builds vs. Containers

**Docker Build:**
- Creates a blueprint (image) for your container
- Follows instructions in the Dockerfile
- Installs all necessary software and dependencies
- Only needs to be run when:
  - First setting up the environment
  - Making changes to the Dockerfile
  - Updating dependencies

**Docker Container:**
- Is a running instance of the built image
- Like a virtual computer running your environment
- Can be started, stopped, and restarted
- Maintains isolation from your host system
- Can have multiple containers from the same image

Think of it like baking:
- The Dockerfile is your recipe
- Building creates your "mix" (image)
- Running a container is like baking a cake from that mix
- You can make multiple cakes (containers) from the same mix (image)

## Step 1: Navigate to Course Directory

Open a terminal window (not VSCode's integrated terminal) and navigate to the course repository:
```
cd ~/computational_genetic_genealogy
```

Note: We use a regular terminal window because some Docker operations may have permission issues in VSCode's integrated terminal. This ensures consistent behavior across all systems.

## Step 2: Build the Container

Build the Docker container using Docker Compose:
```
docker build -t cgg_image .
```

This command reads the Dockerfile and creates an image with all necessary tools and dependencies.

## Step 3: Directory Setup and Sart the Container

Run the directory setup script:
```
poetry run python -m scripts_support.directory_setup
docker compose up -d
```

This .env file is then used by docker-compose.yml to map your directories into the container using volumes:
```yaml
volumes:
  - ${PROJECT_DATA_DIR:-}:/home/ubuntu/data
  - ${PROJECT_RESULTS_DIR:-}:/home/ubuntu/results
  - ${PROJECT_REFERENCES_DIR:-}:/home/ubuntu/references
```

These mappings mean:
- Files in your PROJECT_DATA_DIR appear in /home/ubuntu/data in the container
- Files in your PROJECT_RESULTS_DIR appear in /home/ubuntu/results in the container
- Files in your PROJECT_REFERENCES_DIR appear in /home/ubuntu/references in the container

This command:
1. Reads docker-compose.yml
2. Uses the previously built image
3. Sets up volume mappings using your .env file
4. Starts the container with access to your directories

Option 2:
Where the file path on the left should reflect your own directory,
which gets mapped to the file path on the right in the containter.
```
docker run -d \
  --name cgg_container \
  -w /home/ubuntu \
  -v /home/lakishadavid/data:/home/ubuntu/data \
  -v /home/lakishadavid/results:/home/ubuntu/results \
  -v /home/lakishadavid/references:/home/ubuntu/references \
  cgg_image
```

## When you are finished using the container, stop it using one of the following commands based on how you started it.
Option 1
```
docker compose down
```
or

Option 2
```
docker stop cgg_container
```

### Container Persistence
Once built, your container image persists on your system. This means:
- You only need to `build` once (unless you modify the Dockerfile)
- For regular work, just use `docker compose up`. No need to rebuild unless you modify the Dockerfile or update dependencies.
- The image contains your complete analysis environment
- Your files persist in the mounted directories between sessions

Think of it like your virtual research workspace:
- The image is your lab setup
- Starting the container is like opening your lab for the day
- Your data and results are safely stored between sessions

## Verifying Your Setup

After starting the container, verify everything is working:

pre. If you're using `docker compose`
```
docker compose exec app bash
```
When you're ready to exit the container bash shell, enter `exit`. Your container will still be running until you run `docker compose down`.

1. Check mounted directories:
   ```
   ls /home/ubuntu/data       # Your data files
   ls /home/ubuntu/results    # Analysis outputs
   ls /home/ubuntu/references # Reference materials
   ```

2. Verify the Python environment:
   ```
   python --version
   poetry --version
   ```

## Managing Docker Resources

### Monitoring Resource Usage
View container resource usage:
```
docker stats
```

### Cleaning Up
Regular maintenance commands:
```
# Remove unused containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Clean everything unused
docker system prune
```

### Common Resource Issues
1. **High Memory Usage**
   - Monitor with `docker stats`
   - Consider limiting container memory: `docker run --memory=2g`

2. **Disk Space**
   - Check space: `docker system df`
   - Remove unused resources regularly

## Troubleshooting

Common issues you might encounter:

1. **Build Fails**
   - Ensure Docker is running
   - Check internet connection
   - Verify you have enough disk space
   ```
   # Clean up Docker system
   docker system prune
   ```

2. **Directory Setup Issues**
   - Check error messages in the setup script output
   - Ensure you have write permissions in your home directory
   - WSL2 users: Verify correct filesystem permissions

3. **Container Won't Start**
   ```
   # Check container status
   docker ps
   
   # View logs
   docker compose logs
   ```

4. **Volume Mount Errors**
   - Ensure directories exist
   - Check permissions
   - WSL2 users: Verify paths use correct format

## For Future Sessions

After the initial setup, your workflow will be (as long as you haven't deleted the build):

1. Navigate to the project directory:
   ```
   cd ~/computational_genetic_genealogy
   ```

2. Start the container:
   ```
   docker compose up
   ```

3. Begin your analysis work

# Understanding Docker Storage and Backups

## Docker Volumes and Mapping

### What are Volumes?
Docker volumes are like special folders that exist outside your container but can be accessed from inside it. Think of them as bridges between your computer and the container:
- They persist even when the container stops
- They can be shared between containers
- They're managed separately from the container lifecycle

### Volume Mapping (Mounting)
Volume mapping connects a directory on your computer to a directory in the container:
```yaml
volumes:
  - /home/your_username/data:/home/ubuntu/data
```
This means:
- Left side (`/home/your_username/data`): Path on your computer
- Right side (`/home/ubuntu/data`): Where it appears in the container
- Changes in either location instantly reflect in the other

## Data Persistence

### Container vs. Volume Data
When working with Docker, data can exist in two states:
1. **Container Data**
   - Lives inside the container
   - Temporary by default
   - Lost when container is removed
   - Good for: temporary computations, caches

2. **Volume Data**
   - Lives on your computer
   - Persists between container runs
   - Survives container removal
   - Good for: important files, results, datasets

### What Gets Saved vs. What Doesn't

Let's say you:
1. Start the container
2. Install a new Python package: `poetry add pandas`
3. Create a file in a mounted volume: `/home/ubuntu/results/analysis.csv`
   (This directory is connected to the results directory on your computer)
4. Create a file in the container's home directory: `/home/ubuntu/temp_notes.txt`
   (This directory is not mapped to your computer)

When you use `docker save`:
- ✅ Saves: Base image (Ubuntu, Python, initial packages)
- ❌ Doesn't Save: 
  - The newly installed pandas package (added via poetry)
  - The temp_notes.txt file (in unmapped container directory)
  - Any configuration changes
  - Command history
  - Environmental changes

The analysis.csv file is safe because it's in a mounted volume that's connected to your computer's results directory.

## Backup Strategies

### Directory Organization
```
project/
├── data/          # Raw data (mounted volume)
│   ├── raw/
│   └── processed/
├── results/       # Analysis outputs (mounted volume)
│   ├── figures/
│   └── reports/
└── references/    # Reference materials (mounted volume)
```

### Manual Backup Workflow

1. **Daily Backups**
   - Copy critical results files
   - Document container changes
   - Save intermediate analyses

2. **Weekly Backups**
   - Full volume backup
   - Save container image
   - Update documentation

3. **Monthly Archives**
   - Archive complete project state
   - Validate backups
   - Clean up unnecessary files

### Automated Backups

Using our backup script:
```python
# Run automated backup
python container_backup.py <container_id> --backup-path /path/to/backups
```

This script will:
1. Create timestamped backup folders
2. Copy all mounted volume contents
3. Save the container image
4. Generate a backup report

Schedule regular backups:
```bash
# Add to crontab for daily backups at 1 AM
0 1 * * * python /path/to/container_backup.py <container_id> --backup-path /backups
```

### Transfer Protocol

When moving to a new system:
1. Save image: 
   ```bash
   docker save -o image_backup.tar devcontainer-image
   ```
   
2. Backup volumes:
   ```bash
   python container_backup.py <container_id>
   ```
   
3. Transfer files:
   ```bash
   rsync -avz backups/ user@remote:/path/to/destination/
   ```

## Monitoring and Maintenance

### Space Management
```bash
# Check Docker space usage
docker system df

# Clean up unused resources
docker system prune

# Remove specific types
docker container prune  # Remove stopped containers
docker image prune      # Remove unused images
docker volume prune     # Remove unused volumes
```

### Backup Validation
```bash
# Verify backup integrity
md5sum backups/devcontainer-image.tar > checksum.txt
diff checksum.txt previous_checksum.txt

# Test backup restoration
./verify_backup.sh
```

### Performance Monitoring
```bash
# Monitor container resources
docker stats

# Check volume usage
du -h /path/to/volumes/*
```

## Quick Reference

### Common Backup Commands
```bash
# Save container image
docker save -o backup.tar devcontainer-image

# Load saved image
docker load -i backup.tar

# Copy from container
docker cp <container_id>:/home/ubuntu/results ./backup_results

# Copy to container
docker cp ./local_file <container_id>:/home/ubuntu/data/
```

### Maintenance Commands
```bash
# Check container status
docker ps

# View logs
docker compose logs

# Clean up space
docker system prune

# Monitor resources
docker stats
```

Remember: Always verify your backups and test your restore process regularly. The best backup is one you've confirmed you can restore from.

## Troubleshooting

Common issues when saving/copying:

1. **Permission Denied**
   ```bash
   # Fix permissions on destination
   sudo chmod a+rw /path/to/destination
   ```

2. **Space Issues**
   - Check available space: `df -h`
   - Clean up Docker: `docker system prune`
   - Remove old images: `docker image prune`

3. **Path Not Found**
   - Verify container is running
   - Check path exists in container
   - Use absolute paths

4. **Backup Script Errors**
   - Verify container ID is correct
   - Check backup destination permissions
   - Ensure sufficient disk space

5. **Transfer Failures**
   - Verify network connection
   - Check file permissions
   - Confirm sufficient space at destination

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Volume Documentation](https://docs.docker.com/storage/volumes/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Docker Resource Management](https://docs.docker.com/config/containers/resource_constraints/)
- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Docker Backup Strategies](https://docs.docker.com/storage/backup-restore/)
- [Cron Documentation](https://man7.org/linux/man-pages/man5/crontab.5.html)
- [Rsync Manual](https://download.samba.org/pub/rsync/rsync.1)
