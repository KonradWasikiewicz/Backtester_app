from dash import Input, Output, State, callback_context, html, dcc, dash_table, ALL
import dash_bootstrap_components as dbc
import pandas as pd
import logging
import json
import traceback
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Import local modules
from src.services.backtest_service import BacktestService
from src.services.data_service import DataService
from src.services.visualization_service import VisualizationService
from src.core.constants import AVAILABLE_STRATEGIES

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
    def run_backtest(n_clicks, strategy_type, selected_tickers, start_date, end_date,
                     strategy_param_values, strategy_param_ids, risk_features,
                     risk_per_trade, stop_loss_type, stop_loss_value, max_positions):
        """
        Execute backtest when the Run Backtest button is clicked.
        """
        if not n_clicks:
            return "", {"display": "none"}, {"display": "block"}, [], None

        # Validate required inputs
        missing_inputs = []
        if not strategy_type:
            missing_inputs.append("strategy")
        if not selected_tickers:
            missing_inputs.append("tickers")
        if not start_date or not end_date:
            missing_inputs.append("date range")

        if missing_inputs:
            error_msg = f"Please provide required inputs: {', '.join(missing_inputs)}"
            return html.Div([html.I(className="fas fa-exclamation-circle me-2"), error_msg], className="text-danger"), {"display": "none"}, {"display": "block"}, [], None

        # Prepare parameters
        try:
            tickers = selected_tickers if isinstance(selected_tickers, list) else [selected_tickers]
            # Map each parameter id dict's 'param' key to its provided value
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

            # Run backtest
            result = backtest_service.run_backtest(
                strategy_type=strategy_type,
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
         Output("metric-calmar-ratio", "children")],
        Input("results-section", "style")
    )
    def update_performance_metrics(results_style):
        """
        Update performance metrics when results section becomes visible.
        
        Args:
            results_style: Style of the results section
            
        Returns:
            Performance metric components
        """
        if not backtest_service or results_style.get("display") == "none":
            return [None] * 9
        
        try:
            metrics = backtest_service.get_performance_metrics()
            
            # Format metrics with appropriate styling
            total_return = metrics.get("total-return")
            total_return_class = "text-success" if total_return and total_return.startswith("+") else "text-danger"
            
            cagr = metrics.get("cagr")
            cagr_class = "text-success" if cagr and cagr.startswith("+") else "text-danger"
            
            sharpe = metrics.get("sharpe")
            sharpe_class = "text-success" if sharpe and float(sharpe.replace(',', '.')) >= 1.0 else "text-warning"
            
            # Add additional metrics with appropriate formatting
            recovery_factor = metrics.get("recovery-factor", "N/A")
            recovery_class = "text-muted"
            if recovery_factor != "N/A":
                value = float(recovery_factor.replace(',', '.').replace('x', ''))
                recovery_class = "text-success" if value > 1.0 else "text-warning"
            
            calmar_ratio = metrics.get("calmar-ratio", "N/A")
            calmar_class = "text-muted"
            if calmar_ratio != "N/A":
                value = float(calmar_ratio.replace(',', '.'))
                calmar_class = "text-success" if value > 0.5 else "text-warning"
            
            return [
                html.Span(metrics.get("total-return"), className=total_return_class),
                html.Span(metrics.get("cagr"), className=cagr_class),
                html.Span(metrics.get("sharpe"), className=sharpe_class),
                html.Span(metrics.get("max-drawdown"), className="text-danger"),
                html.Span(metrics.get("win-rate"), className="text-info"),
                html.Span(metrics.get("profit-factor"), className="text-info"),
                html.Span(metrics.get("avg-trade"), className="text-info"),
                html.Span(recovery_factor, className=recovery_class),
                html.Span(calmar_ratio, className=calmar_class)
            ]
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}", exc_info=True)
            return [None] * 9
    
    @app.callback(
        Output("portfolio-chart", "figure"),
        Input("results-section", "style")
    )
    def update_portfolio_chart(results_style):
        """
        Update portfolio performance chart when results section becomes visible.
        
        Args:
            results_style: Style of the results section
            
        Returns:
            Plotly figure for portfolio performance chart
        """
        if not backtest_service or results_style.get("display") == "none":
            return {}
        
        try:
            # Get portfolio chart from the backtest service
            # This now uses the visualization service internally
            return backtest_service.get_portfolio_chart(chart_type="value") or {}
        except Exception as e:
            logger.error(f"Error updating portfolio chart: {e}", exc_info=True)
            return {}
    
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
                data=trades_data,
                style_table={"overflowX": "auto"},
                style_cell={
                    "textAlign": "left",
                    "padding": "10px",
                    "backgroundColor": "#2a2e39",
                    "color": "#e0e0e0"
                },
                style_header={
                    "backgroundColor": "#1e222d",
                    "color": "#ffffff",
                    "fontWeight": "bold",
                    "textAlign": "center"
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
                page_size=10,
                sort_action="native",
                filter_action="native"
            )
        except Exception as e:
            logger.error(f"Error updating trades table: {e}", exc_info=True)
            return f"Error displaying trades: {str(e)}"