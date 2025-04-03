"""
Visualization Package Initialization

This package contains modules for generating Plotly charts and Dash components
to visualize backtest results, portfolio performance, and trade analysis.
"""

import logging

logger = logging.getLogger(__name__)

# Importuj główną klasę wizualizatora
try:
    from .visualizer import BacktestVisualizer
    logger.debug("Successfully imported BacktestVisualizer.")
except ImportError as e:
    logger.error(f"Failed to import BacktestVisualizer: {e}")
    # Fallback definition
    class BacktestVisualizer: pass

# Możesz też zaimportować kluczowe funkcje z chart_utils, jeśli są często używane bezpośrednio
try:
    from .chart_utils import (
        create_empty_chart,
        create_styled_chart
        # Importuj inne, jeśli potrzebujesz, np.:
        # create_trade_histogram_figure,
        # create_allocation_chart
    )
    logger.debug("Successfully imported key chart utility functions.")
except ImportError as e:
    logger.error(f"Failed to import chart utility functions: {e}")
    def create_empty_chart(*args, **kwargs): return None
    def create_styled_chart(*args, **kwargs): return None
    # ... fallbacki dla innych funkcji ...


# Opcjonalnie zdefiniuj __all__
# __all__ = [
#     'BacktestVisualizer',
#     'create_empty_chart',
#     'create_styled_chart'
#     # Dodaj inne eksportowane elementy
# ]

logger.info("Visualization package initialized.")