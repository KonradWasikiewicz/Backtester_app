import pandas as pd
import numpy as np
from .base import Strategy

class BollingerBandsStrategy(Strategy):
    def __init__(self, window=20, num_std=2):
        self.window = window
        self.num_std = num_std

    def generate_signals(self, data_dict):
        signals = {}
        for ticker, df in data_dict.items():
            df = df.copy()
            
            # Calculate middle band (SMA)
            df['middle_band'] = df['Close'].rolling(window=self.window).mean()
            
            # Calculate rolling standard deviation
            rolling_std = df['Close'].rolling(window=self.window).std()
            
            # Calculate upper and lower bands
            df['upper_band'] = df['middle_band'] + (rolling_std * self.num_std)
            df['lower_band'] = df['middle_band'] - (rolling_std * self.num_std)
            
            # Generate signals
            df['Signal'] = 0  # Initialize signals
            
            # Buy signal when price crosses below lower band
            df.loc[df['Close'] < df['lower_band'], 'Signal'] = 1
            
            # Sell signal when price crosses above upper band
            df.loc[df['Close'] > df['upper_band'], 'Signal'] = -1
            
            signals[ticker] = df
            
        return signals