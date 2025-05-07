import pandas as pd
import numpy as np
import logging
import traceback
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import plotly.io as pio # Import pio

# Configure logging
logger = logging.getLogger(__name__)

# Import local modules
from src.core.backtest_manager import BacktestManager
from src.core.constants import AVAILABLE_STRATEGIES
from src.core.config import config
from src.services.data_service import DataService
from src.services.visualization_service import VisualizationService
from src.visualization.visualizer import BacktestVisualizer
from src.core.constants import CHART_THEME

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
                     initial_capital: float = 100000.0,
                     strategy_params: Optional[Dict[str, Any]] = None,
                     risk_params: Optional[Dict[str, Any]] = None,
                     cost_params: Optional[Dict[str, Any]] = None,
                     rebalancing_params: Optional[Dict[str, Any]] = None,
                     progress_callback: Optional[callable] = None
                     ) -> Dict[str, Any]:
        """
        Run a backtest with the specified parameters and return results formatted for the store.
        
        Args:
            strategy_type: The type of strategy to run.
            tickers: List of ticker symbols.
            start_date: Backtest start date.
            end_date: Backtest end date.
            initial_capital: The starting capital for the backtest.
            strategy_params: Dictionary of strategy-specific parameters.
            risk_params: Dictionary of risk management parameters.
            cost_params: Dictionary of trading cost parameters (commission, slippage).
            rebalancing_params: Dictionary of portfolio rebalancing parameters.
            progress_callback: Optional function to report progress updates.
            
        Returns:
            Dictionary containing backtest results formatted for the backtest-results-store.
        """
        try:
            if progress_callback: progress_callback((2, "Service Started. Initializing Manager..."))
            logger.info(f"Running backtest: Strategy={strategy_type}, Tickers={tickers}, Start={start_date}, End={end_date}, Capital={initial_capital}, Costs={cost_params}, Rebalancing={rebalancing_params}")

            # Update configuration with date range
            config.START_DATE = start_date
            config.END_DATE = end_date

            # Convert initial_capital string to float
            try:
                parsed_capital = float(str(initial_capital).replace(' ', '').replace(',', ''))
            except (ValueError, TypeError):
                logger.error(f"Invalid format for initial_capital: {initial_capital}. Using default 100000.0")
                parsed_capital = 100000.0

            # Re-initialize BacktestManager
            self.backtest_manager = BacktestManager(initial_capital=parsed_capital)
            if progress_callback: progress_callback((5, "Manager Initialized. Starting Core Engine..."))

            # Run the core backtest
            signals, results, stats = self.backtest_manager.run_backtest(
                strategy_type=strategy_type,
                tickers=tickers,
                strategy_params=strategy_params,
                risk_params=risk_params,
                cost_params=cost_params,
                rebalancing_params=rebalancing_params,
                progress_callback=progress_callback # Pass down
            )

            # Store raw results
            self.current_signals = signals
            self.current_results = results
            self.current_stats = stats

            # Check if core backtest was successful
            success = signals is not None and results is not None and stats is not None

            if not success:
                error_msg_detail = "Core backtest failed."
                if stats and "error" in stats:
                    error_msg_detail = stats["error"]
                elif results and "error" in results:
                    error_msg_detail = results["error"]

                logger.error(f"Core backtest execution failed. Details: {error_msg_detail}")
                if progress_callback: progress_callback((70, f"Core Engine Failed: {error_msg_detail[:30]}..."))
                return {"success": False, "error": error_msg_detail}

            if progress_callback: progress_callback((71, "Core Engine Finished. Processing Results..."))
            
            # --- Generate outputs for the store --- 
            metrics_dict = self.get_performance_metrics()
            trades_list = self.get_trades_table_data()
            if progress_callback: progress_callback((80, "Metrics Processed. Generating Visualizations..."))

            # Initialize visualizer
            visualizer = BacktestVisualizer()
            visualizer.theme = CHART_THEME

            # Generate chart figures
            portfolio_values = results.get("Portfolio_Value")
            benchmark_values = results.get("Benchmark")

            value_fig = visualizer.create_equity_curve_figure(portfolio_values, benchmark_values, chart_type="value")
            returns_fig = visualizer.create_equity_curve_figure(portfolio_values, benchmark_values, chart_type="returns")
            drawdown_fig = visualizer.create_equity_curve_figure(portfolio_values, benchmark_values, chart_type="drawdown")
            heatmap_fig = visualizer.create_monthly_returns_heatmap(portfolio_values)

            # Convert figures to JSON
            value_json = pio.to_json(value_fig) if value_fig else None
            returns_json = pio.to_json(returns_fig) if returns_fig else None
            drawdown_json = pio.to_json(drawdown_fig) if drawdown_fig else None
            heatmap_json = pio.to_json(heatmap_fig) if heatmap_fig else None
            if progress_callback: progress_callback((95, "Visualizations Generated. Finalizing..."))

            # Prepare the final dictionary for the store
            store_output = {
                "success": True,
                "metrics": metrics_dict,
                "trades_data": trades_list,
                "portfolio_value_chart_json": value_json,
                "portfolio_returns_chart_json": returns_json,
                "drawdown_chart_json": drawdown_json,
                "heatmap_json": heatmap_json,
                "selected_tickers": tickers
            }
            logger.info("Successfully generated backtest results package for store.")
            return store_output

        except Exception as e:
            logger.error(f"Error running backtest service method: {e}", exc_info=True)
            if progress_callback: progress_callback((99, f"Service Error: {type(e).__name__}"))
            return {"success": False, "error": f"Service error: {e}"}

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Generate performance metrics dictionary from current backtest stats.

        Returns:
            Dict of raw metric values (or empty dict if no stats).
        """
        if not self.current_stats or not self.backtest_manager:
            logger.warning("get_performance_metrics called but no stats available.")
            return {}

        metrics = {}
        try:
            # --- Standard Performance Metrics (Raw Values) ---
            start_balance = self.backtest_manager.initial_capital
            # Safely get end balance
            end_balance = start_balance # Default to start if results are missing
            if self.current_results and "Portfolio_Value" in self.current_results and not self.current_results["Portfolio_Value"].empty:
                end_balance = self.current_results["Portfolio_Value"].iloc[-1]

            metrics = {
                "starting-balance": start_balance,
                "ending-balance": end_balance,
                "total-return": self.current_stats.get('Total Return', 0), # Raw percentage
                "cagr": self.current_stats.get('CAGR', 0), # Raw percentage
                "sharpe": self.current_stats.get('Sharpe Ratio', 0),
                "max-drawdown": self.current_stats.get('Max Drawdown', 0), # Raw percentage
                "calmar-ratio": self.current_stats.get('Calmar Ratio', 0),
                "recovery-factor": self.current_stats.get('Recovery Factor', 0),
                "trades-count": self.current_stats.get('total_trades', 0),
                "win-rate": self.current_stats.get('Win Rate', 0) * 100, # Convert to percentage
                "profit-factor": self.current_stats.get('Profit Factor', np.nan), # Use NaN for undefined
                "avg-trade": self.current_stats.get('Avg Trade Pct', 0), # Use Avg Trade Pct
                "signals-generated": self.current_stats.get('total_entry_signals', 0),
                "rejected-signals-total": self.current_stats.get('total_rejected_signals', 0),
            }
            # Handle potential NaN for profit factor
            if pd.isna(metrics["profit-factor"]):
                 metrics["profit-factor"] = 0 # Or some other indicator like 'inf' or None

            return metrics
        except Exception as e:
            logger.error(f"Error generating performance metrics dictionary: {e}", exc_info=True)
            return {}

    def get_signals_chart(self, ticker: str):
        """
        Generate signals and trades chart figure for a specific ticker.
        Uses BacktestVisualizer.

        Args:
            ticker: Ticker symbol to display

        Returns:
            Plotly figure object or None
        """
        if isinstance(ticker, list) and len(ticker) > 0:
            ticker = ticker[0]

        if not isinstance(ticker, str) or not self.current_signals or ticker not in self.current_signals:
            logger.warning(f"Cannot generate signals chart. Invalid ticker ('{ticker}') or no signal data.")
            return None

        try:
            signals_df = self.current_signals.get(ticker)
            # Ensure trades data is available and filter for the ticker
            trades_list = self.current_results.get("trades", [])
            ticker_trades = [t for t in trades_list if t.get('ticker') == ticker]

            if signals_df is None or signals_df.empty:
                 logger.warning(f"No signal data found for ticker {ticker} in current_signals.")
                 return None

            # Use BacktestVisualizer to create the chart figure
            visualizer = BacktestVisualizer()
            visualizer.theme = CHART_THEME
            # Pass the filtered trades list
            fig = visualizer.create_signals_chart(ticker, signals_df, ticker_trades)
            return fig

        except Exception as e:
            logger.error(f"Error generating signals chart figure for {ticker}: {e}", exc_info=True)
            return None

    def get_trades_table_data(self) -> List[Dict[str, Any]]:
        """
        Get trade history data formatted for Dash DataTable.

        Returns:
            List of trade records formatted for DataTable.
        """
        if not self.current_results or "trades" not in self.current_results:
            logger.warning("get_trades_table_data called but no results or trades available.")
            return []

        try:
            trades = self.current_results["trades"]
            formatted_trades = []
            for t in trades:
                entry_dt = pd.to_datetime(t.get('entry_date'))
                exit_dt = pd.to_datetime(t.get('exit_date'))
                duration_val = t.get('duration', None)
                # Ensure duration is a string or None
                duration_str = str(duration_val) if duration_val is not None else None

                formatted_trades.append({
                    # Match IDs used in backtest_callbacks.py update_trades_table
                    'entry_date': entry_dt.strftime('%Y-%m-%d %H:%M') if entry_dt else None,
                    'exit_date': exit_dt.strftime('%Y-%m-%d %H:%M') if exit_dt else None,
                    'ticker': t.get('ticker'),
                    'direction': t.get('direction', 'LONG'), # Assume LONG if missing
                    'entry_price': t.get('entry_price'),
                    'exit_price': t.get('exit_price'),
                    'size': t.get('size'), # Use 'size' instead of 'shares'
                    'pnl': t.get('pnl'),
                    'return_pct': t.get('return_pct'), # Use 'return_pct'
                    'duration': duration_str, # Use formatted duration string
                    'stop_loss_hit': t.get('stop_loss_hit', False),
                    'take_profit_hit': t.get('take_profit_hit', False),
                })
            return formatted_trades
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