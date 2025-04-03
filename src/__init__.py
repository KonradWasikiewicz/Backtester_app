"""
Source Package Initialization (src)

This is the top-level package for the Backtester application's source code.
It contains sub-packages for core logic, strategies, portfolio management,
analysis, UI components, and visualization.
"""

import logging
import sys
from pathlib import Path

# Ustawienie podstawowej konfiguracji logowania, jeśli nie zostało to zrobione gdzie indziej
# Można to zrobić tutaj, aby mieć pewność, że logger jest skonfigurowany
# przed importem jakichkolwiek podpakietów, które mogą go używać.
# Jednak preferowane jest robienie tego w głównym punkcie wejścia aplikacji (np. app.py).
# Jeśli app.py już to robi, ta sekcja może być zakomentowana lub usunięta.
# logging.basicConfig(
#     level=logging.INFO, # Można pobrać z config lub zmiennej środowiskowej
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         # logging.FileHandler("app_main.log"), # Log do innego pliku?
#         logging.StreamHandler(sys.stdout) # Loguj do konsoli
#     ]
# )

logger = logging.getLogger(__name__) # Pobierz logger dla tego pakietu

logger.info("Initializing 'src' package...")

# Możesz tutaj zaimportować najważniejsze elementy z podpakietów,
# aby były dostępne bezpośrednio jako `from src import ...`,
# ale może to prowadzić do długiego czasu importu lub problemów z zależnościami cyklicznymi.
# Zazwyczaj lepiej jest importować bezpośrednio z podpakietów (np. from src.core import ...).

# Przykłady (opcjonalne):
# try:
#     from .core import config, BacktestManager
#     from .strategies import AVAILABLE_STRATEGIES
#     from .portfolio import PortfolioManager, RiskManager
#     logger.debug("Successfully re-exported key components from 'src'.")
# except ImportError as e:
#     logger.error(f"Failed to re-export components from 'src' subpackages: {e}")

# Wersja aplikacji (opcjonalne)
__version__ = "0.1.0" # Przykładowa wersja

logger.info(f"Source package 'src' version {__version__} initialized.")

# Możesz też dodać sprawdzenia środowiska, np. wersji Pythona
# if sys.version_info < (3, 8):
#     logger.warning("Application might require Python 3.8 or higher.")