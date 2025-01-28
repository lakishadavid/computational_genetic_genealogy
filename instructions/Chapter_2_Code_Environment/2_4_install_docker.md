# Installing Docker

Docker is an essential tool for computational research that helps create consistent environments across different computers. We'll use Docker to ensure everyone has the same setup for running genetic genealogy analyses.

## Prerequisites

Before installing Docker, ensure:
- You have administrator access on your computer
- Your system meets the minimum requirements:
  - **Windows**: Windows 10/11 Pro, Enterprise, or Education (64-bit)
  - **WSL2 users**: WSL2 installed and configured
  - **macOS**: macOS 10.15 or newer
  - **Linux**: 64-bit version of Ubuntu, Debian, Fedora, or similar

## Step 1: Installation Instructions

### Windows Users

#### WSL2 Users
1. Visit [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
2. Download Docker Desktop Installer
3. Run the installer (must be administrator)
4. During installation:
   - Enable WSL2 features if prompted
   - Keep Hyper-V enabled if asked
   - Leave "Use WSL2 instead of Hyper-V" checked

### macOS Users

#### Intel Processor
1. Visit [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
2. Download Intel Chip installer
3. Drag Docker.app to Applications
4. Open Docker from Applications

#### Apple Silicon (M1/M2)
1. Visit [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
2. Download Apple Silicon installer
3. Drag Docker.app to Applications
4. Open Docker from Applications
5. Note: Some images may need Rosetta 2 compatibility


---
## Step 2: In Ubuntu Terminal
Run these commands in sequence:
```
# Update system
sudo apt-get update -y

# Install prerequisites
sudo apt-get install -y ca-certificates curl

# Set up Docker repository
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update and install Docker
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Set up permissions
sudo groupadd docker
sudo usermod -aG docker $USER
sudo systemctl restart docker
newgrp docker
```

---

#### Other Linux Distributions
Visit [Install Docker Engine](https://docs.docker.com/engine/install/) and select your distribution.

## Verification Steps

### 1. Check Installation
Open a terminal (WSL2 users: open WSL2 terminal) and run:
```
docker --version
docker compose version
```
You should see version information for both commands.

### 2. Run Test Container
```
docker run hello-world
```
You should see a success message explaining the steps Docker took.

### 3. Check Docker Desktop (Windows/macOS)
- Open Docker Desktop
- Look for the green "Running" status
- Check Resources tab for memory allocation

### 4. Ubuntu Specific Check

```
docker image ls
docker ps
# Should show no error
```

## Troubleshooting

### Common Issues

1. **"Cannot connect to the Docker daemon"**
   - Windows/macOS: Ensure Docker Desktop is running
   - Linux: Run `sudo systemctl start docker`
   - WSL2: Check Docker Desktop WSL integration

2. **Permission Issues (Linux/WSL2)**
   ```
   # Fix group membership
   sudo groupadd docker
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. **WSL2 Integration Issues**
   - Open Docker Desktop
   - Go to Settings → Resources → WSL Integration
   - Enable integration for your distro
   - Restart Docker Desktop

4. **Virtualization Issues (Windows)**
   - Enable virtualization in BIOS
   - Ensure Hyper-V is enabled
   - Check WSL2 installation

5. **Resource Issues**
   - Increase memory allocation in Docker Desktop
   - Clear unused images: `docker system prune`

## Next Steps

After successful installation:
1. We'll learn to build and run containers
2. Set up our computational environment
3. Run genetic genealogy tools

If you encounter issues, please reach out to the course instructor for assistance.

## Additional Resources

- [Docker Get Started Guide](https://docs.docker.com/get-started/)
- [Docker Desktop Manual](https://docs.docker.com/desktop/)
- [Docker WSL2 Backend](https://docs.docker.com/desktop/wsl/)
- [Docker System Requirements](https://docs.docker.com/desktop/install/windows-install/#system-requirements)
