import pandas as pd
import numpy as np
from typing import Dict
from .base import BaseStrategy

class RSIStrategy(BaseStrategy):
    """Relative Strength Index strategy implementation"""
    
    def __init__(self, tickers, period=14, overbought=70, oversold=30):
        """Initialize strategy with parameters"""
        super().__init__(tickers)
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
    
    def calculate_rsi(self, data):
        """Calculate RSI indicator"""
        delta = data.diff()
        gain = delta.mask(delta < 0, 0)
        loss = -delta.mask(delta > 0, 0)
        
        avg_gain = gain.rolling(window=self.period).mean()
        avg_loss = loss.rolling(window=self.period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_signals(self, ticker, data):
        """
        Generate buy/sell signals using RSI.
        
        Args:
            ticker: The ticker symbol for the current data
            data: DataFrame with price data
            
        Returns:
            DataFrame with signals
        """
        # Create copy to avoid modifying original data
        df = data.copy()
        
        # Calculate RSI
        df['RSI'] = self.calculate_rsi(df['Close'])
        
        # Initialize signal column
        df['Signal'] = 0.0
        
        # Create signals
        # Buy signal (1) when RSI crosses below oversold level
        # Sell signal (-1) when RSI crosses above overbought level
        df['Signal'] = np.where(df['RSI'] < self.oversold, 1.0, 
                       np.where(df['RSI'] > self.overbought, -1.0, 0.0))
        
        # Generate position column
        df['Position'] = df['Signal']
        
        return df[['RSI', 'Signal', 'Position']]
