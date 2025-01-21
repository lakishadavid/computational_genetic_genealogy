# Cloning the Course Repository

After installing Git and VSCode, our next step is to download (or "clone" in Git terminology) the course materials from GitHub. In computational research, code sharing platforms like GitHub are essential for distributing analysis pipelines and datasets. For this course, we'll be working with a repository that contains computational tools for genetic genealogy analysis.

## Understanding Git Clone vs. ZIP Download

GitHub offers two ways to get repository files: cloning and downloading as a ZIP file. While downloading a ZIP might seem simpler, we'll use cloning for several important reasons:

### Why Clone?
- **Version Control**: Cloning maintains the Git connection, allowing you to:
  - Easily get updates when course materials are modified
  - Track your own changes to the code
  - Submit your work through Git if required
- **Complete History**: Access the full development history of the course materials
- **Reproducibility**: Better align with research best practices for computational reproducibility
- **Real-world Practice**: Learn workflows used in research and industry

### When to Download ZIP?
While we'll use cloning in this course, downloading a ZIP file can be useful when:
- You only need a quick read-only copy of the files
- You're on a restricted system where Git installation isn't possible
- You want to share code with someone who doesn't use Git

To download as ZIP:
1. Visit the repository on GitHub
2. Click the green "Code" button
3. Select "Download ZIP"

However, note that the ZIP download:
- Won't track future updates to course materials
- Doesn't include version control capabilities
- Requires manually downloading again for updates

## Choosing Where to Clone

### For Windows (non-WSL2) Users
- Choose a location in your Windows filesystem (e.g., `Documents/Courses`)
- Avoid paths with spaces or special characters

### For WSL2 Users
- Recommended: Clone into your WSL2 filesystem (e.g., `~/courses` or `/home/yourusername/courses`)
- Why? Better performance and compatibility with Linux-based tools
- Note: You can still access these files from Windows at `\\wsl$\Ubuntu\home\yourusername\courses`
- Avoid cloning into Windows filesystem mounted in WSL2 (`/mnt/c/...`) for better performance

### For macOS/Linux Users
- Choose any location in your home directory (e.g., `~/courses`)
- Avoid paths with spaces or special characters

## Cloning Options

You can clone the repository in two ways - through VSCode or using the command line. Choose the method you're most comfortable with.

### Option 1: Cloning via Command Line (Recommended for Researchers)

This method works universally across all systems and helps build command-line familiarity.

1. Open your terminal:
   - **Windows**: Command Prompt or PowerShell
   - **WSL2**: WSL2 terminal or VSCode's integrated WSL2 terminal
   - **macOS/Linux**: Terminal app

2. Navigate to where you want to store the course materials:
   ```
   cd path/to/your/preferred/directory
   ```
   Examples:
   - Windows: `cd Documents\Courses`
   - WSL2: `cd ~/courses`
   - macOS/Linux: `cd ~/courses`

3. Clone the repository:
   ```
   git clone https://github.com/lakishadavid/computational_genetic_genealogy.git
   ```

4. Navigate into the new directory:
   ```
   cd computational_genetic_genealogy
   ```

### Option 2: Cloning via VSCode

1. Open VSCode
   - WSL2 users: Make sure you're in a WSL2 window (check bottom-left corner)

2. Access the Command Palette:
   - Keyboard shortcut: `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS)
   - Alternative navigation: View → Command Palette

3. Type "Git: Clone" and select it from the dropdown

4. Enter the repository URL:
   ```
   https://github.com/lakishadavid/computational_genetic_genealogy
   ```

5. Choose a location to save the repository:
   - WSL2 users: Select a location in your WSL2 filesystem
   - Others: Choose any convenient location

6. If prompted to open the repository, click "Open"

## Verification

After cloning, verify that you have the course materials:

1. You should see a new directory named `computational_genetic_genealogy`

2. Inside this directory, you should find several files and folders

3. Run this command to verify Git is tracking the repository:
   ```
   git status
   ```
   You should see a message indicating this is a Git repository

4. WSL2 users - verify access:
   - Try accessing files from both WSL2 and Windows
   - In VSCode, ensure you can open and edit files
   - Terminal commands should work in both WSL2 terminal and VSCode's integrated terminal

## Troubleshooting

Common issues you might encounter:

1. **"Permission denied" error**
   - Check if you have a GitHub account and are logged in
   - Ensure you have stable internet connection
   - Verify you have write permissions in your chosen directory
   - WSL2 users: Check file permissions in WSL2 filesystem

2. **"Could not resolve host" error**
   - Check your internet connection
   - Verify the repository URL is correct
   - If you're behind a university proxy, configure Git to use it:
     ```
     git config --global http.proxy http://proxy.university.edu:port
     ```
   - WSL2 users: Ensure WSL2 has network connectivity

3. **Empty or incomplete repository**
   - Try cloning again
   - Check your internet connection stability
   - Verify you're using the correct repository URL

4. **WSL2-specific issues**
   - "Error: Permission denied": Use `chmod` to fix permissions
   - Slow performance: Ensure you're not working in `/mnt/c/`
   - VSCode not connecting: Reload WSL2 window

## Next Steps

Once you've successfully cloned the repository, you'll have local access to all course materials. In later lessons, we'll learn how to:
- Navigate the repository structure
- Update your local copy when new materials are added
- Use Git to manage your own analysis code

If you encounter any issues during this process, please reach out to the course instructor for assistance.

## Additional Resources

- [GitHub's Guide to Cloning](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)
- [Git Clone Documentation](https://git-scm.com/docs/git-clone)
- [Visual Studio Code Git Integration](https://code.visualstudio.com/docs/editor/versioncontrol)
- [Working with WSL2 in VSCode](https://code.visualstudio.com/docs/remote/wsl)
