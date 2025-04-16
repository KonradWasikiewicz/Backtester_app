"""
Central location for application-wide constants and configurations.
"""

import logging
import os
from pathlib import Path
import numpy as np
import pandas as pd

# --- Logging Setup ---
logger = logging.getLogger(__name__)

# --- Path Constants ---
APP_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = APP_ROOT / "data"
# os.makedirs(DATA_DIR, exist_ok=True) # Opcjonalne

# --- Trading Constants ---
TRADING_DAYS_PER_YEAR: int = 252
RISK_FREE_RATE: float = 0.02

# --- Strategy Definitions ---
AVAILABLE_STRATEGIES: list[dict[str, str]] = [
    {"label": "Relative Strength Index (RSI)", "value": "RSI"},
    {"label": "Moving Average Crossover (MAC)", "value": "MAC"},
    {"label": "Bollinger Bands", "value": "BB"},
    # Add other strategies here
]

# --- Strategy Descriptions ---
STRATEGY_DESCRIPTIONS: dict[str, str] = {
    "RSI": "Buys when RSI crosses below a defined threshold (e.g., 30), sells when RSI crosses above another threshold (e.g., 70).",
    "MAC": "Buys when the shorter-term Moving Average crosses above the longer-term Moving Average, sells on the reverse cross.",
    "BB": "Buys when the price touches or crosses below the lower Bollinger Band, sells when the price touches or crosses above the upper band.",
    # --- ADD DESCRIPTIONS FOR ALL YOUR STRATEGIES ---
}

# --- Default Strategy Parameters ---
DEFAULT_STRATEGY_PARAMS: dict[str, dict] = {
    "RSI": {"rsi_period": 14, "buy_threshold": 30, "sell_threshold": 70},
    "MAC": {"fast_ma": 12, "slow_ma": 26, "signal_ma": 9},
    "BB": {"bb_period": 20, "bb_std_dev": 2.0},
    # --- ADD DEFAULT PARAMS FOR ALL YOUR STRATEGIES ---
}

# --- Strategy Class Mapping (Consider moving elsewhere if circular imports occur) ---
try:
    from src.strategies.moving_average import MovingAverageStrategy
    from src.strategies.rsi import RSIStrategy
    from src.strategies.bollinger import BollingerBandsStrategy
    # Import other strategy classes...

    STRATEGY_CLASS_MAP: dict[str, type] = {
        "RSI": RSIStrategy,
        "MAC": MovingAverageStrategy,
        "BB": BollingerBandsStrategy,
        # --- ADD MAPPINGS FOR ALL YOUR STRATEGIES ---
    }
except ImportError as e:
    logger.error(f"Could not import strategy classes in constants.py: {e}. Check paths/names.", exc_info=True)
    STRATEGY_CLASS_MAP = {}

# --- Log Loaded Strategy Information ---
try:
    strategy_ids = [strategy['value'] for strategy in AVAILABLE_STRATEGIES if isinstance(strategy, dict) and 'value' in strategy]
    logger.info(f"Available strategy IDs loaded from AVAILABLE_STRATEGIES: {strategy_ids}")

    available_ids = set(strategy_ids)
    described_ids = set(STRATEGY_DESCRIPTIONS.keys())
    param_ids = set(DEFAULT_STRATEGY_PARAMS.keys())
    class_map_ids = set(STRATEGY_CLASS_MAP.keys())

    if not available_ids == described_ids:
        logger.warning(f"Mismatch: AVAILABLE_STRATEGIES vs STRATEGY_DESCRIPTIONS. Missing descriptions: {available_ids - described_ids}. Extra descriptions: {described_ids - available_ids}")
    if not available_ids == param_ids:
        logger.warning(f"Mismatch: AVAILABLE_STRATEGIES vs DEFAULT_STRATEGY_PARAMS. Missing params: {available_ids - param_ids}. Extra params: {param_ids - available_ids}")
    if not available_ids == class_map_ids:
         logger.warning(f"Mismatch: AVAILABLE_STRATEGIES vs STRATEGY_CLASS_MAP. Missing classes: {available_ids - class_map_ids}. Extra classes: {class_map_ids - available_ids}")

except Exception as e:
    logger.error(f"Error processing strategy definitions for logging: {e}. Check structures in constants.py.", exc_info=True)

# --- Visualization Configuration ---
VISUALIZATION_CONFIG: dict[str, str | list[str]] = {
    'plot_bgcolor': '#1E1E1E',
    'paper_bgcolor': '#1E1E1E',
    'font_color': '#EAEAEA',
    'colorway': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'],
    'equity_curve_color': '#1f77b4',
    'drawdown_color': '#d62728',
    'buy_marker_color': '#2ca02c',
    'sell_marker_color': '#d62728',
}

# --- DODANA STAŁA CHART_THEME ---
# Ustaw domyślny motyw plotly lub własny. 'plotly_dark' pasuje do ciemnego tła.
CHART_THEME: str = 'plotly_dark'

# --- Other Application Constants ---
# DEFAULT_COMMISSION: float = 0.001
# DEFAULT_SLIPPAGE: float = 0.0005

logger.info("Constants module loaded.")
logger.info(f"Application Root Directory: {APP_ROOT}")
logger.info(f"Data Directory: {DATA_DIR}")
