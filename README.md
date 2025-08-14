# Claude Code Documentation Mirror

[![Last Update](https://img.shields.io/github/last-commit/ericbuess/claude-code-docs/main.svg?label=docs%20updated)](https://github.com/ericbuess/claude-code-docs/commits/main)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-blue)]()
[![Beta](https://img.shields.io/badge/status-early%20beta-orange)](https://github.com/ericbuess/claude-code-docs/issues)

Local mirror of Claude Code documentation files from https://docs.anthropic.com/en/docs/claude-code/, updated every 3 hours.

## ⚠️ Early Beta Notice

**This is an early beta release**. There may be errors or unexpected behavior. If you encounter any issues, please [open an issue](https://github.com/ericbuess/claude-code-docs/issues) - your feedback helps improve the tool!

## 🆕 Version 0.4.0 - Windows Compatibility

**New in this version:**
- 🪟 **Windows Support**: Full Windows 10+ compatibility with PowerShell and Command Prompt
- 🐍 **Python Installer**: Cross-platform Python installer replaces bash-only version
- 🔧 **Dependency Reduction**: Eliminates jq and curl dependencies
- 🛡️ **Enhanced Safety**: Better error handling and recovery across all platforms
- 🍎 **macOS/Linux**: Maintains full compatibility with improved reliability

To update:
```bash
# Windows (PowerShell)
curl -o install.py https://raw.githubusercontent.com/ericbuess/claude-code-docs/main/install.py; python install.py

# macOS/Linux (Python installer)
curl -o install.py https://raw.githubusercontent.com/ericbuess/claude-code-docs/main/install.py && python3 install.py

# macOS/Linux (Legacy bash)
curl -fsSL https://raw.githubusercontent.com/ericbuess/claude-code-docs/main/install.sh | bash
```

## Why This Exists

- **Faster access** - Reads from local files instead of fetching from web
- **Automatic updates** - Attempts to stay current with the latest documentation
- **Track changes** - See what changed in docs over time
- **Claude Code changelog** - Quick access to official release notes and version history
- **Better Claude Code integration** - Allows Claude to explore documentation more effectively

## Platform Compatibility

- ✅ **Windows**: Fully supported (Windows 10+, PowerShell and Command Prompt)
- ✅ **macOS**: Fully supported (tested on macOS 12+)
- ✅ **Linux**: Fully supported (Ubuntu, Debian, Fedora, etc.)

### Prerequisites

This tool requires the following to be installed:
- **Python 3.6+** - For running the cross-platform installer (usually pre-installed on macOS/Linux)
- **git** - For cloning and updating the repository (usually pre-installed)
- **Claude Code** - Obviously :)

**Note**: The new Python installer eliminates the need for `jq` and `curl` dependencies!

## Installation

### Windows
Download and run the Python installer:

```powershell
# Download the installer
curl -o install.py https://raw.githubusercontent.com/ericbuess/claude-code-docs/main/install.py
# Run the installer
python install.py
```

Or using PowerShell's `Invoke-WebRequest`:

```powershell
# Download and run in one step
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/ericbuess/claude-code-docs/main/install.py" -OutFile "install.py"; python install.py
```

### macOS/Linux (New Python Installer)
```bash
curl -o install.py https://raw.githubusercontent.com/ericbuess/claude-code-docs/main/install.py && python3 install.py
```

### macOS/Linux (Legacy Bash Installer)
```bash
curl -fsSL https://raw.githubusercontent.com/ericbuess/claude-code-docs/main/install.sh | bash
```

This will:
1. Install to the appropriate location:
   - **Windows**: `%USERPROFILE%\.claude-code-docs` (e.g., `C:\Users\YourName\.claude-code-docs`)
   - **macOS/Linux**: `~/.claude-code-docs`
2. Create the `/docs` slash command with platform-appropriate helper scripts
3. Set up automatic update hooks in Claude Code settings

**Note**: The command is `/docs (user)` - it will show in your command list with "(user)" after it to indicate it's a user-created command.

## Usage

The `/docs` command provides instant access to documentation with optional freshness checking.

### Default: Lightning-fast access (no checks)
```bash
/docs hooks        # Instantly read hooks documentation
/docs mcp          # Instantly read MCP documentation
/docs memory       # Instantly read memory documentation
```

You'll see: `📚 Reading from local docs (run /docs -t to check freshness)`

### Check documentation sync status with -t flag
```bash
/docs -t           # Show sync status with GitHub
/docs -t hooks     # Check sync status, then read hooks docs
/docs -t mcp       # Check sync status, then read MCP docs
```

### See what's new
```bash
/docs what's new   # Show recent documentation changes with diffs
```

### Read Claude Code changelog
```bash
/docs changelog    # Read official Claude Code release notes and version history
```

The changelog feature fetches the latest release notes directly from the official Claude Code repository, showing you what's new in each version.

### Uninstall
```bash
/docs uninstall    # Get commnd to remove claude-code-docs completely
```

### Creative usage examples
```bash
# Natural language queries work great
/docs what environment variables exist and how do I use them?
/docs explain the differences between hooks and MCP

# Check for recent changes
/docs -t what's new in the latest documentation?
/docs changelog    # Check Claude Code release notes

# Search across all docs
/docs find all mentions of authentication
/docs how do I customize Claude Code's behavior?
```

## How Updates Work

The documentation attempts to stay current:
- GitHub Actions runs periodically to fetch new documentation
- When you use `/docs`, it checks for updates
- Updates are pulled when available
- You may see "🔄 Updating documentation..." when this happens

Note: If automatic updates fail, you can always run the installer again to get the latest version.

## Updating from Previous Versions

Regardless of which version you have installed, simply run:

```bash
curl -fsSL https://raw.githubusercontent.com/ericbuess/claude-code-docs/main/install.sh | bash
```

The installer will handle migration and updates automatically.

## Troubleshooting

### Command not found
If `/docs` returns "command not found":
1. Check if the command file exists: `ls ~/.claude/commands/docs.md`
2. Restart Claude Code to reload commands
3. Re-run the installation script

### Documentation not updating
If documentation seems outdated:
1. Run `/docs -t` to check sync status and force an update
2. Manually update: `cd ~/.claude-code-docs && git pull`
3. Check if GitHub Actions are running: [View Actions](https://github.com/ericbuess/claude-code-docs/actions)

### Installation errors
- **"Python not found"**: Install Python 3.6+ from python.org or Windows Store
- **"git not found"**: Install Git for Windows from git-scm.com
- **"Failed to clone repository"**: Check your internet connection and firewall settings
- **"Permission denied"**: On Windows, run as Administrator or check antivirus software
- **"Failed to update settings.json"**: Check file permissions on Claude settings directory

## Uninstalling

To completely remove the docs integration:

```bash
/docs uninstall
```

Or run:
```bash
~/.claude-code-docs/uninstall.sh
```

See [UNINSTALL.md](UNINSTALL.md) for manual uninstall instructions.

## Security Notes

- The installer modifies `~/.claude/settings.json` to add an auto-update hook
- The hook only runs `git pull` when reading documentation files
- All operations are limited to the documentation directory
- No data is sent externally - everything is local
- **Repository Trust**: The installer clones from GitHub over HTTPS. For additional security, you can:
  - Fork the repository and install from your own fork
  - Clone manually and run the installer from the local directory
  - Review all code before installation

## What's New

### v0.4.0 (Latest) - Windows Compatibility
- **🪟 Full Windows Support**: Works on Windows 10+ with PowerShell and Command Prompt
- **🐍 Cross-Platform Python Installer**: Replaces bash-only installer with Python version
- **🔧 Dependency Elimination**: No longer requires jq or curl
- **🛡️ Enhanced Safety**: Better error handling and atomic file operations
- **🚀 Improved Performance**: Faster dependency checking and git operations

### v0.3.3
- Added Claude Code changelog integration (`/docs changelog`)
- Fixed shell compatibility for macOS users (zsh/bash)
- Improved documentation and error messages
- Added platform compatibility badges

## Contributing

**Contributions are welcome!** This is a community project and we'd love your help:

- 🪟 **Windows Support**: Want to help add Windows compatibility? [Fork the repository](https://github.com/ericbuess/claude-code-docs/fork) and submit a PR!
- 🐛 **Bug Reports**: Found something not working? [Open an issue](https://github.com/ericbuess/claude-code-docs/issues)
- 💡 **Feature Requests**: Have an idea? [Start a discussion](https://github.com/ericbuess/claude-code-docs/issues)
- 📝 **Documentation**: Help improve docs or add examples

You can also use Claude Code itself to help build features - just fork the repo and let Claude assist you!

## Known Issues

As this is an early beta, you might encounter some issues:
- Auto-updates may occasionally fail on some network configurations
- Some documentation links might not resolve correctly

If you find any issues not listed here, please [report them](https://github.com/ericbuess/claude-code-docs/issues)!

## License

Documentation content belongs to Anthropic.
This mirror tool is open source - contributions welcome!
