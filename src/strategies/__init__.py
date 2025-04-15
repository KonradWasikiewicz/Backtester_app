"""
Strategies Package Initialization

This package contains implementations of trading strategies including base classes
and concrete strategy implementations like Moving Average, RSI, and Bollinger Bands.
"""

import logging
from .base import BaseStrategy

logger = logging.getLogger(__name__)

# --- Import specific strategy classes ---
# Ensure import paths are correct relative to the project structure
try:
    from .moving_average import MovingAverageStrategy
except ImportError as e:
    logger.error(f"Failed to import MovingAverageStrategy: {e}")
    MovingAverageStrategy = None # Set to None if import fails

try:
    from .rsi import RSIStrategy
except ImportError as e:
    logger.error(f"Failed to import RSIStrategy: {e}")
    RSIStrategy = None

try:
    from .bollinger import BollingerBandsStrategy
except ImportError as e:
    logger.error(f"Failed to import BollingerBandsStrategy: {e}")
    BollingerBandsStrategy = None

# --- Registry of Available Strategies ---
# Keys of this dictionary are used in the UI dropdown
# Values are the actual strategy classes
AVAILABLE_STRATEGIES = {}

# Add strategies to the registry only if they were successfully imported
if MovingAverageStrategy:
    AVAILABLE_STRATEGIES["Moving Average Crossover"] = MovingAverageStrategy
else:
    logger.warning("MovingAverageStrategy not available.")

if RSIStrategy:
    AVAILABLE_STRATEGIES["Relative Strength Index"] = RSIStrategy
else:
    logger.warning("RSIStrategy not available.")

if BollingerBandsStrategy:
    AVAILABLE_STRATEGIES["Bollinger Bands"] = BollingerBandsStrategy  # Fixed display name
else:
    logger.warning("BollingerBandsStrategy not available.")


# --- Helper Functions ---
def get_strategy_class(strategy_name: str) -> type[BaseStrategy] | None:
    """
    Retrieves the strategy class object based on its registered name.

    Args:
        strategy_name (str): The key used in the AVAILABLE_STRATEGIES dictionary.

    Returns:
        type[BaseStrategy] | None: The strategy class if found, otherwise None.
    """
    strategy_class = AVAILABLE_STRATEGIES.get(strategy_name)
    if strategy_class is None:
        logger.warning(f"Strategy class for name '{strategy_name}' not found in AVAILABLE_STRATEGIES.")
    return strategy_class

def get_available_strategy_names() -> list[str]:
    """
    Returns a list of the names (keys) of all registered strategies.

    Returns:
        list[str]: A list of strategy names suitable for UI dropdowns.
    """
    return list(AVAILABLE_STRATEGIES.keys())


# --- Startup Check ---
if not AVAILABLE_STRATEGIES:
    logger.error("CRITICAL: No strategies were successfully imported and registered in AVAILABLE_STRATEGIES.")
else:
    logger.info(f"Registered strategies: {list(AVAILABLE_STRATEGIES.keys())}")