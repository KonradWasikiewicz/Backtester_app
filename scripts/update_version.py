#!/usr/bin/env python
"""
Version Update Script

This script helps manage version updates following Semantic Versioning principles.
It can:
- Increment major, minor, or patch version
- Set pre-release tags (alpha, beta, rc)
- Update the changelog
"""

import sys
import os
import re
from datetime import datetime
import argparse
from pathlib import Path
import importlib.util
from typing import Dict, Any, List, Optional

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

def main() -> None:
    parser = argparse.ArgumentParser(description='Update application version')
    
    # Version increment type
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--major', action='store_true', help='Increment major version')
    group.add_argument('--minor', action='store_true', help='Increment minor version')
    group.add_argument('--patch', action='store_true', help='Increment patch version')
    
    # Optional prerelease tag
    parser.add_argument('--pre', choices=['alpha', 'beta', 'rc'], help='Set prerelease tag')
    parser.add_argument('--pre-num', type=int, help='Prerelease version number (e.g., beta.1)')
    
    # Build metadata
    parser.add_argument('--build', type=str, help='Build metadata (e.g., build.123)')
    
    # Changelog entries
    parser.add_argument('--changes', type=str, nargs='+', required=True, 
                        help='List of changes for the changelog')
    
    args = parser.parse_args()
    
    # Load current version info
    version_info = load_version_info()
    print(f"Current version: {version_info['version']}")
    
    # Update version according to arguments
    if args.major:
        version_info['major'] += 1
        version_info['minor'] = 0
        version_info['patch'] = 0
    elif args.minor:
        version_info['minor'] += 1
        version_info['patch'] = 0
    elif args.patch:
        version_info['patch'] += 1
    
    # Set prerelease if specified
    if args.pre:
        pre_str = args.pre
        if args.pre_num:
            pre_str += f".{args.pre_num}"
        version_info['prerelease'] = pre_str
    else:
        version_info['prerelease'] = ""
    
    # Set build metadata
    version_info['build'] = args.build or ""
    
    # Update version string
    version_info['version'] = f"{version_info['major']}.{version_info['minor']}.{version_info['patch']}"
    if version_info['prerelease']:
        version_info['version'] += f"-{version_info['prerelease']}"
    if version_info['build']:
        version_info['version'] += f"+{version_info['build']}"
    
    # Update the version file
    update_version_file(version_info, args.changes)
    
    print(f"Version updated to: {version_info['version']}")
    print(f"Changes added to changelog:")
    for change in args.changes:
        print(f"  - {change}")

if __name__ == "__main__":
    main()