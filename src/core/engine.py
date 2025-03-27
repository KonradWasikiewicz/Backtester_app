import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple
from decimal import Decimal, ROUND_DOWN
from ..strategies.base import BaseStrategy
from .data import DataLoader
from ..portfolio.models import Trade

class BacktestEngine:
    def __init__(self, strategy, initial_capital=10000):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.reset()
        
    def reset(self):
        self.cash = self.initial_capital
        self.trades = []
        self.portfolio_value = pd.Series(dtype=float)
        
    def run_backtest(self, data: pd.DataFrame) -> dict:
        try:
            current_position = 0
            portfolio_values = []
            trades = []
            
            position_value = 0
            entry_price = None
            entry_date = None
            
            for idx, row in data.iterrows():
                if idx < pd.Timestamp('2020-01-01', tz='UTC'):
                    continue
                    
                close_price = float(row['Close'])
                signal = float(row['Signal'])
                
                # Entry logic
                if signal != 0 and current_position == 0:
                    shares = int(self.cash / close_price)
                    if shares > 0:
                        current_position = shares if signal > 0 else -shares
                        entry_price = close_price
                        entry_date = idx
                        self.cash -= abs(current_position * close_price)
                
                # Exit logic (opposite signal or strong reversal)
                elif current_position != 0 and (
                    (current_position > 0 and signal < 0) or 
                    (current_position < 0 and signal > 0)
                ):
                    # Record trade
                    pl = (close_price - entry_price) * abs(current_position)
                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': idx,
                        'entry_price': entry_price,
                        'exit_price': close_price,
                        'shares': abs(current_position),
                        'direction': 'LONG' if current_position > 0 else 'SHORT',
                        'pnl': pl,
                        'return': (pl / (entry_price * abs(current_position))) * 100
                    })
                    
                    # Reset position
                    self.cash += current_position * close_price
                    current_position = 0
                    entry_price = None
                    entry_date = None
                
                # Update portfolio value
                position_value = current_position * close_price if current_position != 0 else 0
                portfolio_value = self.cash + position_value
                portfolio_values.append(portfolio_value)
            
            return {
                'Portfolio_Value': pd.Series(portfolio_values, index=data[data.index >= pd.Timestamp('2020-01-01', tz='UTC')].index),
                'trades': trades
            }
            
        except Exception as e:
            print(f"Backtest error in engine: {str(e)}")
            return {'Portfolio_Value': pd.Series(dtype=float), 'trades': []}
