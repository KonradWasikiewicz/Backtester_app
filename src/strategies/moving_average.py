from typing import Dict
import pandas as pd
from .base import BaseStrategy

class MovingAverageCrossover(BaseStrategy):
    def __init__(self, short_window=50, long_window=200):
        self.short_window = short_window
        self.long_window = long_window
        
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        self.tickers = list(data.keys())  # Store tickers for position sizing
        signals = {}
        
        for ticker, df in data.items():
            df = df.copy()
            
            # Calculate SMAs using entire dataset (including lookback)
            close_prices = df['Close'].astype(float)
            df['SMA_short'] = close_prices.rolling(
                window=self.short_window,
                min_periods=1
            ).mean()
            
            df['SMA_long'] = close_prices.rolling(
                window=self.long_window,
                min_periods=1
            ).mean()
            
            # Generate signals only for trading period (2020 onwards)
            df['Signal'] = 0
            trading_mask = df.index >= pd.Timestamp('2020-01-01', tz='UTC')
            df.loc[trading_mask & (df['SMA_short'] > df['SMA_long']), 'Signal'] = 1
            df.loc[trading_mask & (df['SMA_short'] < df['SMA_long']), 'Signal'] = -1
            
            signals[ticker] = df
            
        return signals
