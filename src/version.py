"""
Module for managing application version information using Semantic Versioning (SemVer).
"""

# Application version numbers (SemVer: MAJOR.MINOR.PATCH)
MAJOR = 1
MINOR = 0
PATCH = 96

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
RELEASE_DATE = "2025-05-13"

# Changelog for the current version
CHANGELOG = {
    "1.0.96": {
        "date": "2025-05-13",
        "changes": [
            "1",
        ]
    },
    "1.0.95": {
        "date": "2025-05-13",
        "changes": [
            "1",
        ]
    },
    "1.0.94": {
        "date": "2025-05-13",
        "changes": [
            "1",
        ]
    },
    "1.0.93": {
        "date": "2025-05-13",
        "changes": [
            "1",
        ]
    },
    "1.0.92": {
        "date": "2025-05-12",
        "changes": [
            "1",
        ]
    },
    "1.0.91": {
        "date": "2025-05-12",
        "changes": [
            "1",
        ]
    },
    "1.0.90": {
        "date": "2025-05-12",
        "changes": [
            "1",
        ]
    },
    "1.0.89": {
        "date": "2025-05-12",
        "changes": [
            "m",
        ]
    },
    "1.0.88": {
        "date": "2025-05-12",
        "changes": [
            "1",
        ]
    },
    "1.0.87": {
        "date": "2025-05-12",
        "changes": [
            "1",
        ]
    },
    "1.0.86": {
        "date": "2025-05-11",
        "changes": [
            "1",
        ]
    },
    "1.0.85": {
        "date": "2025-05-11",
        "changes": [
            "1",
        ]
    },
    "1.0.84": {
        "date": "2025-05-10",
        "changes": [
            "1",
        ]
    },
    "1.0.83": {
        "date": "2025-05-10",
        "changes": [
            "1",
        ]
    },
    "1.0.82": {
        "date": "2025-05-09",
        "changes": [
            "1",
        ]
    },
    "1.0.81": {
        "date": "2025-05-09",
        "changes": [
            "1",
        ]
    },
    "1.0.80": {
        "date": "2025-05-09",
        "changes": [
            "1",
        ]
    },
    "1.0.79": {
        "date": "2025-05-09",
        "changes": [
            "1",
        ]
    },
    "1.0.78": {
        "date": "2025-05-08",
        "changes": [
            "1",
        ]
    },
    "1.0.77": {
        "date": "2025-05-08",
        "changes": [
            "1",
        ]
    },
    "1.0.76": {
        "date": "2025-05-08",
        "changes": [
            "1",
        ]
    },
    "1.0.75": {
        "date": "2025-05-07",
        "changes": [
            "1",
        ]
    },
    "1.0.74": {
        "date": "2025-05-07",
        "changes": [
            "1",
        ]
    },
    "1.0.73": {
        "date": "2025-05-07",
        "changes": [
            "1",
        ]
    },
    "1.0.72": {
        "date": "2025-05-06",
        "changes": [
            "1",
        ]
    },
    "1.0.71": {
        "date": "2025-05-06",
        "changes": [
            "IDs reimagined",
        ]
    },
    "1.0.70": {
        "date": "2025-05-06",
        "changes": [
            "1",
        ]
    },
    "1.0.69": {
        "date": "2025-05-06",
        "changes": [
            "1",
        ]
    },
    "1.0.68": {
        "date": "2025-05-06",
        "changes": [
            "1",
        ]
    },
    "1.0.67": {
        "date": "2025-05-05",
        "changes": [
            "1",
        ]
    },
    "1.0.66": {
        "date": "2025-05-05",
        "changes": [
            "1",
        ]
    },
    "1.0.65": {
        "date": "2025-05-05",
        "changes": [
            "1",
        ]
    },
    "1.0.64": {
        "date": "2025-05-05",
        "changes": [
            "1",
        ]
    },
    "1.0.63": {
        "date": "2025-05-05",
        "changes": [
            "1",
        ]
    },
    "1.0.62": {
        "date": "2025-05-04",
        "changes": [
            "1",
        ]
    },
    "1.0.61": {
        "date": "2025-05-04",
        "changes": [
            "1",
        ]
    },
    "1.0.60": {
        "date": "2025-05-02",
        "changes": [
            "1",
        ]
    },
    "1.0.59": {
        "date": "2025-05-02",
        "changes": [
            "1",
        ]
    },
    "1.0.58": {
        "date": "2025-05-02",
        "changes": [
            "# Please enter the commit message for your changes. Lines starting",
        ]
    },
    "1.0.57": {
        "date": "2025-05-02",
        "changes": [
            "1",
        ]
    },
    "1.0.56": {
        "date": "2025-04-30",
        "changes": [
            "1",
        ]
    },
    "1.0.55": {
        "date": "2025-04-30",
        "changes": [
            "1",
        ]
    },
    "1.0.54": {
        "date": "2025-04-30",
        "changes": [
            "1",
        ]
    },
    "1.0.53": {
        "date": "2025-04-29",
        "changes": [
            "1",
        ]
    },
    "1.0.52": {
        "date": "2025-04-28",
        "changes": [
            "1",
        ]
    },
    "1.0.51": {
        "date": "2025-04-28",
        "changes": [
            "1",
        ]
    },
    "1.0.50": {
        "date": "2025-04-28",
        "changes": [
            "1",
        ]
    },
    "1.0.49": {
        "date": "2025-04-26",
        "changes": [
            "1",
        ]
    },
    "1.0.48": {
        "date": "2025-04-26",
        "changes": [
            "1",
        ]
    },
    "1.0.47": {
        "date": "2025-04-25",
        "changes": [
            "1",
        ]
    },
    "1.0.46": {
        "date": "2025-04-25",
        "changes": [
            "1",
        ]
    },
    "1.0.45": {
        "date": "2025-04-25",
        "changes": [
            "major functionality update - comparison",
        ]
    },
    "1.0.44": {
        "date": "2025-04-25",
        "changes": [
            "1",
        ]
    },
    "1.0.43": {
        "date": "2025-04-25",
        "changes": [
            "2",
        ]
    },
    "1.0.42": {
        "date": "2025-04-24",
        "changes": [
            "1",
        ]
    },
    "1.0.41": {
        "date": "2025-04-24",
        "changes": [
            "1",
        ]
    },
    "1.0.40": {
        "date": "2025-04-24",
        "changes": [
            "1",
        ]
    },
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