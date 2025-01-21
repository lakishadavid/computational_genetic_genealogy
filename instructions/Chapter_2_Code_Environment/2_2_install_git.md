# Installing and Configuring Git

In computational genetic genealogy, managing code and data effectively is crucial. Git is the industry standard version control system that helps us track changes, collaborate with other researchers, and maintain reproducible research workflows. Throughout this course, you'll use Git to access course materials and manage your own code developments.

## What is Git?
Git is a distributed version control system originally developed by Linus Torvalds (creator of Linux) to manage large software projects. In research, Git helps us:
- Track changes in our code and analysis scripts
- Collaborate with other researchers without overwriting each other's work
- Maintain different versions of our analysis pipelines
- Document when and why changes were made
- Share our work with the broader scientific community

## Installation Instructions

Before installing, note that Git might already be installed on your system. If you're using a Unix-based system (macOS or Linux), Git often comes pre-installed. We'll verify this in the steps below.

### Windows
1. Download the Git installer from [Git for Windows](https://gitforwindows.org/)
2. Run the downloaded .exe file
3. During installation:
   - Accept the default options
   - When prompted about "Adjusting your PATH environment", select "Git from the command line and also from 3rd-party software" - this ensures Git is accessible from any terminal
   - For "Configuring the line ending conversions", choose "Checkout Windows-style, commit Unix-style line endings" - this helps prevent compatibility issues when sharing code

### macOS
1. If you have [Homebrew](https://brew.sh/) installed:
   ```
   brew install git
   ```
2. Otherwise, download the installer from [Git Downloads](https://git-scm.com/download/mac)

### Linux (Ubuntu/Debian)
```
sudo apt-get update
sudo apt-get install git
```

For other Linux distributions, see [Git Downloads](https://git-scm.com/download/linux)

## Verifying Your Installation

1. Open a terminal:
   - **Windows**: Press Windows + R, type cmd, and press Enter
   - **macOS**: Press Command + Space, type terminal, and press Enter
   - **Linux**: Press Ctrl + Alt + T

2. Verify Git is installed by typing:
   ```
   git --version
   ```
   You should see something like: `git version 2.x.x`

## Initial Configuration

After installing Git, you'll need to set up your identity. This information will be associated with any changes you make to the code:
```
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

This configuration step is important for research reproducibility and collaboration, as it helps track who made which changes to the analysis pipeline.

## ON 338 Davenport Hall Computers
```
wsl --install -d Ubuntu
```
Follow the prompts. enter username: ubuntu, password: ubuntu.
For here on out, you should be able to search for Ubuntu to launch the Ubuntu window. 
In the Ubuntu window, enter
```
lsb_release -a
```
The Ubuntu version should be at least Ubuntu 24.04.1 LTS.


## Troubleshooting

### Common Issues

1. **"git is not recognized as an internal or external command" (Windows)**
   - Close and reopen your command prompt (the PATH needs to be refreshed)
   - If the error persists, check if Git is added to your PATH:
     1. Search for "Environment Variables" in Windows
     2. Under System Variables, find and select "Path"
     3. Check if Git's installation path (typically `C:\Program Files\Git\cmd`) is listed

2. **"Permission denied" (macOS/Linux)**
   - Add `sudo` before the installation command
   - Ensure you have administrator privileges
   - On university computers, you might need to contact IT for installation permissions

3. **Installation fails**
   - Temporarily disable antivirus software
   - Run the installer as administrator
   - Clear download cache and try downloading again
   - On managed computers (like university labs), contact your IT department

## Verification Exercise

To ensure everything is working:

1. Open your terminal
2. Run these commands:
   ```
   git --version
   git config --global user.name
   git config --global user.email
   ```
3. You should see your Git version and the name/email you configured

## Next Steps

Once Git is installed and configured, we'll use it to clone our course repository containing the genetic genealogy analysis tools and datasets we'll use throughout the semester. If you encounter any issues during installation, please reach out to the course instructor for assistance.

## Additional Resources

While we'll cover the Git commands needed for this course, if you're interested in learning more:
- [Git Documentation](https://git-scm.com/doc)
- [GitHub's Git Guides](https://github.com/git-guides)
- [Version Control in Research](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1004668) - An excellent paper on using version control in computational research
