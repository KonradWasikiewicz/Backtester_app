from typing import Dict
import pandas as pd
from .base import BaseStrategy

class MovingAverageCrossover(BaseStrategy):
    """
    Moving Average Crossover strategy
    
    Generates buy signals when short-term MA crosses above long-term MA
    Generates sell signals when short-term MA crosses below long-term MA
    """
    
    def __init__(self, short_window=50, long_window=200):
        super().__init__(short_window=short_window, long_window=long_window)
        self.short_window = short_window
        self.long_window = long_window
        
    def _generate_signal_for_ticker(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate signals for a single ticker based on MA crossover
        
        Args:
            df: Price data for a single ticker
            
        Returns:
            DataFrame with added MA indicators and Signal column
        """
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
        
        return df
