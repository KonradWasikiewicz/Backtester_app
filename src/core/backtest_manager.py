import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple, Any, Optional
from pathlib import Path
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import necessary modules
from .constants import AVAILABLE_STRATEGIES
from .data import DataLoader
from .engine import BacktestEngine
from .config import config
from ..strategies.base import BaseStrategy
from ..strategies.moving_average import MovingAverageCrossover
from ..strategies.rsi import RSIStrategy
from ..strategies.bollinger import BollingerBandsStrategy
from ..analysis.metrics import (
    calculate_cagr, calculate_sharpe_ratio, calculate_sortino_ratio,
    calculate_max_drawdown, calculate_calmar_ratio, calculate_pure_profit_score
)

class BacktestManager:
    """
    Manages the backtest process, handling data, strategies, and results
    """
    def __init__(self, initial_capital=10000, data_loader=None):
        self.initial_capital = initial_capital
        self.data_loader = data_loader or DataLoader()
        
    def create_strategy(self, strategy_type: str, **params) -> Optional[BaseStrategy]:
        """Create a strategy instance based on type and parameters"""
        try:
            if strategy_type == "BB":
                return BollingerBandsStrategy(
                    window=params.get('window', 20),
                    num_std=params.get('num_std', 2)
                )
            elif strategy_type == "MA":
                return MovingAverageCrossover(
                    short_window=params.get('short_window', 50),
                    long_window=params.get('long_window', 200)
                )
            elif strategy_type == "RSI":
                return RSIStrategy(
                    period=params.get('period', 14),
                    overbought=params.get('overbought', 70),
                    oversold=params.get('oversold', 30)
                )
            else:
                raise ValueError(f"Unknown strategy type: {strategy_type}")
        except Exception as e:
            print(f"Error creating strategy: {str(e)}")
            return None
    
    def load_data(self) -> Tuple[Dict[str, pd.DataFrame], Optional[pd.DataFrame]]:
        """Load data for backtesting"""
        try:
            data_dict = {}
            available_tickers = DataLoader.get_available_tickers()
            
            for ticker in available_tickers:
                try:
                    df = DataLoader.load_data(ticker)
                    if df is not None and not df.empty:
                        data_dict[ticker] = df
                except Exception as e:
                    print(f"Failed to load {ticker}: {str(e)}")
            
            benchmark_data = None
            try:
                benchmark_data = DataLoader.load_data(config.BENCHMARK_TICKER)
                if benchmark_data is not None:
                    benchmark_data = benchmark_data.ffill().bfill()
            except Exception:
                pass
                
            return data_dict, benchmark_data
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return {}, None
    
    def calculate_performance_stats(self, results):
        """Calculate performance statistics from backtest results"""
        if 'Portfolio_Value' not in results:
            logger.error("Portfolio_Value not found in results")
            return {}
            
        portfolio_values = results['Portfolio_Value']
        
        # Calculate returns
        returns = portfolio_values.pct_change().dropna()
        
        # Calculate basic performance metrics
        total_return = (portfolio_values.iloc[-1] / portfolio_values.iloc[0] - 1) * 100
        
        # Calculate drawdowns
        previous_peaks = portfolio_values.cummax()
        drawdowns = (portfolio_values - previous_peaks) / previous_peaks * 100
        max_drawdown = drawdowns.min()
        
        # Calculate annualized metrics
        days = (portfolio_values.index[-1] - portfolio_values.index[0]).days
        years = days / 365.25
        cagr = ((1 + total_return/100) ** (1/years) - 1) * 100 if years > 0 else 0
        
        # Risk metrics
        vol = returns.std() * np.sqrt(252)  # Annualized
        sharpe_ratio = (cagr/100 - 0.02) / vol if vol > 0 else 0
        
        # Downside risk
        downside_returns = returns[returns < 0]
        downside_vol = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0.0001
        sortino_ratio = (cagr/100 - 0.02) / downside_vol if downside_vol > 0 else 0
        
        # Recovery factor
        recovery_factor = abs(total_return / max_drawdown) if max_drawdown != 0 else 0
        
        # Pure profit score (proprietary metric)
        consistency = len(returns[returns > 0]) / len(returns) if len(returns) > 0 else 0
        pure_profit_score = (cagr * consistency) / (abs(max_drawdown) + 0.0001) * 10
        
        # Trade statistics
        trades = results.get('trades', [])
        winning_trades = len([t for t in trades if t.get('pnl', 0) > 0])
        win_rate = (winning_trades / len(trades) * 100) if trades else 0
        
        return {
            'total_return': total_return,
            'cagr': cagr,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': abs(cagr / max_drawdown) if max_drawdown != 0 else 0,
            'recovery_factor': recovery_factor,
            'pure_profit_score': pure_profit_score,
            'volatility': vol * 100,
            'win_rate': win_rate,
            'total_trades': len(trades),
            'Portfolio_Value': results['Portfolio_Value'],
            'Benchmark': results.get('Benchmark', None)
        }
    
    def run_backtest(self, strategy_type, **strategy_params):
        """Run backtest with specified strategy"""
        try:
            # Get strategy class
            if strategy_type not in AVAILABLE_STRATEGIES:
                raise ValueError(f"Strategy {strategy_type} not available")
                
            strategy_class = AVAILABLE_STRATEGIES[strategy_type]
            
            # Create strategy instance with params
            strategy = strategy_class(**strategy_params)
            
            # Get data for strategy
            data = self.data_loader.get_data()
            
            # Generate signals
            signals = strategy.generate_signals(data)
            
            # Prepare for backtest
            portfolio_values = pd.DataFrame()
            engine = BacktestEngine(initial_capital=self.initial_capital)
            engine.set_strategy(strategy)  # Set strategy AFTER initialization
            
            # Run backtest for each ticker
            for ticker, ticker_data in signals.items():
                result = engine.run_backtest(ticker, ticker_data)
                if result and 'Portfolio_Value' in result:
                    portfolio_values[ticker] = result['Portfolio_Value']
            
            # Get trading dates (common to all series)
            trading_dates = portfolio_values.index
            
            # Calculate final portfolio value
            combined_results = {
                'Portfolio_Value': portfolio_values.sum(axis=1),
                'trades': engine.trades,
                'signals': signals
            }
            
            # Add benchmark if available
            benchmark_data = self.data_loader.get_benchmark_data()
            if benchmark_data is not None:
                benchmark_start_date = trading_dates[0]
                benchmark_data = benchmark_data.loc[benchmark_data.index >= benchmark_start_date]
                
                # Calculate benchmark performance
                benchmark_start_price = benchmark_data['Close'].iloc[0]
                benchmark_shares = self.initial_capital / benchmark_start_price
                combined_results['Benchmark'] = benchmark_data['Close'] * benchmark_shares
            
            # Calculate stats
            stats = self.calculate_performance_stats(combined_results)
            
            return signals, combined_results, stats
            
        except Exception as e:
            logger.error(f"Backtest manager error: {str(e)}", exc_info=True)
            return None, None, None
