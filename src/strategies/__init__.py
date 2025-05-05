"""
Strategies Package Initialization

This package contains implementations of trading strategies including base classes
and concrete strategy implementations like Moving Average, RSI, and Bollinger Bands.
"""

import logging
from src.strategies.base import BaseStrategy

logger = logging.getLogger(__name__)

# --- Import specific strategy classes ---
# Remove try...except to see full tracebacks on import failure
from src.strategies.moving_average import MovingAverageStrategy
from src.strategies.rsi import RSIStrategy
from src.strategies.bollinger import BollingerBandsStrategy

# --- Registry of Available Strategies ---
# Keys should match what backtest_manager expects (e.g., 'MAC', 'RSI')
AVAILABLE_STRATEGIES = {}

# Add strategies to the registry
# Check if the import succeeded (variable will exist)
if 'MovingAverageStrategy' in locals() and MovingAverageStrategy:
    AVAILABLE_STRATEGIES["MAC"] = MovingAverageStrategy # Use 'MAC' key
else:
    logger.warning("MovingAverageStrategy not available.")

if 'RSIStrategy' in locals() and RSIStrategy:
    AVAILABLE_STRATEGIES["RSI"] = RSIStrategy # Use 'RSI' key
else:
    logger.warning("RSIStrategy not available.")

if 'BollingerBandsStrategy' in locals() and BollingerBandsStrategy:
    AVAILABLE_STRATEGIES["BB"] = BollingerBandsStrategy # Use 'BB' key
else:
    logger.warning("BollingerBandsStrategy not available.")


# --- Helper Functions ---
def get_strategy_class(strategy_key: str) -> type[BaseStrategy] | None:
    """
    Retrieves the strategy class object based on its registered key.

    Args:
        strategy_key (str): The key used in the AVAILABLE_STRATEGIES dictionary (e.g., 'RSI', 'MAC').

    Returns:
        type[BaseStrategy] | None: The strategy class if found, otherwise None.
    """
    strategy_class = AVAILABLE_STRATEGIES.get(strategy_key)
    if strategy_class is None:
        logger.warning(f"Strategy class for key '{strategy_key}' not found in AVAILABLE_STRATEGIES.")
    return strategy_class

def get_available_strategy_names() -> list[str]:
    """
    Returns a list of the display names of all registered strategies.
    NOTE: This might need adjustment if UI needs display names different from keys.
    For now, returning the keys used by the backend.

    Returns:
        list[str]: A list of strategy keys ('MAC', 'RSI', 'BB').
    """
    return list(AVAILABLE_STRATEGIES.keys())


# --- Startup Check ---
if not AVAILABLE_STRATEGIES:
    logger.error("CRITICAL: No strategies were successfully imported and registered in AVAILABLE_STRATEGIES.")
else:
    logger.info(f"Registered strategies: {list(AVAILABLE_STRATEGIES.keys())}")