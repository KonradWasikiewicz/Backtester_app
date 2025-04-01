import numpy as np
import pandas as pd

class RSIStrategy:
    """Relative Strength Index strategy implementation"""
    
    def __init__(self, tickers, window=14, overbought=70, oversold=30):
        """Initialize strategy with parameters"""
        self.tickers = tickers
        self.window = window
        self.overbought = overbought
        self.oversold = oversold
        
    def generate_signals(self, ticker, data):
        """Generate buy/sell signals using RSI."""
        # Create copy to avoid modifying original data
        df = data.copy()
        
        # Calculate price changes
        delta = df['Close'].diff()
        
        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calculate average gain and loss over specified window
        avg_gain = gain.rolling(window=self.window).mean()
        avg_loss = loss.rolling(window=self.window).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Initialize signal column
        df['Signal'] = 0.0
        
        # Create signals
        # Buy signal (1) when RSI drops below oversold level
        # Sell signal (-1) when RSI rises above overbought level
        df['Signal'] = np.where(df['RSI'] < self.oversold, 1.0, 
                       np.where(df['RSI'] > self.overbought, -1.0, 0.0))
        
        # Generate trading signals
        df['Position'] = df['Signal']
        
        return df[['RSI', 'Signal', 'Position']]
