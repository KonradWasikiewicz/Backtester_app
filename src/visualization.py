import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict
import pandas as pd
from matplotlib.ticker import FuncFormatter, AutoMinorLocator
from matplotlib.dates import AutoDateLocator, DateFormatter
import yfinance as yf

class BacktestVisualizer:
    def __init__(self, figsize=(16, 10)):
        self.figsize = figsize
        plt.style.use('seaborn-darkgrid')

    def plot_strategy_performance(self, data: pd.DataFrame, strategy_name: str,
                                strategy_params: Dict, stats: Dict, save_path: str = None):
        # Utworzenie figure z odpowiednimi proporcjami
        fig = plt.figure(figsize=self.figsize)
        gs = fig.add_gridspec(3, 2, width_ratios=[3.5, 1], height_ratios=[1, 1, 1],
                            hspace=0.3, wspace=0.3)

        # Wykresy
        self._setup_price_plot(fig.add_subplot(gs[0, 0]), data)
        self._setup_portfolio_plot(fig.add_subplot(gs[1, 0]), data)
        self._setup_drawdown_plot(fig.add_subplot(gs[2, 0]), data)

        # Panel informacyjny
        self._setup_info_panel(fig.add_subplot(gs[:, 1]), strategy_name,
                             strategy_params, stats)

        # Tytuł główny
        fig.suptitle(f"Backtest {strategy_name} - {strategy_params.get('Symbol', '')}",
                    fontsize=14, y=0.95)

        # Zapis i wyświetlenie
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, bbox_inches='tight', dpi=300)
        plt.show()

    def _setup_price_plot(self, ax, data):
        # Wykres ceny i sygnałów z ulepszoną legendą i formatowaniem
        ax.plot(data.index, data['Close'], label='Close Price')
        ax.scatter(data[data['Signal'] == 1].index,
                   data[data['Signal'] == 1]['Close'],
                   marker='^', color='g', label='Buy')
        ax.scatter(data[data['Signal'] == -1].index,
                   data[data['Signal'] == -1]['Close'],
                   marker='v', color='r', label='Sell')
        ax.set_title('Price and Signals')
        ax.legend()

    def _setup_portfolio_plot(self, ax, data):
        try:
            # Load S&P500 data from the CSV instead of fetching it
            sp500_data = pd.read_csv('data/historical_prices.csv')
            sp500_data = sp500_data[sp500_data['Ticker'] == '^GSPC']
            sp500_data['Date'] = pd.to_datetime(sp500_data['Date'])
            sp500_data.set_index('Date', inplace=True)

            # Align dates with portfolio data
            sp500_data = sp500_data.loc[data.index[0]:data.index[-1]]

            if not sp500_data.empty:
                # Calculate S&P500 returns
                sp500_returns = sp500_data['Close'].pct_change()
                sp500_cum_returns = (1 + sp500_returns).cumprod()
                sp500_normalized = sp500_cum_returns * data['Portfolio_Value'].iloc[0]

                # Plot both portfolio and S&P500
                ax.plot(data.index, data['Portfolio_Value'], label='Portfolio')
                ax.plot(data.index, sp500_normalized, label='S&P500', alpha=0.7, linestyle='--')
            else:
                # If no S&P500 data, just plot portfolio
                ax.plot(data.index, data['Portfolio_Value'], label='Portfolio')
        except Exception as e:
            # Fallback to just portfolio plot if there's any error
            ax.plot(data.index, data['Portfolio_Value'], label='Portfolio')

        ax.set_title('Portfolio Value ($)')
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax.legend()

    def _setup_drawdown_plot(self, ax, data):
        # Wykres drawdownu z ulepszoną osią Y
        portfolio_max = data['Portfolio_Value'].cummax()
        drawdown = (data['Portfolio_Value'] - portfolio_max) / portfolio_max
        ax.fill_between(data.index, drawdown, 0, color='red', alpha=0.3)
        ax.set_title('Drawdown (%)')
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x*100:.1f}%'))

    def _setup_info_panel(self, ax, strategy_name, strategy_params, stats):
        # Panel informacyjny z lepszym formatowaniem
        ax.axis('off')
        strategy_info = [
            f"Strategia: {strategy_name}",
            "\nParametry:",
            *[f"  {k}: {v}" for k, v in strategy_params.items()],
            "\nStatystyki:",
            f"  Kapitał początkowy: ${stats.get('initial_capital', 100000):,.2f}",
            f"  Kapitał końcowy: ${stats.get('final_capital', 0):,.2f}",
            f"  Zwrot całkowity: {stats.get('total_return', 0):,.2f}%",
            f"  Liczba transakcji: {stats.get('total_trades', 0)}",
            f"  Win rate: {stats.get('win_rate', 0)*100:.1f}%",
            f"  Średni zysk: ${stats.get('avg_profit', 0):,.2f}",
            f"  Max drawdown: {stats.get('max_drawdown', 0)*100:.1f}%",
            f"  Sharpe Ratio: {stats.get('sharpe_ratio', 0):.2f}",
            f"  Annual Turnover: {stats.get('annual_turnover', 0):.2f}x"
        ]

        ax.text(0.05, 0.95, '\n'.join(strategy_info),
                fontsize=10,
                verticalalignment='top',
                linespacing=1.5,
                bbox=dict(facecolor='white',
                          edgecolor='gray',
                          alpha=0.9,
                          pad=10))
