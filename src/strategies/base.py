import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, tickers):
        """Initialize base strategy with tickers"""
        self.tickers = tickers if isinstance(tickers, list) else [tickers]
    
    @abstractmethod
    def generate_signals(self, ticker, data):
        """
        Generate trading signals for a ticker.
        
        Args:
            ticker: The ticker symbol
            data: DataFrame with price data
            
        Returns:
            DataFrame with signals
        """
        pass
    
    def run_strategy(self, data_dict):
        """
        Run strategy across all tickers.
        
        Args:
            data_dict: Dict mapping tickers to DataFrames with price data
            
        Returns:
            Dict mapping tickers to DataFrames with signals
        """
        signals = {}
        
        for ticker in self.tickers:
            if ticker in data_dict:
                ticker_data = data_dict[ticker]
                if not ticker_data.empty:
                    signals[ticker] = self.generate_signals(ticker, ticker_data)
        
        return signals