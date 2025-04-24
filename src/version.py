"""
Module for managing application version information using Semantic Versioning (SemVer).
"""

# Application version numbers (SemVer: MAJOR.MINOR.PATCH)
MAJOR = 1
MINOR = 0
PATCH = 39

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
RELEASE_DATE = "2025-04-24"

# Changelog for the current version
CHANGELOG = {
    "1.0.39": {
        "date": "2025-04-24",
        "changes": [
            "1",
        ]
    },
    "1.0.38": {
        "date": "2025-04-24",
        "changes": [
            "2",
        ]
    },
    "1.0.37": {
        "date": "2025-04-24",
        "changes": [
            "1",
        ]
    },
    "1.0.36": {
        "date": "2025-04-24",
        "changes": [
            "1",
        ]
    },
    "1.0.35": {
        "date": "2025-04-23",
        "changes": [
            "1",
        ]
    },
    "1.0.34": {
        "date": "2025-04-23",
        "changes": [
            "1",
        ]
    },
    "1.0.33": {
        "date": "2025-04-23",
        "changes": [
            "1",
        ]
    },
    "1.0.32": {
        "date": "2025-04-23",
        "changes": [
            "2",
        ]
    },
    "1.0.31": {
        "date": "2025-04-22",
        "changes": [
            "1",
        ]
    },
    "1.0.30": {
        "date": "2025-04-22",
        "changes": [
            "1",
        ]
    },
    "1.0.29": {
        "date": "2025-04-22",
        "changes": [
            "1",
        ]
    },
    "1.0.28": {
        "date": "2025-04-18",
        "changes": [
            "1",
        ]
    },
    "1.0.27": {
        "date": "2025-04-18",
        "changes": [
            "1",
        ]
    },
    "1.0.26": {
        "date": "2025-04-17",
        "changes": [
            "1",
        ]
    },
    "1.0.25": {
        "date": "2025-04-17",
        "changes": [
            "o4-mini 2",
        ]
    },
    "1.0.24": {
        "date": "2025-04-17",
        "changes": [
            "o4 mini",
        ]
    },
    "1.0.23": {
        "date": "2025-04-17",
        "changes": [
            "1",
        ]
    },
    "1.0.22": {
        "date": "2025-04-16",
        "changes": [
            "2",
        ]
    },
    "1.0.21": {
        "date": "2025-04-16",
        "changes": [
            "1",
        ]
    },
    "1.0.20": {
        "date": "2025-04-16",
        "changes": [
            "1",
        ]
    },
    "1.0.19": {
        "date": "2025-04-15",
        "changes": [
            "minor arch drift",
        ]
    },
    "1.0.18": {
        "date": "2025-04-15",
        "changes": [
            "1",
        ]
    },
    "1.0.17": {
        "date": "2025-04-15",
        "changes": [
            "1",
        ]
    },
    "1.0.16": {
        "date": "2025-04-15",
        "changes": [
            "1",
        ]
    },
    "1.0.15": {
        "date": "2025-04-15",
        "changes": [
            "1",
        ]
    },
    "1.0.14": {
        "date": "2025-04-15",
        "changes": [
            "2",
        ]
    },
    "1.0.13": {
        "date": "2025-04-15",
        "changes": [
            "2",
        ]
    },
    "1.0.12": {
        "date": "2025-04-15",
        "changes": [
            "1",
        ]
    },
    "1.0.11": {
        "date": "2025-04-15",
        "changes": [
            "2",
        ]
    },
    "1.0.10": {
        "date": "2025-04-14",
        "changes": [
            "1",
        ]
    },
    "1.0.9": {
        "date": "2025-04-14",
        "changes": [
            "1",
        ]
    },
    "1.0.8": {
        "date": "2025-04-14",
        "changes": [
            "patch",
        ]
    },
    "1.0.7": {
        "date": "2025-04-14",
        "changes": [
            "dash console integration",
        ]
    },
    "1.0.6": {
        "date": "2025-04-14",
        "changes": [
            "1",
        ]
    },
    "1.0.5": {
        "date": "2025-04-11",
        "changes": [
            "patch mainly versioning and callbacs",
        ]
    },
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