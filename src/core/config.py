from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

class Config:
    """Global configuration"""
    
    def __init__(self):
        self.ROOT_DIR = Path(__file__).parent.parent.parent
        self.DATA_DIR = self.ROOT_DIR / "data"
        self.DATA_FILE = self.DATA_DIR / "historical_prices.csv"
        self.TICKERS_FILE = self.DATA_DIR / "tickers.csv"
        self.BENCHMARK_TICKER = 'SPY'
        
    @property
    def default_tickers(self) -> List[str]:
        """Get tickers from tickers.csv file or fallback to default"""
        try:
            if self.TICKERS_FILE.exists():
                df = pd.read_csv(self.TICKERS_FILE)
                # Exclude benchmark from trading tickers
                return sorted([t for t in df['Ticker'].unique() if t != self.BENCHMARK_TICKER])
            else:
                # Fallback to hardcoded defaults
                return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA']
        except Exception as e:
            print(f"Error reading tickers file: {str(e)}")
            return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA']

    @property
    def available_tickers(self) -> List[str]:
        """Get unique tickers from historical data"""
        if self.DATA_FILE.exists():
            df = pd.read_csv(self.DATA_FILE)
            tickers = sorted(df['Ticker'].unique())
            return [t for t in tickers if t != self.BENCHMARK_TICKER]
        return self.default_tickers

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