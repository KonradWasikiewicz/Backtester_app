from typing import Dict
import pandas as pd
import numpy as np
from .base import BaseStrategy

class MovingAverageCrossover(BaseStrategy):
    def __init__(self, short_window=50, long_window=200):
        self.short_window = short_window
        self.long_window = long_window
        
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        signals = {}
        
        for ticker, df in data.items():
            df = df.copy()
            df['SMA_short'] = df['Close'].rolling(window=self.short_window).mean()
            df['SMA_long'] = df['Close'].rolling(window=self.long_window).mean()
            
            df['Signal'] = 0
            df.loc[df['SMA_short'] > df['SMA_long'], 'Signal'] = 1
            df.loc[df['SMA_short'] < df['SMA_long'], 'Signal'] = -1
            
            signals[ticker] = df
            
        return signals
