#############################################################
# Installing WSL2 and Ubuntu from the Microsoft Store (Instructions for MacOS users below)
#############################################################

Follow these steps to install WSL2 and Ubuntu on your Windows system directly through the Microsoft Store.

---

## **1. Open the Microsoft Store**
1. Press the `Windows` key to open the Start Menu.
2. Type **Microsoft Store** and press `Enter` to open it.

---

## **2. Search for Ubuntu**
1. Inside the Microsoft Store, click the **Search bar** (usually at the top).
2. Type **Ubuntu** and press `Enter`.

---

## **3. Choose a Version**
1. Select one of the available Ubuntu versions (e.g., **Ubuntu 22.04 LTS**).
2. Click the **Get** or **Install** button. This will download and install the Ubuntu app on your system.

---

## **4. Wait for Installation**
1. The store will automatically download and install Ubuntu. You will see the progress in the Microsoft Store.
2. Once the installation is complete, you will see an **Open** button.

---

## **5. Open and Set Up Ubuntu**
1. Click the **Open** button in the Microsoft Store, or search for **Ubuntu** in the Start Menu and open it.
2. On the first launch, Ubuntu will complete its installation. This process may take a few minutes.
3. After installation, you will be prompted to create:
   - A **username** for the Ubuntu environment.
   - A **password** for your new user (this does not have to match your Windows credentials).

---

## **6. Update Ubuntu**
Once you are in the Ubuntu terminal, update its packages to ensure everything is up to date:
```
sudo apt-get update && sudo apt-get upgrade -y
```


## **7. In your Ubuntu terminal window**
```
git --version
```
If you do not see a git version or get a message indicating that git is not installed, enter:
```
sudo apt-get install git curl build-essential -y
git --version
```
You should now see the version of git installed on your computer.

Now we need to setup the git configuration. Enter:
```
git config --global user.name "FirstName LastName"
git config --global user.email "youremail@address.com"
```
#############################################################
# Comprehensive Guide for Mac Users to Install and Run Ubuntu
#############################################################

This guide provides instructions for Mac users to **install and run an Ubuntu environment** on their system. It includes multiple methods, such as virtualization (e.g., VirtualBox, Multipass) and lightweight containers (e.g., Docker), allowing you to choose the best solution for your needs.

---

## **1. Install VirtualBox to Run a Full Ubuntu System**

VirtualBox allows you to run a complete Ubuntu system in a virtual machine on your Mac.

### Step-by-Step Instructions:
1. **Install VirtualBox:**
   - Open the Terminal on your Mac.
   - Use Homebrew to install VirtualBox:
     ```bash
     brew install --cask virtualbox
     ```

2. **Download Ubuntu ISO:**
   - Visit the official [Ubuntu Downloads Page](https://ubuntu.com/download).
   - Download the latest version of the Ubuntu ISO file (e.g., Ubuntu 22.04 LTS).

3. **Set Up the Virtual Machine:**
   - Open **VirtualBox**.
   - Click on **New** to create a new virtual machine.
   - Set the following:
     - **Name:** Ubuntu
     - **Type:** Linux
     - **Version:** Ubuntu (64-bit)
   - Assign **RAM and CPU** resources (e.g., 4GB RAM, 2 CPUs).
   - Create a new virtual hard disk and allocate at least 20GB of storage.

4. **Install Ubuntu:**
   - Start the virtual machine and select the downloaded Ubuntu ISO as the startup disk.
   - Follow the on-screen instructions to complete the Ubuntu installation.

5. **Access Ubuntu:**
   - Once installed, you can start the virtual machine anytime from VirtualBox.

---

## **2. Use Multipass for a Lightweight Virtual Ubuntu Environment**

Multipass is a simpler tool for running Ubuntu instances directly on your Mac without complex virtual machine configurations.

### Step-by-Step Instructions:
1. **Install Multipass:**
   - Use Homebrew to install Multipass:
     ```bash
     brew install --cask multipass
     ```

2. **Launch an Ubuntu Instance:**
   - Start an Ubuntu instance with:
     ```bash
     multipass launch --name ubuntu
     ```
   - By default, it will launch the latest Ubuntu LTS version.

3. **Access the Ubuntu Shell:**
   - Connect to the instance:
     ```bash
     multipass shell ubuntu
     ```

4. **Manage Instances:**
   - List running instances:
     ```bash
     multipass list
     ```
   - Stop or delete an instance:
     ```bash
     multipass stop ubuntu
     multipass delete ubuntu
     multipass purge
     ```

---

## **3. Use Docker for a Minimal Ubuntu Environment**

If you only need a lightweight Ubuntu terminal, Docker is a great option.

### Step-by-Step Instructions:
1. **Install Docker:**
   - Use Homebrew to install Docker:
     ```bash
     brew install --cask docker
     ```

2. **Start Docker Desktop:**
   - Open Docker Desktop from your Applications folder and ensure it is running.

3. **Run an Ubuntu Container:**
   - Pull and run the latest Ubuntu image:
     ```bash
     docker run -it ubuntu
     ```
   - This gives you a minimal Ubuntu environment in a container.

4. **Persist Data (Optional):**
   - Use volume mapping to save data:
     ```bash
     docker run -it -v ~/ubuntu_data:/data ubuntu
     ```

---

## **4. Install Ubuntu-Like Tools on macOS**

If you don't need a full Ubuntu system, you can install commonly used Linux tools on macOS.

### Step-by-Step Instructions:
1. **Install Homebrew:**
   - Install Homebrew if it's not already installed:
     ```bash
     /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
     ```

2. **Install Common Linux Tools:**
   - Use Homebrew to install tools like `wget`, `curl`, `gcc`, etc.:
     ```bash
     brew install wget curl gcc
     ```

3. **Install Python:**
   - Use Homebrew to install Python:
     ```bash
     brew install python
     ```

4. **Install Linuxbrew for `apt`-like Functionality (Optional):**
   - Tap the Linuxbrew core:
     ```bash
     brew tap homebrew/linuxbrew-core
     ```
   - Install `apt`:
     ```bash
     brew install apt
     ```

---

## **5. Summary of Methods**

| Method               | Use Case                                             |
|----------------------|-----------------------------------------------------|
| **VirtualBox**       | Full Ubuntu system with GUI.                        |
| **Multipass**        | Lightweight Ubuntu instances for quick tasks.       |
| **Docker**           | Minimal Ubuntu environment for development.         |
| **Linuxbrew Tools**  | Install common Linux tools directly on macOS.       |

Choose the method that best fits your needs. With these instructions, you can easily set up and run an Ubuntu environment on macOS.

## **6. Update Ubuntu**
Once you are in the Ubuntu terminal, update its packages to ensure everything is up to date:
```
sudo apt-get update && sudo apt-get upgrade -y
```


## **7. In your Ubuntu terminal window**
```
git --version
```
If you do not see a git version or get a message indicating that git is not installed, enter:
```
sudo apt-get install git curl build-essential -y
git --version
```
You should now see the version of git installed on your computer.

Now we need to setup the git configuration. Enter:
```
git config --global user.name "FirstName LastName"
git config --global user.email "youremail@address.com"
