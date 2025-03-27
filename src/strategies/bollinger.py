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
        super().generate_signals(data)  # Initialize tickers
        signals = {}
        
        for ticker, df in data.items():
            df = df.copy()
            
            # Calculate Bollinger Bands using the entire dataset
            close_prices = df['Close'].astype(float)
            df['MA'] = close_prices.rolling(window=self.window, min_periods=1).mean()
            df['std'] = close_prices.rolling(window=self.window, min_periods=1).std()
            df['Upper'] = df['MA'] + (df['std'] * self.num_std)
            df['Lower'] = df['MA'] - (df['std'] * self.num_std)
            
            # Generate signals only for trading period
            df['Signal'] = 0
            trading_mask = df.index >= pd.Timestamp('2020-01-01', tz='UTC')
            
            # Long signal when price crosses below lower band
            long_signal = (close_prices < df['Lower']) & trading_mask
            # Short signal when price crosses above upper band
            short_signal = (close_prices > df['Upper']) & trading_mask
            
            df.loc[long_signal, 'Signal'] = 1
            df.loc[short_signal, 'Signal'] = -1
            
            signals[ticker] = df
            
        return signals