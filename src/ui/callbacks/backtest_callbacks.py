from dash import Input, Output, State, callback_context, html, dcc, dash_table, ALL, no_update
import dash_bootstrap_components as dbc
import pandas as pd
import logging
import json
import traceback
from typing import Dict, List, Any, Optional
from datetime import datetime # ADDED import
import plotly.graph_objects # CORRECTED: Removed 'as go' alias initially, will use full path

# Configure logging
logger = logging.getLogger(__name__)

# Import local modules
from src.services.backtest_service import BacktestService
from src.services.data_service import DataService
from src.services.visualization_service import VisualizationService
from src.core.constants import AVAILABLE_STRATEGIES
from src.visualization.chart_utils import _create_base_layout # ADDED import
# --- ADDED: Import layout functions for results section ---
from src.ui.layouts.results_display import (
    create_overview_metrics,
    create_portfolio_value_returns_chart,
    create_drawdown_chart,
    create_monthly_returns_heatmap,
    create_trades_table,
    create_signals_chart,
    create_no_results_placeholder
)

# Create shared service instances
backtest_service = None
data_service = None
visualization_service = None

def register_backtest_callbacks(app):
    """
    Register all backtest execution and results display callbacks with the Dash app.

    Args:
        app: The Dash application instance
    """
    global backtest_service, data_service, visualization_service

    # Initialize the services
    try:
        if backtest_service is None:
            backtest_service = BacktestService()

        if data_service is None:
            data_service = DataService()

        if visualization_service is None:
            visualization_service = VisualizationService()

        logger.info("Services initialized for backtest callbacks")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}", exc_info=True)
        # We'll handle this in the callbacks

    # --- MODIFIED: run_backtest callback - Removed ticker-selector outputs ---
    @app.callback(
        [Output("backtest-status", "children"),
         Output("results-loading", "children"),
         Output("backtest-results-store", "data")],
        Input("run-backtest-button", "n_clicks"),
        [State("strategy-dropdown", "value"),
         State("initial-capital-input", "value"),
         State("ticker-input", "value"),
         State("backtest-start-date", "date"),
         State("backtest-end-date", "date"),
         State({"type": "strategy-param", "strategy": ALL, "param": ALL}, "value"),
         State({"type": "strategy-param", "strategy": ALL, "param": ALL}, "id"),
         State("risk-features-checklist", "value"),
         State("max-risk-per-trade", "value"),
         State("stop-loss-type", "value"),
         State("stop-loss-value", "value"),
         State("max-position-size", "value")],
        prevent_initial_call=True
    )
    def run_backtest(n_clicks, strategy_type, initial_capital_str, selected_tickers, start_date, end_date,
                     strategy_param_values, strategy_param_ids, risk_features,
                     risk_per_trade, stop_loss_type, stop_loss_value, max_positions):
        """
        Execute backtest when the Run Backtest button is clicked.
        Updates the content of the dcc.Loading component and signals completion via dcc.Store.
        """
        if not n_clicks:
            # MODIFIED: Removed last two return values
            return "", create_no_results_placeholder(), no_update

        # --- Convert and validate initial capital ---
        initial_capital = None
        if initial_capital_str:
            try:
                initial_capital = float(str(initial_capital_str).replace(" ", ""))
            except ValueError:
                error_msg = html.Div([html.I(className="fas fa-exclamation-circle me-2"), "Invalid Initial Capital format."], className="text-danger")
                # MODIFIED: Removed last two return values
                return error_msg, create_no_results_placeholder(), no_update

        # Validate required inputs
        missing_inputs = []
        if not strategy_type: missing_inputs.append("strategy")
        if not selected_tickers: missing_inputs.append("tickers")
        if not start_date or not end_date: missing_inputs.append("date range")
        if initial_capital is None or initial_capital < 1000: missing_inputs.append("valid initial capital (>= 1 000)")

        if missing_inputs:
            error_msg_text = f"Please provide required inputs: {', '.join(missing_inputs)}"
            error_msg = html.Div([html.I(className="fas fa-exclamation-circle me-2"), error_msg_text], className="text-danger")
            # MODIFIED: Removed last two return values
            return error_msg, create_no_results_placeholder(), no_update

        # Prepare parameters
        try:
            tickers = selected_tickers if isinstance(selected_tickers, list) else [selected_tickers]
            strategy_params = {param_id["param"]: strategy_param_values[i] for i, param_id in enumerate(strategy_param_ids)}
            risk_params = {
                "continue_iterate": False,
                "use_position_sizing": "position_sizing" in (risk_features or []),
                "use_stop_loss": "stop_loss" in (risk_features or []),
                "use_take_profit": "take_profit" in (risk_features or []),
                "use_market_filter": "market_filter" in (risk_features or []),
                "use_drawdown_protection": "drawdown_protection" in (risk_features or []),
                "stop_loss_pct": float(stop_loss_value) / 100.0 if stop_loss_value and stop_loss_type in ["fixed", "percent"] else 0.99,
                "risk_per_trade_pct": float(risk_per_trade) / 100.0 if risk_per_trade else None,
                "max_open_positions": int(max_positions) if max_positions else 5
            }

            # Run backtest
            result = backtest_service.run_backtest(
                strategy_type=strategy_type,
                initial_capital=initial_capital,
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                strategy_params=strategy_params,
                risk_params=risk_params
            )

            if result.get("success"):
                status_msg = html.Div([html.I(className="fas fa-check-circle me-2"), "Backtest completed successfully"], className="text-success")

                # Build the results section layout dynamically
                results_layout = html.Div(
                    id="results-section", # Keep the ID for other callbacks
                    children=[
                        create_overview_metrics(
                            metrics_ids=[
                                "total-return", "cagr", "sharpe", "max-drawdown", "calmar-ratio",
                                "recovery-factor", "starting-balance", "ending-balance"
                            ],
                            header="Strategy Performance Overview"
                        ),
                        create_overview_metrics(
                            metrics_ids=[
                                "signals-generated", "trades-count", "rejected-signals-total",
                                "win-rate", "profit-factor", "avg-trade",
                                "rejected-signals-cash", "rejected-signals-risk",
                                "rejected-signals-maxpos", "rejected-signals-exists",
                                "rejected-signals-filter", "rejected-signals-other"
                            ],
                            header="Trade & Signal Execution Overview"
                        ),
                        create_portfolio_value_returns_chart(),
                        create_drawdown_chart(),
                        dbc.Row([dbc.Col(create_monthly_returns_heatmap(), width=12, className="mb-4")]),
                        dbc.Row([dbc.Col(create_trades_table(), width=12, className="mb-4")]),
                        create_signals_chart()
                    ]
                )
                # --- MODIFIED: Return success status, results layout, timestamp for store ---
                return status_msg, results_layout, datetime.now().isoformat()
            else:
                error_msg_text = f"Backtest failed: {result.get('error', 'Unknown error')}"
                error_msg = html.Div([html.I(className="fas fa-exclamation-circle me-2"), error_msg_text], className="text-danger")
                # MODIFIED: Removed last two return values
                return error_msg, create_no_results_placeholder(), no_update

        except Exception as e:
            logger.error(f"Error running backtest: {e}", exc_info=True)
            error_msg_text = f"Error running backtest: {str(e)}"
            error_msg = html.Div([html.I(className="fas fa-exclamation-circle me-2"), error_msg_text], className="text-danger")
            # MODIFIED: Removed last two return values
            return error_msg, create_no_results_placeholder(), no_update

    # --- ADDED: Callback to update ticker selector after results are loaded ---
    @app.callback(
        [Output("ticker-selector", "options"),
         Output("ticker-selector", "value")],
        Input("backtest-results-store", "data"),
        prevent_initial_call=True
    )
    def update_ticker_selector_options(results_timestamp):
        """
        Update the ticker selector options and value after backtest results are available.
        """
        if not backtest_service or not results_timestamp:
            return [], None # Return empty options and no value if no results

        try:
            # CORRECTED: Access the attribute directly instead of calling a non-existent method
            signals_data = backtest_service.current_signals
            if not signals_data:
                logger.warning("No signals data found in backtest service (current_signals) to populate ticker selector.")
                return [], None

            # Extract tickers that actually have signals
            tickers_with_signals = list(signals_data.keys())
            if not tickers_with_signals:
                logger.warning("No tickers with signals found in backtest results (current_signals)." )
                return [], None

            ticker_options = [{"label": ticker, "value": ticker} for ticker in tickers_with_signals]
            default_ticker = ticker_options[0]["value"] if ticker_options else None

            logger.debug(f"Updating ticker selector with options: {ticker_options}, default: {default_ticker}")
            return ticker_options, default_ticker

        except Exception as e:
            logger.error(f"Error updating ticker selector options: {e}", exc_info=True)
            return [], None # Return empty on error

    # --- MODIFIED: Update performance metrics callback ---
    @app.callback(
        [Output("metric-total-return", "children"),
         Output("metric-cagr", "children"),
         Output("metric-sharpe", "children"),
         Output("metric-max-drawdown", "children"),
         Output("metric-win-rate", "children"),
         Output("metric-profit-factor", "children"),
         Output("metric-avg-trade", "children"),
         Output("metric-recovery-factor", "children"),
         Output("metric-calmar-ratio", "children"),
         Output("metric-starting-balance", "children"),
         Output("metric-ending-balance", "children"),
         Output("metric-signals-generated", "children"), # Total entry signals
         Output("metric-trades-count", "children"), # Executed trades
         # Add outputs for the detailed rejection metrics
         Output("metric-rejected-signals-total", "children"),
         Output("metric-rejected-signals-cash", "children"),
         Output("metric-rejected-signals-risk", "children"),
         Output("metric-rejected-signals-maxpos", "children"),
         Output("metric-rejected-signals-exists", "children"),
         Output("metric-rejected-signals-filter", "children"),
         Output("metric-rejected-signals-other", "children")],
        # MODIFIED: Triggered by the results store data
        Input("backtest-results-store", "data")
    )
    # MODIFIED: Function signature accepts store data
    def update_performance_metrics(results_timestamp):
        """
        Update performance metrics when backtest results are available (signaled by store).
        """
        num_metrics = 20
        # MODIFIED: Check if timestamp exists
        if not backtest_service or not results_timestamp:
            return ["--"] * num_metrics # Return default placeholder for all

        try:
            metrics = backtest_service.get_performance_metrics()
            if not metrics:
                 return ["--"] * num_metrics

            # Helper to get metric or default
            def get_metric(key, default="--"):
                return metrics.get(key, default)

            # --- Format Standard Metrics (with styling) ---
            total_return = get_metric("total-return")
            total_return_class = "text-success" if total_return != "--" and total_return.startswith("+") else "text-danger"

            cagr = get_metric("cagr")
            cagr_class = "text-success" if cagr != "--" and cagr.startswith("+") else "text-danger"

            sharpe = get_metric("sharpe")
            sharpe_val = 0
            try:
                sharpe_val = float(sharpe.replace(',', '.')) if sharpe != "--" else 0
            except ValueError:
                pass # Keep sharpe_val as 0
            sharpe_class = "text-success" if sharpe_val >= 1.0 else ("text-warning" if sharpe_val > 0 else "text-danger")

            recovery_factor = get_metric("recovery-factor", "N/A")
            recovery_class = "text-muted"
            if recovery_factor != "N/A":
                try:
                    value = float(recovery_factor.replace(',', '.').replace('x', ''))
                    recovery_class = "text-success" if value > 1.0 else "text-warning"
                except ValueError:
                     pass # Keep muted class

            calmar_ratio = get_metric("calmar-ratio", "N/A")
            calmar_class = "text-muted"
            if calmar_ratio != "N/A":
                try:
                    value = float(calmar_ratio.replace(',', '.'))
                    calmar_class = "text-success" if value > 0.5 else "text-warning"
                except ValueError:
                    pass # Keep muted class

            # --- Return all metrics in the order of the Outputs ---
            return [
                # Standard Metrics
                html.Span(total_return, className=total_return_class),
                html.Span(cagr, className=cagr_class),
                html.Span(sharpe, className=sharpe_class),
                html.Span(get_metric("max-drawdown"), className="text-danger"),
                html.Span(get_metric("win-rate"), className="text-info"),
                html.Span(get_metric("profit-factor"), className="text-info"),
                html.Span(get_metric("avg-trade"), className="text-info"),
                html.Span(recovery_factor, className=recovery_class),
                html.Span(calmar_ratio, className=calmar_class),
                html.Span(get_metric("starting-balance"), className="text-muted"),
                html.Span(get_metric("ending-balance"), className="text-info"),
                html.Span(get_metric("signals-generated"), className="text-muted"), # Total entry signals
                html.Span(get_metric("trades-count"), className="text-info"), # Executed trades
                # Detailed Rejection Metrics
                html.Span(get_metric("rejected-signals-total"), className="text-warning"),
                html.Span(get_metric("rejected-signals-cash"), className="text-warning"),
                html.Span(get_metric("rejected-signals-risk"), className="text-warning"),
                html.Span(get_metric("rejected-signals-maxpos"), className="text-warning"),
                html.Span(get_metric("rejected-signals-exists"), className="text-warning"),
                html.Span(get_metric("rejected-signals-filter"), className="text-warning"),
                html.Span(get_metric("rejected-signals-other"), className="text-warning")
            ]
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}", exc_info=True)
            return ["Error"] * num_metrics # Return error message for all

    # --- MODIFIED: Update portfolio chart callback ---
    @app.callback(
        Output("portfolio-chart", "figure"),
        [Input("btn-chart-value", "n_clicks"),
         Input("btn-chart-returns", "n_clicks"),
         # MODIFIED: Triggered by the results store data
         Input("backtest-results-store", "data")],
        prevent_initial_call=True
    )
    # MODIFIED: Function signature accepts store data
    def update_portfolio_chart(n_value, n_returns, results_timestamp):
        """
        Update portfolio performance chart based on selected type and when results are available.
        """
        # MODIFIED: Check if timestamp exists
        if not backtest_service or not results_timestamp:
            # Return default empty figure if no results or section hidden
            # Use a basic layout structure matching plotly figure dictionary
            return {'data': [], 'layout': {'template': 'plotly_dark', 'height': 400, 'title': 'Portfolio Performance', 'xaxis': {'visible': False}, 'yaxis': {'visible': False}, 'annotations': [{'text': 'Run backtest to see results', 'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'align': 'center'}]}}

        # Determine chart type based on button clicks
        ctx = callback_context
        chart_type = "value" # Default to value
        if ctx.triggered:
            triggered_input = ctx.triggered[0]["prop_id"]
            if "btn-chart-returns" in triggered_input:
                chart_type = "returns"
            elif "btn-chart-value" in triggered_input:
                chart_type = "value"
            # If triggered by store, default to value

        logger.debug(f"Updating portfolio chart with type: {chart_type} (Trigger: {ctx.triggered[0]['prop_id'] if ctx.triggered else 'None'})")

        try:
            figure = backtest_service.get_portfolio_chart(chart_type=chart_type)

            if not figure:
                 logger.warning(f"get_portfolio_chart returned None for type {chart_type}")
                 empty_layout = _create_base_layout(
                     title=f"Portfolio Performance ({chart_type.capitalize()}) - No Data",
                     height=400
                 )
                 empty_layout.annotations = [
                     # CORRECTED: Use full path instead of 'go' alias
                     plotly.graph_objects.layout.Annotation(
                         text="No data available for this view.",
                         showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5
                     )
                 ]
                 empty_layout.xaxis.visible = False
                 empty_layout.yaxis.visible = False
                 return {'data': [], 'layout': empty_layout}

            # CORRECTED: Return figure as dictionary
            return figure.to_dict()
        except Exception as e:
            logger.error(f"Error updating portfolio chart (type: {chart_type}): {e}", exc_info=True)
            # Return a styled empty figure dictionary with error message
            # CORRECTED: Call _create_base_layout directly
            empty_layout = _create_base_layout(
                 title=f"Error loading {chart_type.capitalize()} chart",
                 height=400
            )
            empty_layout.annotations = [
                # CORRECTED: Use full path instead of 'go' alias
                plotly.graph_objects.layout.Annotation(
                    text=f"Error: {str(e)}",
                    showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5
                )
            ]
            empty_layout.xaxis.visible = False
            empty_layout.yaxis.visible = False
            return {'data': [], 'layout': empty_layout}

    # Callback to manage button states (outline) - NO CHANGE NEEDED
    @app.callback(
        [Output("btn-chart-value", "outline"),
         Output("btn-chart-returns", "outline")],
        [Input("btn-chart-value", "n_clicks"),
         Input("btn-chart-returns", "n_clicks")],
    )
    def update_chart_button_styles(n_value, n_returns):
        ctx = callback_context
        # Default: Value selected if no clicks yet or context unclear
        if not ctx.triggered_id:
            return False, True

        button_id = ctx.triggered_id.split(".")[0]
        if button_id == "btn-chart-returns":
            return True, False
        else: # Default to value button
            return False, True

    # --- MODIFIED: Update drawdown chart callback ---
    @app.callback(
        Output("drawdown-chart", "figure"),
        # MODIFIED: Triggered by the results store data
        Input("backtest-results-store", "data")
    )
    # MODIFIED: Function signature accepts store data
    def update_drawdown_chart(results_timestamp):
        """
        Update the separate portfolio drawdown chart when results are available.
        """
        chart_type = "drawdown"
        # MODIFIED: Check if timestamp exists
        if not backtest_service or not results_timestamp:
            # Return default empty figure
            return {'data': [], 'layout': {'template': 'plotly_dark', 'height': 300, 'title': 'Portfolio Drawdown', 'xaxis': {'visible': False}, 'yaxis': {'visible': False}, 'annotations': [{'text': 'Run backtest to see results', 'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'align': 'center'}]}}

        logger.debug(f"Updating drawdown chart")

        try:
            figure = backtest_service.get_portfolio_chart(chart_type=chart_type)
            if not figure:
                 logger.warning(f"get_portfolio_chart returned None for type {chart_type}")
                 empty_layout = _create_base_layout(
                     title="Portfolio Drawdown - No Data",
                     height=300
                 )
                 empty_layout.annotations = [
                     # CORRECTED: Use full path instead of 'go' alias
                     plotly.graph_objects.layout.Annotation(
                         text="No data available for this view.",
                         showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5
                     )
                 ]
                 empty_layout.xaxis.visible = False
                 empty_layout.yaxis.visible = False
                 return {'data': [], 'layout': empty_layout}
            # CORRECTED: Return figure as dictionary
            return figure.to_dict()
        except Exception as e:
            logger.error(f"Error updating drawdown chart: {e}", exc_info=True)
            empty_layout = _create_base_layout(
                 title="Error loading Drawdown chart",
                 height=300
            )
            empty_layout.annotations = [
                # CORRECTED: Use full path instead of 'go' alias
                plotly.graph_objects.layout.Annotation(
                    text=f"Error: {str(e)}",
                    showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5
                )
            ]
            empty_layout.xaxis.visible = False
            empty_layout.yaxis.visible = False
            return {'data': [], 'layout': empty_layout}

    # --- MODIFIED: Update monthly returns heatmap callback ---
    @app.callback(
        Output("monthly-returns-heatmap", "figure"),
        # MODIFIED: Triggered by the results store data
        Input("backtest-results-store", "data")
    )
    # MODIFIED: Function signature accepts store data
    def update_monthly_returns_heatmap(results_timestamp):
        """
        Update monthly returns heatmap when results are available.
        """
        # MODIFIED: Check if timestamp exists
        if not backtest_service or not results_timestamp:
            return {}

        try:
            # Get monthly returns heatmap from the backtest service
            # This now uses the visualization service internally
            return backtest_service.get_monthly_returns_heatmap() or {}
        except Exception as e:
            logger.error(f"Error updating monthly returns heatmap: {e}", exc_info=True)
            return {}

    # --- MODIFIED: Update signals chart callback ---
    @app.callback(
        Output("signals-chart", "figure"),
        # MODIFIED: Triggered by store data and ticker selector
        [Input("backtest-results-store", "data"),
         Input("ticker-selector", "value")]
    )
    # MODIFIED: Function signature accepts store data
    def update_signals_chart(results_timestamp, ticker):
        """
        Update signals chart when results are available or ticker selection changes.
        """
        # MODIFIED: Check if timestamp exists
        if not backtest_service or not results_timestamp or not ticker:
            return {}

        try:
            # If ticker is a list, use only the first element
            ticker_value = ticker[0] if isinstance(ticker, list) and len(ticker) > 0 else ticker
            return backtest_service.get_signals_chart(ticker_value) or {}
        except Exception as e:
            logger.error(f"Error updating signals chart: {e}", exc_info=True)
            return {}

    # --- MODIFIED: Update trades table callback ---
    @app.callback(
        Output("trades-table-container", "children"),
        # MODIFIED: Triggered by the results store data
        Input("backtest-results-store", "data")
    )
    # MODIFIED: Function signature accepts store data
    def update_trades_table(results_timestamp):
        """
        Update trades table when results are available.
        """
        # MODIFIED: Check if timestamp exists
        if not backtest_service or not results_timestamp:
            return "Run a backtest to view trade history."

        try:
            trades_data = backtest_service.get_trades_table_data()
            if not trades_data:
                return "No trades were executed in this backtest."

            # Define the font family consistent with the CSS
            consistent_font = "'system-ui', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif"

            # Format exit reasons
            formatted_trades_data = []
            for trade in trades_data:
                raw_reason = trade.get('reason', '')
                formatted_reason = raw_reason.replace('_', ' ').title() if raw_reason else 'Unknown'
                trade['reason'] = formatted_reason # Update the reason in the dictionary
                formatted_trades_data.append(trade)

            return dash_table.DataTable(
                id="trades-table",
                columns=[
                    {"name": "Ticker", "id": "ticker"},
                    {"name": "Entry Date", "id": "entry_date"},
                    {"name": "Exit Date", "id": "exit_date"},
                    {"name": "Entry Price", "id": "entry_price", "type": "numeric", "format": dash_table.FormatTemplate.money(2)},
                    {"name": "Exit Price", "id": "exit_price", "type": "numeric", "format": dash_table.FormatTemplate.money(2)},
                    {"name": "P/L ($)", "id": "profit_loss", "type": "numeric", "format": dash_table.FormatTemplate.money(2)},
                    {"name": "P/L (%)", "id": "profit_loss_pct", "type": "numeric", "format": dash_table.FormatTemplate.percentage(2)},
                    {"name": "Shares", "id": "shares", "type": "numeric", "format": {"specifier": ",d"}},
                    {"name": "Exit Reason", "id": "reason"}
                ],
                data=formatted_trades_data, # Use formatted data
                style_table={"overflowX": "auto", "width": "100%"}, # Ensure table uses full width
                style_cell={
                    "textAlign": "left",
                    "padding": "10px",
                    "backgroundColor": "#2a2e39",
                    "color": "#e0e0e0",
                    "fontFamily": consistent_font # Explicitly set font family
                },
                style_header={
                    "backgroundColor": "#1e222d",
                    "color": "#ffffff",
                    "fontWeight": "bold",
                    "textAlign": "center",
                    "fontFamily": consistent_font # Explicitly set font family for header
                },
                style_data_conditional=[
                    {
                        "if": {"filter_query": "{profit_loss_pct} < 0"},
                        "color": "#ff4a68"  # Red for losses
                    },
                    {
                        "if": {"filter_query": "{profit_loss_pct} >= 0"},
                        "color": "#00cc96"  # Green for gains
                    }
                ],
                sort_action="native",
                # filter_action="native" # Removed filter action to hide the filter row
            )
        except Exception as e:
            logger.error(f"Error updating trades table: {e}", exc_info=True)
            return f"Error displaying trades: {str(e)}"

    # --- ADDED: Callback to manage main loader visibility ---
    @app.callback(
        Output("results-loading", "className"),
        [
            Input("portfolio-chart-loading", "loading_state"),
            Input("drawdown-chart-loading", "loading_state"),
            Input("heatmap-chart-loading", "loading_state"),
            Input("trades-table-loading", "loading_state"),
            Input("signals-chart-loading", "loading_state"),
            Input("backtest-results-store", "data") # Also trigger when backtest finishes/fails
        ],
        prevent_initial_call=True
    )
    def manage_main_loader_visibility(portfolio_ls, drawdown_ls, heatmap_ls, trades_ls, signals_ls, results_timestamp):
        """
        Hides the main fullscreen loader only when all individual result components have finished loading.
        """
        # If backtest hasn't run or failed (no timestamp), keep loader visible (without finished class)
        if not results_timestamp:
            return "main-loader-fullscreen"

        # Check if any of the individual loaders are still loading
        # loading_state is None initially, check for that too
        still_loading = (
            (portfolio_ls and portfolio_ls.get("is_loading")) or
            (drawdown_ls and drawdown_ls.get("is_loading")) or
            (heatmap_ls and heatmap_ls.get("is_loading")) or
            (trades_ls and trades_ls.get("is_loading")) or
            (signals_ls and signals_ls.get("is_loading"))
        )

        if still_loading:
            # Keep loader visible if anything is still loading
            return "main-loader-fullscreen"
        else:
            # Add the 'loading-finished' class to hide the spinner via CSS
            return "main-loader-fullscreen loading-finished"