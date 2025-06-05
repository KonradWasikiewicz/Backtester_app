"""
UI Package Initialization

This package contains modules related to the user interface components
and callback functions organized into subpackages.
"""

import logging

logger = logging.getLogger(__name__)

# Import main components for easier access
# Example: from src.ui import create_metric_card_with_tooltip
try:
    from .components import create_metric_card, create_metric_card_with_tooltip
    logger.debug("Successfully imported UI components.")
except ImportError as e:
    logger.error(f"Failed to import UI components: {e}")
    # Define empty functions as fallback if critical
    def create_metric_card(*args, **kwargs): return None
    def create_metric_card_with_tooltip(*args, **kwargs): return None

logger.info("UI package initialized.")
