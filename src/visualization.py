import matplotlib.pyplot as plt
import seaborn as sns
from typing import List
import pandas as pd

class BacktestVisualizer:
    def __init__(self, figsize=(15, 10)):
        self.figsize = figsize
        plt.style.use('seaborn')

    def plot_strategy_performance(self, data: pd.DataFrame, save_path: str = None):
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=self.figsize)

        # Wykres ceny i sygnałów
        ax1.plot(data.index, data['Close'], label='Close Price')
        ax1.scatter(data[data['Signal'] == 1].index,
                   data[data['Signal'] == 1]['Close'],
                   marker='^', color='g', label='Buy')
        ax1.scatter(data[data['Signal'] == -1].index,
                   data[data['Signal'] == -1]['Close'],
                   marker='v', color='r', label='Sell')
        ax1.set_title('Price and Signals')
        ax1.legend()

        # Wykres wartości portfela
        ax2.plot(data.index, data['Portfolio_Value'])
        ax2.set_title('Portfolio Value')

        # Wykres drawdownu
        portfolio_max = data['Portfolio_Value'].cummax()
        drawdown = (data['Portfolio_Value'] - portfolio_max) / portfolio_max
        ax3.fill_between(data.index, drawdown, 0, color='red', alpha=0.3)
        ax3.set_title('Drawdown')

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path)
        plt.show()

    def plot_trade_analysis(self, trades: List, save_path: str = None):
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=self.figsize)

        # Rozkład zysków/strat
        pnls = [trade.pnl for trade in trades]
        sns.histplot(pnls, ax=ax1)
        ax1.set_title('PnL Distribution')

        # Krzywa kapitału
        cumulative_pnl = pd.Series(pnls).cumsum()
        ax2.plot(cumulative_pnl)
        ax2.set_title('Cumulative PnL')

        # Długość trzymania pozycji
        holding_periods = [(trade.exit_date - trade.entry_date).days for trade in trades]
        sns.histplot(holding_periods, ax=ax3)
        ax3.set_title('Holding Periods')

        # Win ratio w czasie
        wins = pd.Series([1 if trade.pnl > 0 else 0 for trade in trades])
        win_ratio = wins.rolling(20).mean()
        ax4.plot(win_ratio)
        ax4.set_title('Win Ratio (20-trade MA)')

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path)
        plt.show()
