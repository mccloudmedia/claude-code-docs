#!/usr/bin/env python3
"""
Claude Code Docs Cross-Platform Installer v0.4.0
Converts from bash-only to Windows/macOS/Linux support

This installer replaces install.sh with cross-platform Python implementation.
"""

import os
import sys
import platform
import subprocess
import json
import shutil
from pathlib import Path
import re
from typing import List, Optional, Dict, Any

# Version and configuration
INSTALLER_VERSION = "0.4.0"
INSTALL_BRANCH = "main"
REPO_URL = "https://github.com/ericbuess/claude-code-docs.git"

class CrossPlatformInstaller:
    def __init__(self):
        self.os_type = self._detect_os()
        self.install_dir = self._get_install_dir()
        self.claude_dir = self._get_claude_dir()
        self.old_installations = []
        self.git_executable = None
        
        # Print OS detection info (use ASCII for Windows compatibility)
        print(f"[+] Detected {self.os_type.title()}")
        print(f"[+] Install directory: {self.install_dir}")
        print(f"[+] Claude directory: {self.claude_dir}")
        
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
    
    def _get_install_dir(self) -> Path:
        """Get the installation directory for this platform"""
        if self.os_type == "windows":
            # Use USERPROFILE on Windows instead of ~
            user_profile = os.environ.get("USERPROFILE")
            if user_profile:
                return Path(user_profile) / ".claude-code-docs"
            else:
                # Fallback to HOME if USERPROFILE is not set
                home = os.environ.get("HOME")
                if home:
                    return Path(home) / ".claude-code-docs"
                else:
                    raise RuntimeError("Could not determine user home directory on Windows")
        else:
            # macOS and Linux use ~ which expands to HOME
            home = os.environ.get("HOME")
            if home:
                return Path(home) / ".claude-code-docs"
            else:
                # Fallback using Path.home() for cross-platform compatibility
                return Path.home() / ".claude-code-docs"
    
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
        if self.git_executable:
            return self.git_executable
            
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
                            self.git_executable = git_path
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
                            self.git_executable = path
                            return path
                    except (subprocess.TimeoutExpired, OSError):
                        continue
        
        return None
    
    def _run_git_command(self, args: List[str], cwd: Optional[Path] = None, 
                        capture_output: bool = True, timeout: int = 30,
                        check: bool = False) -> subprocess.CompletedProcess:
        """Run a git command with proper error handling"""
        git_exe = self._find_git_executable()
        if not git_exe:
            raise RuntimeError("Git executable not found")
        
        cmd = [git_exe] + args
        try:
            return subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=check
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Git command timed out: {' '.join(cmd)}")
        except subprocess.CalledProcessError as e:
            if check:
                raise RuntimeError(f"Git command failed: {' '.join(cmd)}\nError: {e.stderr}")
            return e
    
    def _git_get_current_branch(self, repo_dir: Path) -> str:
        """Get current git branch"""
        try:
            result = self._run_git_command(
                ["rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_dir
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return "unknown"
        except Exception:
            return "unknown"
    
    def _git_has_uncommitted_changes(self, repo_dir: Path, exclude_manifest: bool = True) -> bool:
        """Check if repository has uncommitted changes"""
        try:
            result = self._run_git_command(
                ["status", "--porcelain"],
                cwd=repo_dir
            )
            if result.returncode != 0:
                return False
            
            changes = result.stdout.strip()
            if not changes:
                return False
            
            if exclude_manifest:
                # Filter out docs_manifest.json changes
                filtered_changes = []
                for line in changes.split('\n'):
                    if line.strip() and "docs/docs_manifest.json" not in line:
                        filtered_changes.append(line)
                return len(filtered_changes) > 0
            
            return True
        except Exception:
            return False
    
    def _git_has_conflicts(self, repo_dir: Path, exclude_manifest: bool = True) -> bool:
        """Check if repository has merge conflicts"""
        try:
            result = self._run_git_command(
                ["status", "--porcelain"],
                cwd=repo_dir
            )
            if result.returncode != 0:
                return False
            
            changes = result.stdout.strip()
            if not changes:
                return False
            
            # Look for conflict markers (UU, AA, DD)
            conflict_lines = []
            for line in changes.split('\n'):
                if line.strip() and line.startswith(('UU', 'AA', 'DD')):
                    if exclude_manifest and "docs/docs_manifest.json" in line:
                        continue
                    conflict_lines.append(line)
            
            return len(conflict_lines) > 0
        except Exception:
            return False
    
    def _git_has_untracked_files(self, repo_dir: Path) -> bool:
        """Check if repository has untracked files (excluding temp files)"""
        try:
            result = self._run_git_command(
                ["status", "--porcelain"],
                cwd=repo_dir
            )
            if result.returncode != 0:
                return False
            
            changes = result.stdout.strip()
            if not changes:
                return False
            
            # Look for untracked files (??) but ignore temp files
            temp_extensions = ['.tmp', '.log', '.swp']
            for line in changes.split('\n'):
                if line.strip() and line.startswith('??'):
                    filename = line[3:].strip()
                    if not any(filename.endswith(ext) for ext in temp_extensions):
                        return True
            
            return False
        except Exception:
            return False
    
    def _git_abort_operations(self, repo_dir: Path):
        """Abort any in-progress git operations"""
        try:
            # Abort merge
            self._run_git_command(["merge", "--abort"], cwd=repo_dir)
        except Exception:
            pass
        
        try:
            # Abort rebase
            self._run_git_command(["rebase", "--abort"], cwd=repo_dir)
        except Exception:
            pass
    
    def _git_force_clean_checkout(self, repo_dir: Path, target_branch: str) -> bool:
        """Force a clean checkout to target branch"""
        try:
            # Clear any stale index
            self._run_git_command(["reset"], cwd=repo_dir)
            
            # Force checkout target branch (handles detached HEAD, wrong branch, etc.)
            result = self._run_git_command(
                ["checkout", "-B", target_branch, f"origin/{target_branch}"],
                cwd=repo_dir
            )
            if result.returncode != 0:
                return False
            
            # Reset to clean state (discards all local changes)
            result = self._run_git_command(
                ["reset", "--hard", f"origin/{target_branch}"],
                cwd=repo_dir
            )
            if result.returncode != 0:
                return False
            
            # Clean any untracked files
            self._run_git_command(["clean", "-fd"], cwd=repo_dir)
            
            return True
        except Exception:
            return False
    
    def _safe_git_update(self, repo_dir: Path) -> bool:
        """Safely update git repository - Python implementation of bash safe_git_update()"""
        try:
            # Get current branch
            current_branch = self._git_get_current_branch(repo_dir)
            target_branch = INSTALL_BRANCH
            
            # Inform user about branch status
            if current_branch != target_branch:
                print(f"  Switching from {current_branch} to {target_branch} branch...")
            else:
                print(f"  Updating {target_branch} branch...")
            
            # Set git config for pull strategy if not set
            try:
                result = self._run_git_command(["config", "pull.rebase"], cwd=repo_dir)
                if result.returncode != 0:
                    self._run_git_command(["config", "pull.rebase", "false"], cwd=repo_dir)
            except Exception:
                pass
            
            print("Updating to latest version...")
            
            # Try regular pull first
            try:
                result = self._run_git_command(
                    ["pull", "--quiet", "origin", target_branch],
                    cwd=repo_dir,
                    timeout=60
                )
                if result.returncode == 0:
                    return True
            except Exception:
                pass
            
            # If pull failed, try more aggressive approach
            print("  Standard update failed, trying harder...")
            
            # Fetch latest
            try:
                result = self._run_git_command(
                    ["fetch", "origin", target_branch],
                    cwd=repo_dir,
                    timeout=60
                )
                if result.returncode != 0:
                    print("  [!] Could not fetch from GitHub (offline?)")
                    return False
            except Exception:
                print("  [!] Could not fetch from GitHub (offline?)")
                return False
            
            # If we're switching branches, skip change detection - just force clean
            needs_user_confirmation = False
            if current_branch != target_branch:
                print("  Branch switch detected, forcing clean state...")
            else:
                # Check what kind of changes we have (only when staying on same branch)
                has_conflicts = self._git_has_conflicts(repo_dir, exclude_manifest=True)
                has_local_changes = self._git_has_uncommitted_changes(repo_dir, exclude_manifest=True)
                has_untracked = self._git_has_untracked_files(repo_dir)
                
                needs_user_confirmation = has_conflicts or has_local_changes or has_untracked
                
                # If we have significant changes, ask user for confirmation
                if needs_user_confirmation:
                    print("")
                    print("[!] WARNING: Local changes detected in your installation:")
                    if has_conflicts:
                        print("  • Merge conflicts need resolution")
                    if has_local_changes:
                        print("  • Modified files (other than docs_manifest.json)")
                    if has_untracked:
                        print("  • Untracked files")
                    print("")
                    print("The installer will reset to a clean state, discarding these changes.")
                    print("Note: Changes to docs_manifest.json are handled automatically.")
                    print("")
                    
                    # Ask for confirmation
                    try:
                        response = input("Continue and discard local changes? [y/N]: ").strip().lower()
                        if response not in ['y', 'yes']:
                            print("Installation cancelled. Your local changes are preserved.")
                            print("To proceed later, either:")
                            print("  1. Manually resolve the issues, or")
                            print("  2. Run the installer again and choose 'y' to discard changes")
                            return False
                    except (EOFError, KeyboardInterrupt):
                        print("\nInstallation cancelled.")
                        return False
                    
                    print("  Proceeding with clean installation...")
                else:
                    # Check for manifest-only changes
                    result = self._run_git_command(["status", "--porcelain"], cwd=repo_dir)
                    if result.returncode == 0:
                        manifest_changes = [line for line in result.stdout.split('\n') 
                                          if line.strip() and "docs/docs_manifest.json" in line]
                        if manifest_changes:
                            conflict_markers = [line for line in manifest_changes if line.startswith('UU')]
                            if conflict_markers:
                                print("  Resolving manifest file conflicts automatically...")
                            else:
                                print("  Handling manifest file updates automatically...")
            
            # Force clean state
            if needs_user_confirmation:
                print("  Forcing clean update (discarding local changes)...")
            else:
                print("  Updating to clean state...")
            
            # Abort any in-progress operations
            self._git_abort_operations(repo_dir)
            
            # Force clean checkout
            if self._git_force_clean_checkout(repo_dir, target_branch):
                print("  [+] Updated successfully to clean state")
                return True
            else:
                print("  [!] Failed to force clean checkout")
                return False
                
        except Exception as e:
            print(f"  [!] Error during git update: {e}")
            return False
    
    def _create_windows_helper_scripts(self) -> bool:
        """Create Windows batch and PowerShell helper scripts"""
        try:
            # Create batch file wrapper for Command Prompt
            batch_script = self.install_dir / "claude-docs-helper.bat"
            # Convert Windows paths to forward slashes for bash compatibility
            bash_install_dir = str(self.install_dir).replace('\\', '/')
            
            batch_content = f'''@echo off
REM Claude Code Docs Helper - Windows Batch Wrapper
REM This script provides Windows compatibility for the documentation system

setlocal enabledelayedexpansion

REM Check if Git Bash is available and use it to run the shell script
where bash >nul 2>nul
if %errorlevel% == 0 (
    REM Git Bash is available, use it to run the shell script
    bash "{bash_install_dir}/claude-docs-helper.sh" %*
    exit /b %errorlevel%
)

REM Fallback: Try to use PowerShell to run a Python equivalent
where python >nul 2>nul
if %errorlevel% == 0 (
    REM Python is available, use it to run our Python helper
    python "{self.install_dir / "claude-docs-helper.py"}" %*
    exit /b %errorlevel%
)

REM If nothing else works, show error
echo [ERROR] Neither bash nor python found
echo Please install Git for Windows or Python to use Claude Code Docs
exit /b 1
'''
            
            # Create PowerShell wrapper
            ps_script = self.install_dir / "claude-docs-helper.ps1"
            ps_content = f'''# Claude Code Docs Helper - PowerShell Wrapper
# This script provides Windows PowerShell compatibility

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

# Check if bash is available (Git Bash)
if (Get-Command bash -ErrorAction SilentlyContinue) {{
    # Use bash to run the shell script
    & bash "{bash_install_dir}/claude-docs-helper.sh" @Arguments
    exit $LASTEXITCODE
}}

# Check if python is available
if (Get-Command python -ErrorAction SilentlyContinue) {{
    # Use Python to run our Python helper
    & python "{self.install_dir / "claude-docs-helper.py"}" @Arguments
    exit $LASTEXITCODE
}}

# If nothing works, show error
Write-Host "[ERROR] Neither bash nor python found" -ForegroundColor Red
Write-Host "Please install Git for Windows or Python to use Claude Code Docs" -ForegroundColor Yellow
exit 1
'''
            
            # Write the files
            with open(batch_script, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            with open(ps_script, 'w', encoding='utf-8') as f:
                f.write(ps_content)
            
            print(f"[+] Created Windows helper scripts")
            return True
            
        except Exception as e:
            print(f"[!] Failed to create Windows helper scripts: {e}")
            return False
    
    def check_dependencies(self) -> bool:
        """Check for required tools and system capabilities"""
        print("Checking dependencies...")
        
        all_good = True
        
        # 1. Python Version Check
        version = sys.version_info
        if version.major >= 3 and version.minor >= 6:
            print(f"[+] Python {version.major}.{version.minor}.{version.micro} (compatible)")
        else:
            print(f"[!] Error: Python {version.major}.{version.minor} detected")
            print("    This installer requires Python 3.6 or newer")
            print("    Please upgrade Python and try again")
            all_good = False
        
        # 2. Git Detection (cross-platform)
        git_found = self._check_git_availability()
        if not git_found:
            all_good = False
        
        # 3. Network Connectivity Test
        if not self._check_network_connectivity():
            all_good = False
        
        # 4. Directory Permissions
        if not self._check_directory_permissions():
            all_good = False
        
        # 5. Disk Space Check (optional but informative)
        self._check_disk_space()
        
        # 6. Platform-specific checks
        if not self._check_platform_specific():
            all_good = False
        
        if all_good:
            print("[+] All dependencies satisfied")
            return True
        else:
            print("[!] Dependency check failed - please resolve the issues above")
            return False

    
    def _check_git_availability(self) -> bool:
        """Check if git is available and working"""
        # Use the existing git detection logic
        git_exe = self._find_git_executable()
        if git_exe:
            try:
                result = subprocess.run(
                    [git_exe, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    version_line = result.stdout.strip()
                    print(f"[+] Git found: {version_line}")
                    return True
            except Exception as e:
                print(f"[!] Git test failed: {e}")
        
        # Provide platform-specific installation guidance
        print("[!] Error: Git is required but not found")
        print("    Please install Git and try again:")
        
        if self.os_type == "windows":
            print("    • Download from: https://git-scm.com/download/windows")
            print("    • Or install via winget: winget install Git.Git")
            print("    • Or install via chocolatey: choco install git")
        elif self.os_type == "macos":
            print("    • Install Xcode Command Line Tools: xcode-select --install")
            print("    • Or install via Homebrew: brew install git")
            print("    • Or install via MacPorts: port install git")
        elif self.os_type == "linux":
            print("    • Ubuntu/Debian: sudo apt install git")
            print("    • Fedora/RHEL: sudo dnf install git")
            print("    • Arch: sudo pacman -S git")
            print("    • SUSE: sudo zypper install git")
        
        return False
    
    def _check_network_connectivity(self) -> bool:
        """Test network connectivity to GitHub"""
        try:
            import socket
            # Test connection to GitHub
            with socket.create_connection(("github.com", 443), timeout=10):
                print("[+] Network connectivity: OK")
                return True
        except socket.timeout:
            print("[!] Error: Network timeout connecting to github.com")
            print("    Please check your internet connection")
            return False
        except socket.gaierror as e:
            print(f"[!] Error: DNS resolution failed for github.com: {e}")
            print("    Please check your DNS settings")
            return False
        except Exception as e:
            print(f"[!] Error: Network connectivity test failed: {e}")
            print("    Please check your internet connection and firewall settings")
            return False
    
    def _check_directory_permissions(self) -> bool:
        """Check write permissions to required directories"""
        directories_to_check = [
            ("Install directory parent", self.install_dir.parent),
            ("Claude configuration", self.claude_dir.parent)
        ]
        
        all_good = True
        
        for desc, directory in directories_to_check:
            try:
                # Ensure directory exists
                directory.mkdir(parents=True, exist_ok=True)
                
                # Test write permissions
                test_file = directory / ".claude-docs-install-test"
                test_file.write_text("permission test")
                test_file.unlink()
                
                print(f"[+] Write permissions OK: {desc} ({directory})")
                
            except PermissionError:
                print(f"[!] Error: No write permission to {desc} ({directory})")
                if self.os_type == "windows":
                    print("    Try running as Administrator or check folder permissions")
                else:
                    print("    Try running with sudo or check folder permissions")
                all_good = False
            except Exception as e:
                print(f"[!] Error: Cannot write to {desc} ({directory}): {e}")
                all_good = False
        
        return all_good
    
    def _check_disk_space(self, min_space_mb: int = 50) -> bool:
        """Check available disk space (informational)"""
        try:
            total, used, free = shutil.disk_usage(self.install_dir.parent)
            free_mb = free // (1024 * 1024)
            
            if free_mb >= min_space_mb:
                print(f"[+] Disk space: {free_mb} MB available")
                return True
            else:
                print(f"[!] Warning: Low disk space - {free_mb} MB available (recommended: {min_space_mb} MB)")
                print("    Installation may fail if disk becomes full")
                return False
                
        except Exception as e:
            print(f"[!] Warning: Could not check disk space: {e}")
            return True  # Not critical, so don't fail
    
    def _check_platform_specific(self) -> bool:
        """Platform-specific dependency checks"""
        all_good = True
        
        if self.os_type == "windows":
            # Check for PowerShell or Command Prompt compatibility
            try:
                # Test basic subprocess functionality
                result = subprocess.run(
                    ["cmd", "/c", "echo", "test"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print("[+] Windows Command Prompt: Available")
                else:
                    print("[!] Warning: Windows Command Prompt test failed")
            except Exception:
                print("[!] Warning: Cannot execute Windows commands")
            
            # Check for PowerShell
            try:
                result = subprocess.run(
                    ["powershell", "-Command", "Write-Host test"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print("[+] PowerShell: Available")
                else:
                    print("[i] PowerShell: Not available (not required)")
            except Exception:
                print("[i] PowerShell: Not available (not required)")
                
        elif self.os_type == "macos":
            # Check for basic Unix tools
            try:
                result = subprocess.run(
                    ["which", "bash"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print("[+] macOS: Bash shell available")
                else:
                    print("[!] Warning: Bash shell not found")
            except Exception:
                print("[!] Warning: Cannot check for bash shell")
                
        elif self.os_type == "linux":
            # Check for basic Unix tools
            try:
                result = subprocess.run(
                    ["which", "bash"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print("[+] Linux: Bash shell available")
                else:
                    print("[!] Warning: Bash shell not found")
            except Exception:
                print("[!] Warning: Cannot check for bash shell")
        
        return all_good


    def find_existing_installations(self) -> List[Path]:
        """Find existing claude-code-docs installations from config files
        
        Converts the bash find_existing_installations() function to Python.
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
                # Don't fail installation if we can't read command file
                print(f"[!] Warning: Could not read command file {docs_command_file}: {e}")
        
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
                # Don't fail installation if we can't read settings file
                print(f"[!] Warning: Could not read settings file {settings_file}: {e}")
        
        # Also check current directory if running from an installation
        current_dir = Path.cwd()
        manifest_file = current_dir / "docs" / "docs_manifest.json"
        if manifest_file.exists() and current_dir != self.install_dir:
            paths.append(current_dir)
        
        # Deduplicate and exclude new location (bash: printf '%s\n' "${paths[@]}" | grep -v "^$INSTALL_DIR$" | sort -u)
        unique_paths = []
        seen_paths = set()
        
        for path in paths:
            # Resolve to absolute path for comparison
            abs_path = path.resolve()
            install_abs = self.install_dir.resolve()
            
            # Skip if this is the install directory or if we've seen this path
            if abs_path != install_abs and abs_path not in seen_paths:
                unique_paths.append(abs_path)
                seen_paths.add(abs_path)
        
        # Sort for consistent output
        unique_paths.sort()
        
        return unique_paths
    
    def clone_or_update_repo(self) -> bool:
        """Clone new repo or update existing one - Main implementation"""
        print("")
        print("Checking repository status...")
        
        # Check if already installed at target location
        manifest_file = self.install_dir / "docs" / "docs_manifest.json"
        if self.install_dir.exists() and manifest_file.exists():
            print(f"[+] Found installation at {self.install_dir}")
            print("  Updating to latest version...")
            
            # Update it safely
            if self._safe_git_update(self.install_dir):
                # Change to install directory for subsequent operations
                os.chdir(self.install_dir)
                return True
            else:
                print("[!] Failed to update existing installation")
                return False
        else:
            # Need to install at new location
            if len(self.old_installations) > 0:
                # Migration case - do fresh install
                old_install = self.old_installations[0]
                print(f"[+] Found existing installation at: {old_install}")
                print(f"   Migrating to: {self.install_dir}")
                print("")
                return self._migrate_installation(old_install)
            else:
                # Fresh installation
                print("No existing installation found")
                print(f"Installing fresh to {self.install_dir}...")
                return self._fresh_clone()
    
    def _migrate_installation(self, old_dir: Path) -> bool:
        """Migrate from old location to new standard location"""
        try:
            # Check if old dir has uncommitted changes
            should_preserve = False
            if (old_dir / ".git").exists():
                should_preserve = self._git_has_uncommitted_changes(old_dir, exclude_manifest=False)
                
                if should_preserve:
                    print("[!] Uncommitted changes detected in old installation")
            
            # Fresh install at new location
            if not self._fresh_clone():
                return False
            
            # Remove old directory if safe
            if not should_preserve:
                print("Removing old installation...")
                try:
                    shutil.rmtree(old_dir)
                    print("[+] Old installation removed")
                except Exception as e:
                    print(f"[!] Could not remove old installation: {e}")
            else:
                print("")
                print(f"[i] Old installation preserved at: {old_dir}")
                print("   (has uncommitted changes)")
            
            print("")
            print("[+] Migration complete!")
            return True
            
        except Exception as e:
            print(f"[!] Migration failed: {e}")
            return False
    
    def _fresh_clone(self) -> bool:
        """Perform a fresh git clone"""
        try:
            # Ensure parent directory exists
            self.install_dir.parent.mkdir(parents=True, exist_ok=True)
            
            # Remove install dir if it exists but is incomplete
            if self.install_dir.exists():
                try:
                    shutil.rmtree(self.install_dir)
                except Exception as e:
                    print(f"[!] Could not remove incomplete installation: {e}")
                    return False
            
            # Clone the repository
            print(f"Cloning repository to {self.install_dir}...")
            result = self._run_git_command([
                "clone", "-b", INSTALL_BRANCH, REPO_URL, str(self.install_dir)
            ], timeout=120)
            
            if result.returncode != 0:
                print(f"[!] Failed to clone repository: {result.stderr}")
                return False
            
            # Change to install directory
            os.chdir(self.install_dir)
            
            # Verify clone was successful
            if not (self.install_dir / "docs" / "docs_manifest.json").exists():
                print("[!] Clone appears incomplete - missing docs_manifest.json")
                return False
            
            print("[+] Repository cloned successfully")
            return True
            
        except Exception as e:
            print(f"[!] Failed to clone repository: {e}")
            return False
    
    def _create_python_helper(self) -> bool:
        """Create Python helper script for cross-platform compatibility"""
        try:
            python_helper = self.install_dir / "claude-docs-helper.py"
            
            helper_content = '''#!/usr/bin/env python3
"""
Claude Code Docs Helper - Python Implementation
Provides cross-platform documentation access
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.resolve()
    
    # Check if the shell script exists
    shell_script = script_dir / "claude-docs-helper.sh"
    
    if shell_script.exists():
        # Try to run the shell script with bash if available
        try:
            result = subprocess.run(
                ["bash", str(shell_script)] + sys.argv[1:],
                capture_output=False,
                text=True
            )
            sys.exit(result.returncode)
        except FileNotFoundError:
            # Bash not found, fall back to basic functionality
            pass
    
    # Basic fallback implementation
    docs_dir = script_dir / "docs"
    
    if len(sys.argv) > 1:
        if "what" in sys.argv[1].lower() and "new" in sys.argv[1].lower():
            print("📚 Recent documentation updates:")
            print("\\nFor the latest changes, check:")
            print(f"📎 https://github.com/ericbuess/claude-code-docs/commits/main/docs")
            print("\\n📚 COMMUNITY MIRROR - NOT AFFILIATED WITH ANTHROPIC")
        else:
            # Try to show the requested doc
            topic = sys.argv[1].replace("-", "_").replace(" ", "_")
            doc_file = docs_dir / f"{topic}.md"
            
            if doc_file.exists():
                print("📚 COMMUNITY MIRROR: https://github.com/ericbuess/claude-code-docs")
                print("📖 OFFICIAL DOCS: https://docs.anthropic.com/en/docs/claude-code")
                print("")
                with open(doc_file, 'r', encoding='utf-8') as f:
                    print(f.read())
                print(f"\\n📖 Official page: https://docs.anthropic.com/en/docs/claude-code/{topic}")
            else:
                print(f"❌ Documentation for '{topic}' not found")
                print("\\nAvailable topics:")
                for md_file in sorted(docs_dir.glob("*.md")):
                    print(f"  - {md_file.stem}")
    else:
        # List available docs
        print("📚 Available documentation topics:")
        for md_file in sorted(docs_dir.glob("*.md")):
            print(f"  - {md_file.stem}")
        print("\\nUsage: /docs <topic>")

if __name__ == "__main__":
    main()
'''
            
            with open(python_helper, 'w', encoding='utf-8') as f:
                f.write(helper_content)
            
            # Make it executable on Unix systems
            if self.os_type != "windows":
                os.chmod(python_helper, 0o755)
            
            print("[+] Created Python helper script")
            return True
            
        except Exception as e:
            print(f"[!] Failed to create Python helper: {e}")
            return False
    
    def _setup_helper_script(self) -> bool:
        """Set up the helper script from template"""
        try:
            print("")
            print("Setting up helper script...")
            
            template_file = self.install_dir / "scripts" / "claude-docs-helper.sh.template"
            helper_script = self.install_dir / "claude-docs-helper.sh"
            
            if template_file.exists():
                # Copy template to helper script
                shutil.copy2(template_file, helper_script)
                
                # Make executable on Unix-like systems
                if self.os_type != "windows":
                    try:
                        os.chmod(helper_script, 0o755)
                    except Exception:
                        pass  # Not critical on Windows
                        
                print("[+] Helper script installed from template")
                
                # Also create Python helper for Windows
                if self.os_type == "windows":
                    self._create_python_helper()
                
                return True
            else:
                print("  [!] Template file missing, attempting recovery...")
                
                # Try to download template directly
                try:
                    import urllib.request
                    template_url = f"https://raw.githubusercontent.com/ericbuess/claude-code-docs/{INSTALL_BRANCH}/scripts/claude-docs-helper.sh.template"
                    
                    with urllib.request.urlopen(template_url, timeout=30) as response:
                        template_content = response.read().decode('utf-8')
                    
                    with open(helper_script, 'w', encoding='utf-8') as f:
                        f.write(template_content)
                    
                    # Make executable on Unix-like systems
                    if self.os_type != "windows":
                        try:
                            os.chmod(helper_script, 0o755)
                        except Exception:
                            pass
                    
                    print("  [+] Helper script downloaded directly")
                    return True
                    
                except Exception as e:
                    print(f"  [!] Failed to download helper script: {e}")
                    print("  Please check your installation and try again")
                    return False
                    
        except Exception as e:
            print(f"[!] Failed to setup helper script: {e}")
            return False
    
    def setup_claude_command(self) -> bool:
        """Set up the /docs slash command"""
        try:
            # Ensure commands directory exists
            commands_dir = self.claude_dir / "commands"
            commands_dir.mkdir(parents=True, exist_ok=True)
            
            # Command file path
            command_file = commands_dir / "docs.md"
            
            if self.os_type == "windows":
                # Create Windows-specific helper scripts
                if not self._create_windows_helper_scripts():
                    return False
                
                # Use Python directly for better compatibility with Claude
                python_helper_path = str(self.install_dir / "claude-docs-helper.py")
                
                # Create the command content that works on Windows
                command_content = f'''Execute the Claude Code Docs helper script using Python

Usage:
- /docs - List all available documentation topics
- /docs <topic> - Read specific documentation with link to official docs
- /docs -t - Check sync status without reading a doc
- /docs -t <topic> - Check freshness then read documentation
- /docs whats new - Show recent documentation changes (or "what's new")

Examples of expected output:

When reading a doc:
📚 COMMUNITY MIRROR: https://github.com/ericbuess/claude-code-docs
📖 OFFICIAL DOCS: https://docs.anthropic.com/en/docs/claude-code

[Doc content here...]

📖 Official page: https://docs.anthropic.com/en/docs/claude-code/hooks

When showing what's new:
📚 Recent documentation updates:

• 5 hours ago:
  📎 https://github.com/ericbuess/claude-code-docs/commit/eacd8e1
  📄 data-usage: https://docs.anthropic.com/en/docs/claude-code/data-usage
     ➕ Added: Privacy safeguards
  📄 security: https://docs.anthropic.com/en/docs/claude-code/security
     ✨ Data flow and dependencies section moved here

📎 Full changelog: https://github.com/ericbuess/claude-code-docs/commits/main/docs
📚 COMMUNITY MIRROR - NOT AFFILIATED WITH ANTHROPIC

Every request checks for the latest documentation from GitHub (takes ~0.4s).
The helper script handles all functionality including auto-updates.

Execute: python "{python_helper_path}" $ARGUMENTS
'''
            else:
                # Unix-style path for macOS and Linux
                helper_path = str(self.install_dir / "claude-docs-helper.sh")
                
                # Create the command content with Unix-style paths
                command_content = f'''Execute the Claude Code Docs helper script at {helper_path}

Usage:
- /docs - List all available documentation topics
- /docs <topic> - Read specific documentation with link to official docs
- /docs -t - Check sync status without reading a doc
- /docs -t <topic> - Check freshness then read documentation
- /docs whats new - Show recent documentation changes (or "what's new")

Examples of expected output:

When reading a doc:
📚 COMMUNITY MIRROR: https://github.com/ericbuess/claude-code-docs
📖 OFFICIAL DOCS: https://docs.anthropic.com/en/docs/claude-code

[Doc content here...]

📖 Official page: https://docs.anthropic.com/en/docs/claude-code/hooks

When showing what's new:
📚 Recent documentation updates:

• 5 hours ago:
  📎 https://github.com/ericbuess/claude-code-docs/commit/eacd8e1
  📄 data-usage: https://docs.anthropic.com/en/docs/claude-code/data-usage
     ➕ Added: Privacy safeguards
  📄 security: https://docs.anthropic.com/en/docs/claude-code/security
     ✨ Data flow and dependencies section moved here

📎 Full changelog: https://github.com/ericbuess/claude-code-docs/commits/main/docs
📚 COMMUNITY MIRROR - NOT AFFILIATED WITH ANTHROPIC

Every request checks for the latest documentation from GitHub (takes ~0.4s).
The helper script handles all functionality including auto-updates.

Execute: {helper_path} "$ARGUMENTS"
'''

            # Write the command file
            with open(command_file, 'w', encoding='utf-8') as f:
                f.write(command_content)
            
            print(f"[+] Created /docs command at {command_file}")
            return True
            
        except Exception as e:
            print(f"[!] Failed to create /docs command: {e}")
            return False
    
    def setup_claude_hooks(self) -> bool:
        """Set up automatic update hooks in settings.json"""
        try:
            # Ensure Claude directory exists
            self.claude_dir.mkdir(parents=True, exist_ok=True)
            
            settings_file = self.claude_dir / "settings.json"
            
            # Determine the hook command based on OS
            if self.os_type == "windows":
                # Use batch file on Windows
                hook_command = str(self.install_dir / "claude-docs-helper.bat") + " hook-check"
            else:
                # Use shell script on Unix-like systems
                hook_command = str(self.install_dir / "claude-docs-helper.sh") + " hook-check"
            
            # Load existing settings or create new structure
            settings_data = {}
            if settings_file.exists():
                try:
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        settings_data = json.load(f)
                    print("[+] Loaded existing Claude settings")
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    print(f"[!] Could not read existing settings.json, creating new: {e}")
                    settings_data = {}
            else:
                print("[+] Creating new Claude settings file")
            
            # Ensure hooks structure exists
            if "hooks" not in settings_data:
                settings_data["hooks"] = {}
            if "PreToolUse" not in settings_data["hooks"]:
                settings_data["hooks"]["PreToolUse"] = []
            
            # Remove ALL existing hooks that contain "claude-code-docs" anywhere in the command
            original_hooks = settings_data["hooks"]["PreToolUse"]
            cleaned_hooks = []
            removed_count = 0
            
            for hook in original_hooks:
                if isinstance(hook, dict) and "hooks" in hook:
                    # Check if any sub-hook contains claude-code-docs
                    contains_claude_docs = False
                    for sub_hook in hook.get("hooks", []):
                        if isinstance(sub_hook, dict) and "command" in sub_hook:
                            command = sub_hook["command"]
                            if isinstance(command, str) and "claude-code-docs" in command:
                                contains_claude_docs = True
                                break
                    
                    if not contains_claude_docs:
                        cleaned_hooks.append(hook)
                    else:
                        removed_count += 1
                else:
                    # Keep hooks that don't have the expected structure
                    cleaned_hooks.append(hook)
            
            # Add our new hook
            new_hook = {
                "matcher": "Read",
                "hooks": [
                    {
                        "type": "command",
                        "command": hook_command
                    }
                ]
            }
            
            cleaned_hooks.append(new_hook)
            settings_data["hooks"]["PreToolUse"] = cleaned_hooks
            
            # Write to temporary file first (atomic update)
            temp_file = settings_file.with_suffix('.json.tmp')
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(settings_data, f, indent=2, ensure_ascii=False)
                
                # Atomic rename (works on all platforms)
                if settings_file.exists():
                    # Create backup
                    backup_file = settings_file.with_suffix('.json.backup')
                    shutil.copy2(settings_file, backup_file)
                
                # Replace original with temp file
                if os.name == 'nt':  # Windows
                    # On Windows, need to remove target first
                    if settings_file.exists():
                        settings_file.unlink()
                temp_file.replace(settings_file)
                
                if removed_count > 0:
                    print(f"[+] Removed {removed_count} old claude-code-docs hook(s)")
                print(f"[+] Added new PreToolUse hook: {hook_command}")
                print(f"[+] Updated Claude settings at {settings_file}")
                
                return True
                
            except Exception as e:
                # Cleanup temp file if something went wrong
                if temp_file.exists():
                    temp_file.unlink()
                raise e
                
        except Exception as e:
            print(f"[!] Failed to setup Claude hooks: {e}")
            return False
    
    def cleanup_old_installations(self) -> bool:
        """Clean up old installations safely
        
        Converts the bash cleanup_old_installations() function to Python.
        Safely removes old claude-code-docs installations while preserving
        any repositories with uncommitted changes.
        """
        # Use the old_installations list that was populated during initialization
        if not self.old_installations:
            return True
        
        print("")
        print("Cleaning up old installations...")
        print(f"Found {len(self.old_installations)} old installation(s) to remove:")
        
        for old_dir in self.old_installations:
            # Skip empty paths (defensive programming)
            if not old_dir or not str(old_dir).strip():
                continue
            
            print(f"  - {old_dir}")
            
            # Check if it has uncommitted changes
            git_dir = old_dir / ".git"
            if git_dir.is_dir():
                # This is a git repository - check for uncommitted changes
                try:
                    # Check git status (bash equivalent: git status --porcelain)
                    has_changes = self._git_has_uncommitted_changes(old_dir, exclude_manifest=False)
                    
                    if not has_changes:
                        # Clean repository - safe to remove
                        try:
                            shutil.rmtree(old_dir)
                            print(f"    [+] Removed (clean)")
                        except Exception as e:
                            print(f"    [!] Could not remove: {e}")
                    else:
                        # Has uncommitted changes - preserve it
                        print(f"    [!] Preserved (has uncommitted changes)")
                        
                except Exception as e:
                    # If we can't check git status, preserve the directory for safety
                    print(f"    [!] Preserved (could not check git status: {e})")
            else:
                # Not a git repository - preserve it for safety
                print(f"    [!] Preserved (not a git repo)")
        
        return True
    
    def install(self) -> bool:
        """Main installation process"""
        print(f"Claude Code Docs Cross-Platform Installer v{INSTALLER_VERSION}")
        print("=" * 50)
        
        # Step 1: Check dependencies
        if not self.check_dependencies():
            return False
            
        # Step 2: Find existing installations
        self.old_installations = self.find_existing_installations()
        
        # Step 3: Clone/update repository
        if not self.clone_or_update_repo():
            return False
        
        # Step 3.5: Setup helper script (now that we're in the repo directory)
        if not self._setup_helper_script():
            return False
            
        # Step 4: Set up Claude integration
        if not self.setup_claude_command():
            return False
            
        if not self.setup_claude_hooks():
            return False
            
        # Step 5: Clean up old installations
        if not self.cleanup_old_installations():
            return False
            
        print("\n[SUCCESS] Claude Code Docs installed successfully!")
        print(f"[INFO] Command: /docs (user)")
        print(f"[INFO] Location: {self.install_dir}")
        return True

def test_path_handling():
    """Test cross-platform path handling functions"""
    print("Testing Cross-Platform Path Handling")
    print("=" * 40)
    
    installer = CrossPlatformInstaller()
    
    print(f"OS Type: {installer.os_type}")
    print(f"Install Directory: {installer.install_dir}")
    print(f"Claude Directory: {installer.claude_dir}")
    print(f"Install Directory exists: {installer.install_dir.exists()}")
    print(f"Claude Directory exists: {installer.claude_dir.exists()}")
    
    if installer.os_type == "windows":
        print(f"USERPROFILE: {os.environ.get('USERPROFILE', 'Not set')}")
        print(f"HOME: {os.environ.get('HOME', 'Not set')}")
        print(f"Windows-style install path: {installer.install_dir}")
        print(f"Unix-style bash path: {str(installer.install_dir).replace(chr(92), '/')}")
    
    return True

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_path_handling()
        return
    
    installer = CrossPlatformInstaller()
    
    if installer.install():
        sys.exit(0)
    else:
        print("\n[ERROR] Installation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()