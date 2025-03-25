import pandas as pd
import numpy as np
from typing import Dict
from .base import Strategy

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
