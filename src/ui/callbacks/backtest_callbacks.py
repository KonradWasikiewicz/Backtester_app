import logging
import time
import traceback
from datetime import datetime
import pandas as pd
# Import ALL for pattern-matching callbacks
from dash import Dash, dcc, html, Input, Output, State, callback, no_update, ctx, ClientsideFunction, ALL
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

# Import services and components
from src.services.backtest_service import BacktestService
from src.ui.components import create_metric_card 
from src.visualization.chart_utils import create_empty_chart 
# Corrected import: Use BacktestVisualizer instead of Visualizer
from src.visualization.visualizer import BacktestVisualizer 
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
        if not n_clicks:
            raise PreventUpdate # Use PreventUpdate instead of returning error dict

        triggered_id = ctx.triggered_id
        logger.debug(f"Run backtest triggered by: {triggered_id}")
        if triggered_id != 'run-backtest-button':
             logger.debug("Triggered by something else, preventing update.")
             raise PreventUpdate

        if not all([strategy_type, tickers, start_date, end_date, initial_capital]):
            logger.warning("Run backtest triggered with missing core inputs.")
            # Return error state for the store
            return {"timestamp": time.time(), "success": False, "error": "Missing required configuration (Strategy, Tickers, Dates, Capital)."}

        try:
            # --- Parameter Aggregation ---
            # Strategy Parameters (using pattern-matching results)
            strategy_params = {}
            if strategy_param_values and strategy_param_ids:
                strategy_params = {param_id['index']: value for param_id, value in zip(strategy_param_ids, strategy_param_values) if value is not None}

            # Risk Parameters (only include if the feature was selected)
            risk_params = {}
            selected_risk_features = selected_risk_features or [] # Ensure it's a list
            if 'position_sizing' in selected_risk_features and max_position_size is not None:
                risk_params['max_position_size'] = max_position_size / 100.0
            if 'stop_loss' in selected_risk_features and stop_loss_value is not None and stop_loss_type:
                risk_params['stop_loss'] = {'type': stop_loss_type, 'value': stop_loss_value / 100.0}
            if 'take_profit' in selected_risk_features and take_profit_value is not None and take_profit_type:
                risk_params['take_profit'] = {'type': take_profit_type, 'value': take_profit_value / 100.0}
            if 'risk_per_trade' in selected_risk_features and max_risk_per_trade is not None:
                risk_params['max_risk_per_trade'] = max_risk_per_trade / 100.0
            if 'market_filter' in selected_risk_features and market_trend_lookback is not None:
                risk_params['market_filter'] = {'lookback': market_trend_lookback}
            if 'drawdown_protection' in selected_risk_features:
                if max_drawdown is not None:
                    risk_params['max_drawdown'] = max_drawdown / 100.0
                if max_daily_loss is not None:
                    risk_params['max_daily_loss'] = max_daily_loss / 100.0

            # Trading Costs
            cost_params = {}
            if commission is not None:
                cost_params['commission_pct'] = commission / 100.0
            if slippage is not None:
                cost_params['slippage_pct'] = slippage / 100.0

            # Rebalancing Rules
            rebalancing_params = {}
            if rebalancing_frequency != 'N' and rebalancing_frequency is not None: # Check if not 'None'
                rebalancing_params['frequency'] = rebalancing_frequency
                if rebalancing_threshold is not None:
                     rebalancing_params['threshold_pct'] = rebalancing_threshold / 100.0 # Convert to decimal

            # Clean initial capital (remove spaces, convert to float)
            try:
                cleaned_capital = float(str(initial_capital).replace(" ", "").replace(",", ""))
            except (ValueError, TypeError):
                logger.warning(f"Invalid initial capital format: {initial_capital}. Using default 100,000.")
                cleaned_capital = 100000.0

            logger.info(f"Running backtest with: Strategy={strategy_type}, Tickers={tickers}, Start={start_date}, End={end_date}, Capital={cleaned_capital}, Strategy Params={strategy_params}, Risk Params={risk_params}, Costs={cost_params}, Rebalancing={rebalancing_params}")

            # --- Run backtest via service ---
            # The service now returns the results directly if successful
            results_package = backtest_service.run_backtest(
                strategy_type=strategy_type,
                tickers=tickers,
                start_date=start_date, # Already string
                end_date=end_date,     # Already string
                initial_capital=cleaned_capital,
                strategy_params=strategy_params,
                risk_params=risk_params,
                cost_params=cost_params,
                rebalancing_params=rebalancing_params
            )

            # --- Store results (success or failure) ---
            if results_package.get("success"):
                logger.info("Backtest completed successfully. Preparing results for store.")
                # Fetch all results needed for the UI *here*
                metrics = backtest_service.get_performance_metrics()
                portfolio_chart_fig = backtest_service.get_portfolio_chart(chart_type='cumulative_returns') # Default type
                heatmap_fig = backtest_service.get_monthly_returns_heatmap()
                trades_data = backtest_service.get_trades_table_data()
                # Signals data needs a ticker, handle in its own callback or pass all signals
                # For simplicity, let's pass the signals DataFrame if available
                # signals_df = backtest_service.get_signals_data() # Assuming this method exists
                signals_data = backtest_service.current_signals # Access the attribute directly

                # Convert figures to JSON for storage
                portfolio_chart_json = portfolio_chart_fig.to_json() if portfolio_chart_fig else None
                heatmap_json = heatmap_fig.to_json() if heatmap_fig else None
                # Convert signals data (dict of DataFrames) to JSON
                signals_json = None
                if signals_data:
                    signals_json = {ticker: df.to_json(orient='split', date_format='iso') 
                                    for ticker, df in signals_data.items()}

                store_output = {
                    "timestamp": time.time(),
                    "success": True,
                    "metrics": metrics,
                    "portfolio_chart_json": portfolio_chart_json, # Store JSON
                    "heatmap_json": heatmap_json,             # Store JSON
                    "trades_data": trades_data,               # Store list of dicts
                    "signals_json": signals_json,             # Store JSON representation of signals dict
                    "selected_tickers": tickers               # Store tickers for signal chart context
                }
                logger.debug(f"Storing successful results: Metrics keys: {metrics.keys() if metrics else 'None'}, Trades: {len(trades_data)} rows")
                return store_output
            else:
                error_msg = results_package.get("error", "Unknown error during backtest execution.")
                logger.error(f"Backtest failed: {error_msg}")
                return {"timestamp": time.time(), "success": False, "error": error_msg}

        except Exception as e:
            logger.error(f"Exception during backtest execution callback: {e}", exc_info=True)
            error_msg = f"An unexpected error occurred in the callback: {e}"
            # Ensure traceback is logged
            logger.error(traceback.format_exc())
            return {"timestamp": time.time(), "success": False, "error": error_msg}

    # --- Result Update Callbacks (Triggered by Store) ---

    # Update Metrics Card
    @app.callback(
        Output('metrics-summary-container', 'children'),
        Input('backtest-results-store', 'data'),
        prevent_initial_call=True
    )
    def update_metrics_display(store_data):
        logger.debug("update_metrics_display triggered.")
        if not store_data or not store_data.get("success"):
            # Handle backtest failure or initial state - maybe show an error message card
            error = store_data.get("error", "Backtest failed or not run yet.") if store_data else "Run a backtest to see metrics."
            # You might want a specific component for errors, or return an empty list
            logger.warning(f"Metrics display update skipped or failed: {error}")
            return [html.Div(f"Error: {error}", className="alert alert-danger")] 
            
        try:
            metrics = store_data.get("metrics") # Get metrics from store
            if not metrics:
                 logger.warning("No metrics data found in store.")
                 return [html.Div("No metrics data available in results.", className="alert alert-warning")]
                 
            logger.info(f"Updating metrics display with {len(metrics)} metrics.")
            # Create metric cards based on the retrieved metrics
            # This assumes create_metric_card exists and works as expected
            cards = [
                # Strategy Overview
                create_metric_card("Starting Balance", metrics.get("starting-balance", "N/A"), "bi bi-piggy-bank"),
                create_metric_card("Ending Balance", metrics.get("ending-balance", "N/A"), "bi bi-cash-coin"),
                create_metric_card("Total Return", metrics.get("total-return", "N/A"), "bi bi-graph-up-arrow"),
                create_metric_card("CAGR", metrics.get("cagr", "N/A"), "bi bi-calendar-event"),
                create_metric_card("Sharpe Ratio", metrics.get("sharpe", "N/A"), "bi bi-calculator"),
                create_metric_card("Max Drawdown", metrics.get("max-drawdown", "N/A"), "bi bi-graph-down-arrow", danger=True),
                create_metric_card("Calmar Ratio", metrics.get("calmar-ratio", "N/A"), "bi bi-speedometer2"),
                create_metric_card("Recovery Factor", metrics.get("recovery-factor", "N/A"), "bi bi-arrow-clockwise"),
                
                # Trades Overview
                create_metric_card("Signals Generated", metrics.get("signals-generated", "N/A"), "bi bi-bell"),
                create_metric_card("Trades Executed", metrics.get("trades-count", "N/A"), "bi bi-arrow-left-right"),
                create_metric_card("Win Rate", metrics.get("win-rate", "N/A"), "bi bi-trophy"),
                create_metric_card("Profit Factor", metrics.get("profit-factor", "N/A"), "bi bi-percent"),
                
                # Rejected Signals Overview (Example - adjust as needed)
                create_metric_card("Rejected Signals (Total)", metrics.get("rejected-signals-total", "N/A"), "bi bi-sign-stop", warning=True),
                # Add more rejected signal cards if desired...
            ]
            return cards
        except Exception as e:
            logger.error(f"Error updating metrics display: {e}", exc_info=True)
            return [html.Div(f"Error displaying metrics: {e}", className="alert alert-danger")]

    # Update Portfolio Chart
    @app.callback(
        Output('portfolio-chart', 'figure'),
        Input('backtest-results-store', 'data'),
        # Input('portfolio-chart-type-selector', 'value'), # Removed: Chart type selection logic needs rework if figures aren't pre-generated per type
        prevent_initial_call=True
    )
    def update_portfolio_chart(store_data): # Removed chart_type input
        logger.debug(f"update_portfolio_chart triggered.")
        if not store_data or not store_data.get("success"):
            logger.warning("Portfolio chart update skipped: No successful backtest data in store.")
            return create_empty_chart("Run Backtest for Portfolio Chart").figure 
            
        try:
            # --- Load Figure from Store --- 
            # The run_backtest callback now stores the generated figure JSON.
            portfolio_chart_json = store_data.get("portfolio_chart_json")
            if not portfolio_chart_json:
                 logger.warning("No portfolio chart JSON found in store.")
                 return create_empty_chart("No portfolio chart data available.").figure

            # Recreate the figure from the stored JSON
            # Need to import pandas as pd and plotly.graph_objects as go if not already done at the top
            import pandas as pd
            import plotly.graph_objects as go
            fig = go.Figure(pd.read_json(portfolio_chart_json, orient='split'))

            # --- Removed regeneration logic --- 

            logger.info(f"Updating portfolio chart from stored JSON.")
            return fig if fig else create_empty_chart(f"Could not load portfolio chart from stored data").figure

        except Exception as e:
            logger.error(f"Error updating portfolio chart: {e}", exc_info=True)
            # Need to import create_empty_chart if not already done at the top
            from src.visualization.chart_utils import create_empty_chart
            return create_empty_chart(f"Error: {e}").figure

    # Update Monthly Returns Heatmap
    @app.callback(
        Output('monthly-returns-heatmap', 'figure'),
        Input('backtest-results-store', 'data'),
        prevent_initial_call=True
    )
    def update_heatmap(store_data):
        logger.debug("update_heatmap triggered.")
        if not store_data or not store_data.get("success"):
            logger.warning("Heatmap update skipped: No successful backtest data in store.")
            # Use create_empty_chart and access its figure attribute
            return create_empty_chart("Run Backtest for Heatmap").figure 
            
        try:
            heatmap_json = store_data.get("heatmap_json") # Get JSON from store
            if not heatmap_json:
                logger.warning("No heatmap JSON found in store.")
                return create_empty_chart("No returns data for heatmap.").figure

            fig = go.Figure(go.Figure(pd.read_json(heatmap_json, orient='split'))) # Recreate figure from JSON
            logger.info("Updating monthly returns heatmap.")
            return fig
        except Exception as e:
            logger.error(f"Error updating heatmap: {e}", exc_info=True)
            # Use create_empty_chart for error display
            return create_empty_chart(f"Error: {e}").figure

    # Update Signals Chart (needs ticker selection)
    @app.callback(
        Output('signals-chart', 'figure'),
        Input('backtest-results-store', 'data'),
        Input('instrument-selector', 'value'), # Keep ticker selector input
        prevent_initial_call=True
    )
    def update_signals_chart(store_data, selected_tickers):
        logger.debug(f"update_signals_chart triggered. Selected tickers: {selected_tickers}")
        if not store_data or not store_data.get("success"):
             logger.warning("Signals chart update skipped: No successful backtest data.")
             # Use create_empty_chart and access its figure attribute
             return create_empty_chart("Run Backtest to View Signals").figure 

        if not selected_tickers or len(selected_tickers) != 1:
             logger.debug("Signals chart update skipped: Need exactly one ticker.")
             # Use create_empty_chart and access its figure attribute
             return create_empty_chart("Select One Ticker to View Signals").figure 
             
        ticker = selected_tickers[0]
        try:
            # --- Get signals data from store ---
            signals_json_dict = store_data.get("signals_json")
            if not signals_json_dict or ticker not in signals_json_dict:
                logger.warning(f"No signals JSON data found in store for ticker {ticker}.")
                return create_empty_chart(f"No signal data available for {ticker}").figure

            signals_json = signals_json_dict[ticker]
            signals_df = pd.read_json(signals_json, orient='split')
            if signals_df.empty:
                 logger.warning(f"Signals data for {ticker} is empty after JSON load.")
                 return create_empty_chart(f"Signal data is empty for {ticker}").figure

            # --- Generate chart using Visualizer ---
            # Re-calling service method - assumes service still holds necessary data
            # This is less ideal than passing all needed data via the store, but simpler for now.
            fig = backtest_service.get_signals_chart(ticker=ticker)

            logger.info(f"Updating signals chart for {ticker}.")
            return fig if fig else create_empty_chart(f"Could not generate signal chart for {ticker}").figure
        except Exception as e:
            logger.error(f"Error updating signals chart for {ticker}: {e}", exc_info=True)
            # Use create_empty_chart for error display
            return create_empty_chart(f"Error: {e}").figure

    # Update Trades Table
    @app.callback(
        Output('trades-table', 'data'),
        Output('trades-table', 'tooltip_data'), # Add tooltip output
        Input('backtest-results-store', 'data'),
        prevent_initial_call=True
    )
    def update_trades_table(store_data):
        logger.debug("update_trades_table triggered.")
        if not store_data or not store_data.get("success"):
            logger.warning("Trades table update skipped: No successful backtest data.")
            return [], [] # Return empty data and tooltips
            
        try:
            trades_data = store_data.get("trades_data") # Get trades from store
            if trades_data is None: # Check for None explicitly
                logger.warning("No trades data found in store.")
                return [], []

            logger.info(f"Updating trades table with {len(trades_data)} trades.")
            # Prepare tooltip data (example: show exit reason)
            tooltip_data = []
            if trades_data:
                 tooltip_data = [
                    {
                        # Ensure keys match columns in trades_data exactly
                        column: {'value': str(row.get(column, 'N/A')), 'type': 'markdown'}
                        for column in row # Iterate through keys in the row dict
                    } for row in trades_data
                 ]
                 # Example specific tooltip for profit/loss and reason:
                 tooltip_data = [
                    {
                        'profit_loss_pct': {'value': f"PnL: {row.get('profit_loss_pct', 0):.2f}%", 'type': 'markdown'},
                        'exit_reason': {'value': f"Exit: {row.get('exit_reason', 'N/A')}", 'type': 'markdown'}
                        # Add more tooltips per column if needed
                    } for row in trades_data
                 ]


            return trades_data, tooltip_data
        except Exception as e:
            logger.error(f"Error updating trades table: {e}", exc_info=True)
            return [], [] # Return empty on error

    # --- Main Loader Callback ---
    # Controls the visibility of the main loading overlay
    app.clientside_callback(
        ClientsideFunction(
            namespace='clientside',
            function_name='updateMainLoader'
        ),
        Output('loading-overlay', 'style'),
        # Inputs: loading_state of all components within the results section
        Input('metrics-summary-loader', 'loading_state'),
        Input('portfolio-chart-loader', 'loading_state'),
        Input('monthly-returns-heatmap-loader', 'loading_state'),
        Input('signals-chart-loader', 'loading_state'),
        Input('trades-table-loader', 'loading_state'),
        prevent_initial_call=True
    )

    logger.info("Backtest callbacks registered.")