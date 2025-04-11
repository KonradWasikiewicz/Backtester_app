#!/usr/bin/env python
"""
Version Manager for Backtester App

A unified script that handles all version management tasks:
- Updating version numbers (major, minor, patch)
- Creating Git tags for versions
- Setting up Git hooks for automated versioning
- Rolling back to previous versions
- Managing changelog entries

Usage:
    python version_manager.py update [major|minor|patch] [--changes "Change description"]
    python version_manager.py tag [--push]
    python version_manager.py setup-hooks
    python version_manager.py restore [--version VERSION | --list]
    python version_manager.py info
"""

import os
import sys
import re
import argparse
import subprocess
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
VERSION_FILE_PATH = os.path.join(PROJECT_ROOT, 'src', 'version.py')
CHANGELOG_PATH = os.path.join(PROJECT_ROOT, 'CHANGELOG.md')
VERSION_PATTERN = r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]'
COMMIT_MSG_PATH = '.git/COMMIT_EDITMSG'

# Add project root to sys.path
sys.path.append(PROJECT_ROOT)

# ---- Version Information Functions ----

def load_version_module():
    """Load the version module and return it"""
    if not os.path.exists(VERSION_FILE_PATH):
        print(f"Error: Version file not found at {VERSION_FILE_PATH}")
        sys.exit(1)
    
    # Load the module directly
    spec = importlib.util.spec_from_file_location("version", VERSION_FILE_PATH)
    version_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(version_module)
    
    return version_module

def get_current_version() -> str:
    """Get the current version string from version.py"""
    try:
        version_module = load_version_module()
        return version_module.VERSION
    except Exception as e:
        print(f"Error getting current version: {e}")
        sys.exit(1)

def get_version_info() -> Dict[str, Any]:
    """Get detailed version information from version.py"""
    try:
        version_module = load_version_module()
        return {
            'major': version_module.MAJOR,
            'minor': version_module.MINOR,
            'patch': version_module.PATCH,
            'prerelease': version_module.PRERELEASE,
            'build': version_module.BUILD,
            'version': version_module.VERSION,
            'release_date': version_module.RELEASE_DATE,
            'changelog': version_module.CHANGELOG,
        }
    except Exception as e:
        print(f"Error getting version info: {e}")
        sys.exit(1)

def display_version_info():
    """Display detailed version information"""
    info = get_version_info()
    
    print("\n=== Backtester App Version Information ===\n")
    print(f"Current version: {info['version']}")
    print(f"Release date: {info['release_date']}")
    
    # Major.Minor.Patch breakdown
    print(f"\nSemantic Version:")
    print(f"  Major: {info['major']}")
    print(f"  Minor: {info['minor']}")
    print(f"  Patch: {info['patch']}")
    
    # Pre-release and build info if available
    if info['prerelease']:
        print(f"  Pre-release: {info['prerelease']}")
    if info['build']:
        print(f"  Build metadata: {info['build']}")
    
    # Recent changes from changelog
    version = info['version']
    if version in info['changelog']:
        changes = info['changelog'][version].get('changes', [])
        if changes:
            print("\nChanges in this version:")
            for change in changes:
                print(f"  - {change}")
    
    # Git tag information
    try:
        tag_exists = False
        tag_name = f"v{version}"
        git_tags = run_git_command(["git", "tag"])
        if tag_name in git_tags.split('\n'):
            tag_exists = True
            tag_info = run_git_command(["git", "show", tag_name, "--format=%ai %an"])
            # Fix: Using newline character instead of backslash in f-string expression
            tag_info_first_line = tag_info.split("\n")[0]
            print(f"\nGit tag: {tag_name} (Created: {tag_info_first_line})")
        else:
            print(f"\nGit tag: Not created yet")
    except Exception:
        print("\nGit tag: Could not retrieve tag information")
    
    print("\n===================================\n")

# ---- Version Update Functions ----

def update_version(version_type: str, changes: List[str]) -> Tuple[str, str]:
    """
    Update the version based on SemVer (MAJOR.MINOR.PATCH)
    
    Args:
        version_type (str): Type of version update: 'major', 'minor', or 'patch'
        changes (List[str]): List of change descriptions for the changelog
        
    Returns:
        Tuple[str, str]: (old_version, new_version)
    """
    # Get current version info
    version_info = get_version_info()
    old_version = version_info['version']
    
    # Validate version type
    if version_type not in ('major', 'minor', 'patch'):
        print(f"Error: Invalid version type {version_type}")
        sys.exit(1)
    
    # Update version numbers
    if version_type == 'major':
        version_info['major'] += 1
        version_info['minor'] = 0
        version_info['patch'] = 0
    elif version_type == 'minor':
        version_info['minor'] += 1
        version_info['patch'] = 0
    elif version_type == 'patch':
        version_info['patch'] += 1
    
    # Create new version string
    new_version = f"{version_info['major']}.{version_info['minor']}.{version_info['patch']}"
    if version_info['prerelease']:
        new_version += f"-{version_info['prerelease']}"
    if version_info['build']:
        new_version += f"+{version_info['build']}"
    
    # Update the version file
    try:
        with open(VERSION_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update version numbers
        content = re.sub(r'MAJOR = \d+', f"MAJOR = {version_info['major']}", content)
        content = re.sub(r'MINOR = \d+', f"MINOR = {version_info['minor']}", content)
        content = re.sub(r'PATCH = \d+', f"PATCH = {version_info['patch']}", content)
        
        # Update release date
        today = datetime.now().strftime('%Y-%m-%d')
        content = re.sub(r'RELEASE_DATE = "[^"]*"', f'RELEASE_DATE = "{today}"', content)
        
        # Update changelog in version.py
        new_changelog_entry = f'    "{new_version}": {{\n'
        new_changelog_entry += f'        "date": "{today}",\n'
        new_changelog_entry += '        "changes": [\n'
        for change in changes:
            new_changelog_entry += f'            "{change}",\n'
        new_changelog_entry += '        ]\n'
        new_changelog_entry += '    },'
        
        # Find the start of the CHANGELOG dictionary
        changelog_start = content.find('CHANGELOG = {')
        if changelog_start != -1:
            # Find the position after the opening brace
            changelog_insert_pos = content.find('{', changelog_start) + 1
            # Insert the new changelog entry
            content = content[:changelog_insert_pos] + '\n' + new_changelog_entry + content[changelog_insert_pos:]
        
        # Write updated content back to the file
        with open(VERSION_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Update external changelog file if it exists
        update_external_changelog(new_version, today, version_type, changes)
        
        # Add the files to git staging
        try:
            subprocess.run(["git", "add", VERSION_FILE_PATH], check=True)
            if os.path.exists(CHANGELOG_PATH):
                subprocess.run(["git", "add", CHANGELOG_PATH], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not add files to git staging: {e}")
        
        print(f"Updated version from {old_version} to {new_version}")
        return old_version, new_version
        
    except Exception as e:
        print(f"Error updating version: {e}")
        sys.exit(1)

def update_external_changelog(version: str, date: str, version_type: str, changes: List[str]) -> bool:
    """Update the CHANGELOG.md file with new version information"""
    try:
        if not os.path.exists(CHANGELOG_PATH):
            # Create a new changelog if it doesn't exist
            with open(CHANGELOG_PATH, 'w', encoding='utf-8') as f:
                f.write("# Changelog\n\n")
                f.write("All notable changes to the Backtester App will be documented in this file.\n\n")
        
        with open(CHANGELOG_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Determine change type
        if version_type == 'major':
            change_type = "Major changes with breaking updates"
        elif version_type == 'minor':
            change_type = "New features and non-breaking changes"
        else:
            change_type = "Bug fixes and minor updates"
        
        # Format new changelog entry
        new_entry = f"## [v{version}] - {date}\n\n"
        new_entry += f"### {change_type}\n\n"
        
        # Add changes as bullet points
        if changes:
            for change in changes:
                new_entry += f"- {change}\n"
        else:
            new_entry += "- Maintenance and version update\n"
        
        new_entry += "\n"
        
        # Insert the new entry after the header
        header_match = re.search(r'(# Changelog.*?)(?=\n## |\Z)', content, re.DOTALL)
        if header_match:
            position = header_match.end()
            content = content[:position] + "\n" + new_entry + content[position:]
        else:
            content += f"{new_entry}\n"
        
        with open(CHANGELOG_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"Warning: Could not update CHANGELOG.md: {e}")
        return False

# ---- Git Tag Functions ----

def run_git_command(command: List[str]) -> str:
    """Run a Git command and return its output"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if 'capture_output' in e.__dict__ and e.stderr:
            print(f"Git error: {e.stderr}")
        else:
            print(f"Git error: {e}")
        sys.exit(1)

def create_version_tag(push: bool = False) -> None:
    """Create a Git tag for the current version"""
    # Get the current version
    version = get_current_version()
    tag_name = f"v{version}"
    
    # Check if this tag already exists
    git_tags = run_git_command(["git", "tag"])
    if tag_name in git_tags.split("\n"):
        print(f"Error: Tag {tag_name} already exists.")
        sys.exit(1)
    
    # Check for uncommitted changes
    status = run_git_command(["git", "status", "--porcelain"])
    if status:
        print("Warning: You have uncommitted changes.")
        response = input("Do you want to commit all changes before tagging? (y/n): ")
        if response.lower() == 'y':
            commit_msg = input("Enter commit message: ")
            run_git_command(["git", "add", "."])
            run_git_command(["git", "commit", "-m", commit_msg])
    
    # Get changelog entry for this version
    try:
        version_info = get_version_info()
        changelog = version_info['changelog'].get(version, {})
        changes = changelog.get("changes", [])
        change_list = "\n".join([f"- {change}" for change in changes])
        
        tag_message = f"Version {version}\n\n{change_list}"
    except Exception as e:
        print(f"Warning: Could not get changelog: {e}")
        tag_message = f"Version {version}"
    
    # Create the tag
    print(f"\nCreating tag {tag_name} with message:")
    print(tag_message)
    print("\n")
    
    confirm = input("Confirm tagging operation? (y/n): ")
    if confirm.lower() != 'y':
        print("Tagging operation cancelled")
        return
    
    run_git_command(["git", "tag", "-a", tag_name, "-m", tag_message])
    print(f"Tag {tag_name} created locally.")
    
    # Push the tag if requested
    if push:
        run_git_command(["git", "push", "origin", tag_name])
        print(f"Tag {tag_name} pushed to remote repository.")
    else:
        print(f"Use 'git push origin {tag_name}' to push this tag to the remote repository.")

# ---- Version Rollback Functions ----

def get_available_versions() -> List[str]:
    """Get all available versioned tags from git"""
    try:
        all_tags = run_git_command(["git", "tag", "-l"])
        if not all_tags:
            return []
        
        # Filter only version tags (e.g., v1.0.0)
        version_tags = []
        for tag in all_tags.split("\n"):
            if re.match(r"^v\d+\.\d+\.\d+", tag):
                version_tags.append(tag)
        
        # Sort tags by version components
        version_tags.sort(key=lambda t: [int(x) for x in t.lstrip('v').split('.')], reverse=True)
        return version_tags
    except Exception:
        return []

def display_available_versions() -> None:
    """Display all available versions"""
    versions = get_available_versions()
    
    if not versions:
        print("No versioned tags found in the repository.")
        return
    
    print("\nAvailable versions (most recent first):")
    for i, tag in enumerate(versions):
        # Try to get the tag message for more info
        try:
            tag_info = run_git_command(["git", "show", tag, "--format=%ai %an"])
            tag_date = tag_info.split("\n")[0].split(" ")[0]
            print(f"  {i+1}. {tag} (Released: {tag_date})")
        except:
            print(f"  {i+1}. {tag}")

def restore_version(version_tag: Optional[str] = None, force: bool = False) -> None:
    """Restore to a specific version"""
    # Get available versions
    versions = get_available_versions()
    
    # If no versions found, exit
    if not versions:
        print("No versioned tags found in the repository.")
        sys.exit(1)
    
    # If version not specified, show interactive menu
    if not version_tag:
        print("Available versions:")
        for i, tag in enumerate(versions):
            print(f"  {i+1}. {tag}")
        
        while True:
            try:
                choice = int(input("\nEnter the number of the version to restore (0 to cancel): "))
                if choice == 0:
                    print("Operation cancelled.")
                    return
                if 1 <= choice <= len(versions):
                    version_tag = versions[choice-1]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(versions)}")
            except ValueError:
                print("Please enter a valid number")
    elif version_tag not in versions:
        print(f"Version {version_tag} not found in repository tags.")
        print("Available versions:", ", ".join(versions))
        sys.exit(1)
    
    # Check for uncommitted changes
    status = run_git_command(["git", "status", "--porcelain"])
    if status and not force:
        print("Warning: You have uncommitted changes that will be lost.")
        response = input("Do you want to commit these changes before restoring? (y/n/c): ")
        if response.lower() == 'c':
            print("Operation cancelled.")
            return
        elif response.lower() == 'y':
            commit_msg = input("Enter commit message: ")
            run_git_command(["git", "add", "."])
            run_git_command(["git", "commit", "-m", commit_msg])
    
    # Restore to the specified version
    checkout_cmd = ["git", "checkout", version_tag]
    if force:
        checkout_cmd.append("--force")
    
    print(f"\nRestoring to version {version_tag}...")
    subprocess.run(checkout_cmd, check=True)
    
    # Check if requirements.txt exists and offer to install dependencies
    req_file = os.path.join(PROJECT_ROOT, "requirements.txt")
    if os.path.exists(req_file):
        response = input("Do you want to install dependencies for this version? (y/n): ")
        if response.lower() == 'y':
            print("\nInstalling dependencies...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file], check=True)
                print("✅ Dependencies installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Error installing dependencies: {e}")
    
    print(f"\n✅ Successfully restored to version {version_tag}")
    print("Note: You are now in a 'detached HEAD' state.")
    print("If you want to make changes, consider creating a branch with:")
    print(f"  git checkout -b branch-name-from-{version_tag}")

# ---- Git Hook Functions ----

def detect_version_change_from_commit() -> str:
    """Detect version change type from commit message"""
    try:
        if not os.path.exists(COMMIT_MSG_PATH):
            return 'patch'  # Default to patch if no commit message found
            
        with open(COMMIT_MSG_PATH, 'r', encoding='utf-8') as f:
            commit_msg = f.read().lower()
            
        if re.search(r'breaking|major change|major update', commit_msg):
            return 'major'
        elif re.search(r'new feature|minor change|minor update', commit_msg):
            return 'minor'
        else:
            return 'patch'
    except Exception:
        return 'patch'  # Default to patch if any error

def setup_git_hooks() -> bool:
    """Set up Git pre-commit hook for automatic versioning"""
    hook_path = os.path.join(PROJECT_ROOT, '.git', 'hooks', 'pre-commit')
    hook_content = """#!/bin/sh
# Auto version pre-commit hook
python scripts/version_manager.py auto-update
"""
    
    try:
        with open(hook_path, 'w', encoding='utf-8') as f:
            f.write(hook_content)
        
        # Make the hook executable
        os.chmod(hook_path, 0o755)
        print(f"Git pre-commit hook set up successfully at {hook_path}")
        return True
    except Exception as e:
        print(f"Error setting up git hook: {e}")
        return False

def auto_update_version() -> None:
    """Automatically update version based on commit message"""
    # Detect version type from commit message
    version_type = detect_version_change_from_commit()
    
    # Get commit message for changelog
    try:
        with open(COMMIT_MSG_PATH, 'r', encoding='utf-8') as f:
            commit_msg = f.read().strip()
            # Extract the first line as the change description
            change_description = commit_msg.split('\n')[0]
    except:
        change_description = "Automatic version update"
    
    # Update the version
    old_version, new_version = update_version(version_type, [change_description])
    print(f"Auto-updated version from {old_version} to {new_version} ({version_type})")

# ---- Main Function and Command Line Interface ----

def main():
    parser = argparse.ArgumentParser(description='Unified Version Management for Backtester App')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Update version command
    update_parser = subparsers.add_parser('update', help='Update version numbers')
    update_parser.add_argument('type', choices=['major', 'minor', 'patch'], help='Type of version update')
    update_parser.add_argument('--changes', nargs='+', help='List of changes for changelog')
    
    # Tag version command
    tag_parser = subparsers.add_parser('tag', help='Create Git tag for current version')
    tag_parser.add_argument('--push', action='store_true', help='Push tag to remote repository')
    
    # Setup Git hooks command
    subparsers.add_parser('setup-hooks', help='Set up Git hooks for automatic versioning')
    
    # Restore version command
    restore_parser = subparsers.add_parser('restore', help='Restore to previous version')
    restore_parser.add_argument('--version', type=str, help='Specific version to restore (e.g., v1.0.0)')
    restore_parser.add_argument('--list', action='store_true', help='List available versions')
    restore_parser.add_argument('--force', action='store_true', help='Force checkout (discards local changes)')
    
    # Version info command
    subparsers.add_parser('info', help='Display current version information')
    
    # Auto-update command (used by Git hooks)
    subparsers.add_parser('auto-update', help='Automatically update version based on commit message')
    
    args = parser.parse_args()
    
    # Execute the appropriate command
    if args.command == 'update':
        changes = args.changes or ["Version update"]
        update_version(args.type, changes)
    
    elif args.command == 'tag':
        create_version_tag(args.push)
    
    elif args.command == 'setup-hooks':
        setup_git_hooks()
    
    elif args.command == 'restore':
        if args.list:
            display_available_versions()
        else:
            restore_version(args.version, args.force)
    
    elif args.command == 'info':
        display_version_info()
    
    elif args.command == 'auto-update':
        auto_update_version()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()