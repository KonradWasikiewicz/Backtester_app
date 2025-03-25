from dataclasses import dataclass
from typing import List, Dict
import pandas as pd
from .risk_manager import RiskManager

@dataclass
class Position:
    ticker: str
    entry_date: pd.Timestamp
    entry_price: float
    size: float
    direction: int  # 1 for long, -1 for short
    stop_loss: float
    take_profit: float

@dataclass
class Trade:
    ticker: str
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    return_pct: float
    direction: int
    duration: pd.Timedelta

class PortfolioManager:
    def __init__(self, initial_capital: float, risk_manager: RiskManager):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: List[Position] = []
        self.closed_trades: List[Trade] = []
        self.risk_manager = risk_manager
        
    def open_position(self, signal: Dict) -> Position:
        """Open new position with risk management"""
        position_size = self.risk_manager.calculate_position_size(
            capital=self.current_capital,
            price=signal['price'],
            volatility=signal['volatility']
        )
        
        stop_loss, take_profit = self.risk_manager.calculate_stops(
            entry_price=signal['price'],
            signal=signal['direction']
        )
        
        position = Position(
            ticker=signal['ticker'],
            entry_date=signal['date'],
            entry_price=signal['price'],
            size=position_size,
            direction=signal['direction'],
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.positions.append(position)
        return position

    def close_position(self, position: Position, exit_price: float, exit_date: pd.Timestamp):
        """Close position and record trade"""
        pnl = (exit_price - position.entry_price) * position.size * position.direction
        return_pct = (exit_price / position.entry_price - 1) * 100 * position.direction
        
        trade = Trade(
            ticker=position.ticker,
            entry_date=position.entry_date,
            exit_date=exit_date,
            entry_price=position.entry_price,
            exit_price=exit_price,
            size=position.size,
            pnl=pnl,
            return_pct=return_pct,
            direction=position.direction,
            duration=exit_date - position.entry_date
        )
        
        self.closed_trades.append(trade)
        self.current_capital += pnl
        self.positions.remove(position)
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
            'current_exposure': sum(abs(p.size * p.entry_price) for p in self.positions)
        }
