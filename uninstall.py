#!/usr/bin/env python3
"""
Claude Code Docs Cross-Platform Uninstaller
Converts from bash-only to Windows/macOS/Linux support

This uninstaller replaces uninstall.sh with cross-platform Python implementation.
"""

import os
import sys
import platform
import json
import shutil
import subprocess
from pathlib import Path
import re
from typing import List, Optional

# Version
UNINSTALLER_VERSION = "0.4.0"

class CrossPlatformUninstaller:
    def __init__(self):
        self.os_type = self._detect_os()
        self.claude_dir = self._get_claude_dir()
        self.installations = []
        
        # Print OS detection info (use ASCII for Windows compatibility)
        print(f"[+] Detected {self.os_type.title()}")
        print(f"[+] Claude directory: {self.claude_dir}")
        print("")
        
    def _detect_os(self) -> str:
        """Detect operating system type"""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "darwin":
            return "macos"
        elif system == "linux":
            return "linux"
        else:
            # Default to linux for other unix-like systems
            return "linux"
    
    def _get_claude_dir(self) -> Path:
        """Get Claude configuration directory for this platform"""
        if self.os_type == "windows":
            # Use USERPROFILE on Windows instead of ~
            user_profile = os.environ.get("USERPROFILE")
            if user_profile:
                return Path(user_profile) / ".claude"
            else:
                # Fallback to HOME if USERPROFILE is not set
                home = os.environ.get("HOME")
                if home:
                    return Path(home) / ".claude"
                else:
                    raise RuntimeError("Could not determine user home directory on Windows")
        else:
            # macOS and Linux use ~ which expands to HOME
            home = os.environ.get("HOME")
            if home:
                return Path(home) / ".claude"
            else:
                # Fallback using Path.home() for cross-platform compatibility
                return Path.home() / ".claude"
    
    def _find_git_executable(self) -> Optional[str]:
        """Find git executable path across platforms"""
        # Common git executable names
        git_names = ["git"]
        if self.os_type == "windows":
            git_names.extend(["git.exe", "git.cmd"])
        
        # Try to find git in PATH
        for git_name in git_names:
            try:
                result = subprocess.run(
                    ["where" if self.os_type == "windows" else "which", git_name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    git_path = result.stdout.strip().split('\n')[0]  # Take first result
                    # Verify it works
                    try:
                        test_result = subprocess.run(
                            [git_path, "--version"],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if test_result.returncode == 0:
                            return git_path
                    except (subprocess.TimeoutExpired, OSError):
                        continue
            except (subprocess.TimeoutExpired, OSError):
                continue
        
        # Platform-specific fallback paths
        if self.os_type == "windows":
            fallback_paths = [
                r"C:\Program Files\Git\bin\git.exe",
                r"C:\Program Files (x86)\Git\bin\git.exe",
                r"C:\Git\bin\git.exe",
                r"C:\msys64\usr\bin\git.exe",
                r"C:\Program Files\Git\cmd\git.exe",
            ]
            for path in fallback_paths:
                if Path(path).exists():
                    try:
                        test_result = subprocess.run(
                            [path, "--version"],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if test_result.returncode == 0:
                            return path
                    except (subprocess.TimeoutExpired, OSError):
                        continue
        
        return None
    
    def _run_git_command(self, args: List[str], cwd: Optional[Path] = None) -> Optional[subprocess.CompletedProcess]:
        """Run a git command with proper error handling"""
        git_exe = self._find_git_executable()
        if not git_exe:
            return None
        
        try:
            return subprocess.run(
                [git_exe] + args,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
        except (subprocess.TimeoutExpired, OSError):
            return None
    
    def _git_has_uncommitted_changes(self, repo_dir: Path) -> bool:
        """Check if repository has uncommitted changes
        
        Equivalent to bash: [[ -z "$(git status --porcelain 2>/dev/null)" ]]
        Returns True if there ARE uncommitted changes (opposite of bash logic for clarity)
        """
        try:
            result = self._run_git_command(["status", "--porcelain"], cwd=repo_dir)
            if result is None or result.returncode != 0:
                # If git command fails, assume there might be changes (be conservative)
                return True
            
            # If output is empty, there are no changes
            return bool(result.stdout.strip())
        except Exception:
            # If anything goes wrong, assume there might be changes (be conservative)
            return True

    def find_installations(self) -> List[Path]:
        """Find all claude-code-docs installations
        
        Converts the bash find_all_installations() function to Python.
        Searches ~/.claude/commands/docs.md and ~/.claude/settings.json for
        installation paths from various versions.
        """
        paths = []
        
        # Check command file for paths
        docs_command_file = self.claude_dir / "commands" / "docs.md"
        if docs_command_file.exists():
            try:
                with open(docs_command_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        
                        # v0.1 format: LOCAL DOCS AT: /path/to/claude-code-docs/docs/
                        # Pattern: LOCAL\ DOCS\ AT:\ ([^[:space:]]+)/docs/
                        v01_match = re.search(r'LOCAL\s+DOCS\s+AT:\s+([^\s]+)/docs/', line)
                        if v01_match:
                            path_str = v01_match.group(1)
                            # Convert ~ to home directory (bash: ${path/#\~/$HOME})
                            if path_str.startswith('~'):
                                path_str = str(Path.home()) + path_str[1:]
                            
                            path = Path(path_str)
                            if path.is_dir():
                                paths.append(path)
                        
                        # v0.2+ format: Execute: /path/to/claude-code-docs/helper.sh
                        # Pattern: Execute:.*claude-code-docs
                        if re.search(r'Execute:.*claude-code-docs', line):
                            # Extract path from various formats (bash: grep -o '[^ "]*claude-code-docs[^ "]*')
                            path_matches = re.findall(r'[^ "]*claude-code-docs[^ "]*', line)
                            if path_matches:
                                path_str = path_matches[0]  # Take first match (equivalent to head -1)
                                
                                # Convert ~ to home directory
                                if path_str.startswith('~'):
                                    path_str = str(Path.home()) + path_str[1:]
                                
                                path = Path(path_str)
                                # Get directory part
                                if path.is_dir():
                                    paths.append(path)
                                elif path.parent.is_dir() and path.parent.name == "claude-code-docs":
                                    # If path points to a file, check if parent dir is claude-code-docs
                                    paths.append(path.parent)
                                    
            except Exception as e:
                # Don't fail uninstall if we can't read command file
                print(f"[WARNING] Could not read command file {docs_command_file}: {e}")
        
        # Check settings.json hooks for paths
        settings_file = self.claude_dir / "settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)
                
                # Extract hook commands (bash: jq -r '.hooks.PreToolUse[]?.hooks[]?.command // empty')
                pre_tool_use_hooks = settings_data.get("hooks", {}).get("PreToolUse", [])
                for hook in pre_tool_use_hooks:
                    if isinstance(hook, dict) and "hooks" in hook:
                        for sub_hook in hook.get("hooks", []):
                            if isinstance(sub_hook, dict) and "command" in sub_hook:
                                cmd = sub_hook["command"]
                                if isinstance(cmd, str) and "claude-code-docs" in cmd:
                                    
                                    # Extract paths from v0.1 complex hook format
                                    # Look for patterns like: "/path/to/claude-code-docs/.last_check"
                                    # Pattern: grep -o '"[^"]*claude-code-docs[^"]*"' | sed 's/"//g'
                                    quoted_paths = re.findall(r'"[^"]*claude-code-docs[^"]*"', cmd)
                                    for quoted_path in quoted_paths:
                                        path_str = quoted_path.strip('"')  # Remove quotes
                                        if not path_str:
                                            continue
                                        
                                        # Extract just the directory part
                                        # Pattern: (.*/claude-code-docs)(/.*)?$
                                        dir_match = re.match(r'(.*/claude-code-docs)(/.*)?$', path_str)
                                        if dir_match:
                                            path_str = dir_match.group(1)
                                            
                                            # Convert ~ to home directory
                                            if path_str.startswith('~'):
                                                path_str = str(Path.home()) + path_str[1:]
                                            
                                            path = Path(path_str)
                                            if path.is_dir():
                                                paths.append(path)
                                    
                                    # Also try v0.2+ simpler format
                                    # Pattern: grep -o '[^ "]*claude-code-docs[^ "]*'
                                    simple_paths = re.findall(r'[^ "]*claude-code-docs[^ "]*', cmd)
                                    for path_str in simple_paths:
                                        if not path_str:
                                            continue
                                        
                                        # Convert ~ to home directory
                                        if path_str.startswith('~'):
                                            path_str = str(Path.home()) + path_str[1:]
                                        
                                        # Clean up path to get the claude-code-docs directory
                                        # Pattern: (.*/claude-code-docs)(/.*)?$
                                        dir_match = re.match(r'(.*/claude-code-docs)(/.*)?$', path_str)
                                        if dir_match:
                                            path_str = dir_match.group(1)
                                        
                                        path = Path(path_str)
                                        if path.is_dir():
                                            paths.append(path)
                                            
            except (json.JSONDecodeError, FileNotFoundError) as e:
                # Don't fail uninstall if we can't read settings file
                print(f"[WARNING] Could not read settings file {settings_file}: {e}")
        
        # Deduplicate and return sorted results (bash: printf '%s\n' "${paths[@]}" | sort -u)
        unique_paths = []
        seen_paths = set()
        
        for path in paths:
            # Resolve to absolute path for comparison
            abs_path = path.resolve()
            
            # Skip if we've already seen this path
            if abs_path not in seen_paths:
                unique_paths.append(abs_path)
                seen_paths.add(abs_path)
        
        # Sort for consistent output
        unique_paths.sort()
        
        return unique_paths
    
    def remove_command_file(self) -> bool:
        """Remove the /docs slash command"""
        try:
            # Path to the command file
            command_file = self.claude_dir / "commands" / "docs.md"
            
            if command_file.exists():
                # Remove the command file
                command_file.unlink()
                print(f"[+] Removed /docs command from {command_file}")
                
                # Clean up empty commands directory if it's now empty
                commands_dir = command_file.parent
                try:
                    if commands_dir.exists() and not any(commands_dir.iterdir()):
                        commands_dir.rmdir()
                        print(f"[+] Removed empty commands directory")
                except OSError:
                    # Directory not empty or permission error, that's fine
                    pass
                    
                return True
            else:
                print("[INFO] No /docs command found (already removed or never installed)")
                return True  # Not an error if file doesn't exist
                
        except Exception as e:
            print(f"[ERROR] Failed to remove /docs command: {e}")
            return False
    
    def remove_hooks(self) -> bool:
        """Remove hooks from settings.json"""
        try:
            settings_file = self.claude_dir / "settings.json"
            
            # If settings.json doesn't exist, that's not an error
            if not settings_file.exists():
                print("ℹ️  No Claude settings file found (already removed or never configured)")
                return True
            
            # Read current settings
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except json.JSONDecodeError as e:
                print(f"[ERROR] Failed to parse settings.json: {e}")
                return False
            
            # Create backup first
            backup_file = settings_file.with_suffix('.json.backup')
            try:
                shutil.copy2(settings_file, backup_file)
                print(f"[+] Created backup: {backup_file}")
            except Exception as e:
                print(f"[WARNING] Could not create backup: {e}")
                # Continue anyway, this shouldn't be fatal
            
            # Track if we made any changes
            changed = False
            
            # Remove hooks containing "claude-code-docs"
            if 'hooks' in settings and 'PreToolUse' in settings['hooks']:
                original_hooks = settings['hooks']['PreToolUse']
                if isinstance(original_hooks, list):
                    # Filter out hooks that contain "claude-code-docs" in any hook command
                    filtered_hooks = []
                    for hook_entry in original_hooks:
                        if isinstance(hook_entry, dict) and 'hooks' in hook_entry:
                            # Check if any hook command contains "claude-code-docs"
                            contains_docs = False
                            hooks_list = hook_entry.get('hooks', [])
                            if isinstance(hooks_list, list):
                                for hook in hooks_list:
                                    if isinstance(hook, dict) and 'command' in hook:
                                        command = str(hook['command'])
                                        if 'claude-code-docs' in command:
                                            contains_docs = True
                                            break
                            
                            # Only keep hooks that don't contain claude-code-docs
                            if not contains_docs:
                                filtered_hooks.append(hook_entry)
                    
                    # Update the hooks if we filtered any out
                    if len(filtered_hooks) != len(original_hooks):
                        settings['hooks']['PreToolUse'] = filtered_hooks
                        changed = True
                        removed_count = len(original_hooks) - len(filtered_hooks)
                        print(f"[+] Removed {removed_count} claude-code-docs hook(s)")
            
            # Clean up empty structures
            if 'hooks' in settings:
                # If PreToolUse is now empty, remove it
                if 'PreToolUse' in settings['hooks']:
                    if not settings['hooks']['PreToolUse']:
                        del settings['hooks']['PreToolUse']
                        changed = True
                
                # If hooks object is now empty, remove it entirely
                if not settings['hooks']:
                    del settings['hooks']
                    changed = True
            
            # Write the updated settings if we made changes
            if changed:
                # Use temporary file for atomic write
                temp_file = settings_file.with_suffix('.json.tmp')
                try:
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        json.dump(settings, f, indent=2, ensure_ascii=False)
                    
                    # Atomic replace
                    if self.os_type == "windows":
                        # On Windows, we may need to remove the target first
                        if settings_file.exists():
                            settings_file.unlink()
                    temp_file.replace(settings_file)
                    
                    print(f"[+] Updated Claude settings (backup: {backup_file.name})")
                    
                except Exception as e:
                    print(f"[ERROR] Failed to write updated settings: {e}")
                    # Clean up temp file if it exists
                    if temp_file.exists():
                        temp_file.unlink()
                    return False
            else:
                print("ℹ️  No claude-code-docs hooks found in settings")
                # Remove the backup since we didn't make changes
                if backup_file.exists():
                    try:
                        backup_file.unlink()
                    except:
                        pass  # Not critical if backup cleanup fails
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to remove hooks: {e}")
            return False
    
    def remove_directories(self) -> bool:
        """Safely remove installation directories
        
        Converts the bash directory removal logic to Python.
        Only removes directories that are clean git repositories.
        Preserves directories with uncommitted changes or non-git directories.
        """
        if not self.installations:
            return True
        
        print("")
        print("Removing installation directories...")
        
        for path in self.installations:
            # Skip if directory doesn't exist (defensive programming)
            if not path.is_dir():
                continue
            
            print(f"Processing: {path}")
            
            # Check if it's a git repository
            git_dir = path / ".git"
            if git_dir.is_dir():
                # This is a git repository - check for uncommitted changes
                try:
                    # Check git status (bash equivalent: git status --porcelain)
                    has_changes = self._git_has_uncommitted_changes(path)
                    
                    if not has_changes:
                        # Clean repository - safe to remove
                        try:
                            shutil.rmtree(path)
                            print(f"[+] Removed {path} (clean git repo)")
                        except PermissionError as e:
                            print(f"[ERROR] Could not remove {path}: Permission denied")
                            if self.os_type == "windows":
                                print(f"   Try running as Administrator or check if files are in use")
                            else:
                                print(f"   Try running with sudo or check file permissions")
                        except Exception as e:
                            print(f"[ERROR] Could not remove {path}: {e}")
                    else:
                        # Has uncommitted changes - preserve it
                        print(f"[!] Preserved {path} (has uncommitted changes)")
                        
                except Exception as e:
                    # If we can't check git status, preserve the directory for safety
                    print(f"[!] Preserved {path} (could not check git status: {e})")
            else:
                # Not a git repository - preserve it for safety
                # This matches the bash behavior: only remove git repos
                print(f"[!] Preserved {path} (not a git repo)")
        
        return True
    
    def uninstall(self) -> bool:
        """Main uninstallation process"""
        print(f"Claude Code Docs Cross-Platform Uninstaller v{UNINSTALLER_VERSION}")
        print("=" * 60)
        print("")
        
        # Step 1: Find all installations
        self.installations = self.find_installations()
        
        if self.installations:
            print("Found installations at:")
            for path in self.installations:
                print(f"  [DIR] {path}")
            print("")
        
        # Step 2: Show what will be removed
        print("This will remove:")
        print("  - The /docs command from ~/.claude/commands/docs.md")
        print("  - All claude-code-docs hooks from ~/.claude/settings.json")
        if self.installations:
            print("  - Installation directories (if safe to remove)")
        print("")
        
        # Step 3: Get confirmation
        try:
            response = input("Continue? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("Cancelled.")
                return False
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            return False
        
        # Step 4: Remove command file
        if not self.remove_command_file():
            return False
            
        # Step 5: Remove hooks
        if not self.remove_hooks():
            return False
            
        # Step 6: Remove directories
        if not self.remove_directories():
            return False
        
        print("")
        print("[SUCCESS] Uninstall complete!")
        print("")
        print("To reinstall:")
        if self.os_type == "windows":
            print("curl -o install.py https://raw.githubusercontent.com/mccloudmedia/claude-code-docs/main/install.py; python install.py")
        else:
            print("curl -o install.py https://raw.githubusercontent.com/mccloudmedia/claude-code-docs/main/install.py && python3 install.py")
        
        return True

def main():
    """Main entry point"""
    uninstaller = CrossPlatformUninstaller()
    
    if uninstaller.uninstall():
        sys.exit(0)
    else:
        print("\n[ERROR] Uninstall failed")
        sys.exit(1)

if __name__ == "__main__":
    main()