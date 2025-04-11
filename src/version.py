"""
Module for managing application version information using Semantic Versioning (SemVer).
"""

# Application version numbers (SemVer: MAJOR.MINOR.PATCH)
MAJOR = 1
MINOR = 0
PATCH = 4

# Build metadata
BUILD = ""

# Pre-release identifier (alpha, beta, rc, etc.)
PRERELEASE = ""

# Version string construction
VERSION = f"{MAJOR}.{MINOR}.{PATCH}"
if PRERELEASE:
    VERSION = f"{VERSION}-{PRERELEASE}"
if BUILD:
    VERSION = f"{VERSION}+{BUILD}"

# Additional version information
VERSION_INFO = {
    "major": MAJOR,
    "minor": MINOR,
    "patch": PATCH,
    "prerelease": PRERELEASE,
    "build": BUILD,
    "full": VERSION,
}

# Release date information
RELEASE_DATE = "2025-04-11"

# Changelog for the current version
CHANGELOG = {
    "1.0.4": {
        "date": "2025-04-11",
        "changes": [
            "patch",
        ]
    },
    "1.0.3": {
        "date": "2025-04-11",
        "changes": [
            "versioning apparentely works",
        ]
    },
    "1.0.2": {
        "date": "2025-04-10",
        "changes": [
            "General code maintenance and improvements",
        ]
    },
    "1.0.1": {
        "date": "2025-04-10",
        "changes": [
            "General code maintenance and improvements",
        ]
    },
    "1.0.0": {
        "date": "2025-04-10",
        "changes": [
            "Initial stable release",
            "Implemented basic backtesting functionality",
            "Added strategy configuration and visualization components"
        ]
    },
    # Add previous versions when making updates
}

def get_version():
    """
    Returns the current application version string.
    
    Returns:
        str: The current version string
    """
    return VERSION

def get_version_info():
    """
    Returns detailed version information as a dictionary.
    
    Returns:
        dict: Dictionary with version details
    """
    return VERSION_INFO.copy()

def get_changelog():
    """
    Returns the application changelog.
    
    Returns:
        dict: Dictionary with version history and changes
    """
    return CHANGELOG.copy()