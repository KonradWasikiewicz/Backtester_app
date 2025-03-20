import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Trade:
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_price: float
    exit_price: float
    position_size: float
    pnl: float
    signal: int

class BacktestEngine:
    def __init__(self, initial_capital: float = 100000, commission: float = 0.001,
                 slippage: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.trades: List[Trade] = []
        self.portfolio_values = None

    def run_backtest(self, data: pd.DataFrame) -> pd.DataFrame:
        data = data.copy()
        data['Return'] = data['Close'].pct_change()
        data['Position'] = data['Signal'].shift(1)
        data['Trade'] = data['Position'].diff().fillna(0)

        # Symulacja poślizgu cenowego
        data['Entry_Price'] = data['Close'] * (1 + self.slippage * np.sign(data['Trade']))

        # Obliczenie zwrotów z uwzględnieniem kosztów
        data['Strategy_Return'] = data['Return'] * data['Position']
        data['Transaction_Costs'] = abs(data['Trade']) * (self.commission + self.slippage)
        data['Net_Return'] = data['Strategy_Return'] - data['Transaction_Costs']

        # Wartość portfela
        data['Portfolio_Value'] = self.initial_capital * (1 + data['Net_Return']).cumprod()
        self.portfolio_values = data['Portfolio_Value']  # Store portfolio values

        # Rejestracja transakcji
        self._record_trades(data)

        return data

    def _record_trades(self, data: pd.DataFrame) -> None:
        """Rejestruje wszystkie transakcje"""
        position = 0
        entry_price = None
        entry_date = None

        for idx, row in data.iterrows():
            if row['Trade'] != 0:
                if position == 0:  # Wejście w pozycję
                    position = row['Position']
                    entry_price = row['Entry_Price']
                    entry_date = idx
                else:  # Zamknięcie pozycji
                    pnl = position * (row['Entry_Price'] - entry_price)
                    self.trades.append(Trade(
                        entry_date=entry_date,
                        exit_date=idx,
                        entry_price=entry_price,
                        exit_price=row['Entry_Price'],
                        position_size=abs(position),
                        pnl=pnl,
                        signal=position
                    ))
                    position = 0

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

        return {
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'win_rate': len(winning_trades) / len(pnls),
            'avg_profit': np.mean(pnls),
            'sharpe_ratio': sharpe_ratio,
            'profit_factor': abs(sum(winning_trades) / sum(pnl for pnl in pnls if pnl < 0))
                           if any(pnl < 0 for pnl in pnls) else float('inf'),
            'max_drawdown': max_drawdown
        }
