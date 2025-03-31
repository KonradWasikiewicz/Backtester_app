from enum import Enum
import pandas as pd
import plotly.graph_objects as go

# Import strategy classes
from ..strategies.moving_average import MovingAverageCrossover
from ..strategies.rsi import RSIStrategy
from ..strategies.bollinger import BollingerBandsStrategy

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
    "MA": MovingAverageCrossover,
    "RSI": RSIStrategy,
    "BB": BollingerBandsStrategy
}

# Default tickers for demo purposes
DEFAULT_TICKERS = ["AAPL", "MSFT", "AMZN", "GOOGL", "META"]

# Chart theming
CHART_THEME = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor='#1e222d',
        plot_bgcolor='#1e222d',
        font={'color': '#ffffff'},
        xaxis={
            'gridcolor': '#2a2e39',
            'zerolinecolor': '#2a2e39',
        },
        yaxis={
            'gridcolor': '#2a2e39',
            'zerolinecolor': '#2a2e39',
        }
    )
)

# Dropdown styling
DROPDOWN_STYLE = {
    'backgroundColor': '#1e222d',
    'color': '#ffffff',
}