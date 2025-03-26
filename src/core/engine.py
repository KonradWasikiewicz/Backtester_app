import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple
from decimal import Decimal, ROUND_DOWN
from ..strategies.base import BaseStrategy
from .data import DataLoader
from ..portfolio.models import Trade

class BacktestEngine:
    def __init__(self, strategy: BaseStrategy, initial_capital=100000):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.available_cash = initial_capital
        self.current_capital = initial_capital
        self.positions = {}
        self.trades = []
        self.portfolio_values = None
        self.commission = 0.001
        self.slippage = 0.001
        self.position_size_pct = 0.1
        self.cash = initial_capital  # Add cash attribute
        
    def run(self, strategy_type: str) -> Tuple[Dict, pd.DataFrame, Dict]:
        """Run backtest with specified strategy"""
        try:
            data_dict = self.load_data()
            
            # Ensure all dataframes have same date range
            min_date = max(df.index.min() for df in data_dict.values())
            max_date = min(df.index.max() for df in data_dict.values())
            
            for ticker in data_dict:
                mask = (data_dict[ticker].index >= min_date) & (data_dict[ticker].index <= max_date)
                data_dict[ticker] = data_dict[ticker][mask]
            
            # Generate signals
            signals = self.strategy.generate_signals(data_dict)
            
            # Rest of the code...
        except Exception as e:
            print(f"Error running backtest: {e}")
            return {}, pd.DataFrame(), {}

    def calculate_shares(self, price: float) -> int:
        """Calculate number of shares based on position size and available cash"""
        target_position_value = self.current_capital * self.position_size_pct
        max_shares = int(min(
            target_position_value / price,
            self.available_cash / (price * (1 + self.commission + self.slippage))
        ))
        return max_shares

    def run_backtest(self, data: pd.DataFrame) -> dict:
        """Run backtest for a single instrument"""
        try:
            results = {
                'Portfolio_Value': pd.Series(dtype=float),  # Initialize as Series
                'trades': []
            }
            
            self.cash = self.initial_capital  # Reset cash at start
            portfolio_values = []
            current_position = 0
            portfolio_value = self.initial_capital
            
            for idx, row in data.iterrows():
                # Update portfolio value
                close_price = float(row['Close'])
                position_value = current_position * close_price
                portfolio_value = self.cash + position_value
                portfolio_values.append(portfolio_value)
                
                # Update position based on signal
                signal = float(row['Signal'])
                if signal != 0 and current_position == 0:
                    # Calculate new position size
                    position_size = int(self.cash * 0.95 / close_price)
                    current_position = position_size if signal > 0 else -position_size
                    self.cash -= abs(current_position * close_price)
            
            results['Portfolio_Value'] = pd.Series(portfolio_values, index=data.index)
            return results
            
        except Exception as e:
            print(f"Backtest error in engine: {str(e)}")
            return {'Portfolio_Value': pd.Series(dtype=float), 'trades': []}

    def _open_position(self, ticker: str, price: float, shares: int, signal: int, date: pd.Timestamp) -> None:
        self.positions[ticker] = {
            'entry_date': date,
            'entry_price': price,
            'shares': shares,
            'signal': signal
        }

    def _close_position(self, ticker: str, exit_price: float, exit_date: pd.Timestamp, exit_reason: str = "signal") -> float:
        position = self.positions[ticker]
        pnl = (exit_price - position['entry_price']) * position['shares'] * position['signal']
        commission = (position['entry_price'] + exit_price) * position['shares'] * self.commission
        
        trade = Trade(
            trade_id=len(self.trades) + 1,
            ticker=ticker,
            entry_date=position['entry_date'],
            exit_date=exit_date,
            entry_price=position['entry_price'],
            exit_price=exit_price,
            shares=position['shares'],
            strategy=position.get('strategy', 'unknown'),
            direction=position['signal'],
            pnl=pnl,
            return_pct=((exit_price/position['entry_price'] - 1) * 100 * position['signal']),
            cash_used=position['entry_price'] * position['shares'],
            commission=commission,
            holding_period=exit_date - position['entry_date'],
            exit_reason=exit_reason
        )
        
        print(trade.to_print())  # Print detailed trade info to console
        self.trades.append(trade)
        
        self.available_cash += (exit_price * position['shares']) - commission
        del self.positions[ticker]
        return pnl

    def get_statistics(self) -> Dict:
        """Zwraca podstawowe statystyki backtesta"""
        if not self.trades:
            return {}

        pnls = [trade.pnl for trade in self.trades]
        winning_trades = [pnl for pnl in pnls if pnl > 0]
        returns = pd.Series(pnls)

        # Obliczanie Sharpe Ratio (zakładając 252 dni handlowe w roku)
        excess_returns = returns - 0.02/252  # 2% stopa wolna od ryzyka
        sharpe_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std() if len(returns) > 1 else 0

        # Obliczanie max drawdown z zapisanych wartości portfela
        if self.portfolio_values is not None:
            max_drawdown = ((self.portfolio_values - self.portfolio_values.cummax()) /
                          self.portfolio_values.cummax()).min()
        else:
            max_drawdown = 0

        # Obliczanie średniego rocznego turnover'u portfela
        if self.trades:
            total_trading_value = sum(abs(trade.entry_price * trade.shares) +
                                    abs(trade.exit_price * trade.shares)
                                    for trade in self.trades)
            trading_days = (self.trades[-1].exit_date - self.trades[0].entry_date).days
            years = trading_days / 365
            avg_portfolio_value = self.portfolio_values.mean() if self.portfolio_values is not None else self.initial_capital
            turnover = (total_trading_value / (2 * avg_portfolio_value)) / years if years > 0 else 0
        else:
            turnover = 0

        return {
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'win_rate': len(winning_trades) / len(pnls),
            'avg_profit': np.mean(pnls),
            'sharpe_ratio': sharpe_ratio,
            'profit_factor': abs(sum(winning_trades) / sum(pnl for pnl in pnls if pnl < 0))
                           if any(pnl < 0 for pnl in pnls) else float('inf'),
            'max_drawdown': max_drawdown,
            'annual_turnover': turnover
        }
