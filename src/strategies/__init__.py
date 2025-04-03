import logging
from .base import BaseStrategy

# --- Importuj konkretne klasy strategii ---
# Upewnij się, że ścieżki importu są poprawne względem struktury projektu
try:
    from .moving_average import MovingAverageCrossoverStrategy
except ImportError as e:
    logging.error(f"Failed to import MovingAverageCrossoverStrategy: {e}")
    MovingAverageCrossoverStrategy = None # Ustaw na None, jeśli import się nie powiódł

try:
    from .rsi import RSIStrategy
except ImportError as e:
    logging.error(f"Failed to import RSIStrategy: {e}")
    RSIStrategy = None

try:
    from .bollinger import BollingerBandsStrategy
except ImportError as e:
    logging.error(f"Failed to import BollingerBandsStrategy: {e}")
    BollingerBandsStrategy = None

# --- Rejestr Dostępnych Strategii ---
# Klucze tego słownika są używane w dropdownie w UI (app.py)
# Wartości to *klasy* strategii (nie instancje)
AVAILABLE_STRATEGIES = {}

# Dodaj strategie do rejestru tylko jeśli zostały poprawnie zaimportowane
if MovingAverageCrossoverStrategy:
    AVAILABLE_STRATEGIES["MA"] = MovingAverageCrossoverStrategy
    # Można użyć pełnej nazwy jako klucza, jeśli preferowane:
    # AVAILABLE_STRATEGIES["Moving Average Crossover"] = MovingAverageCrossoverStrategy
else:
    logging.warning("MovingAverageCrossoverStrategy not available.")

if RSIStrategy:
    AVAILABLE_STRATEGIES["RSI"] = RSIStrategy
else:
    logging.warning("RSIStrategy not available.")

if BollingerBandsStrategy:
    AVAILABLE_STRATEGIES["BB"] = BollingerBandsStrategy
else:
    logging.warning("BollingerBandsStrategy not available.")


# --- Funkcje Pomocnicze (Opcjonalne) ---
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
        logging.warning(f"Strategy class for name '{strategy_name}' not found in AVAILABLE_STRATEGIES.")
    return strategy_class

def get_available_strategy_names() -> list[str]:
    """
    Returns a list of the names (keys) of all registered strategies.

    Returns:
        list[str]: A list of strategy names suitable for UI dropdowns.
    """
    return list(AVAILABLE_STRATEGIES.keys())


# --- Sprawdzenie przy starcie ---
if not AVAILABLE_STRATEGIES:
    logging.error("CRITICAL: No strategies were successfully imported and registered in AVAILABLE_STRATEGIES.")
else:
    logging.info(f"Registered strategies: {list(AVAILABLE_STRATEGIES.keys())}")