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
        Output('backtesting_progress_bar_container', 'style', allow_duplicate=True), 
        Output('backtesting_progress_bar', 'value', allow_duplicate=True),
        Output('backtesting_progress_bar', 'label', allow_duplicate=True),
        Output("strategy_progress_bar", "style", allow_duplicate=True),
        Output('actual-results-area', 'style', allow_duplicate=True),
        Input('run-backtest-button', 'n_clicks'),
        State('strategy-dropdown', 'value'), 
        State('ticker-input', 'value'),      
        State('backtest-start-date', 'date'), 
        State('backtest-end-date', 'date'),   
        State('initial-capital-input', 'value'),
        State({'type': 'strategy-param-input', 'index': ALL}, 'value'), 
        State({'type': 'strategy-param-input', 'index': ALL}, 'id'),    
        State('risk-features-checklist', 'value'), 
        State('max-position-size', 'value'),
        State('stop-loss-type', 'value'),
        State('stop-loss-value', 'value'),
        State('take-profit-type', 'value'),
        State('take-profit-value', 'value'),
        State('max-risk-per-trade', 'value'),
        State('market-trend-lookback', 'value'),
        State('max-drawdown', 'value'), 
        State('max-daily-loss', 'value'),
        State('commission-input', 'value'),
        State('slippage-input', 'value'),
        State('rebalancing-frequency', 'value'),
        State('rebalancing-threshold', 'value'),
        background=True,
        running=[
            (Output('run-backtest-button', 'disabled'), True, False),
            (Output('backtesting_progress_bar_container', 'style'), {'display': 'block'}, {'display': 'none'}),
            (Output('backtest-status', 'children'), "Running backtest...", ""),
            (Output("strategy_progress_bar", "style"), {'display': 'none'}, no_update),
            (Output('right-panel-col', 'style', allow_duplicate=True),
             {'display': 'none', 'paddingLeft': '15px'}, 
             {'display': 'block', 'paddingLeft': '15px'})
        ],
        progress=[
            Output('backtesting_progress_bar', 'value'),
            Output('backtesting_progress_bar', 'label'),
        ],
        prevent_initial_call=True
    )
    def run_backtest(set_progress, n_clicks, strategy_type, tickers, start_date, end_date, initial_capital,
                     strategy_param_values, strategy_param_ids, 
                     selected_risk_features, 
                     max_position_size, stop_loss_type, stop_loss_value, 
                     take_profit_type, take_profit_value, max_risk_per_trade,
                     market_trend_lookback, max_drawdown, max_daily_loss,
                     commission, slippage, 
                     rebalancing_frequency, rebalancing_threshold 
                     ):
        logger.info("--- run_backtest callback: Entered. 'running' state should hide right-panel-col.") # ADDED LOG
        if not n_clicks:
            logger.warning("run_backtest triggered without click.")
            raise PreventUpdate

        ctx = dash.callback_context
        if not ctx.triggered:
            logger.warning("run_backtest triggered without context.")
            raise PreventUpdate

        logger.info(f"run_backtest: Received tickers: {tickers} (type: {type(tickers)})") # ADDED LOG CONTEXT

        if isinstance(tickers, list) and tickers:
            tickers_list = [str(t).strip() for t in tickers if t]
        elif isinstance(tickers, str) and tickers.strip():
             tickers_list = [t.strip() for t in tickers.split(',') if t.strip()]
        else:
            tickers_list = []

        if not all([strategy_type, tickers_list, start_date, end_date, initial_capital]):
            error_msg = "Missing required inputs: Strategy, Tickers, Start/End Dates, or Initial Capital."
            logger.error(f"run_backtest: Input validation failed: {error_msg}") # ADDED LOG CONTEXT
            return {"timestamp": time.time(), "success": False, "error": error_msg}, \
                   {'display': 'none'}, 0, "Input Error", {'display': 'none'}, {'display': 'none'}

        try:
            start_date_dt = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except ValueError as e:
             error_msg = f"Invalid date format: {e}. Please use YYYY-MM-DD."
             logger.error(f"run_backtest: {error_msg}") # ADDED LOG CONTEXT
             return {"timestamp": time.time(), "success": False, "error": error_msg}, \
                    {'display': 'none'}, 0, "Date Error", {'display': 'none'}, {'display': 'none'}

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
            logger.info("run_backtest: Setting initial progress (1%).") # ADDED LOG
            set_progress((1, "Initializing Backtest...")) 

            logger.info("run_backtest: Calling backtest_service.run_backtest. This might be a long operation.") # ADDED LOG
            start_time = time.time()
            
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
            logger.info(f"run_backtest: backtest_service.run_backtest finished in {end_time - start_time:.2f} seconds.") # ADDED LOG
            results_package["timestamp"] = time.time()

            if results_package.get("success"):
                logger.info(f"run_backtest: Preparing SUCCESSFUL results. Keys: {list(results_package.keys())}") # ADDED LOG
                logger.info("run_backtest: Setting final progress (100% - Complete).") # ADDED LOG
                set_progress((100, "Complete")) 
                logger.info("run_backtest: Exiting. 'running' state should show right-panel-col.") # ADDED LOG
                return results_package, {'display': 'none'}, no_update, no_update, {'display': 'none'}, {'display': 'block'}
            else:
                error_msg = results_package.get('error', 'Unknown backtest failure')
                logger.error(f"run_backtest: Returning FAILED results: {error_msg}") # ADDED LOG CONTEXT
                logger.info("run_backtest: Setting final progress (100% - Failed).") # ADDED LOG
                set_progress((100, "Failed")) 
                logger.info("run_backtest: Exiting. 'running' state should show right-panel-col.") # ADDED LOG
                return results_package, {'display': 'none'}, 0, "Failed", {'display': 'none'}, {'display': 'none'}

        except Exception as e:
            logger.error(f"run_backtest: Exception during execution: {e}", exc_info=True) # ADDED LOG CONTEXT
            error_msg = f"An unexpected error occurred: {e}"
            logger.info("run_backtest: Setting final progress (100% - Error).") # ADDED LOG
            set_progress((100, "Error")) 
            logger.info("run_backtest: Exiting. 'running' state should show right-panel-col.") # ADDED LOG
            return {"timestamp": time.time(), "success": False, "error": error_msg}, \
                   {'display': 'none'}, 0, "Callback Error", {'display': 'none'}, {'display': 'none'}

    # --- Result Update Callbacks (Triggered by Store) ---
    @app.callback(
        [
            Output('performance-metrics-container', 'children'),
            Output('trade-metrics-container', 'children'),
            Output('trades-table-container', 'children'),
            Output('portfolio-chart', 'figure'),
            Output('drawdown-chart', 'figure'),
            Output('monthly-returns-heatmap', 'figure'),
            # Output('signals-chart', 'figure'), # Deferred for now
            Output('ticker-selector', 'options'),
            Output('ticker-selector', 'value')
        ],
        Input('backtest-results-store', 'data'),
        prevent_initial_call=True
    )
    def update_results_display(results_data):
        logger.info("--- update_results_display callback triggered ---")
        if not results_data or not results_data.get('success'):
            logger.warning("--- update_results_display: results_data indicates failure or is invalid. Returning empty/default components.")
            empty_fig = create_empty_chart("No data available")
            return ([], [], html.Div("Backtest failed or no data."), 
                    empty_fig, empty_fig, empty_fig, 
                    [], None)

        metrics = results_data.get('metrics', {})
        trades_list = results_data.get('trades_data', [])
        
        # Simple split for metrics:
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
        heatmap_fig = pio.from_json(results_data.get('heatmap_json')) if results_data.get('heatmap_json') else create_empty_chart("Monthly Returns")
        
        tickers = results_data.get('selected_tickers', [])
        ticker_options = [{'label': t, 'value': t} for t in tickers]
        ticker_value = tickers[0] if tickers else None
        
        logger.info("--- update_results_display callback successfully processed data and is returning updates. ---")
        return (performance_metrics_children, trade_metrics_children, trades_table_component,
                portfolio_chart_fig, drawdown_chart_fig, heatmap_fig,
                ticker_options, ticker_value)

    logger.info("Backtest callbacks registered.")

    # --- Callback to make results panels visible ---
    @app.callback(
        [Output('center-panel-col', 'style'),
         Output('right-panel-col', 'style', allow_duplicate=True)], 
        Input('run-backtest-button', 'n_clicks'),
        prevent_initial_call=True
    )
    def toggle_results_panels_visibility(n_clicks):
        triggered_id = ctx.triggered_id
        logger.info(f"toggle_results_panels_visibility: Triggered by {triggered_id}. n_clicks: {n_clicks}") # ADDED LOG
        if n_clicks and n_clicks > 0:
            center_style = {'display': 'block', 'paddingLeft': '15px', 'paddingRight': '15px'}
            right_style = {'display': 'block', 'paddingLeft': '15px'}
            logger.info(f"toggle_results_panels_visibility: Applying styles - Center: {center_style}, Right: {right_style}") # ADDED LOG
            return center_style, right_style
        logger.warning("toggle_results_panels_visibility: Condition not met or no n_clicks, preventing update.") # ADDED LOG
        raise PreventUpdate