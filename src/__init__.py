"""
Source Package Initialization (src)

This is the top-level package for the Backtester application's source code.
It contains sub-packages for core logic, strategies, portfolio management,
analysis, UI components, and visualization.
"""

import logging
import sys
from pathlib import Path

# Import version from version.py
try:
    from .version import get_version, get_version_info, VERSION as __version__
except ImportError as e:
    logging.warning(f"Failed to import version information: {e}")
    __version__ = "0.0.0"  # Fallback version

# Get logger for this package
logger = logging.getLogger(__name__)

logger.info(f"Initializing 'src' package version {__version__}...")

# Note: We've simplified the logging configuration by centralizing it in app.py
# and app_factory.py, so we don't need any logging setup here.

logger.info(f"Source package 'src' version {__version__} initialized.")