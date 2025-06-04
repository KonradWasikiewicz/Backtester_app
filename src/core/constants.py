"""
Central location for application-wide constants and configurations.
"""

import logging
import os
from pathlib import Path
import numpy as np
import pandas as pd
from typing import Dict, List, Type, Union

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
AVAILABLE_STRATEGIES: List[Dict[str, str]] = [
    {"label": "Relative Strength Index (RSI)", "value": "RSI"},
    {"label": "Moving Average Crossover (MAC)", "value": "MAC"},
    {"label": "Bollinger Bands (BB)", "value": "BB"},
    # Add other strategies here
]

# --- Strategy Descriptions ---
STRATEGY_DESCRIPTIONS: Dict[str, str] = {
    "RSI": "Buys when RSI crosses below a defined threshold (e.g., 30), sells when RSI crosses above another threshold (e.g., 70).",
    "MAC": "Buys when the shorter-term Moving Average crosses above the longer-term Moving Average, sells on the reverse cross.",
    "BB": "Buys when the price touches or crosses below the lower Bollinger Band, sells when the price touches or crosses above the upper band.",
    # --- ADD DESCRIPTIONS FOR ALL YOUR STRATEGIES ---
}

# --- Default Strategy Parameters ---
DEFAULT_STRATEGY_PARAMS: Dict[str, Dict] = {
    "RSI": {"rsi_period": 14, "lower_bound": 30, "upper_bound": 70},
    "MAC": {"short_window": 12, "long_window": 26},
    "BB": {"window": 20, "num_std": 2.0}, # Changed bb_period to window, bb_std_dev to num_std
    # --- ADD DEFAULT PARAMS FOR ALL YOUR STRATEGIES ---
}

# --- Parameter Descriptions for tooltips and documentation ---
PARAM_DESCRIPTIONS: Dict[str, Dict[str, str]] = {
    "RSI": {
        "rsi_period": "Number of lookback periods to calculate the RSI (e.g., 14 days)",
        "lower_bound": "RSI value below which the strategy generates a buy signal (e.g., 30)",
        "upper_bound": "RSI value above which the strategy generates a sell signal (e.g., 70)"
    },
    "MAC": {
        "short_window": "Number of periods for the short-term moving average (e.g., 12)",
        "long_window": "Number of periods for the long-term moving average (e.g., 26)"
    },
    "BB": {
        "window": "Number of periods to compute the Bollinger Bands moving average (e.g., 20)", # Changed bb_period to window
        "num_std": "Number of standard deviations for the upper/lower bands (e.g., 2)" # Changed bb_std_dev to num_std
    }
    # Add entries for other strategies...
}

import importlib

# --- Strategy Class Mapping (dynamic import to avoid missing when dependencies absent) ---
STRATEGY_CLASS_MAP: Dict[str, Type] = {}
# Map strategy keys to their module and class names
_MODULE_MAP: Dict[str, str] = {"RSI": "rsi", "MAC": "moving_average", "BB": "bollinger"}
_CLASS_MAP: Dict[str, str] = {"RSI": "RSIStrategy", "MAC": "MovingAverageStrategy", "BB": "BollingerBandsStrategy"}
for _key, _module in _MODULE_MAP.items():
    try:
        _mod = importlib.import_module(f"src.strategies.{_module}")
        _cls = getattr(_mod, _CLASS_MAP[_key])
        STRATEGY_CLASS_MAP[_key] = _cls
    except Exception as _err:
        logger.warning(f"Could not import strategy class '{_CLASS_MAP[_key]}' for key '{_key}': {_err}")

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
VISUALIZATION_CONFIG: Dict[str, Union[str, List[str]]] = {
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

MONTHLY_RETURNS_DEFAULT_TITLE: str = "Monthly Returns Heatmap"

# --- Other Application Constants ---
# DEFAULT_COMMISSION: float = 0.001
# DEFAULT_SLIPPAGE: float = 0.0005

logger.info("Constants module loaded.")
logger.info(f"Application Root Directory: {APP_ROOT}")
logger.info(f"Data Directory: {DATA_DIR}")
