from dataclasses import dataclass
from datetime import datetime
import pandas as pd

@dataclass
class Trade:
    ticker: str
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_price: float
    exit_price: float
    shares: int
    allocation: float
    pnl: float
    return_pct: float
    direction: int
    duration: pd.Timedelta
    exit_reason: str = "signal"

    def to_dict(self) -> dict:
        return {
            'Ticker': self.ticker,
            'Entry Date': self.entry_date,
            'Exit Date': self.exit_date,
            'Entry Price': f"${self.entry_price:.2f}",
            'Exit Price': f"${self.exit_price:.2f}",
            'Shares': self.shares,
            'P&L': f"${self.pnl:.2f}",
            'Return %': f"{self.return_pct:.2f}%",
            'Direction': "LONG" if self.direction > 0 else "SHORT",
            'Duration': str(self.duration),
            'Exit Reason': self.exit_reason
        }