import pandas as pd
import numpy as np
import logging
import traceback  
from typing import Dict, Tuple, Any, Optional
from pathlib import Path
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import necessary modules
from src.core.constants import AVAILABLE_STRATEGIES, TRADING_DAYS_PER_YEAR
from src.core.data import DataLoader
from src.core.engine import BacktestEngine
from .config import config
from ..strategies.moving_average import MovingAverageCrossoverStrategy
from ..strategies.rsi import RSIStrategy
from ..strategies.bollinger_bands import BollingerBandsStrategy
from ..analysis.metrics import (
    calculate_cagr, calculate_sharpe_ratio, calculate_sortino_ratio,
    calculate_max_drawdown, calculate_calmar_ratio, calculate_pure_profit_score
)

class BacktestManager:
    """Manager for running backtests across multiple strategies and instruments"""
    
    def __init__(self, initial_capital=100000.0):
        self.initial_capital = initial_capital
        self.data_loader = DataLoader()
        self.logger = logging.getLogger(__name__)
        
    def run_backtest(self, strategy_type, **strategy_params):
        """Run backtest with specified strategy type and parameters"""
        try:
            # Get all available tickers
            available_tickers = self.data_loader.get_available_tickers()
            
            if not available_tickers:
                raise ValueError("No ticker data available")
                
            # Create strategy instance
            strategy_class = AVAILABLE_STRATEGIES.get(strategy_type)
            if not strategy_class:
                raise ValueError(f"Unknown strategy type: {strategy_type}")
                
            # Use all available tickers
            strategy = strategy_class(
                tickers=available_tickers,
                **strategy_params
            )
            
            # Log startup message
            self.logger.info(f"Running backtest with {strategy_type} strategy for {len(available_tickers)} tickers: {', '.join(available_tickers)}")
            
            # Run tests for each ticker
            signals = {}
            results = {}
            all_trades = []
            
            for ticker in available_tickers:
                # Get data for this ticker
                data = self.data_loader.get_ticker_data(ticker)
                if data is None or data.empty:
                    continue
                    
                # Generate signals
                ticker_signals = strategy.generate_signals(ticker, data)
                if ticker_signals is not None:
                    signals[ticker] = ticker_signals
                    
                # Create backtest engine
                engine = BacktestEngine(
                    initial_capital=self.initial_capital / len(available_tickers),
                    strategy=strategy
                )
                
                # Run backtest
                ticker_results = engine.run_backtest(ticker, data.join(ticker_signals))
                if ticker_results:
                    results[ticker] = ticker_results
                    
                    # Collect trades
                    if 'trades' in ticker_results:
                        all_trades.extend(ticker_results['trades'])
                        
            # Log summary of results
            total_trades = len(all_trades)
            tickers_with_trades = {trade.get('ticker') for trade in all_trades if trade.get('ticker')}
            
            self.logger.info(f"Backtest completed with {total_trades} trades across {len(tickers_with_trades)} tickers")
            
            # Combine results
            combined_results = self._combine_results(results)
            
            # Add benchmark data
            combined_results['Benchmark'] = self._get_benchmark_data()
            
            # Add all trades
            combined_results['trades'] = all_trades
            
            # Calculate portfolio stats
            stats = self._calculate_portfolio_stats(combined_results)
            
            return signals, combined_results, stats
            
        except Exception as e:
            self.logger.error(f"Backtest manager error: {str(e)}")
            traceback.print_exc()
            return None, None, None

    def _combine_results(self, ticker_results):
        """
        Combine individual ticker results into portfolio-level results.
        
        Args:
            ticker_results (dict): Dictionary with ticker as key and results dict as value
            
        Returns:
            dict: Combined portfolio results
        """
        if not ticker_results:
            return {}
            
        # Get the earliest common date among all ticker results
        all_series = []
        for ticker, results in ticker_results.items():
            if 'Portfolio_Value' in results and not results['Portfolio_Value'].empty:
                all_series.append(results['Portfolio_Value'])
        
        if not all_series:
            return {}
            
        # Find the common date range
        common_index = all_series[0].index
        for series in all_series[1:]:
            common_index = common_index.intersection(series.index)
        
        if len(common_index) == 0:
            return {}
        
        # Initialize combined portfolio series
        combined_portfolio = pd.Series(0.0, index=common_index)
        
        # Sum up portfolio values across tickers
        for ticker, results in ticker_results.items():
            if 'Portfolio_Value' in results and not results['Portfolio_Value'].empty:
                ticker_series = results['Portfolio_Value'].reindex(common_index)
                combined_portfolio = combined_portfolio.add(ticker_series, fill_value=0)
        
        # Collect all trades
        all_trades = []
        for ticker, results in ticker_results.items():
            if 'trades' in results:
                all_trades.extend(results['trades'])
        
        # Sort trades by entry date
        all_trades.sort(key=lambda x: pd.to_datetime(x.get('entry_date', '1970-01-01')))
        
        # Create combined results dictionary
        combined_results = {
            'Portfolio_Value': combined_portfolio,
            'trades': all_trades
        }
        
        return combined_results

    def _get_benchmark_data(self):
        """Get benchmark data for comparison, aligned with backtest period"""
        try:
            # Load benchmark data
            benchmark_df = pd.read_csv(
                self.data_loader.data_path,
                parse_dates=['Date']
            )
            
            # Filter for benchmark ticker
            benchmark_df = benchmark_df[benchmark_df['Ticker'] == self.data_loader.benchmark_ticker].copy()
            
            if len(benchmark_df) == 0:
                self.logger.warning(f"Benchmark ticker {self.data_loader.benchmark_ticker} not found in data")
                return pd.Series()
                
            # Set date as index
            benchmark_df.set_index('Date', inplace=True)
            
            # Sort by date
            benchmark_df = benchmark_df.sort_index()
            
            # Select Close price
            benchmark_series = benchmark_df['Close']
            
            # Get the backtest start date from config
            start_date = pd.to_datetime(config.START_DATE)
            end_date = pd.to_datetime(config.END_DATE)
            
            # Filter benchmark to match backtest period
            benchmark_series = benchmark_series[
                (benchmark_series.index >= start_date) & 
                (benchmark_series.index <= end_date)
            ]
            
            # Normalize to 100 at start for percentage comparison
            benchmark_series = benchmark_series / benchmark_series.iloc[0] * 100
            
            return benchmark_series
            
        except Exception as e:
            self.logger.error(f"Error loading benchmark data: {str(e)}")
            return pd.Series()

    def _calculate_portfolio_stats(self, results):
        """
        Calculate portfolio performance statistics from backtest results.
        
        Args:
            results (dict): Combined backtest results
            
        Returns:
            dict: Dictionary of calculated statistics
        """
        if not results or 'Portfolio_Value' not in results:
            return {}
            
        portfolio_series = results.get('Portfolio_Value')
        benchmark_series = results.get('Benchmark')
        
        if portfolio_series is None or len(portfolio_series) == 0:
            return {}
        
        # Copy the portfolio series data to include in results
        stats = {'Portfolio_Value': portfolio_series, 'Benchmark': benchmark_series}
        
        # Calculate basic return metrics
        initial_value = portfolio_series.iloc[0]
        final_value = portfolio_series.iloc[-1]
        
        # Calculate total return
        total_return = ((final_value / initial_value) - 1) * 100
        stats['total_return'] = total_return
        
        # Calculate CAGR (annualized return)
        days = (portfolio_series.index[-1] - portfolio_series.index[0]).days
        years = days / 365.0
        
        if years > 0:
            cagr = ((final_value / initial_value) ** (1 / years) - 1) * 100
        else:
            cagr = 0
        stats['cagr'] = cagr
        
        # Calculate maximum drawdown
        roll_max = portfolio_series.cummax()
        drawdown = (portfolio_series / roll_max - 1) * 100
        max_drawdown = drawdown.min()
        stats['max_drawdown'] = max_drawdown
        
        # Calculate daily returns
        daily_returns = portfolio_series.pct_change().dropna()
        
        # Calculate Sharpe Ratio
        risk_free_rate = float(self.risk_free_rate) / 100 if hasattr(self, 'risk_free_rate') else 0.02
        excess_returns = daily_returns - risk_free_rate / 252  # Daily risk-free rate
        sharpe_ratio = 0
        
        if len(excess_returns) > 0 and excess_returns.std() > 0:
            sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
        stats['sharpe_ratio'] = sharpe_ratio
        
        # Calculate Sortino Ratio
        downside_returns = daily_returns[daily_returns < 0]
        sortino_ratio = 0
        
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            sortino_ratio = (daily_returns.mean() - risk_free_rate / 252) / downside_returns.std() * np.sqrt(252)
        stats['sortino_ratio'] = sortino_ratio
        
        # Calculate winning days percentage
        winning_days = (daily_returns > 0).sum()
        total_days = len(daily_returns)
        win_rate = (winning_days / total_days * 100) if total_days > 0 else 0
        stats['win_rate'] = win_rate
        
        # Store trade information
        stats['trades'] = results.get('trades', [])
        
        return stats
