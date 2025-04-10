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
from src.services.data_service import DataService
from src.services.visualization_service import VisualizationService

class BacktestService:
    """
    Service class for handling backtest operations, providing an interface
    between UI callbacks and the core backtest engine.
    """
    
    def __init__(self):
        """Initialize the BacktestService with required services and managers."""
        try:
            # Initialize related services
            self.data_service = DataService()
            self.visualization_service = VisualizationService()
            
            # Initialize core business logic
            self.backtest_manager = BacktestManager()
            
            # Result storage
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
            
            # Check if operation was successful
            success = signals is not None and results is not None and stats is not None
            
            return {
                "success": success,
                "signals": signals if signals is not None else {},
                "results": results if results is not None else {},
                "stats": stats if stats is not None else {},
                "tickers": tickers
            }
        
        except Exception as e:
            logger.error(f"Error running backtest: {e}", exc_info=True)
            return {"success": False, "error": str(e), "signals": {}, "results": {}, "stats": {}}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Generate performance metrics from current backtest results.
        
        Returns:
            Dict of formatted metric values
        """
        if not self.current_stats:
            return {}
        
        metrics = {}
        
        try:
            # Format total return with sign
            total_return = self.current_stats.get('Total Return', 0)
            total_return_str = f"+{total_return:.2f}%" if total_return >= 0 else f"{total_return:.2f}%"
            
            # Format CAGR with sign
            cagr = self.current_stats.get('CAGR', 0)
            cagr_str = f"+{cagr:.2f}%" if cagr >= 0 else f"{cagr:.2f}%"
            
            # Format metrics for display
            metrics = {
                "total-return": total_return_str,
                "cagr": cagr_str,
                "sharpe": f"{self.current_stats.get('Sharpe Ratio', 0):.2f}",
                "max-drawdown": f"{self.current_stats.get('Max Drawdown', 0):.2f}%",
                "win-rate": f"{self.current_stats.get('Win Rate', 0) * 100:.1f}%",
                "profit-factor": f"{self.current_stats.get('Profit Factor', 0):.2f}",
                "avg-trade": f"${self.current_stats.get('Avg Trade', 0):.2f}",
                
                # Additional metrics
                "recovery-factor": f"{self.current_stats.get('Recovery Factor', 0):.2f}x",
                "calmar-ratio": f"{self.current_stats.get('Calmar Ratio', 0):.2f}"
            }
            
            return metrics
        except Exception as e:
            logger.error(f"Error generating performance metrics: {e}", exc_info=True)
            return {}
    
    def get_portfolio_chart(self, chart_type: str = "value"):
        """
        Generate a portfolio performance chart using the visualization service.
        
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
            
            return self.visualization_service.create_portfolio_chart(
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
        Generate monthly returns heatmap using the visualization service.
        
        Returns:
            Plotly figure object
        """
        if not self.current_results or "Portfolio_Value" not in self.current_results:
            return None
        
        try:
            portfolio_series = self.current_results["Portfolio_Value"]
            return self.visualization_service.create_monthly_returns_heatmap(portfolio_series)
        except Exception as e:
            logger.error(f"Error generating monthly returns heatmap: {e}", exc_info=True)
            return None
    
    def get_signals_chart(self, ticker: str):
        """
        Generate signals and trades chart for a specific ticker using the visualization service.
        
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
            
            return self.visualization_service.create_signals_chart(ticker, signals_df, trades)
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
            return self.visualization_service.prepare_trades_for_table(trades)
        except Exception as e:
            logger.error(f"Error formatting trades table data: {e}", exc_info=True)
            return []
            
    def get_available_strategies(self) -> Dict[str, Dict]:
        """
        Get available trading strategies with descriptions.
        
        Returns:
            Dict of strategy information
        """
        return AVAILABLE_STRATEGIES