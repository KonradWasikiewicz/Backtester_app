import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        pass

class MovingAverageCrossover(Strategy):
    def __init__(self, short_window: int = 20, long_window: int = 50):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data = data.copy()
        data['SMA_short'] = data['Close'].rolling(window=self.short_window).mean()
        data['SMA_long'] = data['Close'].rolling(window=self.long_window).mean()
        data['Signal'] = np.where(data['SMA_short'] > data['SMA_long'], 1, -1)
        return data

class RSIStrategy(Strategy):
    def __init__(self, period: int = 14, overbought: int = 70, oversold: int = 30):
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data = data.copy()
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        data['Signal'] = np.where(data['RSI'] < self.oversold, 1,
                                np.where(data['RSI'] > self.overbought, -1, 0))
        return data

class BollingerBandsStrategy(Strategy):
    def __init__(self, window: int = 20, num_std: float = 2.0):
        self.window = window
        self.num_std = num_std

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data = data.copy()
        data['SMA'] = data['Close'].rolling(window=self.window).mean()
        data['STD'] = data['Close'].rolling(window=self.window).std()
        data['Upper'] = data['SMA'] + (data['STD'] * self.num_std)
        data['Lower'] = data['SMA'] - (data['STD'] * self.num_std)
        data['Signal'] = np.where(data['Close'] < data['Lower'], 1,
                                np.where(data['Close'] > data['Upper'], -1, 0))
        return data
