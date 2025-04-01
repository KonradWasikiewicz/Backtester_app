import numpy as np
import pandas as pd

class BollingerBandsStrategy:
    """Bollinger Bands strategy implementation"""
    
    def __init__(self, tickers, window=20, num_std=2.0):
        """Initialize strategy with parameters"""
        self.tickers = tickers
        self.window = window
        self.num_std = num_std
        
    def generate_signals(self, ticker, data):
        """Generate buy/sell signals using Bollinger Bands."""
        # Create copy to avoid modifying original data
        df = data.copy()
        
        # Calculate rolling mean and standard deviation
        df['SMA'] = df['Close'].rolling(window=self.window).mean()
        rolling_std = df['Close'].rolling(window=self.window).std()
        
        # Calculate Bollinger Bands
        df['Upper_Band'] = df['SMA'] + (rolling_std * self.num_std)
        df['Lower_Band'] = df['SMA'] - (rolling_std * self.num_std)
        
        # Initialize signal column
        df['Signal'] = 0.0
        
        # Create signals
        # Buy signal (1) when price crosses below lower band
        # Sell signal (-1) when price crosses above upper band
        df['Signal'] = np.where(df['Close'] < df['Lower_Band'], 1.0, 
                       np.where(df['Close'] > df['Upper_Band'], -1.0, 0.0))
        
        # Generate trading signals
        df['Position'] = df['Signal']
        
        return df[['SMA', 'Upper_Band', 'Lower_Band', 'Signal', 'Position']]