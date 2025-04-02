from enum import Enum
import pandas as pd
import plotly.graph_objects as go

# Import strategy classes
from src.strategies.moving_average import MovingAverageCrossoverStrategy
from src.strategies.bollinger import BollingerBandsStrategy
from src.strategies.rsi import RSIStrategy

class SignalType(Enum):
    BUY = 1
    SELL = -1
    HOLD = 0

class TimeFrame(Enum):
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1m"

# Strategy types
class StrategyType(Enum):
    MOVING_AVERAGE = "MA"
    RSI = "RSI"
    BOLLINGER_BANDS = "BB"

TRADING_DAYS_PER_YEAR: int = 252
RISK_FREE_RATE: float = 0.02
BENCHMARK_TICKER: str = "SPY"

# Dictionary mapping strategy types to actual classes (not strings)
AVAILABLE_STRATEGIES = {
    'MA': MovingAverageCrossoverStrategy,
    'BB': BollingerBandsStrategy,
    'RSI': RSIStrategy
}

# Chart theming
CHART_THEME = 'plotly_dark'

# Dropdown styling
DROPDOWN_STYLE = {
    'backgroundColor': '#1e222d',
    'color': '#ffffff',
}