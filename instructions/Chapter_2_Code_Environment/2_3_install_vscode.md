# Installing Visual Studio Code (VSCode)

Visual Studio Code (VSCode) is a powerful, free code editor that we'll use throughout this course. While there are many code editors available (like PyCharm, Sublime Text, or Jupyter), we've chosen VSCode because it:
- Provides excellent integration with Git and Docker
- Offers a consistent experience across all operating systems
- Includes built-in features for scientific computing
- Is widely used in both research and industry

## Installation Instructions

### Step 1: Download and Install VSCode

1. Visit the [VSCode Downloads Page](https://code.visualstudio.com/download)
2. Download the appropriate version for your system:
   - **Windows**: 
     - Regular Windows: Download the .exe installer
     - WSL2 users: Download the .exe installer, but also see the WSL extension setup below
   - **macOS**: Choose between Intel or Apple Silicon versions
   - **Linux**: Select the appropriate package format (.deb, .rpm, etc.)
3. Run the installer:
   - **Windows**: 
     - Regular Windows: Run the .exe file and follow the prompts
     - WSL2 users: Install in Windows, not in WSL2 environment
   - **macOS**: Drag Visual Studio Code.app to your Applications folder
   - **Linux**: Use your package manager or software center to install the downloaded package

### Step 2: Verify Installation

1. Launch VSCode:
   - **Windows**: 
     - Regular Windows: Search for "Visual Studio Code" in the Start Menu
     - WSL2 users: Launch from Start Menu, then connect to WSL (we'll cover this in extension setup)
   - **macOS**: Open from Applications folder or use Spotlight (Cmd + Space)
   - **Linux**: Search for "code" in your applications menu

2. Check the version:
   - Keyboard shortcut: `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS)
   - Alternative navigation: Click View → Command Palette
   - Type "About" and select "About Visual Studio Code"
   - You should see version information

## Essential Extensions for This Course

VSCode becomes more powerful through extensions. Here are the ones we'll need:

### Required Extensions
1. **Python Extension Pack** (by Microsoft)
   - Provides Python language support
   - Includes debugging tools
   - Enables Jupyter notebook integration
   - **Why**: Essential for all Python development in this course

2. **WSL** (by Microsoft)
   - Required for WSL2 users
   - Enables seamless development in WSL2 environment
   - **Why**: Ensures consistent environment for WSL2 users

3. **Docker** (by Microsoft)
   - Enables Docker container management
   - Provides container visualization
   - **Why**: We'll use Docker for our computational environment

4. **Git Graph** (by mhutchie)
   - Visualizes Git history
   - Makes Git operations more intuitive
   - **Why**: Helps understand version control operations

5. **Jupyter** (by Microsoft)
   - Already included in Python Extension Pack
   - Enhanced notebook support
   - **Why**: We'll use Jupyter notebooks for analysis

6. **Remote Development** (by Microsoft)
   - Includes WSL, SSH, and Dev Containers extensions
   - **Why**: Essential for WSL2 users and container development

7. **Code Spell Checker** (by Street Side Software)
   - Helps catch typos in code and comments
   - **Why**: Important for documentation and reproducibility

### Installing Extensions

1. Open the Extensions panel:
   - Keyboard shortcut: `Ctrl+Shift+X` (Windows/Linux) or `Cmd+Shift+X` (macOS)
   - Alternative navigation: Click View → Extensions or click the Extensions icon in the left sidebar
   
2. Search for each required extension by name and verify the publisher (listed above)

3. Click "Install" for each extension

4. Restart VSCode when prompted

## Configuring VSCode

### Basic Settings
1. Open Settings:
   - Keyboard shortcut: `Ctrl+,` (Windows/Linux) or `Cmd+,` (macOS)
   - Alternative navigation: File → Preferences → Settings (Windows/Linux) or Code → Preferences → Settings (macOS)

2. Recommended settings for research:
   - Enable "Auto Save": Files → Auto Save
   - Set "Editor: Font Size": Search for "font size" in settings
   - Enable "Editor: Word Wrap": Search for "word wrap" in settings

### Python Configuration
1. Select a Python interpreter:
   - Keyboard shortcut: `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS)
   - Alternative navigation: View → Command Palette
   - Type "Python: Select Interpreter"
   - Choose your installed Python version
   (Note: We'll update this after setting up Docker)

## Verification Steps

Ensure everything is working:

1. **Basic Python Test**
   - Create a new file: File → New File or `Ctrl+N`/`Cmd+N`
   - Save it as `test.py`
   - Type: `print("Hello, Computational Genetic Genealogy!")`
   - Run: Click play button or right-click → Run Python File

2. **Jupyter Notebook Test**
   - Create new notebook: Command Palette → "Create New Jupyter Notebook"
   - In a cell, type: `import pandas as pd`
   - In another cell: `pd.DataFrame({'test': [1,2,3]})`
   - Run both cells using the play button or `Shift+Enter`

3. **Git Integration Test**
   - Open Command Palette
   - Type "Git: Show Git Graph"
   - Should open Git Graph panel (empty until we clone repository)

4. **WSL Test** (WSL2 users only)
   - Click the green button in bottom left corner
   - Select "New WSL Window"
   - Verify you can access your WSL2 filesystem

5. **Docker Extension Test**
   - Look for Docker icon in left sidebar
   - Click it to open Docker panel
   - Should show Docker connection status

## Troubleshooting

Common issues and solutions:

1. **VSCode won't launch**
   - Try uninstalling and reinstalling
   - Check system requirements
   - Verify your user account has proper permissions
   - WSL2 users: Ensure WSL2 is properly installed

2. **Python extension not working**
   - Ensure Python is installed on your system
   - WSL2 users: Install Python in WSL2 environment
   - Reload VSCode
   - Select the correct interpreter

3. **Git integration not showing**
   - Verify Git is installed (from our previous lesson)
   - WSL2 users: Install Git in WSL2 environment
   - Reload VSCode
   - Check Git configuration

## Next Steps

Once VSCode is set up, we'll:
1. Use it to clone our course repository
2. Configure it for Docker development
3. Start working with our computational tools

If you encounter any issues during setup, please reach out to the course instructor for assistance.

## Additional Resources

- [VSCode Documentation](https://code.visualstudio.com/docs)
- [Python in VSCode](https://code.visualstudio.com/docs/languages/python)
- [WSL in VSCode](https://code.visualstudio.com/docs/remote/wsl)
- [VSCode Tips and Tricks](https://code.visualstudio.com/docs/getstarted/tips-and-tricks)