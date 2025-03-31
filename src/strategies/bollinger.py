import pandas as pd
import numpy as np
from typing import Dict
from .base import BaseStrategy

class BollingerBandsStrategy(BaseStrategy):
    """
    Bollinger Bands strategy
    
    Generates buy signals when price crosses below lower band
    Generates sell signals when price crosses above upper band
    """
    
    def __init__(self, window=20, num_std=2, **kwargs):
        super().__init__(**kwargs)
        self.window = window
        self.num_std = num_std
        
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Generate trading signals based on Bollinger Bands.
        
        Args:
            data: Dictionary of DataFrames with ticker data
            
        Returns:
            Dictionary of DataFrames with added Signal column
        """
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
            
            # Generate signals
            df['Signal'] = 0
            
            # Buy signal: price crosses below lower band
            df.loc[(close_prices < df['Lower']) & 
                   (close_prices.shift(1) >= df['Lower'].shift(1)), 'Signal'] = 1
            
            # Sell signal: price crosses above upper band
            df.loc[(close_prices > df['Upper']) & 
                   (close_prices.shift(1) <= df['Upper'].shift(1)), 'Signal'] = -1
            
            # Limit signals to trading period
            trading_start = pd.Timestamp('2020-01-01')
            df.loc[df.index < trading_start, 'Signal'] = 0
            
            signals[ticker] = df
            
        return signals