from enum import Enum
from typing import Dict, Any

class SignalType(Enum):
    BUY = 1
    SELL = -1
    HOLD = 0

class TimeFrame(Enum):
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1m"

TRADING_DAYS_PER_YEAR: int = 252
RISK_FREE_RATE: float = 0.02
BENCHMARK_TICKER: str = '^GSPC'

CHART_THEME = {
    'paper_bgcolor': '#1e222d',
    'plot_bgcolor': '#1e222d',
    'font_color': '#e1e1e1',
    'grid_color': '#2a2e39'
}

DROPDOWN_STYLE = {
    'backgroundColor': '#1e222d',
    'color': '#e1e1e1',
    'option': {
        'backgroundColor': '#1e222d',
        'color': '#e1e1e1',
        'hover': '#2a2e39'
    }
}

AVAILABLE_STRATEGIES: Dict[str, Any] = {
    "MA": "Moving Average Crossover",
    "RSI": "Relative Strength Index",
    "BB": "Bollinger Bands"
}