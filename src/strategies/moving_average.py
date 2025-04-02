import numpy as np
import pandas as pd
from .base import BaseStrategy

class MovingAverageCrossoverStrategy(BaseStrategy):
    """Moving Average Crossover strategy implementation"""
    
    def __init__(self, tickers, short_window=20, long_window=50):
        """Initialize strategy with parameters"""
        super().__init__(tickers)
        self.short_window = short_window
        self.long_window = long_window
        
    def generate_signals(self, ticker, data):
        """Generate buy/sell signals using moving average crossover."""
        # Create copy to avoid modifying original data
        df = data.copy()
        
        # Calculate moving averages
        df['SMA_Short'] = df['Close'].rolling(window=self.short_window).mean()
        df['SMA_Long'] = df['Close'].rolling(window=self.long_window).mean()
        
        # Initialize signal column
        df['Signal'] = 0.0
        
        # Create signals
        # Buy signal (1) when short MA crosses above long MA
        # Sell signal (-1) when short MA crosses below long MA
        df['Signal'] = np.where(df['SMA_Short'] > df['SMA_Long'], 1.0, 
                       np.where(df['SMA_Short'] < df['SMA_Long'], -1.0, 0.0))
        
        # Generate position column - this is the current position, not the change in position
        df['Position'] = df['Signal']
        
        return df[['SMA_Short', 'SMA_Long', 'Signal', 'Position']]
