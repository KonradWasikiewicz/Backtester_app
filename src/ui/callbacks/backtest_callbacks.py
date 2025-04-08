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
from src.core.constants import AVAILABLE_STRATEGIES

# Create a shared backtest service instance
backtest_service = None

def register_backtest_callbacks(app):
    """
    Register all backtest execution and results display callbacks with the Dash app.
    
    Args:
        app: The Dash application instance
    """
    global backtest_service
    
    # Initialize the backtest service
    if backtest_service is None:
        try:
            backtest_service = BacktestService()
        except Exception as e:
            logger.error(f"Failed to initialize BacktestService: {e}", exc_info=True)
            # We'll handle this in the callbacks
    
    @app.callback(
        [Output("backtest-status", "children"),
         Output("results-section", "style"),
         Output("no-results-placeholder", "style"),
         Output("ticker-selector", "options"),
         Output("ticker-selector", "value")],
        Input("run-backtest-button", "n_clicks"),
        [State("strategy-selector", "value"),
         State("ticker-checklist", "value"),
         # Date inputs - we now use the direct date pickers
         State("slider-start-date-picker", "date"),
         State("slider-end-date-picker", "date"),
         # Strategy parameters pattern matching state
         State({"type": "strategy-param", "index": ALL}, "value"),
         State({"type": "strategy-param", "index": ALL}, "id"),
         # Risk parameters
         State("position-sizing-selector", "value"),
         State("risk-per-trade", "value"),
         State("stop-loss-selector", "value"),
         State("stop-loss-value", "value"),
         State("max-positions", "value"),
         State("use-market-filter", "value")]
    )
    def run_backtest(n_clicks, strategy_type, selected_tickers, 
                    start_date, end_date,
                    strategy_param_values, strategy_param_ids, position_sizing, risk_per_trade,
                    stop_loss_type, stop_loss_value, max_positions, use_market_filter):
        """
        Execute backtest when the Run Backtest button is clicked.
        
        Returns:
            Status message, visibility settings for results, ticker options, and selected ticker
        """
        if not n_clicks:
            return (
                "", 
                {"display": "none"}, 
                {"display": "block"}, 
                [], 
                None
            )
        
        if not backtest_service:
            error_msg = "Backtest service initialization failed. Please check the logs."
            return (
                html.Div([html.I(className="fas fa-exclamation-circle me-2"), error_msg], className="text-danger"),
                {"display": "none"},
                {"display": "block"},
                [], 
                None
            )
        
        # Check required inputs
        if not strategy_type or not selected_tickers or not start_date or not end_date:
            missing = []
            if not strategy_type: missing.append("strategy")
            if not selected_tickers: missing.append("tickers")
            if not start_date or not end_date: missing.append("date range")
            
            error_msg = f"Please provide required inputs: {', '.join(missing)}"
            return (
                html.Div([html.I(className="fas fa-exclamation-circle me-2"), error_msg], className="text-danger"),
                {"display": "none"},
                {"display": "block"},
                [], 
                None
            )
        
        # Process tickers - now tickers are already a list from the checklist
        tickers = selected_tickers  # These are already in uppercase from the DataLoader
        if not tickers:
            error_msg = "Please select at least one ticker."
            return (
                html.Div([html.I(className="fas fa-exclamation-circle me-2"), error_msg], className="text-danger"),
                {"display": "none"},
                {"display": "block"},
                [], 
                None
            )
        
        # Process strategy parameters
        try:
            strategy_params = {}
            for i, param_id in enumerate(strategy_param_ids):
                param_name = param_id["index"]
                param_value = strategy_param_values[i]
                strategy_params[param_name] = param_value
            
            # Process risk parameters
            risk_params = {}
            
            # Map position_sizing_method to RiskManager parameters
            if position_sizing == "risk":
                risk_params["stop_loss_pct"] = float(risk_per_trade) / 100.0 if risk_per_trade is not None else 0.02
            elif position_sizing == "equal":
                # For equal sizing, use minimum risk and adjust max_position_size
                risk_params["stop_loss_pct"] = 0.02  # default value
                risk_params["max_position_size"] = 1.0 / float(max_positions) if max_positions > 0 else 0.2
            
            # Map stop-loss type
            if stop_loss_type == "fixed":
                risk_params["stop_loss_pct"] = float(stop_loss_value) / 100.0 if stop_loss_value is not None else 0.02
            elif stop_loss_type == "trailing":
                risk_params["use_trailing_stop"] = True
                risk_params["trailing_stop_activation"] = 0.02  # 2% default
                risk_params["trailing_stop_distance"] = float(stop_loss_value) / 100.0 if stop_loss_value is not None else 0.015
            elif stop_loss_type == "none":
                # Use a very large value if no stop
                risk_params["stop_loss_pct"] = 0.99
            
            # Set maximum number of positions
            risk_params["max_open_positions"] = int(max_positions) if max_positions is not None else 5
            
            # Market filter
            risk_params["use_market_filter"] = bool(use_market_filter)
            
            # Fixed: Show a loading message with proper spinner implementation
            status_div = html.Div([
                html.I(className="fas fa-spinner fa-spin me-2"),
                "Running backtest..."
            ], className="text-primary")
            
            # Run the backtest
            result = backtest_service.run_backtest(
                strategy_type=strategy_type,
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                strategy_params=strategy_params,
                risk_params=risk_params
            )
            
            if result["success"]:
                # Create ticker options for the signals chart dropdown
                ticker_options = [{"label": ticker, "value": ticker} for ticker in tickers if ticker in result.get("signals", {})]
                
                return (
                    html.Div([html.I(className="fas fa-check-circle me-2"), "Backtest completed successfully"], className="text-success"),
                    {"display": "block"},
                    {"display": "none"},
                    ticker_options,
                    ticker_options[0]["value"] if ticker_options else None
                )
            else:
                error_msg = f"Backtest failed: {result.get('error', 'Unknown error')}"
                logger.error(f"Backtest failed: {result}")
                return (
                    html.Div([html.I(className="fas fa-exclamation-circle me-2"), error_msg], className="text-danger"),
                    {"display": "none"},
                    {"display": "block"},
                    [], 
                    None
                )
                
        except Exception as e:
            logger.error(f"Error running backtest: {e}", exc_info=True)
            error_msg = f"Error running backtest: {str(e)}"
            return (
                html.Div([html.I(className="fas fa-exclamation-circle me-2"), error_msg], className="text-danger"),
                {"display": "none"},
                {"display": "block"},
                [], 
                None
            )
    
    @app.callback(
        [Output("metric-total-return", "children"),
         Output("metric-cagr", "children"),
         Output("metric-sharpe", "children"),
         Output("metric-max-drawdown", "children"),
         Output("metric-win-rate", "children"),
         Output("metric-profit-factor", "children"),
         Output("metric-avg-trade", "children")],
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
            return [None] * 7
        
        try:
            metrics = backtest_service.get_performance_metrics()
            return [
                metrics.get("total-return"),
                metrics.get("cagr"),
                metrics.get("sharpe"),
                metrics.get("max-drawdown"),
                metrics.get("win-rate"),
                metrics.get("profit-factor"),
                metrics.get("avg-trade")
            ]
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}", exc_info=True)
            return [None] * 7
    
    @app.callback(
        Output("portfolio-chart", "figure"),
        [Input("results-section", "style"),
         Input("btn-chart-value", "n_clicks"),
         Input("btn-chart-returns", "n_clicks"),
         Input("btn-chart-drawdown", "n_clicks")]
    )
    def update_portfolio_chart(results_style, btn_value, btn_returns, btn_drawdown):
        """
        Update portfolio chart based on which chart type button was clicked.
        
        Returns:
            Portfolio chart figure
        """
        if not backtest_service or results_style.get("display") == "none":
            return {}
        
        ctx = callback_context
        if not ctx.triggered:
            chart_type = "value"  # Default chart type
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "btn-chart-value":
                chart_type = "value"
            elif button_id == "btn-chart-returns":
                chart_type = "returns"
            elif button_id == "btn-chart-drawdown":
                chart_type = "drawdown"
            else:
                chart_type = "value"  # Default
        
        try:
            return backtest_service.get_portfolio_chart(chart_type)
        except Exception as e:
            logger.error(f"Error updating portfolio chart: {e}", exc_info=True)
            return {}
    
    @app.callback(
        [Output("btn-chart-value", "outline"),
         Output("btn-chart-returns", "outline"),
         Output("btn-chart-drawdown", "outline")],
        [Input("btn-chart-value", "n_clicks"),
         Input("btn-chart-returns", "n_clicks"),
         Input("btn-chart-drawdown", "n_clicks")]
    )
    def update_chart_button_styles(btn_value, btn_returns, btn_drawdown):
        """
        Update chart button styles to show which one is active.
        
        Returns:
            Button outline states
        """
        ctx = callback_context
        if not ctx.triggered:
            return False, True, True  # Default: Value chart active
        
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if button_id == "btn-chart-value":
            return False, True, True
        elif button_id == "btn-chart-returns":
            return True, False, True
        elif button_id == "btn-chart-drawdown":
            return True, True, False
        
        return False, True, True  # Default
    
    @app.callback(
        Output("monthly-returns-heatmap", "figure"),
        Input("results-section", "style")
    )
    def update_monthly_heatmap(results_style):
        """
        Update monthly returns heatmap when results section becomes visible.
        
        Args:
            results_style: Style of the results section
            
        Returns:
            Monthly returns heatmap figure
        """
        if not backtest_service or results_style.get("display") == "none":
            return {}
        
        try:
            return backtest_service.get_monthly_returns_heatmap()
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
            return backtest_service.get_signals_chart(ticker)
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