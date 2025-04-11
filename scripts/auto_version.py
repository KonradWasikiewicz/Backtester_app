#!/usr/bin/env python
"""
Automatic Version Manager for Backtester App

This script automatically handles versioning based on commit messages.
It can be used as a git pre-commit hook to automate versioning.

Usage:
1. As a standalone script: python auto_version.py [patch|minor|major]
2. As a git pre-commit hook (automatically detects version change from commit message)
"""

import os
import sys
import re
import subprocess
from datetime import datetime

# Constants
VERSION_FILE_PATH = os.path.join('src', 'version.py')
CHANGELOG_PATH = 'CHANGELOG.md'
VERSION_PATTERN = r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]'
COMMIT_MSG_PATH = '.git/COMMIT_EDITMSG'

def get_current_version():
    """Get the current version from the version file"""
    try:
        with open(VERSION_FILE_PATH, 'r', encoding='utf-8') as f:
            version_content = f.read()
            match = re.search(VERSION_PATTERN, version_content)
            if match:
                return match.group(1)
            else:
                print(f"Error: Version pattern not found in {VERSION_FILE_PATH}")
                return None
    except FileNotFoundError:
        print(f"Error: Version file not found at {VERSION_FILE_PATH}")
        return None

def update_version(version_type='patch'):
    """
    Update the version based on SemVer (MAJOR.MINOR.PATCH)
    
    Args:
        version_type (str): Type of version update: 'patch', 'minor', or 'major'
    """
    current_version = get_current_version()
    if not current_version:
        return False
    
    # Parse current version
    try:
        major, minor, patch = map(int, current_version.split('.'))
    except ValueError:
        print(f"Error: Invalid version format {current_version}")
        return False
    
    # Update version
    if version_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif version_type == 'minor':
        minor += 1
        patch = 0
    elif version_type == 'patch':
        patch += 1
    else:
        print(f"Error: Invalid version type {version_type}")
        return False
    
    new_version = f"{major}.{minor}.{patch}"
    
    # Update version file
    try:
        with open(VERSION_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = re.sub(VERSION_PATTERN, f'__version__ = "{new_version}"', content)
        
        with open(VERSION_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated version from {current_version} to {new_version}")
        
        # Update changelog if it exists
        update_changelog(current_version, new_version, version_type)
        
        # Add version file to git staging
        subprocess.run(['git', 'add', VERSION_FILE_PATH])
        if os.path.exists(CHANGELOG_PATH):
            subprocess.run(['git', 'add', CHANGELOG_PATH])
        
        return True
    except Exception as e:
        print(f"Error updating version: {str(e)}")
        return False

def update_changelog(old_version, new_version, version_type):
    """Update the changelog with the new version"""
    if not os.path.exists(CHANGELOG_PATH):
        # Create a new changelog if it doesn't exist
        with open(CHANGELOG_PATH, 'w', encoding='utf-8') as f:
            f.write("# Changelog\n\n")
            f.write("All notable changes to the Backtester App will be documented in this file.\n\n")
    
    # Get commit messages since last version tag
    try:
        git_log = subprocess.run(
            ['git', 'log', '--pretty=format:%s', f'v{old_version}..HEAD'],
            capture_output=True, text=True
        ).stdout
    except:
        # If the previous tag doesn't exist, get recent commits
        git_log = subprocess.run(
            ['git', 'log', '-5', '--pretty=format:%s'],
            capture_output=True, text=True
        ).stdout
    
    # Filter out version bump commits
    commits = [
        commit for commit in git_log.splitlines()
        if "version bump" not in commit.lower() and commit.strip()
    ]
    
    with open(CHANGELOG_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Determine change type
    if version_type == 'major':
        change_type = "Major changes with breaking updates"
    elif version_type == 'minor':
        change_type = "New features and non-breaking changes"
    else:
        change_type = "Bug fixes and minor updates"
    
    # Format new changelog entry
    new_entry = f"## [v{new_version}] - {today}\n\n"
    new_entry += f"### {change_type}\n\n"
    
    # Add commit messages as bullet points
    if commits:
        for commit in commits:
            new_entry += f"- {commit}\n"
    else:
        new_entry += "- Maintenance and version update\n"
    
    new_entry += "\n"
    
    # Insert the new entry after the header
    header_match = re.search(r'(# Changelog.*?)\n\n', content, re.DOTALL)
    if header_match:
        position = header_match.end()
        content = content[:position] + new_entry + content[position:]
    else:
        content += f"\n{new_entry}"
    
    with open(CHANGELOG_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated changelog for version {new_version}")
    return True

def detect_version_change_from_commit():
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

def setup_git_hook():
    """Set up git pre-commit hook"""
    hook_path = '.git/hooks/pre-commit'
    hook_content = """#!/bin/sh
# Auto version pre-commit hook
python scripts/auto_version.py auto
"""
    
    try:
        with open(hook_path, 'w', encoding='utf-8') as f:
            f.write(hook_content)
        
        # Make the hook executable
        os.chmod(hook_path, 0o755)
        print(f"Git pre-commit hook set up successfully at {hook_path}")
        return True
    except Exception as e:
        print(f"Error setting up git hook: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python auto_version.py [patch|minor|major|auto|setup]")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    if action == 'setup':
        setup_git_hook()
    elif action in ('patch', 'minor', 'major'):
        update_version(action)
    elif action == 'auto':
        version_type = detect_version_change_from_commit()
        update_version(version_type)
    else:
        print(f"Unknown action: {action}")
        print("Usage: python auto_version.py [patch|minor|major|auto|setup]")
        sys.exit(1)