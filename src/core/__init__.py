"""
Core Package Initialization

This package forms the core of the backtesting application,
containing essential components like the backtest manager, data loader,
configuration handling, and the main backtesting engine logic.
"""

import logging

logger = logging.getLogger(__name__)

# Importuj najważniejsze klasy i obiekty z modułów w tym pakiecie
try:
    from .config import config
    logger.debug("Successfully imported config object.")
except ImportError as e:
    logger.error(f"Failed to import config object: {e}")
    # Fallback - może być trudny, bo config jest fundamentalny
    class MockConfig: pass
    config = MockConfig()

try:
    from .data import DataLoader
    logger.debug("Successfully imported DataLoader.")
except ImportError as e:
    logger.error(f"Failed to import DataLoader: {e}")
    class DataLoader: pass

try:
    # Główny menedżer - kluczowy komponent
    from .backtest_manager import BacktestManager
    logger.debug("Successfully imported BacktestManager.")
except ImportError as e:
    logger.error(f"CRITICAL: Failed to import BacktestManager: {e}")
    class BacktestManager: pass # Aplikacja prawdopodobnie nie zadziała bez tego

try:
    # Silnik - jeśli logika pętli jest oddzielona od managera
    from .engine import BacktestEngine
    logger.debug("Successfully imported BacktestEngine.")
except ImportError as e:
    # To może być mniej krytyczne, jeśli logika jest w Managerze
    logger.warning(f"Failed to import BacktestEngine: {e}")
    class BacktestEngine: pass

try:
    # Stałe i wyjątki, jeśli są potrzebne globalnie
    from .constants import AVAILABLE_STRATEGIES, CHART_THEME, TRADING_DAYS_PER_YEAR, RISK_FREE_RATE # Importuj stałe
    logger.debug("Successfully imported constants.")
except ImportError as e:
    logger.warning(f"Failed to import constants: {e}")
    AVAILABLE_STRATEGIES = {}; CHART_THEME = {}; TRADING_DAYS_PER_YEAR = 252; RISK_FREE_RATE = 0.02

try:
    from .exceptions import BacktestError, DataError, StrategyError # Importuj niestandardowe wyjątki
    logger.debug("Successfully imported custom exceptions.")
except ImportError as e:
    logger.warning(f"Failed to import custom exceptions: {e}")
    class BacktestError(Exception): pass
    class DataError(BacktestError): pass
    class StrategyError(BacktestError): pass


# Opcjonalnie zdefiniuj __all__
# __all__ = [
#     'config',
#     'DataLoader',
#     'BacktestManager',
#     'BacktestEngine',
#     'AVAILABLE_STRATEGIES', # Eksportuj także stałe, jeśli potrzebne
#     'BacktestError', 'DataError', 'StrategyError' # Eksportuj wyjątki
# ]

logger.info("Core package initialized.")