import pandas as pd
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.core.config import config
from ..strategies.base import BaseStrategy
from ..portfolio.portfolio_manager import PortfolioManager
from ..portfolio.risk_manager import RiskManager

class BacktestEngine:
    """Engine for running backtests on a single ticker"""
    
    def __init__(self, initial_capital=100000.0, strategy=None):
        """Initialize backtest engine with capital and strategy"""
        self.initial_capital = initial_capital
        self.strategy = strategy
        self.logger = logging.getLogger(__name__)
        self.risk_manager = RiskManager()
        self.portfolio_manager = PortfolioManager(initial_capital, self.risk_manager)
        
    def run_backtest(self, ticker, data):
        """Run a backtest for a single ticker with proper risk management"""
        try:
            # Check for required data
            if data is None or data.empty or 'Signal' not in data.columns:
                return None
                
            # Filter data by configured dates
            start_date = pd.to_datetime(config.START_DATE)
            end_date = pd.to_datetime(config.END_DATE)
            
            # Get data before start date for initial signal generation
            pre_period_data = data.loc[data.index < start_date].copy() if len(data.loc[data.index < start_date]) > 0 else None
            trading_period_data = data.loc[(data.index >= start_date) & (data.index <= end_date)].copy()
            
            if len(trading_period_data) == 0:
                return None
                
            # Initialize portfolio tracking
            portfolio_values = []
            position_active = False
            
            # Process signals
            for date, row in trading_period_data.iterrows():
                price = row['Close']
                signal = row['Signal']
                
                # Process signals if there's a change
                if signal != 0:
                    if signal > 0 and not position_active:  # Buy signal
                        # Create signal dict for portfolio manager
                        buy_signal = {
                            'ticker': ticker,
                            'date': date,
                            'price': price,
                            'direction': 1,
                            'volatility': data['Close'].pct_change().rolling(20).std().iloc[-1]
                        }
                        
                        # Open position using portfolio manager
                        position = self.portfolio_manager.open_position(buy_signal)
                        if position:
                            position_active = True
                    
                    elif signal < 0 and position_active:  # Sell signal
                        # Close position
                        trade = self.portfolio_manager.close_position(ticker, price, date)
                        position_active = False
                
                # Track portfolio value
                current_prices = {ticker: price}
                portfolio_value = self.portfolio_manager.update_portfolio_value(current_prices)
                portfolio_values.append({'date': date, 'value': portfolio_value})
            
            # Close any remaining positions at the end
            if position_active:
                last_date = trading_period_data.index[-1]
                last_price = trading_period_data['Close'].iloc[-1]
                self.portfolio_manager.close_position(ticker, last_price, last_date)
            
            # Create portfolio series
            portfolio_series = pd.Series(
                [pv['value'] for pv in portfolio_values],
                index=[pv['date'] for pv in portfolio_values]
            )
            
            return {
                'Portfolio_Value': portfolio_series,
                'trades': self.portfolio_manager.closed_trades
            }
            
        except Exception as e:
            self.logger.error(f"Backtest error in engine for {ticker}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
