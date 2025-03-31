import pandas as pd
import numpy as np
from typing import Dict
from .base import BaseStrategy

class MovingAverageCrossover(BaseStrategy):
    """
    Moving Average Crossover strategy
    
    Generates buy signals when short-term MA crosses above long-term MA
    Generates sell signals when short-term MA crosses below long-term MA
    """
    
    def __init__(self, short_window=20, long_window=50, **kwargs):
        super().__init__(**kwargs)
        self.short_window = short_window
        self.long_window = long_window
        
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Generate trading signals based on moving average crossover.
        
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
            
            # Calculate moving averages
            df['short_ma'] = close_prices.rolling(window=self.short_window).mean()
            df['long_ma'] = close_prices.rolling(window=self.long_window).mean()
            
            # Generate signals
            df['Signal'] = 0
            
            # Buy signal: short MA crosses above long MA
            df.loc[(df['short_ma'] > df['long_ma']) & 
                   (df['short_ma'].shift(1) <= df['long_ma'].shift(1)), 'Signal'] = 1
            
            # Sell signal: short MA crosses below long MA
            df.loc[(df['short_ma'] < df['long_ma']) & 
                   (df['short_ma'].shift(1) >= df['long_ma'].shift(1)), 'Signal'] = -1
            
            # Limit signals to trading period
            trading_start = pd.Timestamp('2020-01-01')
            df.loc[df.index < trading_start, 'Signal'] = 0
            
            signals[ticker] = df
            
        return signals
