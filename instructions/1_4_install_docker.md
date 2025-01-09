## Docker

### Step 1: Install Docker

#### For Windows Users
To install Docker Desktop on Windows, visit the following URL for the installation package and detailed setup instructions:
[Install Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/)

---

#### For macOS Users
To install Docker Desktop on macOS, visit the following URL for the installation package and detailed setup instructions:
[Install Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/)

---

#### For Linux Users
To install Docker Engine on Linux, visit the following URL. Select your Linux distribution (e.g., Ubuntu, CentOS, Fedora) and follow the instructions provided:
[Install Docker Engine for Linux](https://docs.docker.com/engine/install/)

---

#### For Ubuntu users (Davenport Hall Room 338 Computers)

Open an Ubuntu terminal window and enter the following commands:

```bash
# Step 1: Update the package lists
sudo apt-get update -y

# Step 2: Install prerequisite packages
# `ca-certificates`: Ensure HTTPS support
# `curl`: Command-line tool for downloading files
sudo apt-get install -y ca-certificates curl

# Step 3: Create a directory for Docker's GPG key
sudo install -m 0755 -d /etc/apt/keyrings

# Step 4: Download Docker's official GPG key
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc

# Step 5: Set permissions for the GPG key
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Step 6: Add Docker's repository to the system's Apt sources
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Step 7: Update package lists to include Docker's repository
sudo apt-get update -y

# Step 8: Install Docker packages
# `docker-ce`: Docker Community Edition
# `docker-ce-cli`: Command-line interface for Docker
# `containerd.io`: Container runtime for Docker
# `docker-buildx-plugin`: BuildKit plugin for Docker
# `docker-compose-plugin`: Docker Compose plugin
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Step 8: Revise Permissions
sudo groupadd docker
sudo usermod -aG docker $(whoami)
sudo systemctl restart docker
newgrp docker

---

#### Step 2: Verify Docker Installation

After installing Docker, confirm it is working correctly:

1. Open a terminal and run the following command:
   ```bash
   docker --version
   docker compose version
   ```
This should display the installed Docker version and Docker Compose version.

### Step 3: Confirm your installation

For Option 1 and Option 2, test the installation by running the following command in a terminal window:

    ```bash
    docker run hello-world
    ```
You should see something along the lines of the following:

---
Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
    (amd64)
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.

To try something more ambitious, you can run an Ubuntu container with:
 $ docker run -it ubuntu bash

Share images, automate workflows, and more with a free Docker ID:
 https://hub.docker.com/

For more examples and ideas, visit:
 https://docs.docker.com/get-started/