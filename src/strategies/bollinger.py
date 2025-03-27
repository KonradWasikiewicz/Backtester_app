import pandas as pd
import numpy as np
from typing import Dict
from .base import BaseStrategy

class BollingerBandsStrategy(BaseStrategy):
    def __init__(self, window=20, num_std=2):
        super().__init__()
        self.window = window
        self.num_std = num_std
        
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        self.tickers = list(data.keys())
        signals = {}
        
        for ticker, df in data.items():
            df = df.copy()
            close_prices = df['Close'].astype(float)
            
            # Calculate Bollinger Bands
            df['MA'] = close_prices.rolling(window=self.window).mean()
            df['std'] = close_prices.rolling(window=self.window).std()
            df['Upper'] = df['MA'] + (self.num_std * df['std'])
            df['Lower'] = df['MA'] - (self.num_std * df['std'])
            
            # Generate signals using pandas operations
            df['Signal'] = pd.Series(0, index=df.index)
            df.loc[close_prices < df['Lower'], 'Signal'] = 1
            df.loc[close_prices > df['Upper'], 'Signal'] = -1
            
            # Only keep signals for trading period
            df.loc[df.index < pd.Timestamp('2020-01-01', tz='UTC'), 'Signal'] = 0
            
            signals[ticker] = df
            
        return signals