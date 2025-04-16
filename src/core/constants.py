# src/core/constants.py
import logging
import os
from pathlib import Path

# --- CORRECTED IMPORT PATH: Import from src.strategies ---
from src.strategies.moving_average import MovingAverageStrategy # Corrected path and class name
from src.strategies.rsi import RSIStrategy # Corrected path and class name
from src.strategies.bollinger import BollingerBandsStrategy
# Import other strategy classes if they exist...
# from src.strategies.example_strategy import ExampleStrategy # Corrected path

# Configure logging for this module
logger = logging.getLogger(__name__)

# Dictionary of available strategies
# Keys (e.g., "Moving Average Crossover") will be displayed in the UI.
# Values (e.g., MovingAverageStrategy) are the actual classes to use.
AVAILABLE_STRATEGIES = [
    {"label": "Relative Strength Index", "value": "RSI"},
    {"label": "Moving Average Crossover", "value": "MAC"},
    # ... inne strategie
]

STRATEGY_DESCRIPTIONS = {
    "RSI": "The Relative Strength Index (RSI) strategy buys when the RSI drops below a certain level (e.g., 30) and sells when it rises above another level (e.g., 70).",
    "MAC": "The Moving Average Crossover strategy generates buy signals when a shorter-term moving average crosses above a longer-term moving average, and sell signals on the reverse cross.",
    # ... opisy dla innych strategii (klucze muszą pasować do 'value' z AVAILABLE_STRATEGIES)
    "Default": "No description available." # Opcjonalny opis domyślny
}

# Log available strategies when the module starts
logger.info(f"Available strategies loaded: {list(AVAILABLE_STRATEGIES.keys())}")

# Define TRADING_DAYS_PER_YEAR as a constant
TRADING_DAYS_PER_YEAR = 252  # Default number of trading days in a year

# Define CHART_THEME as a constant
CHART_THEME = {
    "background_color": "#ffffff",
    "grid_color": "#e6e6e6",
    "line_color": "#007bff",
    "font_color": "#333333"
}

# Define APP_ROOT as the root directory of the application
APP_ROOT = Path(__file__).resolve().parent.parent.parent

# Define DATA_DIR as a constant
DATA_DIR = os.path.join(APP_ROOT, "data")  # Path to the data directory

# Define RISK_FREE_RATE as a constant
RISK_FREE_RATE = 0.02  # Default risk-free rate (2%)

# You can add other constants used in the project here if needed
# e.g., DEFAULT_COMMISSION = 0.001
# e.g., DEFAULT_SLIPPAGE = 0.0005
