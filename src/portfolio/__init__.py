"""
Portfolio Package Initialization

This package contains modules related to portfolio management,
including position tracking, cash management, trade execution logic,
and risk management integration.
"""

import logging

logger = logging.getLogger(__name__)

# Import main classes from this package for easier access
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

# Note: models.py with Trade class was removed in this version

logger.info("Portfolio package initialized.")