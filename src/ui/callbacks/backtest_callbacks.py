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
        Output('run-backtest-button', 'disabled'),
        Output('progress-bar-container', 'style'), # Show/hide progress bar
        Output('progress-bar', 'value'),
        Output('progress-bar', 'label'),
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
            # Return 5-element tuple on validation error
            return {"timestamp": time.time(), "success": False, "error": error_msg}, False, {'display': 'none'}, 0, "Input Error"

        try:
            start_date_dt = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except ValueError as e:
             error_msg = f"Invalid date format: {e}. Please use YYYY-MM-DD."
             logger.error(error_msg)
             # Return 5-element tuple on date format error
             return {"timestamp": time.time(), "success": False, "error": error_msg}, False, {'display': 'none'}, 0, "Date Error"

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
            set_progress((1, "Running Backtest..."))

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

            if results_package.get("success"):
                logger.info("--- run_backtest callback: Returning SUCCESSFUL results package from service ---")
                set_progress((10, "Complete"))
                # Return only store data; running state handles others
                return results_package, dash.no_update, dash.no_update, dash.no_update, dash.no_update
            else:
                error_msg = results_package.get('error', 'Unknown backtest failure')
                logger.error(f"--- run_backtest callback: Returning FAILED results package from service: {error_msg} ---")
                set_progress((10, "Failed"))
                # Return 5-element tuple on service failure
                return results_package, False, {'display': 'none'}, 0, "Failed"

        except Exception as e:
            logger.error(f"Exception during run_backtest callback execution: {e}", exc_info=True)
            error_msg = f"An unexpected error occurred in the backtest callback: {e}"
            logger.error(traceback.format_exc())
            set_progress((10, "Error"))
            # Return 5-element tuple on callback exception
            return {"timestamp": time.time(), "success": False, "error": error_msg}, False, {'display': 'none'}, 0, "Callback Error"

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
        if not results_data or not results_data.get('success'):
            raise PreventUpdate

        # Extract metrics, charts, and tables from results_data
        metrics = results_data.get('metrics', {})
        charts = {
            'portfolio_value': results_data.get('portfolio_value_chart_json'),
            'returns': results_data.get('portfolio_returns_chart_json'),
            'drawdown': results_data.get('drawdown_chart_json'),
            'heatmap': results_data.get('heatmap_json')
        }
        trades_table = results_data.get('trades_data', [])

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

        return metrics_children, charts_children, table_children

    # --- REMOVED Main Loader Callback ---
    # The background callback's running state handles the button disabling and progress bar

    logger.info("Backtest callbacks registered.")