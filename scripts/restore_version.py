#!/usr/bin/env python
"""
Version Restoration Script

This script helps restore the application to a previous version tagged in Git.
It provides a clean, safe way to roll back to a stable version in case of issues.
"""

import sys
import os
import subprocess
import re
import argparse
from typing import List, Optional

# Ensure the src directory is in the path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
sys.path.append(PROJECT_ROOT)

def run_git_command(command: List[str], capture_output: bool = True) -> Optional[str]:
    """Run a git command and return its output if requested"""
    try:
        if capture_output:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        else:
            subprocess.run(command, check=True)
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error executing Git command: {e}")
        print(f"Error details: {e.stderr}")
        sys.exit(1)

def get_available_versions() -> List[str]:
    """Get all available versioned tags from git"""
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

def install_dependencies(requirements_file: str) -> None:
    """Install dependencies from requirements.txt"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_file], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Error installing dependencies: {e}")
        print("You may need to manually install dependencies.")

def main() -> None:
    parser = argparse.ArgumentParser(description="Restore application to a previous version")
    parser.add_argument("--list", action="store_true", help="List available versions")
    parser.add_argument("--version", type=str, help="Specific version to restore (e.g., v1.0.0)")
    parser.add_argument("--deps", action="store_true", help="Also install dependencies for the version")
    parser.add_argument("--force", action="store_true", help="Force checkout (discards local changes)")
    
    args = parser.parse_args()
    
    # Get available versions
    versions = get_available_versions()
    
    # If no versions found, exit
    if not versions:
        print("No versioned tags found in the repository.")
        sys.exit(1)
    
    # List versions if requested
    if args.list:
        print("Available versions (most recent first):")
        for i, tag in enumerate(versions):
            # Try to get the tag message for more info
            try:
                tag_message = run_git_command(["git", "tag", "-l", "-n", tag])
                print(f"  {i+1}. {tag} - {tag_message}")
            except:
                print(f"  {i+1}. {tag}")
        sys.exit(0)
    
    # If version not specified, show interactive menu
    version_tag = args.version
    if not version_tag:
        print("Available versions:")
        for i, tag in enumerate(versions):
            print(f"  {i+1}. {tag}")
        
        while True:
            try:
                choice = int(input("\nEnter the number of the version to restore (0 to cancel): "))
                if choice == 0:
                    print("Operation cancelled.")
                    sys.exit(0)
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
    if status and not args.force:
        print("Warning: You have uncommitted changes that will be lost.")
        response = input("Do you want to commit these changes before restoring? (y/n/c): ")
        if response.lower() == 'c':
            print("Operation cancelled.")
            sys.exit(0)
        elif response.lower() == 'y':
            commit_msg = input("Enter commit message: ")
            run_git_command(["git", "add", "."])
            run_git_command(["git", "commit", "-m", commit_msg])
    
    # Restore to the specified version
    checkout_cmd = ["git", "checkout", version_tag]
    if args.force:
        checkout_cmd.append("--force")
    
    print(f"\nRestoring to version {version_tag}...")
    run_git_command(checkout_cmd, capture_output=False)
    
    # Install dependencies if requested
    if args.deps:
        req_file = os.path.join(PROJECT_ROOT, "requirements.txt")
        if os.path.exists(req_file):
            print("\nInstalling dependencies...")
            install_dependencies(req_file)
        else:
            print("\nNo requirements.txt file found for this version.")
    
    print(f"\n✅ Successfully restored to version {version_tag}")
    print("Note: You are now in a 'detached HEAD' state.")
    print("If you want to make changes, consider creating a branch with:")
    print(f"  git checkout -b branch-name-from-{version_tag}")

if __name__ == "__main__":
    main()