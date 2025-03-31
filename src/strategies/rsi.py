import pandas as pd
import numpy as np
from typing import Dict
from .base import BaseStrategy

class RSIStrategy(BaseStrategy):
    """
    Relative Strength Index (RSI) strategy
    
    Generates buy signals when RSI drops below oversold level
    Generates sell signals when RSI rises above overbought level
    """
    
    def __init__(self, period=14, overbought=70, oversold=30, **kwargs):
        super().__init__(**kwargs)
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Generate trading signals based on RSI levels.
        
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
            
            # Calculate RSI
            delta = close_prices.diff()
            gain = delta.where(delta > 0, 0).rolling(window=self.period).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=self.period).mean()
            
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Generate signals
            df['Signal'] = 0
            
            # Buy signal: RSI crosses below oversold level
            df.loc[(df['RSI'] < self.oversold) & 
                   (df['RSI'].shift(1) >= self.oversold), 'Signal'] = 1
            
            # Sell signal: RSI crosses above overbought level
            df.loc[(df['RSI'] > self.overbought) & 
                   (df['RSI'].shift(1) <= self.overbought), 'Signal'] = -1
            
            # Limit signals to trading period
            trading_start = pd.Timestamp('2020-01-01')
            df.loc[df.index < trading_start, 'Signal'] = 0
            
            signals[ticker] = df
            
        return signals
