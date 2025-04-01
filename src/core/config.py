from pathlib import Path
import os

class Config:
    """Configuration settings for the application"""
    
    # Data settings
    DATA_PATH = "data/historical_prices.csv"
    BENCHMARK_TICKER = "SPY"
    
    # Backtest settings
    START_DATE = "2020-01-01"
    END_DATE = "2023-12-31"
    INITIAL_CAPITAL = 100000.0
    
    # Strategy parameters
    MOVING_AVERAGE_SHORT = 20
    MOVING_AVERAGE_LONG = 50
    BOLLINGER_PERIOD = 20
    BOLLINGER_STD = 2.0
    RSI_PERIOD = 14
    RSI_OVERBOUGHT = 70
    RSI_OVERSOLD = 30
    
    # Performance calculation
    RISK_FREE_RATE = 0.02  # 2% annual risk-free rate
    TRADING_DAYS_PER_YEAR = 252
    
    # Other settings
    LOG_LEVEL = "INFO"

# Create an instance of the Config class to export
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
    "initial_capital": Config.INITIAL_CAPITAL,
    "commission_rate": 0.001,  # 0.1%
    "slippage": 0.001,  # 0.1%
    "benchmark_ticker": Config.BENCHMARK_TICKER
}