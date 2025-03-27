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
            
            # Calculate Bollinger Bands using the entire dataset
            df['MA'] = close_prices.rolling(window=20, min_periods=20).mean()
            df['std'] = close_prices.rolling(window=20, min_periods=20).std()
            df['Upper'] = df['MA'] + (2 * df['std'])
            df['Lower'] = df['MA'] - (2 * df['std'])
            
            # Initialize signals
            df['Signal'] = 0
            
            # Generate signals only for trading period
            trade_mask = df.index >= pd.Timestamp('2020-01-01', tz='UTC')
            for i in range(1, len(df)):
                if not trade_mask.iloc[i]:
                    continue
                    
                # Buy signal: price crosses below lower band
                if close_prices.iloc[i-1] >= df['Lower'].iloc[i-1] and close_prices.iloc[i] < df['Lower'].iloc[i]:
                    df.iloc[i, df.columns.get_loc('Signal')] = 1
                    
                # Sell signal: price crosses above upper band
                elif close_prices.iloc[i-1] <= df['Upper'].iloc[i-1] and close_prices.iloc[i] > df['Upper'].iloc[i]:
                    df.iloc[i, df.columns.get_loc('Signal')] = -1
            
            signals[ticker] = df
            
        return signals