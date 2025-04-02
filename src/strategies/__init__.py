from .base import BaseStrategy
from .moving_average import MovingAverageCrossoverStrategy as MovingAverageStrategy
from .rsi import RSIStrategy
from .bollinger import BollingerBandsStrategy

__all__ = [
    'MovingAverageStrategy',
    'RSIStrategy',
    'BollingerBandsStrategy',
    'BaseStrategy'
]

# Strategy registry
AVAILABLE_STRATEGIES = {
    "MA": MovingAverageStrategy,
    "RSI": RSIStrategy,
    "BB": BollingerBandsStrategy
}

def get_strategy_class(strategy_name):
    """Get a strategy class by name"""
    return AVAILABLE_STRATEGIES.get(strategy_name)

def get_available_strategy_names():
    """Get list of available strategy names"""
    return list(AVAILABLE_STRATEGIES.keys())