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
        self.tickers = list(data.keys())
        signals = {}
        
        for ticker, df in data.items():
            df = df.copy()
            close_prices = df['Close'].astype(float)
            
            # Calculate RSI
            delta = close_prices.diff()
            gain = delta.where(delta > 0, 0).rolling(window=self.period).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=self.period).mean()
            
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Generate signals
            df['Signal'] = pd.Series(0, index=df.index)
            df.loc[df['RSI'] < self.oversold, 'Signal'] = 1
            df.loc[df['RSI'] > self.overbought, 'Signal'] = -1
            
            # Only keep signals for trading period
            df.loc[df.index < pd.Timestamp('2020-01-01', tz='UTC'), 'Signal'] = 0
            
            signals[ticker] = df
            
        return signals
