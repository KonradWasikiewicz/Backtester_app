from typing import Dict
import pandas as pd

class BaseStrategy:
    """Base class for all trading strategies"""
    
    def __init__(self, tickers, **kwargs):
        """Initialize strategy with parameters"""
        self.tickers = tickers
        
    def generate_signals(self, ticker, data):
        """
        Generate buy/sell signals for a given ticker and data.
        
        Args:
            ticker: The ticker symbol for the current data
            data: DataFrame with price data
            
        Returns:
            DataFrame with signals
        """
        raise NotImplementedError("Subclasses must implement this method")