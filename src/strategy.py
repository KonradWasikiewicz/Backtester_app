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
        """
        Generuje sygnały kupna (-1 sprzedaż, 1 kupno) na podstawie średnich kroczących.
        """
        data = data.copy()
        data['SMA_short'] = data['Close'].rolling(window=self.short_window).mean()
        data['SMA_long'] = data['Close'].rolling(window=self.long_window).mean()
        data['Signal'] = 0
        data.loc[data['SMA_short'] > data['SMA_long'], 'Signal'] = 1
        data.loc[data['SMA_short'] <= data['SMA_long'], 'Signal'] = -1
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

        data['Signal'] = 0
        data.loc[data['RSI'] < self.oversold, 'Signal'] = 1
        data.loc[data['RSI'] > self.overbought, 'Signal'] = -1
        return data

class BollingerBandsStrategy(Strategy):
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        self.period = period
        self.std_dev = std_dev

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data = data.copy()
        data['SMA'] = data['Close'].rolling(window=self.period).mean()
        data['STD'] = data['Close'].rolling(window=self.period).std()
        data['Upper'] = data['SMA'] + (self.std_dev * data['STD'])
        data['Lower'] = data['SMA'] - (self.std_dev * data['STD'])

        data['Signal'] = 0
        data.loc[data['Close'] < data['Lower'], 'Signal'] = 1
        data.loc[data['Close'] > data['Upper'], 'Signal'] = -1
        return data
