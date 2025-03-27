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
        """Reset engine state"""
        self.cash = self.initial_capital
        self.positions = {}  # {ticker: {'shares': n, 'cost_basis': price, 'entry_date': date}}
        self.trades = []
        
    def run_backtest(self, ticker: str, data: pd.DataFrame) -> dict:
        try:
            trading_data = data.copy()
            portfolio_values = []
            
            # Split initial capital equally among tickers
            ticker_allocation = self.initial_capital / len(self.strategy.tickers)
            available_cash = ticker_allocation
            current_position = 0
            
            # Process each day
            for i in range(len(trading_data)):
                current_day = trading_data.iloc[i]
                current_date = trading_data.index[i]
                
                # Skip processing for lookback period
                if current_date < pd.Timestamp('2020-01-01', tz='UTC'):
                    continue
                
                # Get previous day's signal (only if not in lookback period)
                if i > 0 and trading_data.iloc[i-1].name >= pd.Timestamp('2020-01-01', tz='UTC'):
                    prev_signal = trading_data.iloc[i-1]['Signal']
                else:
                    prev_signal = 0  # No signal at the start of trading period
                
                # Handle entries
                if current_position == 0 and prev_signal == 1:
                    max_shares = int(available_cash / current_day['Open'])
                    if max_shares > 0:
                        current_position = max_shares
                        cost = max_shares * current_day['Open']
                        available_cash -= cost
                        self.positions[ticker] = {
                            'shares': max_shares,
                            'cost_basis': current_day['Open'],
                            'entry_date': current_date
                        }
                
                # Handle exits
                elif current_position != 0 and prev_signal in [-1, 0]:
                    exit_price = current_day['Open']
                    proceeds = current_position * exit_price
                    available_cash += proceeds
                    
                    # Record trade
                    self.trades.append({
                        'entry_date': self.positions[ticker]['entry_date'],
                        'exit_date': current_date,
                        'ticker': ticker,
                        'direction': 'LONG',
                        'shares': current_position,
                        'entry_price': self.positions[ticker]['cost_basis'],
                        'exit_price': exit_price,
                        'pnl': proceeds - (current_position * self.positions[ticker]['cost_basis'])
                    })
                    
                    current_position = 0
                    if ticker in self.positions:
                        del self.positions[ticker]
                
                # Calculate daily value for this ticker
                position_value = current_position * current_day['Close']
                daily_value = position_value + available_cash
                portfolio_values.append(daily_value)
            
            # Create series only for trading period
            trading_period = trading_data[trading_data.index >= pd.Timestamp('2020-01-01', tz='UTC')]
            portfolio_series = pd.Series(portfolio_values, index=trading_period.index)
            
            return {
                'Portfolio_Value': portfolio_series,
                'trades': [t for t in self.trades if t['ticker'] == ticker]
            }
            
        except Exception as e:
            print(f"Backtest error in engine: {str(e)}")
            return {'Portfolio_Value': pd.Series(), 'trades': []}
    
    def get_statistics(self):
        """Calculate trading statistics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'win_rate': 0.0,
                'avg_trade_return': 0.0
            }
        
        winning_trades = len([t for t in self.trades if t['pnl'] > 0])
        total_trades = len(self.trades)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0.0,
            'avg_trade_return': sum(t['pnl'] for t in self.trades) / total_trades if total_trades > 0 else 0.0
        }
