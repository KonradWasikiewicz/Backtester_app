import pandas as pd
from typing import List, Dict
from src.portfolio.portfolio_manager import Trade

class TradeAnalyzer:
    @staticmethod
    def analyze_trades(trades: List[Trade]) -> Dict:
        if not trades:
            return {}
            
        df = pd.DataFrame([vars(t) for t in trades])
        
        # Performance metrics
        total_pnl = df['pnl'].sum()
        win_rate = (df['pnl'] > 0).mean()
        profit_factor = abs(df[df['pnl'] > 0]['pnl'].sum() / df[df['pnl'] < 0]['pnl'].sum()) if (df['pnl'] < 0).any() else float('inf')
        
        # Trade statistics
        avg_winner = df[df['pnl'] > 0]['pnl'].mean() if (df['pnl'] > 0).any() else 0
        avg_loser = df[df['pnl'] < 0]['pnl'].mean() if (df['pnl'] < 0).any() else 0
        largest_winner = df['pnl'].max()
        largest_loser = df['pnl'].min()
        
        # Time analysis
        avg_duration = df['duration'].mean()
        
        return {
            'total_trades': len(trades),
            'winning_trades': (df['pnl'] > 0).sum(),
            'losing_trades': (df['pnl'] < 0).sum(),
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_winner': avg_winner,
            'avg_loser': avg_loser,
            'largest_winner': largest_winner,
            'largest_loser': largest_loser,
            'avg_trade_duration': avg_duration,
            'avg_return_pct': df['return_pct'].mean()
        }
