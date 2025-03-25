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
            df['SMA_short'] = df['Close'].astype(float).rolling(window=self.short_window).mean()
            df['SMA_long'] = df['Close'].astype(float).rolling(window=self.long_window).mean()
            
            df['Signal'] = 0
            # Use numpy.where instead of direct comparison
            df['Signal'] = np.where(df['SMA_short'] > df['SMA_long'], 1,
                                  np.where(df['SMA_short'] < df['SMA_long'], -1, 0))
            
            signals[ticker] = df
            
        return signals
