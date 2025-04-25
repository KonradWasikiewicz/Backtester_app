import logging
import time
import traceback
from datetime import datetime
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, callback, no_update, ctx, ClientsideFunction
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

# Import services and components
from src.services.backtest_service import BacktestService
from src.ui.components import create_metric_card 
from src.visualization.chart_utils import create_empty_chart 
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
        State('strategy-selector', 'value'),
        State('instrument-selector', 'value'),
        State('date-range-slider', 'value'), # Assuming this provides [start_timestamp, end_timestamp]
        State('initial-capital-input', 'value'),
        # Strategy parameters (example, adjust based on actual inputs)
        State({'type': 'strategy-param-input', 'index': 'param1'}, 'value'), 
        State({'type': 'strategy-param-input', 'index': 'param2'}, 'value'),
        # Risk parameters (example)
        State('max-drawdown-input', 'value'),
        State('stop-loss-input', 'value'),
        prevent_initial_call=True
    )
    def run_backtest(n_clicks, strategy_type, tickers, date_range_ts, initial_capital, 
                     param1, param2, max_drawdown, stop_loss):
        if not n_clicks or not strategy_type or not tickers or not date_range_ts:
            logger.warning("Run backtest triggered with insufficient inputs.")
            return {"timestamp": time.time(), "success": False, "error": "Missing required inputs."}

        try:
            # Convert timestamps to 'YYYY-MM-DD' strings
            start_date = datetime.fromtimestamp(date_range_ts[0]).strftime('%Y-%m-%d')
            end_date = datetime.fromtimestamp(date_range_ts[1]).strftime('%Y-%m-%d')
            
            # --- Parameter Aggregation ---
            # This needs to be robust based on how strategy params are dynamically generated
            # Example: Assuming param1 and param2 are relevant for the selected strategy
            strategy_params = {}
            if param1 is not None: strategy_params['param1'] = param1 # Use actual param names
            if param2 is not None: strategy_params['param2'] = param2 # Use actual param names
            
            risk_params = {}
            if max_drawdown is not None: risk_params['max_drawdown'] = max_drawdown / 100.0 # Assuming percentage
            if stop_loss is not None: risk_params['stop_loss'] = stop_loss / 100.0 # Assuming percentage

            logger.info(f"Running backtest with: Strategy={strategy_type}, Tickers={tickers}, Start={start_date}, End={end_date}, Capital={initial_capital}, Strategy Params={strategy_params}, Risk Params={risk_params}")

            # Run backtest via service
            results_data = backtest_service.run_backtest(
                strategy_type=strategy_type,
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                initial_capital=float(initial_capital) if initial_capital else 100000.0,
                strategy_params=strategy_params,
                risk_params=risk_params
            )

            if results_data.get("success"):
                logger.info("Backtest completed successfully.")
                return {"timestamp": time.time(), "success": True}
            else:
                error_msg = results_data.get("error", "Unknown error during backtest execution.")
                logger.error(f"Backtest failed: {error_msg}")
                return {"timestamp": time.time(), "success": False, "error": error_msg}

        except Exception as e:
            logger.error(f"Exception during backtest execution: {e}", exc_info=True)
            error_msg = f"An unexpected error occurred: {e}"
            return {"timestamp": time.time(), "success": False, "error": error_msg}

    # --- Result Update Callbacks (Triggered by Store) ---

    # Update Metrics Card
    @app.callback(
        Output('metrics-summary-container', 'children'),
        Input('backtest-results-store', 'data'),
        prevent_initial_call=True
    )
    def update_metrics_display(store_data):
        if not store_data or not store_data.get("success"):
            # Handle backtest failure or initial state - maybe show an error message card
            error = store_data.get("error", "Backtest failed or not run yet.") if store_data else "Run a backtest to see metrics."
            # You might want a specific component for errors, or return an empty list
            return [html.Div(f"Error: {error}", className="alert alert-danger")] 
            
        try:
            metrics = backtest_service.get_performance_metrics()
            if not metrics:
                 return [html.Div("No metrics data available.", className="alert alert-warning")]
                 
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
        Input('portfolio-chart-type-selector', 'value'), # Add input for chart type
        prevent_initial_call=True
    )
    def update_portfolio_chart(store_data, chart_type):
        if not store_data or not store_data.get("success"):
            # Use create_empty_chart and access its figure attribute
            return create_empty_chart("Run Backtest for Portfolio Chart").figure 
            
        try:
            fig = backtest_service.get_portfolio_chart(chart_type=chart_type) # Pass chart_type
            # Use create_empty_chart if fig is None
            return fig if fig else create_empty_chart("No portfolio data").figure
        except Exception as e:
            logger.error(f"Error updating portfolio chart: {e}", exc_info=True)
            # Use create_empty_chart for error display
            return create_empty_chart(f"Error: {e}").figure

    # Update Monthly Returns Heatmap
    @app.callback(
        Output('monthly-returns-heatmap', 'figure'),
        Input('backtest-results-store', 'data'),
        prevent_initial_call=True
    )
    def update_heatmap(store_data):
        if not store_data or not store_data.get("success"):
            # Use create_empty_chart
            return create_empty_chart("Run Backtest for Heatmap").figure 
            
        try:
            fig = backtest_service.get_monthly_returns_heatmap()
            # Use create_empty_chart if fig is None
            return fig if fig else create_empty_chart("No returns data").figure
        except Exception as e:
            logger.error(f"Error updating heatmap: {e}", exc_info=True)
            # Use create_empty_chart for error display
            return create_empty_chart(f"Error: {e}").figure

    # Update Signals Chart (needs ticker selection)
    @app.callback(
        Output('signals-chart', 'figure'),
        Input('backtest-results-store', 'data'),
        Input('instrument-selector', 'value'), # Assuming this holds selected tickers
        prevent_initial_call=True
    )
    def update_signals_chart(store_data, selected_tickers):
        # Only show chart if one ticker is selected for clarity
        if not store_data or not store_data.get("success") or not selected_tickers or len(selected_tickers) != 1:
             # Use create_empty_chart
             return create_empty_chart("Select One Ticker to View Signals").figure 
             
        ticker = selected_tickers[0]
        try:
            fig = backtest_service.get_signals_chart(ticker=ticker)
            # Use create_empty_chart if fig is None
            return fig if fig else create_empty_chart(f"No signal data for {ticker}").figure
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
        if not store_data or not store_data.get("success"):
            return [], [] # Return empty data and tooltips
            
        try:
            trades_data = backtest_service.get_trades_table_data()
            
            # Prepare tooltip data (example: show exit reason)
            tooltip_data = []
            if trades_data:
                 tooltip_data = [
                    {
                        'profit_loss_pct': {'value': f"{row.get('profit_loss_pct', 0):.2f}%", 'type': 'markdown'},
                        'reason': {'value': row.get('reason', 'N/A'), 'type': 'markdown'} 
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