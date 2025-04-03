"""
Portfolio Package Initialization

This package contains modules related to portfolio management,
including position tracking, cash management, trade execution logic,
and risk management integration.
"""

import logging

logger = logging.getLogger(__name__)

# Importuj główne klasy z tego pakietu dla łatwiejszego dostępu
try:
    from .portfolio_manager import PortfolioManager, Position
    logger.debug("Successfully imported PortfolioManager and Position.")
except ImportError as e:
    logger.error(f"Failed to import PortfolioManager or Position: {e}")
    # Fallback definitions
    class PortfolioManager: pass
    class Position: pass

try:
    from .risk_manager import RiskManager
    logger.debug("Successfully imported RiskManager.")
except ImportError as e:
    logger.error(f"Failed to import RiskManager: {e}")
    # Fallback definition
    class RiskManager: pass

# W tej wersji usunęliśmy models.py, więc nie ma klasy Trade do importu stąd
# Jeśli przywrócisz models.py z klasą Trade:
# try:
#     from .models import Trade
#     logger.debug("Successfully imported Trade model.")
# except ImportError as e:
#     logger.error(f"Failed to import Trade model: {e}")
#     class Trade: pass


# Opcjonalnie zdefiniuj __all__
# __all__ = [
#     'PortfolioManager',
#     'Position',
#     'RiskManager',
#     # 'Trade' # Jeśli używasz klasy Trade z models.py
# ]

logger.info("Portfolio package initialized.")