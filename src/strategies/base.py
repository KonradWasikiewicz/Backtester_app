from abc import ABC, abstractmethod
from typing import Dict
import pandas as pd

class BaseStrategy:
    """Base class for trading strategies"""
    
    def __init__(self):
        self.tickers = []  # Will be populated during signal generation
        self.trades = []

    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Generate trading signals for multiple instruments
        
        Args:
            data (Dict[str, pd.DataFrame]): Price data keyed by ticker
            
        Returns:
            Dict[str, pd.DataFrame]: Signals keyed by ticker
        """
        self.tickers = list(data.keys())
        return {}