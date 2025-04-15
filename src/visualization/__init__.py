"""
Visualization Package Initialization

This package contains modules for generating Plotly charts and Dash components
to visualize backtest results, portfolio performance, and trade analysis.
"""

import logging

logger = logging.getLogger(__name__)

# Import main visualizer class
try:
    from .visualizer import BacktestVisualizer
    logger.debug("Successfully imported BacktestVisualizer.")
except ImportError as e:
    logger.error(f"Failed to import BacktestVisualizer: {e}")
    # Fallback definition
    class BacktestVisualizer: pass

# Import key functions from chart_utils for direct use
try:
    from .chart_utils import (
        create_empty_chart,
        create_styled_chart
        # Add other functions as needed, e.g.:
        # create_trade_histogram_figure,
        # create_allocation_chart
    )
    logger.debug("Successfully imported key chart utility functions.")
except ImportError as e:
    logger.error(f"Failed to import chart utility functions: {e}")
    def create_empty_chart(*args, **kwargs): return None
    def create_styled_chart(*args, **kwargs): return None
    # Additional fallbacks would go here

logger.info("Visualization package initialized.")