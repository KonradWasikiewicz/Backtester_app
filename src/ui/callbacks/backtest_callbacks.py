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
        # --- UPDATED Backtest Progress Bar IDs ---
        Output('backtesting_progress_bar_container', 'style', allow_duplicate=True), # Show/hide progress bar
        Output('backtesting_progress_bar', 'value', allow_duplicate=True),
        Output('backtesting_progress_bar', 'label', allow_duplicate=True),
        # --- ADDED Output to hide Strategy Progress Bar ---
        Output("strategy_progress_bar", "style", allow_duplicate=True),
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
        background=True,
        running=[
            (Output('run-backtest-button', 'disabled'), True, False),
            # --- UPDATED Backtest Progress Bar Container ID ---
            (Output('backtesting_progress_bar_container', 'style'), {'display': 'block'}, {'display': 'none'}),
            (Output('backtest-status', 'children'), "Running backtest...", ""),
            # --- ADDED Running state to hide Strategy Progress Bar ---
            (Output("strategy_progress_bar", "style"), {'display': 'none'}, no_update), # Hide when running starts
        ],
        progress=[
            # --- UPDATED Backtest Progress Bar IDs ---
            Output('backtesting_progress_bar', 'value'),
            Output('backtesting_progress_bar', 'label'),
        ],
        prevent_initial_call=True
    )
    def run_backtest(set_progress, n_clicks, strategy_type, tickers, start_date, end_date, initial_capital,
                     strategy_param_values, strategy_param_ids, # Updated strategy params
                     selected_risk_features, # Added risk features
                     max_position_size, stop_loss_type, stop_loss_value, # Updated risk params
                     take_profit_type, take_profit_value, max_risk_per_trade,
                     market_trend_lookback, max_drawdown, max_daily_loss,
                     commission, slippage, # Added costs
                     rebalancing_frequency, rebalancing_threshold # Added rebalancing
                     ):
        logger.info("--- run_backtest callback triggered (background) ---")
        if not n_clicks:
            logger.warning("run_backtest triggered without click.")
            raise PreventUpdate

        ctx = dash.callback_context
        if not ctx.triggered:
            logger.warning("run_backtest triggered without context.")
            raise PreventUpdate

        logger.info(f"Received tickers: {tickers} (type: {type(tickers)})")

        if isinstance(tickers, list) and tickers:
            tickers_list = [str(t).strip() for t in tickers if t]
        elif isinstance(tickers, str) and tickers.strip():
             tickers_list = [t.strip() for t in tickers.split(',') if t.strip()]
        else:
            tickers_list = []

        if not all([strategy_type, tickers_list, start_date, end_date, initial_capital]):
            error_msg = "Missing required inputs: Strategy, Tickers, Start/End Dates, or Initial Capital."
            logger.error(f"Input validation failed: {error_msg}")
            # Return values must match Outputs (excluding running/progress)
            # Output order: store, backtest_container style, backtest_bar value, backtest_bar label, strategy_bar style
            return {"timestamp": time.time(), "success": False, "error": error_msg}, \
                   {'display': 'none'}, 0, "Input Error", {'display': 'none'}

        try:
            start_date_dt = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except ValueError as e:
             error_msg = f"Invalid date format: {e}. Please use YYYY-MM-DD."
             logger.error(error_msg)
             # Return values must match Outputs
             return {"timestamp": time.time(), "success": False, "error": error_msg}, \
                    {'display': 'none'}, 0, "Date Error", {'display': 'none'}

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
            # --- RE-ADD set_progress call ---
            set_progress((1, "Running Backtest...")) # Use tuple for progress

            results_package = backtest_service.run_backtest(
                strategy_type=strategy_type,
                tickers=tickers_list,
                start_date=start_date_dt,
                end_date=end_date_dt,
                initial_capital=initial_capital,
                strategy_params=strategy_params_dict,
                risk_params=risk_params_dict,
                cost_params=trading_costs_dict,
                rebalancing_params=rebalancing_params_dict
            )

            end_time = time.time()
            logger.info(f"Backtest service call finished in {end_time - start_time:.2f} seconds.")
            results_package["timestamp"] = time.time()

            # --- ADDED LOGGING: Log the structure before returning ---
            if results_package.get("success"):
                logger.info(f"--- run_backtest callback: Preparing SUCCESSFUL results package for store. Keys: {list(results_package.keys())}")
                # Log metrics keys specifically
                if 'metrics' in results_package:
                    logger.debug(f"--- run_backtest callback: Metrics keys: {list(results_package['metrics'].keys())}")
                # Log trades count
                if 'trades_data' in results_package:
                    logger.debug(f"--- run_backtest callback: Trades count: {len(results_package['trades_data'])}")
            else:
                logger.warning(f"--- run_backtest callback: Preparing FAILED results package for store. Error: {results_package.get('error')}")
            # --- END ADDED LOGGING ---

            if results_package.get("success"):
                logger.info("--- run_backtest callback: Returning SUCCESSFUL results package from service ---")
                # --- RE-ADD set_progress call ---
                set_progress((100, "Complete")) # Use tuple for progress
                # Return values must match Outputs
                # Hide strategy bar on success
                return results_package, no_update, no_update, no_update, {'display': 'none'}
            else:
                error_msg = results_package.get('error', 'Unknown backtest failure')
                logger.error(f"--- run_backtest callback: Returning FAILED results package from service: {error_msg} ---")
                # --- RE-ADD set_progress call ---
                set_progress((100, "Failed")) # Use tuple for progress
                # Return values must match Outputs
                # Hide strategy bar on failure
                return results_package, {'display': 'none'}, 0, "Failed", {'display': 'none'}

        except Exception as e:
            logger.error(f"Exception during run_backtest callback execution: {e}", exc_info=True)
            error_msg = f"An unexpected error occurred in the backtest callback: {e}"
            logger.error(traceback.format_exc())
            # --- RE-ADD set_progress call ---
            set_progress((100, "Error")) # Use tuple for progress
            # Return values must match Outputs
            # Hide strategy bar on error
            return {"timestamp": time.time(), "success": False, "error": error_msg}, \
                   {'display': 'none'}, 0, "Callback Error", {'display': 'none'}

    # --- Result Update Callbacks (Triggered by Store) ---
    @app.callback(
        [
            Output('results-metrics', 'children'),
            Output('results-charts', 'children'),
            Output('results-tables', 'children')
        ],
        Input('backtest-results-store', 'data'),
        prevent_initial_call=True
    )
    def update_results_display(results_data):
        # --- ADDED LOGGING: Log received data --- 
        logger.info("--- update_results_display callback triggered ---")
        if not results_data:
            logger.warning("--- update_results_display: Received empty results_data. Preventing update.")
            raise PreventUpdate
        
        logger.debug(f"--- update_results_display: Received data keys: {list(results_data.keys())}")
        logger.debug(f"--- update_results_display: Success flag: {results_data.get('success')}")
        # --- END ADDED LOGGING ---

        if not results_data or not results_data.get('success'):
            logger.warning("--- update_results_display: results_data indicates failure or is invalid. Preventing update.")
            # Optionally return empty components or a message
            no_results_message = html.Div("Backtest failed or produced no results.", className="text-danger p-4")
            return no_results_message, no_results_message, no_results_message # Return message for all 3 outputs

        # Extract metrics, charts, and tables from results_data
        metrics = results_data.get('metrics', {})
        charts = {
            'portfolio_value': results_data.get('portfolio_value_chart_json'),
            'returns': results_data.get('portfolio_returns_chart_json'),
            'drawdown': results_data.get('drawdown_chart_json'),
            'heatmap': results_data.get('heatmap_json')
        }
        trades_table = results_data.get('trades_data', [])

        # --- ADDED LOGGING: Log extracted data --- 
        logger.debug(f"--- update_results_display: Extracted metrics keys: {list(metrics.keys())}")
        logger.debug(f"--- update_results_display: Extracted chart keys: {list(charts.keys())}")
        logger.debug(f"--- update_results_display: Extracted trades count: {len(trades_table)}")
        # --- END ADDED LOGGING ---

        # Create metric cards
        metrics_children = [
            create_metric_card(metric_name, metric_value)
            for metric_name, metric_value in metrics.items()
        ]

        # Create charts
        charts_children = [
            dcc.Graph(figure=pio.from_json(chart_json))
            for chart_json in charts.values() if chart_json
        ]

        # Create trades table
        table_children = dash_table.DataTable(
            data=trades_table,
            columns=[{"name": col, "id": col} for col in trades_table[0].keys()] if trades_table else []
        )

        # --- ADDED LOGGING: Log generated children --- 
        logger.debug(f"--- update_results_display: Generated {len(metrics_children)} metric cards.")
        logger.debug(f"--- update_results_display: Generated {len(charts_children)} chart components.")
        logger.debug(f"--- update_results_display: Generated trades table component: {'Yes' if table_children else 'No'}")
        logger.info("--- update_results_display callback finished successfully ---")
        # --- END ADDED LOGGING ---

        return metrics_children, charts_children, table_children

    logger.info("Backtest callbacks registered.")