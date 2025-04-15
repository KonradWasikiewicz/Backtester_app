"""
Analysis Package Initialization

This package contains modules for calculating performance metrics,
analyzing trades, and other quantitative analysis tools.
"""

import logging

logger = logging.getLogger(__name__)

# Import key functions from modules in this package for easier access
try:
    # Import the most important functions from metrics.py
    from .metrics import (
        calculate_cagr,
        calculate_sharpe_ratio,
        calculate_sortino_ratio,
        calculate_max_drawdown,
        calculate_annualized_volatility,
        calculate_alpha,
        calculate_beta,
        calculate_information_ratio,
        calculate_recovery_factor,
        calculate_trade_statistics
    )
    logger.debug("Successfully imported key metric functions.")
except ImportError as e:
    logger.error(f"Failed to import analysis functions/classes: {e}")
    # Define empty placeholder functions if needed
    def calculate_cagr(*args, **kwargs): return None
    def calculate_sharpe_ratio(*args, **kwargs): return None
    def calculate_sortino_ratio(*args, **kwargs): return None
    def calculate_max_drawdown(*args, **kwargs): return None
    def calculate_annualized_volatility(*args, **kwargs): return None
    def calculate_alpha(*args, **kwargs): return None
    def calculate_beta(*args, **kwargs): return None
    def calculate_information_ratio(*args, **kwargs): return None
    def calculate_recovery_factor(*args, **kwargs): return None
    def calculate_trade_statistics(*args, **kwargs): return None

logger.info("Analysis package initialized.")