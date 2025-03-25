import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict
from decimal import Decimal, ROUND_DOWN
from ..strategies.base import BaseStrategy
from .data import DataLoader

@dataclass
class Trade:
    """Unified trade record format"""
    trade_id: int          # Unikalny identyfikator transakcji
    ticker: str           # Symbol instrumentu
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_price: float
    exit_price: float
    shares: int
    strategy: str         # Nazwa strategii
    direction: int        # 1 dla long, -1 dla short
    pnl: float           # Zysk/strata w walucie
    return_pct: float    # Zwrot procentowy
    cash_used: float     # Wykorzystany kapitał
    commission: float    # Łączna prowizja
    holding_period: pd.Timedelta  # Czas trzymania pozycji
    exit_reason: str     # Powód wyjścia (np. "signal", "stop_loss", "take_profit")

    def to_dict(self) -> dict:
        """Convert trade to dictionary for display"""
        return {
            'ID': self.trade_id,
            'Ticker': self.ticker,
            'Entry Date': self.entry_date.strftime('%Y-%m-%d %H:%M'),
            'Exit Date': self.exit_date.strftime('%Y-%m-%d %H:%M'),
            'Direction': 'LONG' if self.direction == 1 else 'SHORT',
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
        """Format trade for console output"""
        return (
            f"\nTrade #{self.trade_id} - {self.ticker}\n"
            f"{'=' * 40}\n"
            f"Direction: {'LONG' if self.direction == 1 else 'SHORT'}\n"
            f"Entry: {self.entry_date.strftime('%Y-%m-%d')} @ ${self.entry_price:.2f}\n"
            f"Exit:  {self.exit_date.strftime('%Y-%m-%d')} @ ${self.exit_price:.2f}\n"
            f"Shares: {self.shares:,d}\n"
            f"P&L: ${self.pnl:.2f} ({self.return_pct:+.2f}%)\n"
            f"Capital Used: ${self.cash_used:.2f}\n"
            f"Commission: ${self.commission:.2f}\n"
            f"Duration: {self.holding_period}\n"
            f"Exit Reason: {self.exit_reason}\n"
        )

class BacktestEngine:
    def __init__(self, strategy: BaseStrategy, initial_capital=100000):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.data_loader = DataLoader()
        self.positions = {}
        self.cash = initial_capital
        self.portfolio_value = initial_capital
        
    def run(self, ticker):
        # Load data
        data = self.data_loader.load_data(ticker)
        benchmark = self.data_loader.load_benchmark()
        
        # Generate signals
        signals = self.strategy.generate_signals(data)
        
        # Calculate returns
        portfolio_returns = []
        current_position = 0
        
        for i in range(len(data)):
            if i > 0:
                if signals[i] == 1 and current_position <= 0:  # Buy signal
                    current_position = 1
                elif signals[i] == -1 and current_position >= 0:  # Sell signal
                    current_position = -1
                    
            daily_return = current_position * data['Close'].pct_change()[i]
            portfolio_returns.append(daily_return)
            
        portfolio_returns = pd.Series(portfolio_returns, index=data.index)
        
        return {
            'returns': portfolio_returns,
            'benchmark_returns': benchmark['Close'].pct_change(),
            'signals': signals
        }

    def calculate_shares(self, price: float) -> int:
        """Calculate number of shares based on position size and available cash"""
        target_position_value = self.current_capital * self.position_size_pct
        max_shares = int(min(
            target_position_value / price,
            self.available_cash / (price * (1 + self.commission + self.slippage))
        ))
        return max_shares

    def run_backtest(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Run backtest on multiple instruments"""
        # Initialize combined results
        combined_results = pd.DataFrame(index=next(iter(data.values())).index)
        combined_results['Portfolio_Value'] = self.current_capital

        for date in combined_results.index:
            daily_pnl = 0
            
            # Check signals for each instrument
            for ticker, df in data.items():
                current_row = df.loc[date]
                
                # Check for exit signals on existing positions
                if ticker in self.positions:
                    if current_row['Signal'] != self.positions[ticker]['signal']:
                        exit_price = current_row['Close'] * (1 - self.slippage * np.sign(current_row['Signal']))
                        pnl = self._close_position(ticker, exit_price, date)
                        daily_pnl += pnl
                        print(f"\nZamknięcie pozycji {ticker}:")
                        print(f"Data wyjścia: {date}")
                        print(f"Cena wyjścia: ${exit_price:.2f}")
                        print(f"P&L: ${pnl:.2f}")
                
                # Check for entry signals
                if ticker not in self.positions and current_row['Signal'] != 0:
                    entry_shares = self.calculate_shares(current_row['Close'])
                    
                    if entry_shares > 0:
                        entry_price = current_row['Close'] * (1 + self.slippage * np.sign(current_row['Signal']))
                        total_cost = entry_shares * entry_price * (1 + self.commission)
                        
                        if total_cost <= self.available_cash:
                            self._open_position(ticker, entry_price, entry_shares, current_row['Signal'], date)
                            self.available_cash -= total_cost
                            print(f"\nNowa pozycja {ticker}:")
                            print(f"Data wejścia: {date}")
                            print(f"Cena wejścia: ${entry_price:.2f}")
                            print(f"Liczba akcji: {entry_shares}")
                            print(f"Kierunek: {'LONG' if current_row['Signal'] > 0 else 'SHORT'}")
                            print(f"Pozostały cash: ${self.available_cash:.2f}")

            # Update portfolio value
            self.current_capital = self.available_cash + sum(
                pos['shares'] * data[ticker].loc[date, 'Close']
                for ticker, pos in self.positions.items()
            )
            combined_results.loc[date, 'Portfolio_Value'] = self.current_capital

        self.portfolio_values = combined_results['Portfolio_Value']
        return combined_results

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
