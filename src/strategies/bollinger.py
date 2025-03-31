import pandas as pd
import numpy as np
from typing import Dict
from .base import BaseStrategy

class BollingerBandsStrategy(BaseStrategy):
    """
    Bollinger Bands strategy
    
    Generates buy signals when price touches lower band
    Generates sell signals when price touches upper band
    """
    
    def __init__(self, window=20, num_std=2):
        super().__init__(window=window, num_std=num_std)
        self.window = window
        self.num_std = num_std
        
    def _generate_signal_for_ticker(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate signals for a single ticker based on Bollinger Bands
        
        Args:
            df: Price data for a single ticker
            
        Returns:
            DataFrame with added Bollinger Band indicators and Signal column
        """
        close_prices = df['Close'].astype(float)
        
        # Calculate Bollinger Bands
        df['MA'] = close_prices.rolling(window=self.window).mean()
        df['std'] = close_prices.rolling(window=self.window).std()
        df['Upper'] = df['MA'] + (self.num_std * df['std'])
        df['Lower'] = df['MA'] - (self.num_std * df['std'])
        
        # Generate signals using pandas operations
        df['Signal'] = 0
        df.loc[close_prices < df['Lower'], 'Signal'] = 1
        df.loc[close_prices > df['Upper'], 'Signal'] = -1
        
        return df

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
            
            # Generate signals using vector operations
            df['Signal'] = 0
            df.loc[close_prices < df['Lower'], 'Signal'] = 1  # Buy signal
            df.loc[close_prices > df['Upper'], 'Signal'] = -1  # Sell signal
            
            # Limit signals to trading period
            trading_start = pd.Timestamp('2020-01-01', tz='UTC')
            df.loc[df.index < trading_start, 'Signal'] = 0
            
            signals[ticker] = df
        
        return signals