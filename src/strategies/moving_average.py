from typing import Dict
import pandas as pd
from .base import BaseStrategy

class MovingAverageCrossover(BaseStrategy):
    def __init__(self, short_window=50, long_window=200):
        self.short_window = short_window
        self.long_window = long_window
        
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        signals = {}
        
        for ticker, df in data.items():
            df = df.copy()
            close_prices = df['Close'].astype(float)
            
            # Calculate SMAs
            df['SMA_short'] = close_prices.rolling(
                window=self.short_window,
                min_periods=1
            ).mean()
            
            df['SMA_long'] = close_prices.rolling(
                window=self.long_window,
                min_periods=1
            ).mean()
            
            # Calculate signals using vectorized operations
            df['Signal'] = 0
            long_signals = df['SMA_short'] > df['SMA_long']
            short_signals = df['SMA_short'] < df['SMA_long']
            
            df.loc[long_signals, 'Signal'] = 1
            df.loc[short_signals, 'Signal'] = -1
            
            # Fill missing values
            df['Signal'] = df['Signal'].fillna(0)
            df['SMA_short'] = df['SMA_short'].ffill().bfill()
            df['SMA_long'] = df['SMA_long'].ffill().bfill()
            
            signals[ticker] = df
            
        return signals
