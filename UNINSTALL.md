# Uninstalling Claude Code Documentation Mirror

## Cross-Platform Uninstaller (v0.4.0+)

### Python Uninstaller (Recommended)

**Windows:**
```powershell
python "C:\Users\%USERNAME%\.claude-code-docs\uninstall.py"
```

**macOS/Linux:**
```bash
python3 ~/.claude-code-docs/uninstall.py
```

### Legacy Bash Uninstaller (macOS/Linux only)

**For v0.3+ installations:**
```bash
~/.claude-code-docs/uninstall.sh
```

**Or use the docs command:**
```bash
/docs uninstall
```

## What Gets Removed

The uninstaller will remove:

1. **The /docs command** from `~/.claude/commands/docs.md`
2. **All claude-code-docs hooks** from `~/.claude/settings.json`
3. **Installation directories** (only if they are clean git repositories):
   - **Windows**: `%USERPROFILE%\.claude-code-docs`
   - **macOS/Linux**: `~/.claude-code-docs`
4. **Preserves directories** with uncommitted changes or non-git directories

## Manual Uninstall

If you prefer to uninstall manually:

### 1. Remove the command file:
```bash
rm -f ~/.claude/commands/docs.md
```

### 2. Remove the hook from Claude settings:
Use /hooks in Claude Code CLI or Edit `~/.claude/settings.json` direction to remove the PreToolUse hook that references claude-code-docs.

### 3. Remove the installation directory:

For v0.3+:
```bash
rm -rf ~/.claude-code-docs
```

For older versions:
```bash
rm -rf /path/to/your/claude-code-docs
```

## Multiple Installations

If you have multiple installations (e.g., from testing different versions), the uninstaller will notify you about other locations it finds. You'll need to remove each one separately.

To find all installations:
```bash
find ~ -name "claude-code-docs" -type d 2>/dev/null | grep -v ".claude-code-docs"
```

## Backup Created

The uninstaller may create a backup of your Claude settings at `~/.claude/settings.json.backup` before removing hooks, just in case.

## Complete Removal

After uninstalling, there should be no traces left except:
- The backup file `~/.claude/settings.json.backup` (if hooks were removed)
- Any custom files you added to the installation directory

## Reinstalling

**Windows:**
```powershell
curl -o install.py https://raw.githubusercontent.com/mccloudmedia/claude-code-docs/main/install.py; python install.py
```

**macOS/Linux (Python installer):**
```bash
curl -o install.py https://raw.githubusercontent.com/mccloudmedia/claude-code-docs/main/install.py && python3 install.py
```

**macOS/Linux (Legacy bash):**
```bash
curl -fsSL https://raw.githubusercontent.com/mccloudmedia/claude-code-docs/main/install.sh | bash
```
