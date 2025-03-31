from pathlib import Path
import os

class Config:
    """Application configuration"""
    
    def __init__(self):
        # Base paths
        self.PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
        self.DATA_PATH = self.PROJECT_ROOT / "data"
        self.RESULTS_PATH = self.PROJECT_ROOT / "results"
        
        # Ensure directories exist
        os.makedirs(self.DATA_PATH, exist_ok=True)
        os.makedirs(self.RESULTS_PATH, exist_ok=True)
        
        # Backtest settings
        self.INITIAL_CAPITAL = 10000
        self.BENCHMARK_TICKER = "SPY"
        self.START_DATE = "2019-01-01"
        self.END_DATE = "2023-12-31"
        
        # Trading parameters
        self.COMMISSION_RATE = 0.001  # 0.1%
        self.SLIPPAGE = 0.001  # 0.1%
        self.RISK_FREE_RATE = 0.02  # 2%
        
        # UI settings
        self.APP_TITLE = "Trading Strategy Backtester"
        self.THEME = "dark"


# Create singleton instance
config = Config()

# Visualization config
VISUALIZATION_CONFIG = {
    "chart_height": 450,
    "dark_theme": True,
    "colors": {
        "portfolio": "#17B897",
        "benchmark": "#FF6B6B",
        "profit": "#17B897",
        "loss": "#FF6B6B"
    }
}

# Backtest config
BACKTEST_CONFIG = {
    "initial_capital": config.INITIAL_CAPITAL,
    "commission_rate": config.COMMISSION_RATE,
    "slippage": config.SLIPPAGE,
    "benchmark_ticker": config.BENCHMARK_TICKER
}