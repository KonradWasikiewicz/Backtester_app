import pandas as pd
import numpy as np
from typing import Dict
from .base import BaseStrategy

class RSIStrategy(BaseStrategy):
    """
    Relative Strength Index strategy
    
    Generates buy signals when RSI is below oversold level
    Generates sell signals when RSI is above overbought level
    """
    
    def __init__(self, period=14, overbought=70, oversold=30):
        super().__init__(period=period, overbought=overbought, oversold=oversold)
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        
    def _generate_signal_for_ticker(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate signals for a single ticker based on RSI
        
        Args:
            df: Price data for a single ticker
            
        Returns:
            DataFrame with added RSI indicator and Signal column
        """
        close_prices = df['Close'].astype(float)
        
        # Calculate RSI
        delta = close_prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=self.period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=self.period).mean()
        
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Generate signals
        df['Signal'] = pd.Series(0, index=df.index)
        df.loc[df['RSI'] < self.oversold, 'Signal'] = 1
        df.loc[df['RSI'] > self.overbought, 'Signal'] = -1
        
        return df

    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
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
            
            # Generate signals using vector operations
            df['Signal'] = 0
            df.loc[df['RSI'] < self.oversold, 'Signal'] = 1  # Buy signal
            df.loc[df['RSI'] > self.overbought, 'Signal'] = -1  # Sell signal
            
            # Limit signals to trading period
            trading_start = pd.Timestamp('2020-01-01', tz='UTC')
            df.loc[df.index < trading_start, 'Signal'] = 0
            
            signals[ticker] = df
        
        return signals
