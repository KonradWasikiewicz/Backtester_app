"""
Analysis Package Initialization

This package contains modules for calculating performance metrics,
analyzing trades, and potentially other quantitative analysis tools.
"""

import logging

logger = logging.getLogger(__name__)

# Importuj kluczowe funkcje lub klasy z modułów w tym pakiecie,
# aby można je było łatwiej importować z zewnątrz.
try:
    # Importuj najważniejsze funkcje z metrics.py
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
        # Dodaj inne metryki, jeśli są często używane
    )
    logger.debug("Successfully imported key metric functions.")

    # Importuj TradeAnalyzer, jeśli jest używany (w tej wersji nie jest, ale może być w przyszłości)
    # from .trade_analyzer import TradeAnalyzer
    # logger.debug("Successfully imported TradeAnalyzer.")

except ImportError as e:
    logger.error(f"Failed to import analysis functions/classes: {e}")
    # Można zdefiniować puste funkcje/klasy jako fallback, jeśli to krytyczne
    def calculate_cagr(*args, **kwargs): return None
    def calculate_sharpe_ratio(*args, **kwargs): return None
    # ... i tak dalej dla innych funkcji ...
    # class TradeAnalyzer: pass

# Opcjonalnie zdefiniuj __all__ do kontroli importu '*'
# __all__ = [
#     'calculate_cagr', 'calculate_sharpe_ratio', 'calculate_sortino_ratio',
#     'calculate_max_drawdown', 'calculate_annualized_volatility', 'calculate_alpha',
#     'calculate_beta', 'calculate_information_ratio', 'calculate_recovery_factor',
#     'calculate_trade_statistics',
#     # 'TradeAnalyzer'
# ]

logger.info("Analysis package initialized.")