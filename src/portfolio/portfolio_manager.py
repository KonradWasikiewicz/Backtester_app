from dataclasses import dataclass
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from .risk_manager import RiskManager

@dataclass
class Position:
    """Class representing a trading position"""
    ticker: str
    entry_date: pd.Timestamp
    entry_price: float
    shares: int
    direction: int  # 1 for long, -1 for short
    allocation: float  # percent of portfolio at entry
    stop_loss: float
    take_profit: float

class PortfolioManager:
    """Manages portfolio positions, equity, and trade execution"""
    
    def __init__(self, initial_capital=10000.0, risk_manager=None):
        """Initialize portfolio with starting capital"""
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # Current open positions
        self.closed_trades = []  # Historical closed trades
        self.risk_manager = risk_manager or RiskManager()  # Use provided or default risk manager
        self.logger = logging.getLogger(__name__)
        
    def open_position(self, signal):
        """
        Open a new position based on a signal.
        
        Args:
            signal: Dict with trade details (ticker, date, price, direction, volatility)
        
        Returns:
            Dict with position details or None if position couldn't be opened
        """
        ticker = signal.get('ticker')
        price = signal.get('price')
        date = signal.get('date')
        direction = signal.get('direction', 1)  # Default to long
        volatility = signal.get('volatility', 0.01)  # Default volatility
        
        # Check if we can open a new position
        if not self.risk_manager.can_open_new_position(len(self.positions)):
            self.logger.info(f"Maximum positions limit reached, ignoring signal for {ticker}")
            return None
        
        # Check if we already have this position
        if ticker in self.positions:
            self.logger.info(f"Position for {ticker} already exists, ignoring signal")
            return None
            
        # Calculate position size based on risk parameters
        shares = self.risk_manager.calculate_position_size(
            capital=self.cash,
            price=price,
            volatility=volatility,
            sector=signal.get('sector')  # Optional sector info
        )
        
        # Check if we have enough cash
        cost = shares * price
        if cost > self.cash:
            # Adjust shares to match available cash
            shares = int(self.cash / price)
            cost = shares * price
            
        if shares <= 0:
            self.logger.info(f"Not enough cash to open position for {ticker}")
            return None
            
        # Calculate stop loss and take profit levels
        stop_loss, take_profit = self.risk_manager.calculate_stops(price, direction)
        
        # Create position
        position = {
            'ticker': ticker,
            'entry_date': date,
            'entry_price': price,
            'shares': shares,
            'direction': direction,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'initial_stop': stop_loss  # Save initial stop for trailing stop calculation
        }
        
        # Update cash and add to positions
        self.cash -= cost
        self.positions[ticker] = position
        
        self.logger.debug(f"Opened position for {ticker}: {shares} shares at ${price:.2f}")
        return position
    
    def close_position(self, ticker, price, date):
        """
        Close an existing position.
        
        Args:
            ticker: Ticker symbol to close
            price: Exit price
            date: Exit date
            
        Returns:
            Dict with trade details or None if position doesn't exist
        """
        if ticker not in self.positions:
            return None
            
        position = self.positions[ticker]
        
        # Calculate profit/loss
        entry_price = position['entry_price']
        shares = position['shares']
        direction = position['direction']
        
        # Calculate P&L
        pnl = (price - entry_price) * shares * direction
        
        # Create trade record
        trade = {
            'ticker': ticker,
            'entry_date': position['entry_date'],
            'exit_date': date,
            'entry_price': entry_price,
            'exit_price': price,
            'shares': shares,
            'pnl': pnl,
            'pnl_pct': (price - entry_price) / entry_price * 100 * direction,
            'direction': direction
        }
        
        # Update cash and remove from positions
        self.cash += (shares * price)
        self.closed_trades.append(trade)
        del self.positions[ticker]
        
        self.logger.debug(f"Closed position for {ticker}: {shares} shares at ${price:.2f}, P&L: ${pnl:.2f}")
        return trade
    
    def update_positions(self, ticker_prices, current_date):
        """
        Update positions based on current prices and check stops.
        
        Args:
            ticker_prices: Dict mapping tickers to current prices
            current_date: Current date
            
        Returns:
            List of trades closed during this update
        """
        closed_this_update = []
        
        for ticker, position in list(self.positions.items()):
            if ticker not in ticker_prices:
                continue
                
            current_price = ticker_prices[ticker]
            direction = position['direction']
            
            # Check stop loss
            if (direction > 0 and current_price <= position['stop_loss']) or \
               (direction < 0 and current_price >= position['stop_loss']):
                # Stop loss triggered
                trade = self.close_position(ticker, current_price, current_date)
                if trade:
                    trade['exit_reason'] = 'stop_loss'
                    closed_this_update.append(trade)
                continue
                
            # Check take profit
            if (direction > 0 and current_price >= position['take_profit']) or \
               (direction < 0 and current_price <= position['take_profit']):
                # Take profit triggered
                trade = self.close_position(ticker, current_price, current_date)
                if trade:
                    trade['exit_reason'] = 'take_profit'
                    closed_this_update.append(trade)
                continue
                
            # Update trailing stop if enabled
            position['stop_loss'] = self.risk_manager.update_trailing_stop(
                entry_price=position['entry_price'],
                current_price=current_price,
                current_stop=position['stop_loss'],
                signal=direction
            )
                
        return closed_this_update
    
    def update_portfolio_value(self, current_prices):
        """
        Calculate current portfolio value.
        
        Args:
            current_prices: Dict mapping tickers to current prices
            
        Returns:
            Current portfolio value
        """
        # Cash component
        total_value = self.cash
        
        # Add value of open positions
        for ticker, position in self.positions.items():
            if ticker in current_prices:
                shares = position['shares']
                price = current_prices[ticker]
                total_value += shares * price
                
        return total_value
    
    def get_portfolio_state(self, current_prices=None):
        """
        Get complete portfolio state.
        
        Args:
            current_prices: Optional dict of current prices
            
        Returns:
            Dict with portfolio state
        """
        if current_prices is None:
            current_prices = {}
            
        position_values = []
        for ticker, position in self.positions.items():
            current_price = current_prices.get(ticker, position['entry_price'])
            value = position['shares'] * current_price
            pnl = (current_price - position['entry_price']) * position['shares'] * position['direction']
            pnl_pct = (current_price - position['entry_price']) / position['entry_price'] * 100 * position['direction']
            
            position_values.append({
                'ticker': ticker,
                'shares': position['shares'],
                'entry_price': position['entry_price'],
                'current_price': current_price,
                'value': value,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'stop_loss': position['stop_loss'],
                'take_profit': position['take_profit']
            })
            
        total_value = self.update_portfolio_value(current_prices)
        
        return {
            'cash': self.cash,
            'positions': position_values,
            'total_value': total_value,
            'closed_trades': self.closed_trades
        }
