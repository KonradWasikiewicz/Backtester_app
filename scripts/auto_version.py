#!/usr/bin/env python
"""
Automated Version Update Script

This script automatically increments the patch version and adds a generic changelog entry.
It's designed to be run before committing changes or as part of a development workflow.
"""

import sys
import os
import re
from datetime import datetime
import importlib.util
import subprocess
import glob
from typing import List, Dict, Any, Set, Optional

# Ensure the src directory is in the path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
sys.path.append(PROJECT_ROOT)

def load_version_info() -> Dict[str, Any]:
    """Load current version information from version.py"""
    version_path = os.path.join(PROJECT_ROOT, 'src', 'version.py')
    if not os.path.exists(version_path):
        print(f"Error: Version file not found at {version_path}")
        sys.exit(1)
    
    # Load the module directly
    spec = importlib.util.spec_from_file_location("version", version_path)
    version_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(version_module)
    
    return {
        'major': version_module.MAJOR,
        'minor': version_module.MINOR,
        'patch': version_module.PATCH,
        'prerelease': version_module.PRERELEASE,
        'build': version_module.BUILD,
        'version': version_module.VERSION,
        'changelog': version_module.CHANGELOG,
    }

def get_changed_files() -> List[str]:
    """Get a list of files that have changed since the last commit"""
    try:
        # Get changed files (both staged and unstaged)
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, check=True
        )
        changed_files = result.stdout.strip().split('\n')
        
        # Also get untracked files
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True, text=True, check=True
        )
        untracked_files = result.stdout.strip().split('\n')
        
        # Combine and filter empty entries
        all_changed_files = changed_files + untracked_files
        return [f for f in all_changed_files if f]
    except subprocess.CalledProcessError:
        print("Warning: Failed to get changed files using Git. Falling back to checking all Python files.")
        return glob.glob(os.path.join(PROJECT_ROOT, "**/*.py"), recursive=True)

def generate_changes_description(changed_files: List[str]) -> List[str]:
    """Generate a list of change descriptions based on modified files"""
    changes = []
    
    # Categorize changes
    code_changes = []
    ui_changes = []
    doc_changes = []
    script_changes = []
    
    for file in changed_files:
        if not file:
            continue
            
        rel_path = os.path.relpath(file, PROJECT_ROOT) if os.path.isabs(file) else file
        
        # Skip certain files
        if rel_path.endswith('.pyc') or '__pycache__' in rel_path:
            continue
            
        if 'ui/' in rel_path or 'visualization/' in rel_path:
            ui_changes.append(rel_path)
        elif rel_path.startswith('docs/'):
            doc_changes.append(rel_path)
        elif rel_path.startswith('scripts/'):
            script_changes.append(rel_path)
        elif rel_path.endswith('.py'):
            code_changes.append(rel_path)
    
    # Generate descriptions based on categories
    if code_changes:
        changes.append(f"Updated code in: {', '.join(f.split('/')[-1] for f in code_changes[:3])}" + 
                      (f" and {len(code_changes) - 3} more files" if len(code_changes) > 3 else ""))
    
    if ui_changes:
        changes.append("Updated UI components")
    
    if doc_changes:
        changes.append("Updated documentation")
    
    if script_changes:
        changes.append("Updated utility scripts")
    
    # If we couldn't categorize anything, add a generic entry
    if not changes:
        changes.append("General code maintenance and improvements")
    
    return changes

def update_version_file(version_info: Dict[str, Any], changes: List[str]) -> None:
    """Update the version.py file with new version information"""
    version_path = os.path.join(PROJECT_ROOT, 'src', 'version.py')
    
    with open(version_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update version numbers
    content = re.sub(r'MAJOR = \d+', f"MAJOR = {version_info['major']}", content)
    content = re.sub(r'MINOR = \d+', f"MINOR = {version_info['minor']}", content)
    content = re.sub(r'PATCH = \d+', f"PATCH = {version_info['patch']}", content)
    
    # Update prerelease and build info
    content = re.sub(r'PRERELEASE = "[^"]*"', f'PRERELEASE = "{version_info["prerelease"]}"', content)
    content = re.sub(r'BUILD = "[^"]*"', f'BUILD = "{version_info["build"]}"', content)
    
    # Update release date
    today = datetime.now().strftime('%Y-%m-%d')
    content = re.sub(r'RELEASE_DATE = "[^"]*"', f'RELEASE_DATE = "{today}"', content)
    
    # Update changelog
    new_version = version_info['version']
    changelog_entry = f'    "{new_version}": {{\n'
    changelog_entry += f'        "date": "{today}",\n'
    changelog_entry += '        "changes": [\n'
    for change in changes:
        changelog_entry += f'            "{change}",\n'
    changelog_entry += '        ]\n'
    changelog_entry += '    },'
    
    # Find the start of the CHANGELOG dictionary
    changelog_start = content.find('CHANGELOG = {')
    if changelog_start != -1:
        # Find the position after the opening brace
        changelog_insert_pos = content.find('{', changelog_start) + 1
        # Insert the new changelog entry
        content = content[:changelog_insert_pos] + '\n' + changelog_entry + content[changelog_insert_pos:]
    
    # Write updated content back to the file
    with open(version_path, 'w', encoding='utf-8') as f:
        f.write(content)

def create_commit_for_version_bump(version: str) -> bool:
    """Create a commit for the version bump"""
    try:
        # Stage version.py
        subprocess.run(["git", "add", "src/version.py"], check=True)
        
        # Create commit
        commit_msg = f"Bump version to {version} [auto]"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        
        print(f"Created commit for version bump to {version}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to create commit: {e}")
        return False

def main() -> None:
    import argparse
    
    parser = argparse.ArgumentParser(description='Automatically increment patch version')
    parser.add_argument('--no-commit', action='store_true', 
                        help='Do not automatically create a commit for the version change')
    parser.add_argument('--tag', action='store_true',
                        help='Create a Git tag for the new version')
    
    args = parser.parse_args()
    
    # Load current version info
    version_info = load_version_info()
    print(f"Current version: {version_info['version']}")
    
    # Increment patch version
    version_info['patch'] += 1
    
    # Update version string
    version_info['version'] = f"{version_info['major']}.{version_info['minor']}.{version_info['patch']}"
    if version_info['prerelease']:
        version_info['version'] += f"-{version_info['prerelease']}"
    if version_info['build']:
        version_info['version'] += f"+{version_info['build']}"
    
    # Get changed files and generate change descriptions
    changed_files = get_changed_files()
    changes = generate_changes_description(changed_files)
    
    # Update the version file
    update_version_file(version_info, changes)
    
    print(f"Version updated to: {version_info['version']}")
    print(f"Changes added to changelog:")
    for change in changes:
        print(f"  - {change}")
    
    # Create commit if requested
    if not args.no_commit:
        create_commit_for_version_bump(version_info['version'])
    
    # Create tag if requested
    if args.tag:
        try:
            # Import this instead of duplicating code
            from tag_version import main as tag_main
            print("\nCreating Git tag for the new version...")
            tag_main()
        except ImportError:
            print("Warning: Could not import tag_version.py. Tag creation skipped.")
            print("You can run 'python scripts/tag_version.py' manually to create a tag.")

if __name__ == "__main__":
    main()