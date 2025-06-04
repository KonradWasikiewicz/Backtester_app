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
from src.core.constants import AVAILABLE_STRATEGIES, CHART_THEME, MONTHLY_RETURNS_DEFAULT_TITLE # Added MONTHLY_RETURNS_DEFAULT_TITLE
from src.core.config import config
from src.services.data_service import DataService
from src.services.visualization_service import VisualizationService
from src.visualization.visualizer import BacktestVisualizer
from src.core.exceptions import DataError, StrategyError, BacktestError # Added

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
        Runs a backtest for the specified strategy, tickers, and parameters.
        Returns a dictionary containing the results and any errors.
        """
        try:
            logger.info(f"--- BacktestService: Starting run_backtest ---")
            if progress_callback: progress_callback((1, "Service: Initializing..."))

            # --- 1. Input Validation and Preparation ---
            if not all([strategy_type, tickers, start_date, end_date, initial_capital is not None]):
                logger.error("Missing required inputs for backtest.")
                return {"success": False, "error": "Missing required inputs."}
            
            if not isinstance(initial_capital, (int, float)) or initial_capital <= 0:
                logger.error(f"Invalid initial capital: {initial_capital}. Must be a positive number.")
                return {"success": False, "error": f"Invalid initial capital: {initial_capital}. Must be a positive number."}

            logger.info(f"Inputs: Strategy={strategy_type}, Tickers={tickers}, Start={start_date}, End={end_date}, Capital=${initial_capital:,.2f}")
            if progress_callback: progress_callback((2, "Service: Inputs Validated. Initializing Backtest Manager..."))

            # --- 2. Initialize Backtest Manager ---
            # Re-initialize BacktestManager with the current initial_capital for this specific run
            current_backtest_manager = BacktestManager(initial_capital=initial_capital)
            logger.info(f"BacktestManager re-initialized with capital: ${initial_capital:,.2f}")
            if progress_callback: progress_callback((3, "Service: Backtest Manager Initialized. Configuring DataLoader..."))

            # --- 3. Configure DataLoader with Date Range ---
            # This step is mostly conceptual for progress, as DataLoader is configured within BacktestManager
            if progress_callback: progress_callback((4, "Service: DataLoader Configuration Simulated. Calling Manager's run_backtest..."))

            # --- 4. Execute Backtest via BacktestManager ---
            # Manager's progress will range from 8% to 80%
            all_signals, combined_results, stats = current_backtest_manager.run_backtest(
                strategy_type=strategy_type,
                tickers=tickers,
                strategy_params=strategy_params or {},
                risk_params=risk_params or {},
                cost_params=cost_params or {},
                rebalancing_params=rebalancing_params or {},
                progress_callback=progress_callback # Pass the callback
            )

            logger.info("Backtest execution completed by BacktestManager.")
            # Service resumes progress from 81%
            SERVICE_RESUME_PROGRESS = 81
            if progress_callback: progress_callback((SERVICE_RESUME_PROGRESS, "Service: Backtest Complete. Processing Results..."))

            # --- 5. Process and Package Results (81% - 98%) --- Range: 18%
            self.current_results = combined_results
            self.current_signals = all_signals
            self.current_stats = stats
            
            # Prepare data for UI
            if progress_callback: progress_callback((SERVICE_RESUME_PROGRESS + 2, "Service: Formatting Metrics...")) # 83%
            formatted_metrics = self.get_performance_metrics()
            
            if progress_callback: progress_callback((SERVICE_RESUME_PROGRESS + 5, "Service: Formatting Trades...")) # 86%
            trades_list = self.get_trades_table_data()
            if progress_callback: progress_callback((SERVICE_RESUME_PROGRESS + 7, "Service: Metrics & Trades Processed. Initializing Visualizer...")) # 88%

            # Initialize visualizer
            visualizer = BacktestVisualizer()
            visualizer.theme = CHART_THEME
            if progress_callback: progress_callback((SERVICE_RESUME_PROGRESS + 9, "Service: Visualizer Initialized. Generating Charts...")) # 90%

            # Generate chart figures
            portfolio_value_series = combined_results.get('Portfolio_Value')
            benchmark_series = combined_results.get('Benchmark')

            # Equity Curve (Value)
            if progress_callback: progress_callback((SERVICE_RESUME_PROGRESS + 10, "Service: Charting Equity (Value)...")) # 91%
            equity_value_fig = visualizer.create_equity_curve_figure(portfolio_value_series, benchmark_series, chart_type="value", initial_capital=initial_capital)
            
            # Equity Curve (Returns)
            if progress_callback: progress_callback((SERVICE_RESUME_PROGRESS + 11, "Service: Charting Equity (Returns)...")) # 92%
            equity_returns_fig = visualizer.create_equity_curve_figure(portfolio_value_series, benchmark_series, chart_type="returns", initial_capital=initial_capital)

            # Drawdown Chart
            if progress_callback: progress_callback((SERVICE_RESUME_PROGRESS + 12, "Service: Charting Drawdown...")) # 93%
            drawdown_fig = visualizer.create_equity_curve_figure(portfolio_value_series, benchmark_series, chart_type="drawdown", initial_capital=initial_capital)

            # Monthly Returns Heatmap
            if progress_callback: progress_callback((SERVICE_RESUME_PROGRESS + 13, "Service: Charting Monthly Returns...")) # 94%
            monthly_returns_fig = MONTHLY_RETURNS_DEFAULT_TITLE # Changed from config.MONTHLY_RETURNS_DEFAULT_TITLE
            if portfolio_value_series is not None and not portfolio_value_series.empty:
                 monthly_returns_fig = visualizer.create_monthly_returns_heatmap(portfolio_value_series)
            else: # Create an empty chart if no data
                 monthly_returns_fig = visualizer.create_empty_chart(MONTHLY_RETURNS_DEFAULT_TITLE) # Changed from config.MONTHLY_RETURNS_DEFAULT_TITLE

            if progress_callback: progress_callback((SERVICE_RESUME_PROGRESS + 14, "Service: Charts Generated. Packaging...")) # 95%

            results_package = {
                "success": True,
                "metrics": formatted_metrics,
                "trades_data": trades_list,
                "portfolio_value_chart_json": equity_value_fig.to_json() if equity_value_fig else None,
                "portfolio_returns_chart_json": equity_returns_fig.to_json() if equity_returns_fig else None,
                "drawdown_chart_json": drawdown_fig.to_json() if drawdown_fig else None,
                "monthly_returns_heatmap_json": monthly_returns_fig.to_json() if monthly_returns_fig else None,
                "selected_tickers": tickers
            }
            logger.info("BacktestService: Successfully processed and packaged results.")
            if progress_callback: progress_callback((SERVICE_RESUME_PROGRESS + 17, "Service: Results Packaged. Finalizing...")) # 98%
            return results_package

        except DataError as de: # Specific data error
            logger.error(f"DataError in BacktestService: {de}", exc_info=True)
            if progress_callback: progress_callback((100, f"Service Error: Data Issue - {str(de)[:30]}..."))
            return {"success": False, "error": f"Data Error: {str(de)}", "metrics": {}, "trades_data": [], "charts": {}}
        except StrategyError as se: # Specific strategy error
            logger.error(f"StrategyError in BacktestService: {se}", exc_info=True)
            if progress_callback: progress_callback((100, f"Service Error: Strategy Issue - {str(se)[:30]}..."))
            return {"success": False, "error": f"Strategy Error: {str(se)}", "metrics": {}, "trades_data": [], "charts": {}}
        except BacktestError as be: # General backtest error
            logger.error(f"BacktestError in BacktestService: {be}", exc_info=True)
            if progress_callback: progress_callback((100, f"Service Error: Backtest Issue - {str(be)[:30]}..."))
            return {"success": False, "error": f"Backtest Error: {str(be)}", "metrics": {}, "trades_data": [], "charts": {}}
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f"Unexpected error in BacktestService run_backtest: {e}\nTraceback:\n{tb_str}")
            # Ensure progress is set to 100% with an error message before returning
            if progress_callback: progress_callback((100, f"Service Error: Unexpected - {str(e)[:30]}..."))
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}", "metrics": {}, "trades_data": [], "charts": {}}

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

    def get_signals_chart(self, ticker: str, indicators: Optional[List[str]] = None):
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
            trades_list = self.current_results.get("trades", [])
            ticker_trades = [t for t in trades_list if t.get('ticker') == ticker]

            if signals_df is None or signals_df.empty:
                logger.warning(f"No signal data found for ticker {ticker} in current_signals.")
                return None

            indicators_dict = {}
            if indicators:
                price_col = 'close' if 'close' in signals_df.columns else 'Close'
                if 'sma50' in indicators and price_col in signals_df.columns:
                    indicators_dict['SMA50'] = signals_df[price_col].rolling(window=50).mean()
                if 'sma200' in indicators and price_col in signals_df.columns:
                    indicators_dict['SMA200'] = signals_df[price_col].rolling(window=200).mean()

            visualizer = BacktestVisualizer()
            visualizer.theme = CHART_THEME
            fig = visualizer.create_signals_chart(ticker, signals_df, ticker_trades, indicators=indicators_dict)
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
