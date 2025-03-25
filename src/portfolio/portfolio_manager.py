from dataclasses import dataclass
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from .risk_manager import RiskManager
from .models import Trade

@dataclass
class Position:
    ticker: str
    entry_date: pd.Timestamp
    entry_price: float
    shares: int
    direction: int  # 1 for long, -1 for short
    allocation: float  # procent portfela w momencie wejścia
    stop_loss: float
    take_profit: float

@dataclass
class PortfolioManager:
    def __init__(self, initial_capital: float, risk_manager: 'RiskManager',
                 max_position_allocation: float = 0.2,
                 max_ticker_allocation: float = 0.3):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, Position] = {}  # ticker -> Position
        self.closed_trades: List[Trade] = []
        self.risk_manager = risk_manager
        self.max_position_allocation = max_position_allocation  # max 20% na pozycję
        self.max_ticker_allocation = max_ticker_allocation     # max 30% na ticker
        
    def get_ticker_exposure(self, ticker: str) -> float:
        """Oblicz obecną ekspozycję na dany ticker"""
        if ticker not in self.positions:
            return 0.0
        position = self.positions[ticker]
        return (position.shares * position.entry_price) / self.current_capital

    def get_total_exposure(self) -> float:
        """Oblicz całkowitą ekspozycję portfela"""
        return sum(self.get_ticker_exposure(ticker) for ticker in self.positions)

    def can_open_position(self, ticker: str, allocation: float) -> bool:
        """Sprawdź czy można otworzyć nową pozycję"""
        current_ticker_exposure = self.get_ticker_exposure(ticker)
        total_exposure = self.get_total_exposure()
        
        return (
            current_ticker_exposure + allocation <= self.max_ticker_allocation and
            total_exposure + allocation <= 1.0
        )

    def calculate_position_size(self, signal: float, close_price: float) -> int:
        """Calculate position size based on signal and available capital"""
        if signal == 0:
            return 0
            
        position_value = self.current_capital * self.position_size
        shares = int(position_value / close_price)  # Convert to int instead of using np.floor
        
        return shares if signal > 0 else -shares

    def open_position(self, signal: Dict) -> Optional[Position]:
        """Otwórz nową pozycję z uwzględnieniem limitów portfelowych"""
        shares = self.calculate_position_size(
            ticker=signal['ticker'],
            price=signal['price'],
            volatility=signal['volatility']
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
        return position

    def close_position(self, ticker: str, exit_price: float, exit_date: pd.Timestamp) -> Optional[Trade]:
        """Zamknij pozycję i zapisz wynik"""
        if ticker not in self.positions:
            return None
            
        position = self.positions[ticker]
        pnl = (exit_price - position.entry_price) * position.shares * position.direction
        return_pct = (exit_price / position.entry_price - 1) * 100 * position.direction
        
        trade = Trade(
            ticker=position.ticker,
            entry_date=position.entry_date,
            exit_date=exit_date,
            entry_price=position.entry_price,
            exit_price=exit_price,
            shares=position.shares,
            allocation=position.allocation,
            pnl=pnl,
            return_pct=return_pct,
            direction=position.direction,
            duration=exit_date - position.entry_date
        )
        
        self.closed_trades.append(trade)
        self.current_capital += pnl
        del self.positions[ticker]
        return trade

    def get_portfolio_stats(self) -> Dict:
        """Get current portfolio statistics"""
        return {
            'current_capital': self.current_capital,
            'open_positions': len(self.positions),
            'total_trades': len(self.closed_trades),
            'total_pnl': sum(trade.pnl for trade in self.closed_trades),
            'win_rate': len([t for t in self.closed_trades if t.pnl > 0]) / len(self.closed_trades) if self.closed_trades else 0,
            'average_trade_duration': pd.Timedelta(sum(t.duration for t in self.closed_trades) / len(self.closed_trades)) if self.closed_trades else pd.Timedelta(0),
            'current_exposure': sum(abs(p.shares * p.entry_price) for p in self.positions.values())
        }

    def calculate_position_value(self, position: dict) -> float:
        """Calculate current position value"""
        if not position:
            return 0.0
        
        # Use float() to ensure we're not treating arrays as callable
        shares = float(position.get('shares', 0))
        price = float(position.get('current_price', 0))
        return shares * price

    def update_portfolio_value(self, current_prices: dict) -> float:
        """Update portfolio value based on current prices"""
        total_value = self.cash
        
        for ticker, position in self.positions.items():
            if ticker in current_prices:
                # Convert to float to avoid numpy array issues
                price = float(current_prices[ticker])
                shares = float(position['shares'])
                total_value += shares * price
        
        return total_value
