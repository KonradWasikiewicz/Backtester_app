from dash import Input, Output, State, callback_context, html, dcc, dash_table, ALL
import dash_bootstrap_components as dbc
import pandas as pd
import logging
import json
import traceback
from typing import Dict, List, Any, Optional
from datetime import datetime
import plotly.graph_objects as go # Added import

# Configure logging
logger = logging.getLogger(__name__)

# Import local modules
from src.services.backtest_service import BacktestService
from src.services.data_service import DataService
from src.services.visualization_service import VisualizationService
from src.core.constants import AVAILABLE_STRATEGIES
from src.visualization.chart_utils import _create_base_layout # ADDED import

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
    
    # Simplified and refactored run_backtest callback
    @app.callback(
        [Output("backtest-status", "children"),
         Output("results-section", "style"),
         Output("no-results-placeholder", "style"),
         Output("ticker-selector", "options"),  # Updates ticker dropdown in results
         Output("ticker-selector", "value")],  # Default select first ticker for signals
        Input("run-backtest-button", "n_clicks"),
        [State("strategy-dropdown", "value"),      # From step 1
         State("initial-capital-input", "value"),  # From step 1 - Added
         State("ticker-input", "value"),          # From step 3
         State("backtest-start-date", "date"),    # From step 2
         State("backtest-end-date", "date"),      # From step 2
         State({"type": "strategy-param", "strategy": ALL, "param": ALL}, "value"),
         State({"type": "strategy-param", "strategy": ALL, "param": ALL}, "id"),
         State("risk-features-checklist", "value"),
         State("max-risk-per-trade", "value"),
         State("stop-loss-type", "value"),
         State("stop-loss-value", "value"),
         State("max-position-size", "value")],
        prevent_initial_call=True
    )
    def run_backtest(n_clicks, strategy_type, initial_capital_str, selected_tickers, start_date, end_date,  # Renamed initial_capital to _str
                     strategy_param_values, strategy_param_ids, risk_features,
                     risk_per_trade, stop_loss_type, stop_loss_value, max_positions):
        """
        Execute backtest when the Run Backtest button is clicked.
        """
        if not n_clicks:
            return "", {"display": "none"}, {"display": "block"}, [], None

        # --- Convert and validate initial capital ---
        initial_capital = None
        if initial_capital_str:
            try:
                # Remove spaces and convert to float
                initial_capital = float(str(initial_capital_str).replace(" ", ""))
            except ValueError:
                # Handle cases where conversion fails (e.g., non-numeric input)
                return html.Div([html.I(className="fas fa-exclamation-circle me-2"), "Invalid Initial Capital format."], className="text-danger"), {"display": "none"}, {"display": "block"}, [], None

        # Validate required inputs
        missing_inputs = []
        if not strategy_type:
            missing_inputs.append("strategy")
        if not selected_tickers:
            missing_inputs.append("tickers")
        if not start_date or not end_date:
            missing_inputs.append("date range")
        # Use the converted numeric value for validation
        if initial_capital is None or initial_capital < 1000:
            missing_inputs.append("valid initial capital (>= 1 000)")

        if missing_inputs:
            error_msg = f"Please provide required inputs: {', '.join(missing_inputs)}"
            return html.Div([html.I(className="fas fa-exclamation-circle me-2"), error_msg], className="text-danger"), {"display": "none"}, {"display": "block"}, [], None

        # Prepare parameters
        try:
            tickers = selected_tickers if isinstance(selected_tickers, list) else [selected_tickers]
            strategy_params = {param_id["param"]: strategy_param_values[i] for i, param_id in enumerate(strategy_param_ids)}
            risk_params = {
                # Set continue_iterate to False by default, regardless of the risk_features input
                "continue_iterate": False,  # Removed conditional to prevent continuous iteration prompts
                "use_position_sizing": "position_sizing" in (risk_features or []),
                "use_stop_loss": "stop_loss" in (risk_features or []),
                "use_take_profit": "take_profit" in (risk_features or []),
                "use_market_filter": "market_filter" in (risk_features or []),
                "use_drawdown_protection": "drawdown_protection" in (risk_features or []),
                "stop_loss_pct": float(stop_loss_value) / 100.0 if stop_loss_value and stop_loss_type in ["fixed", "percent"] else 0.99,
                "risk_per_trade_pct": float(risk_per_trade) / 100.0 if risk_per_trade else None,
                "max_open_positions": int(max_positions) if max_positions else 5
            }

            # Run backtest using the converted numeric initial_capital
            result = backtest_service.run_backtest(
                strategy_type=strategy_type,
                initial_capital=initial_capital,  # Use the converted float value
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                strategy_params=strategy_params,
                risk_params=risk_params
            )

            if result.get("success"):
                ticker_options = [{"label": ticker, "value": ticker} for ticker in tickers if ticker in result.get("signals", {})]
                default_ticker = ticker_options[0]["value"] if ticker_options else None
                return html.Div([html.I(className="fas fa-check-circle me-2"), "Backtest completed successfully"], className="text-success"), {"display": "block"}, {"display": "none"}, ticker_options, default_ticker
            else:
                error_msg = f"Backtest failed: {result.get('error', 'Unknown error')}"
                return html.Div([html.I(className="fas fa-exclamation-circle me-2"), error_msg], className="text-danger"), {"display": "none"}, {"display": "block"}, [], None

        except Exception as e:
            logger.error(f"Error running backtest: {e}", exc_info=True)
            error_msg = f"Error running backtest: {str(e)}"
            return html.Div([html.I(className="fas fa-exclamation-circle me-2"), error_msg], className="text-danger"), {"display": "none"}, {"display": "block"}, [], None
    
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
        Input("results-section", "style")
    )
    def update_performance_metrics(results_style):
        """
        Update performance metrics when results section becomes visible.
        """
        num_metrics = 20 # Updated count of metrics (13 standard + 7 rejection details)
        if not backtest_service or results_style.get("display") == "none":
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
    
    @app.callback(
        Output("portfolio-chart", "figure"),
        # ADDED: Trigger based on chart type buttons
        [Input("btn-chart-value", "n_clicks"),
         Input("btn-chart-returns", "n_clicks"),
         Input("btn-chart-drawdown", "n_clicks")],
        State("results-section", "style"), # Keep state for visibility check
        # Removed original Input("results-section", "style") as it's now a State
        prevent_initial_call=True # Prevent running on load
    )
    def update_portfolio_chart(n_value, n_returns, n_drawdown, results_style): # Updated inputs/state
        """
        Update portfolio performance chart based on selected type and when results are visible.
        """
        # Check visibility first
        if not backtest_service or results_style.get("display") == "none":
            # Return default empty figure if no results or section hidden
            # Use a basic layout structure matching plotly figure dictionary
            return {'data': [], 'layout': {'template': 'plotly_dark', 'height': 400, 'title': 'Portfolio Performance', 'xaxis': {'visible': False}, 'yaxis': {'visible': False}, 'annotations': [{'text': 'Run backtest to see results', 'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'align': 'center'}]}}

        # Determine which button was clicked last
        ctx = callback_context
        # Default to 'value' if no button triggered (e.g., initial load after backtest)
        chart_type = "value"
        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "btn-chart-returns":
                chart_type = "returns"
            elif button_id == "btn-chart-drawdown":
                chart_type = "drawdown"
            # else: chart_type remains "value"

        logger.debug(f"Updating portfolio chart with type: {chart_type}")

        try:
            # Get the appropriate chart figure from the backtest service
            figure = backtest_service.get_portfolio_chart(chart_type=chart_type)

            if not figure:
                 logger.warning(f"get_portfolio_chart returned None for type {chart_type}")
                 # Return a styled empty figure dictionary
                 # CORRECTED: Call _create_base_layout directly
                 empty_layout = _create_base_layout(
                     title=f"Portfolio Performance ({chart_type.capitalize()}) - No Data",
                     height=400
                 )
                 empty_layout.annotations = [
                     go.layout.Annotation(
                         text="No data available for this view.",
                         showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5
                     )
                 ]
                 empty_layout.xaxis.visible = False
                 empty_layout.yaxis.visible = False
                 return {'data': [], 'layout': empty_layout}

            return figure # Return the figure dictionary directly
        except Exception as e:
            logger.error(f"Error updating portfolio chart (type: {chart_type}): {e}", exc_info=True)
            # Return a styled empty figure dictionary with error message
            # CORRECTED: Call _create_base_layout directly
            empty_layout = _create_base_layout(
                 title=f"Error loading {chart_type.capitalize()} chart",
                 height=400
            )
            empty_layout.annotations = [
                go.layout.Annotation(
                    text=f"Error: {str(e)}",
                    showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5
                )
            ]
            empty_layout.xaxis.visible = False
            empty_layout.yaxis.visible = False
            return {'data': [], 'layout': empty_layout}

    # Callback to manage button states (outline)
    @app.callback(
        [Output("btn-chart-value", "outline"),
         Output("btn-chart-returns", "outline"),
         Output("btn-chart-drawdown", "outline")],
        [Input("btn-chart-value", "n_clicks"),
         Input("btn-chart-returns", "n_clicks"),
         Input("btn-chart-drawdown", "n_clicks")],
        # prevent_initial_call=True # Allow initial state setting
    )
    def update_chart_button_styles(n_value, n_returns, n_drawdown):
        ctx = callback_context
        # Default: Value selected if no clicks yet or context unclear
        if not ctx.triggered_id:
            return False, True, True

        button_id = ctx.triggered_id.split(".")[0]
        if button_id == "btn-chart-returns":
            return True, False, True
        elif button_id == "btn-chart-drawdown":
            return True, True, False
        else: # Default to value button
            return False, True, True

    @app.callback(
        Output("monthly-returns-heatmap", "figure"),
        Input("results-section", "style")
    )
    def update_monthly_returns_heatmap(results_style):
        """
        Update monthly returns heatmap when results section becomes visible.
        
        Args:
            results_style: Style of the results section
            
        Returns:
            Plotly figure for monthly returns heatmap
        """
        if not backtest_service or results_style.get("display") == "none":
            return {}
        
        try:
            # Get monthly returns heatmap from the backtest service
            # This now uses the visualization service internally
            return backtest_service.get_monthly_returns_heatmap() or {}
        except Exception as e:
            logger.error(f"Error updating monthly returns heatmap: {e}", exc_info=True)
            return {}
    
    @app.callback(
        Output("signals-chart", "figure"),
        [Input("results-section", "style"),
         Input("ticker-selector", "value")]
    )
    def update_signals_chart(results_style, ticker):
        """
        Update signals chart when ticker selection changes.
        
        Args:
            results_style: Style of the results section
            ticker: Selected ticker symbol
            
        Returns:
            Signals chart figure
        """
        if not backtest_service or results_style.get("display") == "none" or not ticker:
            return {}
        
        try:
            # If ticker is a list, use only the first element
            ticker_value = ticker[0] if isinstance(ticker, list) and len(ticker) > 0 else ticker
            return backtest_service.get_signals_chart(ticker_value) or {}
        except Exception as e:
            logger.error(f"Error updating signals chart: {e}", exc_info=True)
            return {}
    
    @app.callback(
        Output("trades-table-container", "children"),
        Input("results-section", "style")
    )
    def update_trades_table(results_style):
        """
        Update trades table when results section becomes visible.
        
        Args:
            results_style: Style of the results section
            
        Returns:
            Trades table component
        """
        if not backtest_service or results_style.get("display") == "none":
            return "No trade data available."
        
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