from abc import ABC, abstractmethod
from typing import Dict
import pandas as pd

class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, **kwargs):
        self.tickers = []
        self.params = kwargs
        
    @abstractmethod
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Generate trading signals for the provided data.
        
        Args:
            data: Dictionary mapping ticker symbols to DataFrames with OHLCV data
            
        Returns:
            Dictionary mapping ticker symbols to DataFrames with added Signal column
        """
        pass