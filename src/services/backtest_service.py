import pandas as pd
import numpy as np
import logging
import traceback
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Import local modules
from src.core.backtest_manager import BacktestManager
from src.core.constants import AVAILABLE_STRATEGIES
from src.core.config import config
from src.visualization.visualizer import BacktestVisualizer
from src.ui.components import create_metric_card_with_tooltip

class BacktestService:
    """
    Service class for handling backtest operations, providing an interface
    between UI callbacks and the core backtest engine.
    """
    
    def __init__(self):
        """Initialize the BacktestService with a BacktestManager."""
        try:
            self.backtest_manager = BacktestManager()
            self.visualizer = BacktestVisualizer()
            self.current_results = None
            self.current_signals = None
            self.current_stats = None
            logger.info("BacktestService initialized")
        except Exception as e:
            logger.error(f"Error initializing BacktestService: {e}", exc_info=True)
            raise
    
    def run_backtest(self, 
                     strategy_type: str, 
                     tickers: List[str],
                     start_date: str,
                     end_date: str,
                     strategy_params: Optional[Dict[str, Any]] = None,
                     risk_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run a backtest with the specified parameters.
        
        Args:
            strategy_type: Type of strategy to run
            tickers: List of ticker symbols
            start_date: Start date for backtest (YYYY-MM-DD)
            end_date: End date for backtest (YYYY-MM-DD)
            strategy_params: Parameters for the strategy
            risk_params: Parameters for risk management
            
        Returns:
            Dict containing backtest results information
        """
        try:
            logger.info(f"Starting backtest with strategy: {strategy_type}, tickers: {tickers}")
            logger.info(f"Date range: {start_date} to {end_date}")
            
            # Update configuration with date range
            config.START_DATE = start_date
            config.END_DATE = end_date
            
            # Run the backtest
            signals, results, stats = self.backtest_manager.run_backtest(
                strategy_type=strategy_type,
                tickers=tickers,
                strategy_params=strategy_params,
                risk_params=risk_params
            )
            
            # Store results for later use
            self.current_signals = signals
            self.current_results = results
            self.current_stats = stats
            
            # Sprawdzanie czy operacja zakończyła się sukcesem
            success = signals is not None and results is not None and stats is not None
            
            return {
                "success": success,
                "signals": signals if signals is not None else {},  # Zwracamy faktyczne dane sygnałów
                "results": results if results is not None else {},
                "stats": stats if stats is not None else {},
                "tickers": tickers
            }
        
        except Exception as e:
            logger.error(f"Error running backtest: {e}", exc_info=True)
            return {"success": False, "error": str(e), "signals": {}, "results": {}, "stats": {}}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Generate UI components for performance metrics.
        
        Returns:
            Dict of metric components keyed by metric ID
        """
        if not self.current_stats:
            return {}
        
        metrics = {}
        
        try:
            # Map metric IDs to their respective values and tooltips
            metric_definitions = {
                "total-return": {
                    "value": f"{self.current_stats.get('Total Return', 0):.2f}%", 
                    "tooltip": "Total percentage return over the entire backtest period",
                    "color": self._get_color_for_value(self.current_stats.get('Total Return', 0))
                },
                "cagr": {
                    "value": f"{self.current_stats.get('CAGR', 0):.2f}%",
                    "tooltip": "Compound Annual Growth Rate - annualized return",
                    "color": self._get_color_for_value(self.current_stats.get('CAGR', 0))
                },
                "sharpe": {
                    "value": f"{self.current_stats.get('Sharpe Ratio', 0):.2f}",
                    "tooltip": "Sharpe Ratio - return divided by risk (higher is better)",
                    "color": self._get_color_for_sharpe(self.current_stats.get('Sharpe Ratio', 0))
                },
                "max-drawdown": {
                    "value": f"{self.current_stats.get('Max Drawdown', 0):.2f}%",
                    "tooltip": "Maximum drawdown - largest peak-to-trough decline",
                    "color": "#ff4a68"  # Always red as drawdowns are negative
                },
                "win-rate": {
                    "value": f"{self.current_stats.get('Win Rate', 0) * 100:.1f}%",
                    "tooltip": "Percentage of trades that were profitable",
                    "color": self._get_color_for_win_rate(self.current_stats.get('Win Rate', 0))
                },
                "profit-factor": {
                    "value": f"{self.current_stats.get('Profit Factor', 0):.2f}",
                    "tooltip": "Gross profits divided by gross losses (higher is better)",
                    "color": self._get_color_for_profit_factor(self.current_stats.get('Profit Factor', 0))
                },
                "avg-trade": {
                    "value": f"${self.current_stats.get('Average Trade', 0):.2f}",
                    "tooltip": "Average profit/loss per trade",
                    "color": self._get_color_for_value(self.current_stats.get('Average Trade', 0))
                }
            }
            
            # Create metric components
            for metric_id, metric_data in metric_definitions.items():
                metrics[metric_id] = create_metric_card_with_tooltip(
                    title=metric_id.replace("-", " ").title(),
                    value=metric_data["value"],
                    tooltip_text=metric_data["tooltip"],
                    text_color=metric_data["color"]
                )
            
            return metrics
        
        except Exception as e:
            logger.error(f"Error generating performance metrics: {e}", exc_info=True)
            return {}
    
    def get_portfolio_chart(self, chart_type: str = "value"):
        """
        Generate a portfolio performance chart.
        
        Args:
            chart_type: Type of chart to generate (value, returns, drawdown)
            
        Returns:
            Plotly figure object
        """
        if not self.current_results or "Portfolio_Value" not in self.current_results:
            return None
        
        try:
            portfolio_values = self.current_results["Portfolio_Value"]
            benchmark_series = self.current_results.get("Benchmark")
            
            return self.visualizer.create_equity_curve_figure(
                portfolio_values=portfolio_values,
                benchmark_values=benchmark_series,
                chart_type=chart_type,
                initial_capital=self.backtest_manager.initial_capital
            )
        except Exception as e:
            logger.error(f"Error generating portfolio chart: {e}", exc_info=True)
            return None
    
    def get_monthly_returns_heatmap(self):
        """
        Generate monthly returns heatmap.
        
        Returns:
            Plotly figure object
        """
        if not self.current_results or "Portfolio_Value" not in self.current_results:
            return None
        
        try:
            portfolio_series = self.current_results["Portfolio_Value"]
            return self.visualizer.create_monthly_returns_heatmap(portfolio_series)
        except Exception as e:
            logger.error(f"Error generating monthly returns heatmap: {e}", exc_info=True)
            return None
    
    def get_signals_chart(self, ticker: str):
        """
        Generate signals and trades chart for a specific ticker.
        
        Args:
            ticker: Ticker symbol to display
            
        Returns:
            Plotly figure object
        """
        # Handle case where ticker might be a list
        if isinstance(ticker, list) and len(ticker) > 0:
            ticker = ticker[0]  # Use the first ticker in the list
            
        if (not self.current_signals or 
            not self.current_results or 
            not isinstance(ticker, str) or
            ticker not in self.current_signals):
            return None
        
        try:
            # Get signals for the ticker
            signals_df = self.current_signals[ticker]
            
            # Get trade data for the ticker
            trades = []
            if "trades" in self.current_results:
                trades = [t for t in self.current_results["trades"] if t["ticker"] == ticker]
            
            return self.visualizer.create_signals_chart(ticker, signals_df, trades)
        except Exception as e:
            logger.error(f"Error generating signals chart: {e}", exc_info=True)
            return None
    
    def get_trades_table_data(self) -> List[Dict[str, Any]]:
        """
        Get trade history data for display in a table.
        
        Returns:
            List of trade records formatted for display
        """
        if not self.current_results or "trades" not in self.current_results:
            return []
        
        try:
            trades = self.current_results["trades"]
            formatted_trades = []
            
            for trade in trades:
                formatted_trade = {
                    "ticker": trade["ticker"],
                    "entry_date": trade["entry_date"].strftime("%Y-%m-%d"),
                    "exit_date": trade["exit_date"].strftime("%Y-%m-%d"),
                    "entry_price": trade["entry_price"],  # Keep as raw number
                    "exit_price": trade["exit_price"],    # Keep as raw number
                    "profit_loss": trade["pnl"],          # Keep as raw number
                    "profit_loss_pct": trade["pnl_pct"],  # Keep as raw number
                    "shares": int(trade["shares"]),       # Convert to integer
                    "reason": trade["exit_reason"].capitalize()
                }
                formatted_trades.append(formatted_trade)
            
            return formatted_trades
        except Exception as e:
            logger.error(f"Error formatting trades table data: {e}", exc_info=True)
            return []
    
    def _get_color_for_value(self, value: float) -> str:
        """Helper method to determine color based on value sign."""
        if value > 0:
            return "#00cc96"  # Green for positive
        elif value < 0:
            return "#ff4a68"  # Red for negative
        return "#a9a9a9"      # Gray for zero
    
    def _get_color_for_sharpe(self, value: float) -> str:
        """Helper method to determine color based on Sharpe ratio value."""
        if value >= 1.0:
            return "#00cc96"  # Green for good
        elif value >= 0.5:
            return "#ffa15a"  # Orange for okay
        return "#ff4a68"      # Red for poor
    
    def _get_color_for_win_rate(self, value: float) -> str:
        """Helper method to determine color based on win rate value."""
        win_rate = value * 100 if value <= 1.0 else value  # Convert to percentage if needed
        if win_rate >= 50:
            return "#00cc96"  # Green for good
        elif win_rate >= 40:
            return "#ffa15a"  # Orange for okay
        return "#ff4a68"      # Red for poor
    
    def _get_color_for_profit_factor(self, value: float) -> str:
        """Helper method to determine color based on profit factor value."""
        if value >= 1.5:
            return "#00cc96"  # Green for good
        elif value >= 1.0:
            return "#ffa15a"  # Orange for okay
        return "#ff4a68"      # Red for poor