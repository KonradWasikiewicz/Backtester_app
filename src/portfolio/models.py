from dataclasses import dataclass
from datetime import datetime
import pandas as pd

@dataclass
class Trade:
    trade_id: int
    ticker: str
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_price: float
    exit_price: float
    shares: int
    allocation: float
    strategy: str
    direction: int
    pnl: float
    return_pct: float
    cash_used: float
    commission: float
    holding_period: pd.Timedelta
    exit_reason: str = "signal"

    def to_dict(self) -> dict:
        return {
            'ID': self.trade_id,
            'Ticker': self.ticker,
            'Entry Date': self.entry_date.strftime('%Y-%m-%d %H:%M'),
            'Exit Date': self.exit_date.strftime('%Y-%m-%d %H:%M'),
            'Direction': 'LONG' if self.direction > 0 else 'SHORT',
            'Shares': self.shares,
            'Entry Price': f"${self.entry_price:.2f}",
            'Exit Price': f"${self.exit_price:.2f}",
            'P&L': f"${self.pnl:.2f}",
            'Return %': f"{self.return_pct:.2f}%",
            'Capital Used': f"${self.cash_used:.2f}",
            'Commission': f"${self.commission:.2f}",
            'Duration': str(self.holding_period),
            'Exit Reason': self.exit_reason
        }

    def to_print(self) -> str:
        return (
            f"\nTrade #{self.trade_id} - {self.ticker}\n"
            f"{'=' * 40}\n"
            f"Direction: {'LONG' if self.direction > 0 else 'SHORT'}\n"
            f"Entry: {self.entry_date.strftime('%Y-%m-%d')} @ ${self.entry_price:.2f}\n"
            f"Exit:  {self.exit_date.strftime('%Y-%m-%d')} @ ${self.exit_price:.2f}\n"
            f"Shares: {self.shares:,d}\n"
            f"P&L: ${self.pnl:.2f} ({self.return_pct:+.2f}%)\n"
            f"Capital Used: ${self.cash_used:.2f}\n"
            f"Commission: ${self.commission:.2f}\n"
            f"Duration: {self.holding_period}\n"
            f"Exit Reason: {self.exit_reason}\n"
        )