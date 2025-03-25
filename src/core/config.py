from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

class Config:
    """Global configuration"""
    
    # Paths
    ROOT_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = ROOT_DIR / "data"
    DATA_FILE: Path = DATA_DIR / "historical_prices.csv"
    
    @property
    def available_tickers(self) -> List[str]:
        """Get unique tickers from historical data"""
        if not hasattr(self, '_tickers'):
            df = pd.read_csv(self.DATA_FILE)
            self._tickers = sorted(df['Ticker'].unique())
        return self._tickers

    # Benchmark settings
    BENCHMARK_TICKER: str = '^GSPC'
    
    # Trading parameters
    INITIAL_CAPITAL: float = 100_000
    COMMISSION: float = 0.001

# Visualization configuration
VISUALIZATION_CONFIG: Dict[str, Any] = {
    'chart_theme': {
        'template': 'plotly_dark',
        'paper_bgcolor': '#1e222d',
        'plot_bgcolor': '#1e222d',
        'font_color': '#e1e1e1'
    },
    'colors': {
        'portfolio': '#17B897',
        'benchmark': '#FF6B6B',
        'buy': 'green',
        'sell': 'red'
    }
}

# Backtest configuration
BACKTEST_CONFIG: Dict[str, Any] = {
    'initial_capital': 100_000,
    'commission': 0.001,
    'slippage': 0.001,
    'position_size': 0.1
}

config = Config()