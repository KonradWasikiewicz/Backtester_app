from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from typing import Optional, Dict, Any

@dataclass
class Trade:
    """Class representing a completed trade"""
    
    ticker: str
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_price: float
    exit_price: float
    shares: int
    direction: str
    pnl: float
    
    # Optional fields with defaults
    trade_id: int = 0
    allocation: float = 0.0
    strategy: str = ""
    return_pct: float = 0.0
    cash_used: float = 0.0
    commission: float = 0.0
    holding_period: Optional[pd.Timedelta] = None
    exit_reason: str = "signal"

    def __post_init__(self):
        """Calculate derived values if not provided"""
        if self.holding_period is None:
            self.holding_period = self.exit_date - self.entry_date
            
        if self.cash_used == 0.0:
            self.cash_used = self.entry_price * self.shares
            
        if self.return_pct == 0.0 and self.cash_used != 0:
            self.return_pct = (self.pnl / self.cash_used) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for display"""
        return {
            'ID': self.trade_id,
            'Ticker': self.ticker,
            'Entry Date': self.entry_date.strftime('%Y-%m-%d'),
            'Exit Date': self.exit_date.strftime('%Y-%m-%d'),
            'Direction': self.direction,
            'Shares': self.shares,
            'Entry Price': f"${self.entry_price:.2f}",
            'Exit Price': f"${self.exit_price:.2f}",
            'P&L': f"${self.pnl:.2f}",
            'Return %': f"{self.return_pct:.2f}%",
            'Capital Used': f"${self.cash_used:.2f}",
            'Commission': f"${self.commission:.2f}",
            'Duration': str(self.holding_period).split(' days')[0] + " days",
            'Exit Reason': self.exit_reason
        }

    def to_print(self) -> str:
        """Create a formatted string representation"""
        return (
            f"\nTrade #{self.trade_id} - {self.ticker}\n"
            f"{'=' * 40}\n"
            f"Direction: {self.direction}\n"
            f"Entry: {self.entry_date.strftime('%Y-%m-%d')} @ ${self.entry_price:.2f}\n"
            f"Exit:  {self.exit_date.strftime('%Y-%m-%d')} @ ${self.exit_price:.2f}\n"
            f"Shares: {self.shares:,d}\n"
            f"P&L: ${self.pnl:.2f} ({self.return_pct:+.2f}%)\n"
            f"Capital Used: ${self.cash_used:.2f}\n"
            f"Commission: ${self.commission:.2f}\n"
            f"Duration: {self.holding_period}\n"
            f"Exit Reason: {self.exit_reason}\n"
        )