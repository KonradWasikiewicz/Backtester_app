from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

class Config:
    """
    Central configuration settings for the Backtester application.
    Access settings via the 'config' instance imported from this module.
    Example: from src.core.config import config; print(config.START_DATE)
    """

    # --- Data Settings ---
    # Relative path to the main historical data file from the project root.
    # Assumes the CSV has columns like: Date, Ticker, Open, High, Low, Close, Volume
    DATA_PATH: str = os.environ.get("BACKTESTER_DATA_PATH", "data/historical_prices.csv")

    # Ticker symbol for the benchmark index used for comparison (e.g., Alpha, Beta calculations).
    BENCHMARK_TICKER: str = os.environ.get("BACKTESTER_BENCHMARK", "SPY")

    # --- Backtest Settings ---
    # Default start date for backtesting periods (YYYY-MM-DD format).
    START_DATE: str = os.environ.get("BACKTESTER_START_DATE", "2020-01-01")

    # Default end date for backtesting periods (YYYY-MM-DD format).
    END_DATE: str = os.environ.get("BACKTESTER_END_DATE", "2023-12-31")

    # Default initial capital for running backtests.
    INITIAL_CAPITAL: float = float(os.environ.get("BACKTESTER_CAPITAL", 100000.0))

    # --- Default Strategy Parameters ---
    # These values are used if no parameters are provided when initializing strategies.
    # Moving Average Crossover defaults
    MOVING_AVERAGE_SHORT: int = int(os.environ.get("MA_SHORT", 20))
    MOVING_AVERAGE_LONG: int = int(os.environ.get("MA_LONG", 50))

    # Bollinger Bands defaults
    BOLLINGER_PERIOD: int = int(os.environ.get("BB_PERIOD", 20))
    BOLLINGER_STD: float = float(os.environ.get("BB_STD", 2.0))

    # RSI defaults
    RSI_PERIOD: int = int(os.environ.get("RSI_PERIOD", 14))
    RSI_OVERBOUGHT: int = int(os.environ.get("RSI_OVERBOUGHT", 70))
    RSI_OVERSOLD: int = int(os.environ.get("RSI_OVERSOLD", 30))

    # --- Performance Calculation Settings ---
    # Annual risk-free rate used for calculations like Sharpe Ratio. (e.g., 0.02 for 2%)
    RISK_FREE_RATE: float = float(os.environ.get("RISK_FREE_RATE", 0.02))

    # Assumed number of trading days in a year for annualization calculations.
    TRADING_DAYS_PER_YEAR: int = int(os.environ.get("TRADING_DAYS", 252))

    # --- Application Settings ---
    # Logging level for the application. Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").upper()

    # --- Sanity Checks (Optional but Recommended) ---
    def __post_init__(self):
        # Ensure data path exists if possible (might not exist during CI/CD)
        # if not Path(self.DATA_PATH).exists():
        #     logger.warning(f"Configured DATA_PATH does not exist: {self.DATA_PATH}")

        # Ensure MA windows are logical
        if self.MOVING_AVERAGE_SHORT >= self.MOVING_AVERAGE_LONG:
            logger.warning(f"MA_SHORT ({self.MOVING_AVERAGE_SHORT}) should be less than MA_LONG ({self.MOVING_AVERAGE_LONG}).")

        # Ensure RSI levels are logical
        if self.RSI_OVERSOLD >= self.RSI_OVERBOUGHT:
            logger.warning(f"RSI_OVERSOLD ({self.RSI_OVERSOLD}) should be less than RSI_OVERBOUGHT ({self.RSI_OVERBOUGHT}).")

        # Ensure capital is positive
        if self.INITIAL_CAPITAL <= 0:
            logger.error("INITIAL_CAPITAL must be positive.")
            # Potentially raise error or set a default positive value

        logger.info("Configuration loaded.")


# --- Create an instance of the Config class to be imported by other modules ---
try:
    config = Config()
    # Run post-init checks if defined
    if hasattr(config, '__post_init__'):
        config.__post_init__()
except Exception as e:
    logger.error(f"CRITICAL: Failed to initialize application configuration: {e}")
    logger.error(traceback.format_exc())
    # Fallback to basic config or exit
    class BasicConfig: # Define a minimal fallback
        DATA_PATH="data/historical_prices.csv"; BENCHMARK_TICKER="SPY"; START_DATE="2020-01-01"; END_DATE="2023-12-31"; INITIAL_CAPITAL=100000.0; RISK_FREE_RATE=0.02; TRADING_DAYS_PER_YEAR=252; LOG_LEVEL="INFO"
        MOVING_AVERAGE_SHORT=20; MOVING_AVERAGE_LONG=50; BOLLINGER_PERIOD=20; BOLLINGER_STD=2.0; RSI_PERIOD=14; RSI_OVERBOUGHT=70; RSI_OVERSOLD=30
    config = BasicConfig()
    logger.warning("Using basic fallback configuration.")


# --- Visualization Config (Separate for clarity, could be part of Config class) ---
VISUALIZATION_CONFIG = {
    "chart_height": 400, # Slightly reduced default height
    "dark_theme": True,  # Matches DARKLY theme
    "template": "plotly_dark", # Explicitly set template name
    "colors": {
        "portfolio": "#17B897",    # Teal/Green for portfolio
        "benchmark": "#FF6B6B",    # Red/Pink for benchmark
        "profit": "#28a745",       # Standard Bootstrap success green
        "loss": "#dc3545",         # Standard Bootstrap danger red
        "primary": "#0d6efd",      # Standard Bootstrap primary blue
        "secondary": "#6c757d",    # Standard Bootstrap secondary gray
        "background": "#131722",   # Very dark background
        "card_background": "#1e222d", # Slightly lighter card background
        "grid_color": "#2a2e39",     # Grid line color
        "text_color": "#dee2e6",     # Light text color
        "text_muted": "#6c757d",    # Muted text color
    }
}

# --- Backtest Engine Config (Separate for clarity, could be part of Config class) ---
# These might be passed directly or used by the engine internally
BACKTEST_ENGINE_CONFIG = {
    "commission_rate": 0.0005,  # Example: 0.05% commission per trade
    "slippage_pct": 0.0002,    # Example: 0.02% slippage per trade (adjust based on asset liquidity)
}