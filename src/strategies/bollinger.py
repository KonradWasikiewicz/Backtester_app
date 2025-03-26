import pandas as pd
import numpy as np
from typing import Dict
from .base import BaseStrategy

class BollingerBandsStrategy(BaseStrategy):
    def __init__(self, window=20, num_std=2):
        self.window = window
        self.num_std = num_std
        
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        signals = {}
        
        for ticker, df in data.items():
            df = df.copy()
            # Convert Close prices to float
            close_prices = df['Close'].astype(float)
            
            # Calculate Bollinger Bands
            df['MA'] = close_prices.rolling(window=self.window).mean()
            rolling_std = close_prices.rolling(window=self.window).std()
            df['Upper'] = df['MA'] + (rolling_std * self.num_std)
            df['Lower'] = df['MA'] - (rolling_std * self.num_std)
            
            # Generate signals using boolean conditions
            df['Signal'] = 0
            df.loc[close_prices < df['Lower'], 'Signal'] = 1  # Buy signal
            df.loc[close_prices > df['Upper'], 'Signal'] = -1  # Sell signal
            
            signals[ticker] = df
            
        return signals