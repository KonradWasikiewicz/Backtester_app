"""
Core Package Initialization

This package forms the core of the backtesting application,
containing essential components like the backtest manager, data loader,
configuration handling, and the main backtesting engine logic.
"""

import logging

logger = logging.getLogger(__name__)

# Import essential classes and objects from modules in this package
try:
    from .config import config
    logger.debug("Successfully imported config object.")
except ImportError as e:
    logger.error(f"Failed to import config object: {e}")
    # Basic fallback for config
    class MockConfig: pass
    config = MockConfig()

try:
    from .data import DataLoader
    logger.debug("Successfully imported DataLoader.")
except ImportError as e:
    logger.error(f"Failed to import DataLoader: {e}")
    # Simple placeholder class
    class DataLoader: pass

try:
    # Core manager component
    from .backtest_manager import BacktestManager
    logger.debug("Successfully imported BacktestManager.")
except ImportError as e:
    logger.error(f"CRITICAL: Failed to import BacktestManager: {e}")
    # Application will likely not work without this
    class BacktestManager: pass

try:
    # Engine - if loop logic is separate from manager
    from .engine import BacktestEngine
    logger.debug("Successfully imported BacktestEngine.")
except ImportError as e:
    # May be less critical if logic is in Manager
    logger.warning(f"Failed to import BacktestEngine: {e}")
    class BacktestEngine: pass

try:
    # Constants used across the application
    from .constants import AVAILABLE_STRATEGIES, CHART_THEME, TRADING_DAYS_PER_YEAR, RISK_FREE_RATE
    logger.debug("Successfully imported constants.")
except ImportError as e:
    logger.warning(f"Failed to import constants: {e}")
    # Default values
    AVAILABLE_STRATEGIES = {}
    CHART_THEME = {}
    TRADING_DAYS_PER_YEAR = 252
    RISK_FREE_RATE = 0.02

try:
    # Custom exception classes
    from .exceptions import BacktestError, DataError, StrategyError
    logger.debug("Successfully imported custom exceptions.")
except ImportError as e:
    logger.warning(f"Failed to import custom exceptions: {e}")
    # Basic exception hierarchy
    class BacktestError(Exception): pass
    class DataError(BacktestError): pass
    class StrategyError(BacktestError): pass

logger.info("Core package initialized.")