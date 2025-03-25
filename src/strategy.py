import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List

class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Generate signals for multiple instruments"""
        pass

class MovingAverageCrossover(Strategy):
    def __init__(self, short_window: int = 20, long_window: int = 50):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        signals = {}
        for ticker, df in data.items():
            df = df.copy()
            df['SMA_short'] = df['Close'].rolling(window=self.short_window).mean()
            df['SMA_long'] = df['Close'].rolling(window=self.long_window).mean()
            df['Signal'] = np.where(df['SMA_short'] > df['SMA_long'], 1, -1)
            # Add volatility for position sizing
            df['Volatility'] = df['Close'].pct_change().rolling(window=20).std()
            signals[ticker] = df
        return signals

class RSIStrategy(Strategy):
    def __init__(self, period: int = 14, overbought: int = 70, oversold: int = 30):
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        signals = {}
        for ticker, df in data.items():
            df = df.copy()
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            df['Signal'] = np.where(df['RSI'] < self.oversold, 1,
                                    np.where(df['RSI'] > self.overbought, -1, 0))
            signals[ticker] = df
        return signals

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
