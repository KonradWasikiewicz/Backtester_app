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
# Import layout functions needed for the new callback
from src.ui.layouts.results_display import create_full_results_layout, create_no_results_placeholder 
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
        Input('run-backtest-button', 'n_clicks'),
        # --- Corrected State IDs ---
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
        prevent_initial_call=True
    )
    def run_backtest(n_clicks, strategy_type, tickers, start_date, end_date, initial_capital,
                     strategy_param_values, strategy_param_ids, # Updated strategy params
                     selected_risk_features, # Added risk features
                     max_position_size, stop_loss_type, stop_loss_value, # Updated risk params
                     take_profit_type, take_profit_value, max_risk_per_trade,
                     market_trend_lookback, max_drawdown, max_daily_loss,
                     commission, slippage, # Added costs
                     rebalancing_frequency, rebalancing_threshold # Added rebalancing
                     ):
        logger.info("--- run_backtest callback triggered ---") # ADDED LOG
        if not n_clicks:
            logger.warning("run_backtest triggered without click.")
            raise PreventUpdate

        # --- Input Validation and Preparation ---
        ctx = dash.callback_context
        if not ctx.triggered:
            logger.warning("run_backtest triggered without context.")
            raise PreventUpdate

        logger.info(f"Received tickers: {tickers} (type: {type(tickers)})") # Log received tickers

        # --- FIX: Handle tickers as a list ---
        # Check if tickers is a list and not empty
        if isinstance(tickers, list) and tickers:
            tickers_list = [str(t).strip() for t in tickers if t] # Ensure elements are strings and stripped
        elif isinstance(tickers, str) and tickers.strip(): # Handle case where it might still be a string (e.g., single ticker input)
             tickers_list = [t.strip() for t in tickers.split(',') if t.strip()]
        else:
            tickers_list = [] # Default to empty list if None, empty list, or empty string
        # --- END FIX ---

        # Validate required inputs
        if not all([strategy_type, tickers_list, start_date, end_date, initial_capital]):
            error_msg = "Missing required inputs: Strategy, Tickers, Start/End Dates, or Initial Capital."
            logger.error(f"Input validation failed: {error_msg}")
            return {"timestamp": time.time(), "success": False, "error": error_msg}

        # --- Parameter Gathering and Cleaning ---
        # Example: Convert dates
        start_date_dt = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        end_date_dt = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        # Example: Map strategy params
        strategy_params_dict = {pid['index']: val for pid, val in zip(strategy_param_ids, strategy_param_values)}
        # Example: Build risk params dict
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
        # Example: Build trading costs dict
        trading_costs_dict = {
            'commission_per_trade': commission,
            'slippage_per_trade': slippage
        }
        # Example: Build rebalancing dict
        rebalancing_params_dict = {
            'frequency': rebalancing_frequency,
            'threshold': rebalancing_threshold
        }

        try:
            logger.info("Starting backtest execution...")
            start_time = time.time()

            # Run the backtest using the service
            results_package = backtest_service.run_backtest(
                strategy_type=strategy_type,
                tickers=tickers_list, # Use the cleaned list
                start_date=start_date_dt, # Use the datetime object
                end_date=end_date_dt,   # Use the datetime object
                initial_capital=initial_capital,
                strategy_params=strategy_params_dict, # FIX: Use the correct dict variable
                risk_params=risk_params_dict,         # FIX: Use the correct dict variable
                cost_params=trading_costs_dict,
                rebalancing_params=rebalancing_params_dict
            )

            end_time = time.time()
            logger.info(f"Backtest execution finished in {end_time - start_time:.2f} seconds.")

            # --- Store results (success or failure) ---
            if results_package.get("success"):
                # Prepare data for the store
                store_output = {
                    "timestamp": time.time(),
                    "success": True,
                    "metrics": results_package.get("metrics"),
                    "trades_data": results_package.get("trades_data"),
                    "portfolio_value_chart_json": results_package.get("portfolio_value_chart_json"),
                    "portfolio_returns_chart_json": results_package.get("portfolio_returns_chart_json"),
                    "drawdown_chart_json": results_package.get("drawdown_chart_json"),
                    "heatmap_json": results_package.get("heatmap_json"),
                    # Store selected tickers for the selector
                    "selected_tickers": tickers_list
                }
                logger.info("--- run_backtest: Storing SUCCESSFUL results ---") # ADDED LOG
                return store_output
            else:
                error_msg = results_package.get("error", "Unknown error during backtest execution.")
                logger.error(f"Backtest failed: {error_msg}")
                logger.info("--- run_backtest: Storing FAILED results ---") # ADDED LOG
                return {"timestamp": time.time(), "success": False, "error": error_msg}

        except Exception as e:
            logger.error(f"Exception during backtest execution callback: {e}", exc_info=True)
            error_msg = f"An unexpected error occurred in the callback: {e}"
            logger.error(traceback.format_exc())
            logger.info("--- run_backtest: Storing EXCEPTION results ---") # ADDED LOG
            return {"timestamp": time.time(), "success": False, "error": error_msg}

    # --- Result Update Callbacks (Triggered by Store) ---

    # Update Metrics Card
    @app.callback(
        Output('metrics-summary-container', 'children'),
        Input('backtest-results-store', 'data'),
        prevent_initial_call=True
    )
    def update_metrics_display(store_data):
        logger.info("--- update_metrics_display callback triggered ---") # ADDED LOG
        if not store_data or not store_data.get("success"):
            error = store_data.get("error", "Backtest failed or not run yet.") if store_data else "Run a backtest to see metrics."
            logger.warning(f"Metrics display update skipped or failed: {error}")
            logger.info("--- update_metrics_display: Returning empty list ---") # ADDED LOG
            return [] 

        try:
            metrics = store_data.get("metrics")
            if not metrics:
                 logger.warning("No metrics data found in store for display.")
                 logger.info("--- update_metrics_display: Returning empty list (no metrics) ---") # ADDED LOG
                 return [] 

            logger.info(f"Updating metrics display with {len(metrics)} metrics.")
            # Define the order and labels for metrics
            metric_order = [
                ("starting-balance", "Starting Balance", "fas fa-coins"),
                ("ending-balance", "Ending Balance", "fas fa-wallet"),
                ("total-return", "Total Return (%)", "fas fa-chart-line"),
                ("cagr", "CAGR (%)", "fas fa-calendar-alt"),
                ("sharpe", "Sharpe Ratio", "fas fa-chart-pie"),
                ("max-drawdown", "Max Drawdown (%)", "fas fa-arrow-down"),
                ("calmar-ratio", "Calmar Ratio", "fas fa-balance-scale"),
                ("recovery-factor", "Recovery Factor", "fas fa-undo"),
                ("trades-count", "Total Trades", "fas fa-exchange-alt"),
                ("win-rate", "Win Rate (%)", "fas fa-trophy"),
                ("profit-factor", "Profit Factor", "fas fa-plus-circle"),
                ("avg-trade", "Avg Trade (%)", "fas fa-percentage"),
                ("signals-generated", "Signals Generated", "fas fa-signal"),
                ("rejected-signals-total", "Rejected Signals", "fas fa-ban")
            ]

            cards = []
            for key, label, icon in metric_order:
                value = metrics.get(key)
                if value is not None:
                    # Format value based on type (e.g., percentage, currency)
                    if isinstance(value, (int, float)):
                        if "balance" in key:
                            formatted_value = f"${value:,.2f}"
                        elif "%" in label or key in ["cagr", "max-drawdown", "win-rate", "avg-trade"]:
                            formatted_value = f"{value:.2f}%"
                        elif key in ["sharpe", "calmar-ratio", "profit-factor", "recovery-factor"]:
                            formatted_value = f"{value:.2f}"
                        else:
                            formatted_value = f"{value:,}" # Integer formatting
                    else:
                        formatted_value = str(value) # Fallback for other types

                    cards.append(create_metric_card(label, formatted_value, icon))
                else:
                    logger.warning(f"Metric '{key}' not found in results.")
                    cards.append(create_metric_card(label, "N/A", icon)) # Show N/A if metric missing

            logger.info("--- update_metrics_display: Returning metric cards ---") # ADDED LOG
            return cards
        except Exception as e:
            logger.error(f"Error updating metrics display: {e}", exc_info=True)
            alert = dbc.Alert(f"Error displaying metrics: {e}", color="danger")
            logger.info("--- update_metrics_display: Returning error alert ---") # ADDED LOG
            return [alert]


    # Update Portfolio Chart
    @app.callback(
        Output('portfolio-chart', 'figure'),
        Input('backtest-results-store', 'data'),
        Input('btn-chart-value', 'n_clicks'),
        Input('btn-chart-returns', 'n_clicks'),
        prevent_initial_call=True
    )
    def update_portfolio_chart(store_data, n_value, n_returns):
        logger.info("--- update_portfolio_chart callback triggered ---") # ADDED LOG
        triggered_id = ctx.triggered_id if ctx.triggered_id else 'btn-chart-value'
        chart_type = 'value'
        json_key = 'portfolio_value_chart_json' # Key for value chart JSON
        if triggered_id == 'btn-chart-returns':
            chart_type = 'returns'
            json_key = 'portfolio_returns_chart_json' # Key for returns chart JSON

        logger.info(f"Selected portfolio chart type: {chart_type}")

        if not store_data or not store_data.get("success"):
            logger.warning("Portfolio chart update skipped: No successful backtest data in store.")
            empty_fig = {'data': [], 'layout': {'template': CHART_THEME, 'title': 'Run Backtest for Portfolio Chart'}}
            logger.info(f"--- update_portfolio_chart ({chart_type}): Returning empty figure (no data) ---") # ADDED LOG
            return empty_fig

        try:
            chart_json = store_data.get(json_key)

            if not chart_json:
                 logger.warning(f"No portfolio chart JSON found in store for key '{json_key}'.")
                 empty_fig = {'data': [], 'layout': {'template': CHART_THEME, 'title': f'No {chart_type} chart data available.'}}
                 logger.info(f"--- update_portfolio_chart ({chart_type}): Returning empty figure (no JSON) ---") # ADDED LOG
                 return empty_fig

            fig = pio.from_json(chart_json)
            logger.info(f"--- update_portfolio_chart ({chart_type}): Returning figure from JSON ---") # ADDED LOG
            return fig

        except Exception as e:
            logger.error(f"Error updating portfolio chart ({chart_type}): {e}", exc_info=True)
            error_fig = {'data': [], 'layout': {'template': CHART_THEME, 'title': f'Error: {e}'}}
            logger.info(f"--- update_portfolio_chart ({chart_type}): Returning error figure ---") # ADDED LOG
            return error_fig

    # --- ADDED: Callback to update button outlines ---
    @app.callback(
        Output('btn-chart-value', 'outline'),
        Output('btn-chart-returns', 'outline'),
        Input('btn-chart-value', 'n_clicks'),
        Input('btn-chart-returns', 'n_clicks'),
        prevent_initial_call=True
    )
    def update_portfolio_button_styles(n_value, n_returns):
        # Minimal logging as this is less critical
        # logger.debug("--- update_portfolio_button_styles triggered ---")
        triggered_id = ctx.triggered_id if ctx.triggered_id else 'btn-chart-value'
        if triggered_id == 'btn-chart-returns':
            return True, False # Value outlined, Returns filled
        else: # Default or Value clicked
            return False, True # Value filled, Returns outlined

    # --- ADDED: Update Drawdown Chart ---
    @app.callback(
        Output('drawdown-chart', 'figure'),
        Input('backtest-results-store', 'data'),
        prevent_initial_call=True
    )
    def update_drawdown_chart(store_data):
        logger.info("--- update_drawdown_chart callback triggered ---") # ADDED LOG
        if not store_data or not store_data.get("success"):
            logger.warning("Drawdown chart update skipped: No successful backtest data.")
            empty_fig = {'data': [], 'layout': {'template': CHART_THEME, 'title': 'Run Backtest for Drawdown Chart'}}
            logger.info("--- update_drawdown_chart: Returning empty figure (no data) ---") # ADDED LOG
            return empty_fig

        try:
            drawdown_chart_json = store_data.get("drawdown_chart_json")
            if not drawdown_chart_json:
                logger.warning("No drawdown chart JSON found in store.")
                empty_fig = {'data': [], 'layout': {'template': CHART_THEME, 'title': 'No drawdown data available.'}}
                logger.info("--- update_drawdown_chart: Returning empty figure (no JSON) ---") # ADDED LOG
                return empty_fig

            fig = pio.from_json(drawdown_chart_json)
            logger.info("--- update_drawdown_chart: Returning figure from JSON ---") # ADDED LOG
            return fig
        except Exception as e:
            logger.error(f"Error updating drawdown chart: {e}", exc_info=True)
            error_fig = {'data': [], 'layout': {'template': CHART_THEME, 'title': f'Error: {e}'}}
            logger.info("--- update_drawdown_chart: Returning error figure ---") # ADDED LOG
            return error_fig


    # Update Monthly Returns Heatmap
    @app.callback(
        Output('monthly-returns-heatmap', 'figure'),
        Input('backtest-results-store', 'data'),
        prevent_initial_call=True
    )
    def update_heatmap(store_data):
        logger.info("--- update_heatmap callback triggered ---") # ADDED LOG
        if not store_data or not store_data.get("success"):
            logger.warning("Heatmap update skipped: No successful backtest data in store.")
            empty_fig = {'data': [], 'layout': {'template': CHART_THEME, 'title': 'Run Backtest for Heatmap'}}
            logger.info("--- update_heatmap: Returning empty figure (no data) ---") # ADDED LOG
            return empty_fig

        try:
            heatmap_json = store_data.get("heatmap_json")
            if not heatmap_json:
                logger.warning("No heatmap JSON found in store.")
                empty_fig = {'data': [], 'layout': {'template': CHART_THEME, 'title': 'No returns data for heatmap.'}}
                logger.info("--- update_heatmap: Returning empty figure (no JSON) ---") # ADDED LOG
                return empty_fig

            fig = pio.from_json(heatmap_json)
            logger.info("--- update_heatmap: Returning figure from JSON ---") # ADDED LOG
            return fig
        except Exception as e:
            logger.error(f"Error updating heatmap: {e}", exc_info=True)
            error_fig = {'data': [], 'layout': {'template': CHART_THEME, 'title': f'Error: {e}'}}
            logger.info("--- update_heatmap: Returning error figure ---") # ADDED LOG
            return error_fig

    # Update Signals Chart (needs ticker selection)
    # --- ADD Ticker Selector Update Callback ---
    @app.callback(
        Output('ticker-selector', 'options'),
        Output('ticker-selector', 'value'),
        Input('backtest-results-store', 'data'),
        prevent_initial_call=True
    )
    def update_ticker_selector(store_data):
        logger.info("--- update_ticker_selector callback triggered ---") # ADDED LOG
        if store_data and store_data.get("success"):
            selected_tickers = store_data.get("selected_tickers", [])
            if isinstance(selected_tickers, str):
                 selected_tickers = [selected_tickers] # Ensure it's a list

            if selected_tickers:
                string_tickers = [str(t) for t in selected_tickers] # Ensure strings
                options = [{'label': t, 'value': t} for t in string_tickers]
                logger.info(f"Populating ticker selector with: {string_tickers}")
                default_value = options[0]['value'] if options else None
                logger.info("--- update_ticker_selector: Returning options and value ---") # ADDED LOG
                return options, default_value
            else:
                 logger.warning("No tickers found in successful backtest results for selector.")
                 logger.info("--- update_ticker_selector: Returning empty options (no tickers) ---") # ADDED LOG
                 return [], None
        logger.debug("No successful backtest data, clearing ticker selector.")
        logger.info("--- update_ticker_selector: Returning empty options (no success data) ---") # ADDED LOG
        return [], None

    @app.callback(
        Output('signals-chart', 'figure'),
        Input('backtest-results-store', 'data'),
        Input('ticker-selector', 'value'),
        prevent_initial_call=True
    )
    def update_signals_chart(store_data, selected_ticker):
        logger.info(f"--- update_signals_chart callback triggered. Ticker: {selected_ticker} ---") # ADDED LOG
        # Check store_data first
        if not store_data or not store_data.get("success"):
             logger.warning("Signals chart update skipped: No successful backtest data.")
             empty_fig = {'data': [], 'layout': {'template': CHART_THEME, 'title': 'Run Backtest to View Signals'}}
             logger.info("--- update_signals_chart: Returning empty figure (no data) ---") # ADDED LOG
             return empty_fig

        # Check selected_ticker
        if not selected_ticker:
             logger.debug("Signals chart update skipped: No ticker selected.")
             empty_fig = {'data': [], 'layout': {'template': CHART_THEME, 'title': 'Select a Ticker to View Signals'}}
             logger.info("--- update_signals_chart: Returning empty figure (no ticker) ---") # ADDED LOG
             return empty_fig

        ticker = selected_ticker
        try:
            # Re-calling service method to generate the figure dynamically
            # This assumes backtest_service holds the necessary data from the last run
            # We need to ensure backtest_service has the results loaded.
            # A better approach might be to store signals chart data per ticker in the store.
            # For now, let's assume get_signals_chart can access the latest results.
            fig = backtest_service.get_signals_chart(ticker=ticker)

            if fig:
                logger.info(f"--- update_signals_chart: Returning figure for {ticker} ---") # ADDED LOG
                return fig
            else:
                logger.warning(f"Could not generate signal chart for {ticker}.")
                empty_fig = {'data': [], 'layout': {'template': CHART_THEME, 'title': f'Could not generate signal chart for {ticker}'}}
                logger.info(f"--- update_signals_chart: Returning empty figure (generation failed) for {ticker} ---") # ADDED LOG
                return empty_fig
        except Exception as e:
            logger.error(f"Error updating signals chart for {ticker}: {e}", exc_info=True)
            error_fig = {'data': [], 'layout': {'template': CHART_THEME, 'title': f'Error: {e}'}}
            logger.info(f"--- update_signals_chart: Returning error figure for {ticker} ---") # ADDED LOG
            return error_fig


    # --- MODIFIED Trades Table Callback ---
    @app.callback(
        Output('trades-table-container', 'children'), # Output to the container Div
        Input('backtest-results-store', 'data'),
        prevent_initial_call=True
    )
    def update_trades_table(store_data):
        logger.info("--- update_trades_table callback triggered ---") # ADDED LOG
        if not store_data or not store_data.get("success"):
            logger.warning("Trades table update skipped: No successful backtest data.")
            placeholder = html.Div("Run a backtest to view trade history.")
            logger.info("--- update_trades_table: Returning placeholder (no data) ---") # ADDED LOG
            return placeholder

        try:
            trades_data = store_data.get("trades_data")
            if not trades_data:
                logger.warning("No trades data found in store.")
                no_trades_msg = html.Div("No trades were executed in this backtest.")
                logger.info("--- update_trades_table: Returning 'no trades' message ---") # ADDED LOG
                return no_trades_msg

            logger.info(f"Updating trades table with {len(trades_data)} trades.")

            # Convert list of dicts to DataFrame for easier handling if needed
            trades_df = pd.DataFrame(trades_data)

            # Define columns for the DataTable
            columns = [
                {"name": "Entry Date", "id": "entry_date"},
                {"name": "Exit Date", "id": "exit_date"},
                {"name": "Ticker", "id": "ticker"},
                {"name": "Direction", "id": "direction"},
                {"name": "Entry Price", "id": "entry_price", "type": "numeric", "format": dash_table.Format.Format(precision=2, scheme=dash_table.Format.Scheme.fixed)},
                {"name": "Exit Price", "id": "exit_price", "type": "numeric", "format": dash_table.Format.Format(precision=2, scheme=dash_table.Format.Scheme.fixed)},
                {"name": "Size", "id": "size", "type": "numeric", "format": dash_table.Format.Format(precision=4, scheme=dash_table.Format.Scheme.fixed)},
                {"name": "PnL", "id": "pnl", "type": "numeric", "format": dash_table.Format.Format(precision=2, scheme=dash_table.Format.Scheme.fixed)},
                {"name": "Return (%)", "id": "return_pct", "type": "numeric", "format": dash_table.Format.Format(precision=2, scheme=dash_table.Format.Scheme.percentage)},
                {"name": "Duration", "id": "duration"},
                {"name": "Stop Loss Hit", "id": "stop_loss_hit"},
                {"name": "Take Profit Hit", "id": "take_profit_hit"}
            ]

            # Convert DataFrame back to list of dicts for DataTable
            data_for_table = trades_df.to_dict('records')

            table = dash_table.DataTable(
                id='trades-table',
                columns=columns,
                data=data_for_table,
                page_size=10,  # Show 10 rows per page
                style_table={'overflowX': 'auto'},
                style_header={
                    'backgroundColor': 'rgb(30, 30, 30)',
                    'color': 'white',
                    'fontWeight': 'bold'
                },
                style_data={
                    'backgroundColor': 'rgb(50, 50, 50)',
                    'color': 'white'
                },
                style_cell={
                    'textAlign': 'left',
                    'padding': '5px',
                    'minWidth': '100px', 'width': '150px', 'maxWidth': '200px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                },
                style_data_conditional=[
                    {
                        'if': {'column_id': 'pnl', 'filter_query': '{pnl} > 0'},
                        'color': '#4CAF50' # Green for positive PnL
                    },
                    {
                        'if': {'column_id': 'pnl', 'filter_query': '{pnl} < 0'},
                        'color': '#F44336' # Red for negative PnL
                    },
                     {
                        'if': {'column_id': 'return_pct', 'filter_query': '{return_pct} > 0'},
                        'color': '#4CAF50' # Green for positive return
                    },
                    {
                        'if': {'column_id': 'return_pct', 'filter_query': '{return_pct} < 0'},
                        'color': '#F44336' # Red for negative return
                    }
                ],
                sort_action="native", # Enable sorting
                filter_action="native", # Enable filtering
                export_format="csv", # Allow exporting data
            )
            logger.info("--- update_trades_table: Returning DataTable ---") # ADDED LOG
            return table

        except Exception as e:
            logger.error(f"Error updating trades table: {e}", exc_info=True)
            alert = dbc.Alert(f"Error displaying trades table: {e}", color="danger")
            logger.info("--- update_trades_table: Returning error alert ---") # ADDED LOG
            return alert


    # --- Main Loader Callback ---
    # Keep this as is for now
    app.clientside_callback(
        ClientsideFunction(
            namespace='clientside',
            function_name='updateMainLoader'
        ),
        Output('loading-overlay', 'style'),
        # Use the IDs of the dcc.Loading components defined in results_display.py
        # Input('metrics-summary-container', 'loading_state'), # metrics-summary-container is a Row, doesn't have loading_state
        Input('portfolio-chart-loading', 'loading_state'),
        Input('drawdown-chart-loading', 'loading_state'),
        Input('heatmap-chart-loading', 'loading_state'),
        prevent_initial_call=True
    )

    logger.info("Backtest callbacks registered.")