from .moving_average import MovingAverageCrossoverStrategy
from .rsi import RSIStrategy
from .bollinger_bands import BollingerBandsStrategy
from .base import BaseStrategy

__all__ = [
    'MovingAverageCrossoverStrategy',
    'RSIStrategy',
    'BollingerBandsStrategy',
    'BaseStrategy'
]

# Strategy mapping
STRATEGIES = {
    'MA': MovingAverageCrossoverStrategy,
    'RSI': RSIStrategy,
    'BB': BollingerBandsStrategy
}