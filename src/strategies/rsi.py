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
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Initialize signals
            df['Signal'] = 0
            
            # Generate signals only for trading period
            trade_mask = df.index >= pd.Timestamp('2020-01-01', tz='UTC')
            for i in range(1, len(df)):
                if not trade_mask.iloc[i]:
                    continue
                    
                # Buy signal: RSI crosses below 30
                if df['RSI'].iloc[i-1] >= 30 and df['RSI'].iloc[i] < 30:
                    df.iloc[i, df.columns.get_loc('Signal')] = 1
                    
                # Sell signal: RSI crosses above 70
                elif df['RSI'].iloc[i-1] <= 70 and df['RSI'].iloc[i] > 70:
                    df.iloc[i, df.columns.get_loc('Signal')] = -1
            
            signals[ticker] = df
            
        return signals
