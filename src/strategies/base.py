from abc import ABC, abstractmethod
from typing import Dict
import pandas as pd

class BaseStrategy(ABC):
    """Base class for trading strategies"""
    
    def __init__(self):
        self.tickers = []  # Will be populated during signal generation

    @abstractmethod
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Generate trading signals for given data
        
        Args:
            data (Dict[str, pd.DataFrame]): Price data keyed by ticker
            
        Returns:
            Dict[str, pd.DataFrame]: Signals keyed by ticker
        """
        pass