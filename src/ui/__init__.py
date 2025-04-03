"""
UI Package Initialization

This package contains modules related to the user interface components
and potentially callbacks (though callbacks are currently in app.py).
"""

import logging

logger = logging.getLogger(__name__)

# Importuj główne komponenty, aby były łatwiej dostępne
# Przykład: from src.ui import create_metric_card_with_tooltip
try:
    from .components import create_metric_card, create_metric_card_with_tooltip
    logger.debug("Successfully imported UI components.")
except ImportError as e:
    logger.error(f"Failed to import UI components: {e}")
    # Możesz zdefiniować puste funkcje jako fallback, jeśli to krytyczne
    def create_metric_card(*args, **kwargs): return None
    def create_metric_card_with_tooltip(*args, **kwargs): return None


# Lista komponentów eksportowanych przy imporcie '*' (niezalecane, ale możliwe)
# __all__ = ['create_metric_card', 'create_metric_card_with_tooltip']

logger.info("UI package initialized.")