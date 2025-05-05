import dash # Added import
from dash.exceptions import PreventUpdate
import time
import logging
import traceback
from datetime import datetime
import pandas as pd
# Import ALL for pattern-matching callbacks
from dash import Dash, dcc, html, Input, Output, State, callback, no_update, ctx, ClientsideFunction, ALL
import plotly.graph_objects as go
import plotly.io as pio
import dash_bootstrap_components as dbc # Import dbc
from dash import dash_table # Import dash_table

# Import services and components
from src.services.backtest_service import BacktestService
from src.ui.components import create_metric_card 
# Import layout functions needed for the new callback
from src.visualization.chart_utils import create_empty_chart
# Corrected import: Use BacktestVisualizer instead of Visualizer
from src.visualization.visualizer import BacktestVisualizer
# Import layout functions needed for the new callback - REMOVED UNUSED IMPORTS
# from src.ui.layouts.results_display import create_full_results_layout, create_no_results_placeholder
from src.core.exceptions import BacktestError, DataError
from src.core.constants import CHART_THEME

# Configure logging
logger = logging.getLogger(__name__)

# Initialize services (assuming a singleton or shared instance mechanism if needed)
# In a real Dash app, this might be handled differently (e.g., global variable, app context)
backtest_service = BacktestService()

def register_backtest_callbacks(app: Dash):
    """Register callbacks related to running backtests and displaying results."""

    logger.info("Registering backtest callbacks...")

    # --- Run Backtest Callback ---
    # This callback now outputs to the store instead of directly to result components
    @app.callback(
        Output('backtest-results-store', 'data'),
        # --- ADDED: Outputs for background task state ---
        Output('run-backtest-button', 'disabled'),
        Output('progress-bar-container', 'style'), # Show/hide progress bar
        Output('progress-bar', 'value'),
        Output('progress-bar', 'label'),
        # --- END ADDED ---
        Input('run-backtest-button', 'n_clicks'),
        State('strategy-dropdown', 'value'), # Corrected ID
        State('ticker-input', 'value'),      # Corrected ID
        State('backtest-start-date', 'date'), # Corrected ID and property
        State('backtest-end-date', 'date'),   # Corrected ID and property
        State('initial-capital-input', 'value'),
        # Strategy parameters (assuming pattern matching is correct)
        State({'type': 'strategy-param-input', 'index': ALL}, 'value'), # Use ALL to capture all dynamic params
        State({'type': 'strategy-param-input', 'index': ALL}, 'id'),    # Get IDs to map values
        # Risk parameters (using IDs from the layout)
        State('risk-features-checklist', 'value'), # Get selected risk features
        State('max-position-size', 'value'),
        State('stop-loss-type', 'value'),
        State('stop-loss-value', 'value'),
        State('take-profit-type', 'value'),
        State('take-profit-value', 'value'),
        State('max-risk-per-trade', 'value'),
        State('market-trend-lookback', 'value'),
        State('max-drawdown', 'value'), # Corrected ID
        State('max-daily-loss', 'value'),
        # Trading Costs
        State('commission-input', 'value'),
        State('slippage-input', 'value'),
        # Rebalancing
        State('rebalancing-frequency', 'value'),
        State('rebalancing-threshold', 'value'),
        # --- ADDED: Background=True and manager ---
        background=True,
        running=[
            (Output('run-backtest-button', 'disabled'), True, False),
            (Output('progress-bar-container', 'style'), {'display': 'block'}, {'display': 'none'}),
        ],
        progress=[
            Output('progress-bar', 'value'),
            Output('progress-bar', 'label'),
        ],
        # --- END ADDED ---
        prevent_initial_call=True
    )
    # --- ADDED: set_progress argument ---
    def run_backtest(set_progress, n_clicks, strategy_type, tickers, start_date, end_date, initial_capital,
                     strategy_param_values, strategy_param_ids, # Updated strategy params
                     selected_risk_features, # Added risk features
                     max_position_size, stop_loss_type, stop_loss_value, # Updated risk params
                     take_profit_type, take_profit_value, max_risk_per_trade,
                     market_trend_lookback, max_drawdown, max_daily_loss,
                     commission, slippage, # Added costs
                     rebalancing_frequency, rebalancing_threshold # Added rebalancing
                     ):
        # --- END ADDED ---
        logger.info("--- run_backtest callback triggered (background) ---")
        if not n_clicks:
            logger.warning("run_backtest triggered without click.")
            raise PreventUpdate

        # --- Input Validation and Preparation ---
        ctx = dash.callback_context
        if not ctx.triggered:
            logger.warning("run_backtest triggered without context.")
            raise PreventUpdate

        logger.info(f"Received tickers: {tickers} (type: {type(tickers)})")

        # Handle tickers as a list
        if isinstance(tickers, list) and tickers:
            tickers_list = [str(t).strip() for t in tickers if t]
        elif isinstance(tickers, str) and tickers.strip():
             tickers_list = [t.strip() for t in tickers.split(',') if t.strip()]
        else:
            tickers_list = []

        # Validate required inputs
        if not all([strategy_type, tickers_list, start_date, end_date, initial_capital]):
            error_msg = "Missing required inputs: Strategy, Tickers, Start/End Dates, or Initial Capital."
            logger.error(f"Input validation failed: {error_msg}")
            # Return error structure compatible with store expectations
            return {"timestamp": time.time(), "success": False, "error": error_msg}

        # --- Parameter Gathering and Cleaning ---
        try:
            start_date_dt = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except ValueError as e:
             error_msg = f"Invalid date format: {e}. Please use YYYY-MM-DD."
             logger.error(error_msg)
             return {"timestamp": time.time(), "success": False, "error": error_msg}

        strategy_params_dict = {pid['index']: val for pid, val in zip(strategy_param_ids, strategy_param_values)}
        risk_params_dict = {
            'features': selected_risk_features or [],
            'max_position_size': max_position_size,
            'stop_loss': {'type': stop_loss_type, 'value': stop_loss_value} if stop_loss_type != 'none' else None,
            'take_profit': {'type': take_profit_type, 'value': take_profit_value} if take_profit_type != 'none' else None,
            'max_risk_per_trade': max_risk_per_trade,
            'market_trend_lookback': market_trend_lookback,
            'max_drawdown': max_drawdown,
            'max_daily_loss': max_daily_loss
        }
        trading_costs_dict = {
            'commission_per_trade': commission,
            'slippage_per_trade': slippage
        }
        rebalancing_params_dict = {
            'frequency': rebalancing_frequency,
            'threshold': rebalancing_threshold
        }

        try:
            logger.info("Calling backtest_service.run_backtest...")
            start_time = time.time()

            # --- ADDED: Progress Update --- 
            set_progress((1, "Running Backtest..."))
            # --- END ADDED ---

            # --- MODIFIED: Call service and directly return its output --- 
            # The service now returns the dictionary ready for the store
            results_package = backtest_service.run_backtest(
                strategy_type=strategy_type,
                tickers=tickers_list,
                start_date=start_date_dt,
                end_date=end_date_dt,
                initial_capital=initial_capital, # Service handles parsing
                strategy_params=strategy_params_dict,
                risk_params=risk_params_dict,
                cost_params=trading_costs_dict,
                rebalancing_params=rebalancing_params_dict
            )

            end_time = time.time()
            logger.info(f"Backtest service call finished in {end_time - start_time:.2f} seconds.")

            # Add timestamp to the results package before returning
            results_package["timestamp"] = time.time()

            # --- ADDED: Final Progress Update --- 
            status_label = "Complete" if results_package.get("success") else "Failed"
            set_progress((10, status_label))
            # --- END ADDED ---

            if results_package.get("success"):
                logger.info("--- run_backtest callback: Returning SUCCESSFUL results package from service ---")
            else:
                logger.error(f"--- run_backtest callback: Returning FAILED results package from service: {results_package.get('error')} ---")

            # Return store data, button state (False), progress bar style (None)
            # The running= argument handles the state changes automatically
            return results_package

        except Exception as e:
            # Catch errors specifically from the callback logic/service call
            logger.error(f"Exception during run_backtest callback execution: {e}", exc_info=True)
            error_msg = f"An unexpected error occurred in the backtest callback: {e}"
            logger.error(traceback.format_exc())
            # Return error structure compatible with store expectations
            # Also return button state (False) and hide progress bar
            set_progress((10, "Error")) # Update progress on error
            return {"timestamp": time.time(), "success": False, "error": error_msg}

    # --- Result Update Callbacks (Triggered by Store) ---
    # ... existing result update callbacks ...

    # --- REMOVED Main Loader Callback ---
    # The background callback's running state handles the button disabling and progress bar

    logger.info("Backtest callbacks registered.")