from dataclasses import dataclass
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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
    """Manages portfolio positions and trades"""
    
    def __init__(self, initial_capital: float, risk_manager: Optional[RiskManager] = None,
                 max_position_allocation: float = 0.2,
                 max_ticker_allocation: float = 0.3):
        """Initialize portfolio manager
        
        Args:
            initial_capital: Starting capital
            risk_manager: Risk manager instance
            max_position_allocation: Maximum allocation per position
            max_ticker_allocation: Maximum allocation per ticker
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, Position] = {}  # ticker -> Position
        self.closed_trades = []
        self.risk_manager = risk_manager or RiskManager()
        self.max_position_allocation = max_position_allocation  # max 20% per position
        self.max_ticker_allocation = max_ticker_allocation     # max 30% per ticker
        self.cash = initial_capital
        self.position_size = 0.1  # Default position size (10% of portfolio)
        
    def get_ticker_exposure(self, ticker: str) -> float:
        """Calculate current exposure to a given ticker
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            Current exposure as percentage of portfolio
        """
        if ticker not in self.positions:
            return 0.0
        position = self.positions[ticker]
        return (position.shares * position.entry_price) / self.current_capital

    def get_total_exposure(self) -> float:
        """Calculate total portfolio exposure
        
        Returns:
            Total exposure as percentage of portfolio
        """
        return sum(self.get_ticker_exposure(ticker) for ticker in self.positions)

    def can_open_position(self, ticker: str, allocation: float) -> bool:
        """Check if a new position can be opened
        
        Args:
            ticker: Ticker symbol
            allocation: Proposed allocation
            
        Returns:
            True if position can be opened, False otherwise
        """
        current_ticker_exposure = self.get_ticker_exposure(ticker)
        total_exposure = self.get_total_exposure()
        
        return (
            current_ticker_exposure + allocation <= self.max_ticker_allocation and
            total_exposure + allocation <= 1.0
        )

    def calculate_position_size(self, ticker: str, price: float, volatility: float = 0.01) -> int:
        """Calculate position size based on price and risk parameters
        
        Args:
            ticker: Ticker symbol
            price: Current price
            volatility: Price volatility measure
            
        Returns:
            Number of shares to purchase
        """
        position_value = self.current_capital * self.position_size
        shares = int(position_value / price)
        
        return shares

    def open_position(self, signal: Dict) -> Optional[Position]:
        """Open a new position with portfolio limits
        
        Args:
            signal: Signal dictionary with trade information
            
        Returns:
            Position object if opened, None otherwise
        """
        shares = self.calculate_position_size(
            ticker=signal['ticker'],
            price=signal['price'],
            volatility=signal.get('volatility', 0.01)
        )
        
        if not shares:
            return None
            
        allocation = (shares * signal['price']) / self.current_capital
        stop_loss, take_profit = self.risk_manager.calculate_stops(
            entry_price=signal['price'],
            signal=signal['direction']
        )
        
        position = Position(
            ticker=signal['ticker'],
            entry_date=signal['date'],
            entry_price=signal['price'],
            shares=shares,
            direction=signal['direction'],
            allocation=allocation,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.positions[signal['ticker']] = position
        self.cash -= shares * signal['price']
        return position

    def close_position(self, ticker: str, exit_price: float, exit_date: pd.Timestamp) -> Optional[dict]:
        """Close a position and record the trade
        
        Args:
            ticker: Ticker symbol
            exit_price: Exit price
            exit_date: Exit date
            
        Returns:
            Trade dictionary if closed, None otherwise
        """
        if ticker not in self.positions:
            return None
            
        position = self.positions[ticker]
        pnl = (exit_price - position.entry_price) * position.shares * position.direction
        return_pct = (exit_price / position.entry_price - 1) * 100 * position.direction
        
        trade = {
            'ticker': position.ticker,
            'entry_date': position.entry_date,
            'exit_date': exit_date,
            'entry_price': position.entry_price,
            'exit_price': exit_price,
            'shares': position.shares,
            'allocation': position.allocation,
            'pnl': pnl,
            'return_pct': return_pct,
            'direction': position.direction,
            'duration': exit_date - position.entry_date
        }
        
        self.closed_trades.append(trade)
        self.current_capital += pnl
        self.cash += exit_price * position.shares
        del self.positions[ticker]
        return trade

    def update_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Update portfolio value based on current prices
        
        Args:
            current_prices: Dictionary mapping tickers to current prices
            
        Returns:
            Current portfolio value
        """
        positions_value = sum(
            position.shares * current_prices.get(ticker, position.entry_price) 
            for ticker, position in self.positions.items()
        )
        
        return self.cash + positions_value
