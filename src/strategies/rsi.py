import pandas as pd
import numpy as np
from typing import Dict
from .base import BaseStrategy

class RSIStrategy(BaseStrategy):
    def __init__(self, period=14, overbought=70, oversold=30):
        super().__init__()
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        
    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        delta = prices.diff()
        gain = delta.copy()
        loss = delta.copy()
        
        gain[gain < 0] = 0
        loss[loss > 0] = 0
        loss = abs(loss)
        
        avg_gain = gain.rolling(window=self.period, min_periods=1).mean()
        avg_loss = loss.rolling(window=self.period, min_periods=1).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
        
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        super().generate_signals(data)
        signals = {}
        
        for ticker, df in data.items():
            df = df.copy()
            close_prices = df['Close'].astype(float)
            
            # Calculate RSI using the entire dataset
            df['RSI'] = self.calculate_rsi(close_prices)
            
            # Generate signals only for trading period
            df['Signal'] = 0
            trading_mask = df.index >= pd.Timestamp('2020-01-01', tz='UTC')
            
            # Long signal when RSI crosses below oversold level
            long_signal = (df['RSI'] < self.oversold) & trading_mask
            # Short signal when RSI crosses above overbought level
            short_signal = (df['RSI'] > self.overbought) & trading_mask
            
            df.loc[long_signal, 'Signal'] = 1
            df.loc[short_signal, 'Signal'] = -1
            
            signals[ticker] = df
            
        return signals
