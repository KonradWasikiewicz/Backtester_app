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
from src.core.exceptions import BacktestError, DataError
from src.core.constants import CHART_THEME

# Import centralized IDs
from src.ui.ids.ids import ResultsIDs, WizardIDs, StrategyConfigIDs # Added StrategyConfigIDs for main page inputs

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
        Output(ResultsIDs.BACKTEST_RESULTS_STORE, 'data'),
        Output("loading-overlay", 'style', allow_duplicate=True), 
        Output(ResultsIDs.BACKTEST_PROGRESS_BAR, 'value', allow_duplicate=True),
        Output(ResultsIDs.BACKTEST_PROGRESS_BAR, 'label', allow_duplicate=True),
        Output(WizardIDs.PROGRESS_BAR, "style", allow_duplicate=True), # Wizard progress bar
        Output(ResultsIDs.RIGHT_PANEL_COLUMN, 'style', allow_duplicate=True),
        Output(ResultsIDs.RESULTS_AREA_WRAPPER, 'style', allow_duplicate=True),
        Input('run-backtest-trigger-store', 'data'), 
        State(StrategyConfigIDs.STRATEGY_CONFIG_STORE_MAIN, 'data'),
        background=True,
        running=[
            (Output(StrategyConfigIDs.RUN_BACKTEST_BUTTON_MAIN, 'disabled'), True, False), 
            (Output(WizardIDs.RUN_BACKTEST_BUTTON_WIZARD, 'disabled'), True, False), 
            (Output("loading-overlay", 'style'), 
             {"display": "flex", "position": "absolute", "top": "0", "left": "0", "right": "0", "bottom": "0", "backgroundColor": "rgba(18, 18, 18, 0.85)", "zIndex": "1050", "flexDirection": "column", "alignItems": "center", "justifyContent": "center"}, 
             {"display": "none"}),
            (Output(ResultsIDs.BACKTEST_STATUS_MESSAGE, 'children'), "Running backtest...", ""),
            (Output(WizardIDs.PROGRESS_BAR, "style"), {'display': 'none'}, no_update), 
            (Output(ResultsIDs.RIGHT_PANEL_COLUMN, 'style', allow_duplicate=True),
             {'visibility': 'hidden', 'paddingLeft': '15px'}, 
             {'visibility': 'hidden', 'paddingLeft': '15px'}),
            (Output(ResultsIDs.RESULTS_AREA_WRAPPER, 'style', allow_duplicate=True),
             {'display': 'none'}, 
             {'display': 'none'})
        ],
        progress=[
            Output(ResultsIDs.BACKTEST_PROGRESS_BAR, 'value'),
            Output(ResultsIDs.BACKTEST_PROGRESS_BAR, 'label'),
        ],
        prevent_initial_call=True
    )
    def run_backtest(set_progress, trigger_data, config_data): 
        logger.info("--- run_backtest callback: Entered. 'running' state should hide right-panel-col.")
        if not trigger_data: 
            logger.warning("run_backtest triggered without trigger_data.")
            raise PreventUpdate

        if not config_data:
            logger.warning("run_backtest triggered without config_data.")
            return {"timestamp": time.time(), "success": False, "error": "Configuration data is missing."}, \
                   {"display": "none"}, 0, "Config Error", {'display': 'none'}, no_update, no_update

        logger.info(f"run_backtest: Received config_data: {config_data}")

        # Extract parameters from config_data
        strategy_type = config_data.get("strategy_type")
        tickers = config_data.get("tickers") 
        start_date_str = config_data.get("start_date")
        end_date_str = config_data.get("end_date")
        initial_capital = config_data.get("initial_capital") 
        strategy_params_dict = config_data.get("strategy_params", {})
        risk_params_dict = config_data.get("risk_management", {})
        trading_costs_config = config_data.get("trading_costs", {})
        rebalancing_params_config = config_data.get("rebalancing", {})

        cost_params_dict = {
            'commission_per_trade': trading_costs_config.get('commission_bps'),
            'slippage_per_trade': trading_costs_config.get('slippage_bps')
        }
        rebalancing_params_dict = {
            'frequency': rebalancing_params_config.get('frequency'),
            'threshold': rebalancing_params_config.get('threshold_pct')
        }

        if isinstance(tickers, list) and tickers:
            tickers_list = [str(t).strip() for t in tickers if t]
        elif isinstance(tickers, str) and tickers.strip(): 
             tickers_list = [t.strip() for t in tickers.split(',') if t.strip()]
        else:
            tickers_list = []

        if not all([strategy_type, tickers_list, start_date_str, end_date_str, initial_capital is not None]):
            error_msg = "Missing required inputs from config_data: Strategy, Tickers, Start/End Dates, or Initial Capital."
            logger.error(f"run_backtest: Input validation failed: {error_msg}")
            return {"timestamp": time.time(), "success": False, "error": error_msg}, \
                   {"display": "none"}, 0, "Input Error", {'display': 'none'}, no_update, no_update

        try:
            start_date_dt = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
            end_date_dt = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
        except ValueError as e:
             error_msg = f"Invalid date format in config_data: {e}. Please use YYYY-MM-DD."
             logger.error(f"run_backtest: {error_msg}")
             return {"timestamp": time.time(), "success": False, "error": error_msg}, \
                    {"display": "none"}, 0, "Date Error", {'display': 'none'}, no_update, no_update
        
        if 'features' in risk_params_dict and 'enabled_features' not in risk_params_dict:
            risk_params_dict['enabled_features'] = risk_params_dict.pop('features')

        try:
            logger.info("run_backtest: Setting initial progress (1%).")
            set_progress((1, "Initializing Backtest...")) 

            logger.info("run_backtest: Calling backtest_service.run_backtest. This might be a long operation.")
            start_time = time.time()
            
            results_package = backtest_service.run_backtest(
                strategy_type=strategy_type,
                tickers=tickers_list,
                start_date=start_date_dt, 
                end_date=end_date_dt,     
                initial_capital=initial_capital, 
                strategy_params=strategy_params_dict,
                risk_params=risk_params_dict, 
                cost_params=cost_params_dict, 
                rebalancing_params=rebalancing_params_dict,
                progress_callback=set_progress 
            )

            end_time = time.time()
            logger.info(f"run_backtest: backtest_service.run_backtest finished in {end_time - start_time:.2f} seconds.")
            results_package["timestamp"] = time.time()

            if results_package.get("success"):
                logger.info(f"run_backtest: Preparing SUCCESSFUL results. Keys: {list(results_package.keys())}")
                logger.info("run_backtest: Setting final progress (100% - Complete).")
                set_progress((100, "Complete")) 
                logger.info("run_backtest: Exiting. 'running' state should show right-panel-col.")
                return results_package, {"display": "none"}, no_update, no_update, {'display': 'none'}, no_update, no_update
            else:
                error_msg = results_package.get('error', 'Unknown backtest failure')
                logger.error(f"run_backtest: Returning FAILED results: {error_msg}")
                display_error_msg = (error_msg[:47] + '...') if len(error_msg) > 50 else error_msg
                logger.info(f"run_backtest: Setting final progress (100% - Failed: {display_error_msg}).")
                set_progress((100, f"Failed: {display_error_msg}")) 
                logger.info("run_backtest: Exiting. 'running' state should show right-panel-col.")
                return results_package, {"display": "none"}, 100, f"Failed: {display_error_msg}", {'display': 'none'}, no_update, no_update

        except Exception as e:
            logger.error(f"run_backtest: Exception during execution: {e}", exc_info=True)
            error_msg = f"An unexpected error occurred: {type(e).__name__}"
            display_error_msg = (error_msg[:47] + '...') if len(error_msg) > 50 else error_msg
            logger.info(f"run_backtest: Setting final progress (100% - Error: {display_error_msg}).")
            set_progress((100, f"Error: {display_error_msg}")) 
            logger.info("run_backtest: Exiting. 'running' state should show right-panel-col.")
            return {"timestamp": time.time(), "success": False, "error": error_msg}, \
                   {"display": "none"}, 100, f"Callback Error: {display_error_msg}", {'display': 'none'}, no_update, no_update

    # --- Result Update Callbacks (Triggered by Store) ---
    @app.callback(
        [
            Output(ResultsIDs.PERFORMANCE_METRICS_CONTAINER, 'children'),
            Output(ResultsIDs.TRADE_METRICS_CONTAINER, 'children'),
            Output(ResultsIDs.TRADES_TABLE_CONTAINER, 'children'),
            Output(ResultsIDs.PORTFOLIO_CHART, 'figure'),
            Output(ResultsIDs.DRAWDOWN_CHART, 'figure'),
            Output(ResultsIDs.MONTHLY_RETURNS_HEATMAP, 'figure'),
            Output(ResultsIDs.SIGNALS_TICKER_SELECTOR, 'options'),
            Output(ResultsIDs.SIGNALS_TICKER_SELECTOR, 'value'),
            Output(ResultsIDs.RESULTS_AREA_WRAPPER, 'style'), 
            Output(ResultsIDs.RIGHT_PANEL_COLUMN, 'style', allow_duplicate=True) # ADDED: Control right panel visibility
        ],
        Input(ResultsIDs.BACKTEST_RESULTS_STORE, 'data'),
        prevent_initial_call=True
    )
    def update_results_display(results_data):
        logger.info("--- update_results_display callback triggered ---")
        if not results_data or not results_data.get('success'):
            logger.warning("--- update_results_display: results_data indicates failure or is invalid. Returning empty/default components.")
            empty_fig = create_empty_chart("No data available")
            return ([], [], html.Div("Backtest failed or no data."), 
                    empty_fig, empty_fig, empty_fig, 
                    [], None, {'display': 'none'}, {'visibility': 'hidden', 'paddingLeft': '15px'})

        metrics = results_data.get('metrics', {})
        trades_list = results_data.get('trades_data', [])
        
        perf_metrics = {k: v for k, v in metrics.items() if "Trade" not in k and "Win" not in k and "Loss" not in k and "Ratio" not in k and "Avg" not in k and "Profit Factor" not in k and "Trades" not in k}
        trade_stats = {k: v for k, v in metrics.items() if k not in perf_metrics}

        performance_metrics_children = [
            dbc.Col(create_metric_card(title, f"{value:.2f}" if isinstance(value, (int, float)) else str(value)), width=6, md=4, lg=3) 
            for title, value in perf_metrics.items()
        ] if perf_metrics else [dbc.Col(html.P("No performance metrics available."))]
        
        trade_metrics_children = [
            dbc.Col(create_metric_card(title, f"{value:.2f}" if isinstance(value, (int, float)) else str(value)), width=6, md=4, lg=3)
            for title, value in trade_stats.items()
        ] if trade_stats else [dbc.Col(html.P("No trade statistics available."))]

        trades_table_component = dash_table.DataTable(
            data=trades_list,
            columns=[{'name': i, 'id': i} for i in trades_list[0].keys()] if trades_list else [],
            style_as_list_view=True,
            style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white', 'fontWeight': 'bold'},
            style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white', 'textAlign': 'left', 'padding': '5px'},
            page_size=10,
        ) if trades_list else html.Div("No trades executed.")

        portfolio_chart_fig = pio.from_json(results_data.get('portfolio_value_chart_json')) if results_data.get('portfolio_value_chart_json') else create_empty_chart("Portfolio Value")
        drawdown_chart_fig = pio.from_json(results_data.get('drawdown_chart_json')) if results_data.get('drawdown_chart_json') else create_empty_chart("Drawdown")
        
        monthly_returns_heatmap_fig = pio.from_json(results_data.get('monthly_returns_heatmap_json')) if results_data.get('monthly_returns_heatmap_json') else create_empty_chart("Monthly Returns Heatmap")

        tickers = results_data.get('selected_tickers', [])
        ticker_options = [{'label': t, 'value': t} for t in tickers]
        ticker_value = tickers[0] if tickers else None
        
        logger.info("--- update_results_display callback successfully processed data and is returning updates. ---")
        return (performance_metrics_children, trade_metrics_children, trades_table_component,
                portfolio_chart_fig, drawdown_chart_fig, monthly_returns_heatmap_fig, 
                ticker_options, ticker_value, {'display': 'block'}, {'visibility': 'visible', 'paddingLeft': '15px'})

    logger.info("Backtest callbacks registered.")

    # --- Callback to make results panels visible ---
    @app.callback(
        Output(ResultsIDs.CENTER_PANEL_COLUMN, 'style'), # MODIFIED: Only controls center panel now
        Input('run-backtest-trigger-store', 'data'),
        prevent_initial_call=True
    )
    def toggle_results_panels_visibility(trigger_data): 
        triggered_id = ctx.triggered_id
        logger.info(f"toggle_results_panels_visibility: Triggered by {triggered_id}. trigger_data: {trigger_data}")
        if trigger_data: 
            center_style = {'display': 'block', 'paddingLeft': '15px', 'paddingRight': '15px'} 
            logger.info(f"toggle_results_panels_visibility: Applying styles - Center: {center_style}")
            return center_style # MODIFIED: Return only center_style
        logger.warning("toggle_results_panels_visibility: Condition not met or no trigger_data, preventing update.")
        raise PreventUpdate