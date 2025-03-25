from dataclasses import dataclass
from typing import List, Dict
import pandas as pd
import numpy as np

@dataclass
class Trade:
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_price: float
    exit_price: float
    position_size: float
    pnl: float
    signal: int

class TradeAnalyzer:
    def __init__(self):
        self.trades: List[Trade] = []
        
    def analyze_trades(self, trades: List[Trade]) -> Dict:
        """Calculate trade statistics"""
        if not trades:
            return {}
            
        pnls = [trade.pnl for trade in trades]
        winning_trades = [pnl for pnl in pnls if pnl > 0]
        
        stats = {
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'win_rate': len(winning_trades) / len(trades) if trades else 0,
            'avg_profit': np.mean(pnls) if pnls else 0,
            'profit_factor': abs(sum(winning_trades) / sum(pnl for pnl in pnls if pnl < 0))
                           if any(pnl < 0 for pnl in pnls) else float('inf')
        }
        
        # Add additional metrics
        if trades:
            durations = [(t.exit_date - t.entry_date).days for t in trades]
            stats.update({
                'avg_duration': np.mean(durations),
                'max_duration': max(durations),
                'min_duration': min(durations)
            })
            
        return stats
