from typing import Dict
import pandas as pd
import numpy as np
from .base import BaseStrategy

class MovingAverageCrossover(BaseStrategy):
    def __init__(self, short_window=50, long_window=200):
        self.short_window = short_window
        self.long_window = long_window
        
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Generate trading signals for each instrument"""
        signals = {}
        
        for ticker, df in data.items():
            try:
                df = df.copy()
                close_prices = df['Close'].astype(float)
                
                # Calculate SMAs with minimum periods
                df['SMA_short'] = close_prices.rolling(
                    window=self.short_window,
                    min_periods=1
                ).mean()
                
                df['SMA_long'] = close_prices.rolling(
                    window=self.long_window,
                    min_periods=1
                ).mean()
                
                # Generate signals ensuring all arrays have same length
                df['Signal'] = 0  # Initialize with zeros
                df.loc[df['SMA_short'] > df['SMA_long'], 'Signal'] = 1
                df.loc[df['SMA_short'] < df['SMA_long'], 'Signal'] = -1
                
                # Forward fill any remaining NaN values
                df = df.fillna(method='ffill').fillna(0)
                
                signals[ticker] = df
                
            except Exception as e:
                print(f"Error generating signals for {ticker}: {str(e)}")
                continue
                
        return signals
