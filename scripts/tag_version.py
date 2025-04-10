#!/usr/bin/env python
"""
Version Tagging Script

This script creates a Git tag for the current version defined in version.py.
It ensures that version information in the code and Git tags are synchronized.
"""

import sys
import os
import subprocess
import importlib.util
from pathlib import Path

# Ensure the src directory is in the path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
sys.path.append(PROJECT_ROOT)

def load_version() -> str:
    """Load current version string from version.py"""
    version_path = os.path.join(PROJECT_ROOT, 'src', 'version.py')
    if not os.path.exists(version_path):
        print(f"Error: Version file not found at {version_path}")
        sys.exit(1)
    
    # Load the module directly
    spec = importlib.util.spec_from_file_location("version", version_path)
    version_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(version_module)
    
    return version_module.VERSION

def run_git_command(command):
    """Run a git command and return its output"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing Git command: {e}")
        print(f"Error details: {e.stderr}")
        sys.exit(1)

def main():
    # Get the current version
    version = load_version()
    tag_name = f"v{version}"
    
    # Check if this tag already exists
    git_tags = run_git_command(["git", "tag"])
    if tag_name in git_tags.split("\n"):
        print(f"Error: Tag {tag_name} already exists. Update version.py first.")
        sys.exit(1)
    
    # Check if there are uncommitted changes
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
        spec = importlib.util.spec_from_file_location("version", os.path.join(PROJECT_ROOT, "src", "version.py"))
        version_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(version_module)
        
        changelog = version_module.CHANGELOG.get(version, {})
        changes = changelog.get("changes", [])
        change_list = "\n".join([f"- {change}" for change in changes])
        
        tag_message = f"Version {version}\n\n{change_list}"
    except Exception as e:
        print(f"Warning: Could not get changelog: {e}")
        tag_message = f"Version {version}"
    
    # Create and push the tag
    print(f"\nCreating tag {tag_name} with message:")
    print(tag_message)
    print("\n")
    
    confirm = input("Confirm tagging operation? (y/n): ")
    if confirm.lower() == 'y':
        run_git_command(["git", "tag", "-a", tag_name, "-m", tag_message])
        
        push_confirm = input("Push tag to remote repository? (y/n): ")
        if push_confirm.lower() == 'y':
            run_git_command(["git", "push", "origin", tag_name])
            print(f"Tag {tag_name} created and pushed to remote repository")
        else:
            print(f"Tag {tag_name} created locally. Use 'git push origin {tag_name}' to push to remote.")
    else:
        print("Tagging operation cancelled")

if __name__ == "__main__":
    main()