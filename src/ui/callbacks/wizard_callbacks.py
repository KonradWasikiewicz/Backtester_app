from dash.dependencies import Input, Output, State, MATCH, ALL
import dash
from dash import html, dcc, callback
import logging

# Import AVAILABLE_STRATEGIES
try:
    from src.core.constants import AVAILABLE_STRATEGIES
except ImportError:
    import os
    import sys
    # Add project root to path if import fails
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.core.constants import AVAILABLE_STRATEGIES

# Słownik z opisami strategii dla łatwiejszego zarządzania
STRATEGY_DESCRIPTIONS = {
    "Bollinger Bands": "Bollinger Bands measure market volatility and identify potential overbought or oversold conditions using standard deviation bands around a moving average.",
    "Relative Strength Index": "The Relative Strength Index (RSI) is a momentum oscillator that measures the speed and change of price movements to identify overbought or oversold conditions.",
    "Moving Average Crossover": "This strategy identifies trading signals based on the crossover points of two moving averages (e.g., a short-term MA crossing above or below a long-term MA)."
    # Dodaj opisy dla innych strategii, jeśli istnieją
}

# Configure logging
logger = logging.getLogger(__name__)

def register_wizard_callbacks(app):
    """
    Register callbacks for the wizard interface.
    """
    
    # Callback to show strategy description
    @callback(
        Output('strategy-description-output', 'children'), 
        Input('strategy-dropdown', 'value')
    )
    def update_strategy_description(selected_strategy):
        """Updates the strategy description text based on the dropdown selection."""
        # Get description from dictionary, use default text if strategy not found or none selected
        description_text = STRATEGY_DESCRIPTIONS.get(selected_strategy, "Select a strategy to see its description.")
        # Return HTML component with description text
        return html.P(description_text)

    # Callback to handle step transitions - new accordion-style wizard
    @app.callback(
        [
            # Control visibility of content for each step
            Output("strategy-selection-content", "style"),
            Output("date-range-selection-content", "style"),
            Output("tickers-selection-content", "style"),
            Output("risk-management-content", "style"), 
            Output("trading-costs-content", "style"),
            Output("rebalancing-rules-content", "style"),
            Output("summary-content", "style"),
            # Control the status indicators for each step
            Output("strategy-selection-status", "className"),
            Output("date-range-selection-status", "className"),
            Output("tickers-selection-status", "className"),
            Output("risk-management-status", "className"),
            Output("trading-costs-status", "className"), 
            Output("rebalancing-rules-status", "className"),
            Output("summary-status", "className"),
            # Update progress bar
            Output("wizard-progress", "value")
        ],
        [
            # Trigger on any Confirm button click
            Input("confirm-strategy", "n_clicks"),
            Input("confirm-dates", "n_clicks"),
            Input("confirm-tickers", "n_clicks"),
            Input("confirm-risk", "n_clicks"),
            Input("confirm-costs", "n_clicks"),
            Input("confirm-rebalancing", "n_clicks"),
            # Also trigger when clicking on step headers
            Input("strategy-selection-header", "n_clicks"),
            Input("date-range-selection-header", "n_clicks"),
            Input("tickers-selection-header", "n_clicks"),
            Input("risk-management-header", "n_clicks"),
            Input("trading-costs-header", "n_clicks"),
            Input("rebalancing-rules-header", "n_clicks"),
            Input("summary-header", "n_clicks")
        ],
        [
            # States needed for validation
            State("strategy-selector", "value"),
            State("strategy-selection-content", "style"),
            State("date-range-selection-content", "style"),
            State("tickers-selection-content", "style"),
            State("risk-management-content", "style"),
            State("trading-costs-content", "style"),
            State("rebalancing-rules-content", "style"),
            State("summary-content", "style")
        ],
        prevent_initial_call=True
    )
    def handle_step_transition(
        # Clicks for confirm buttons
        strategy_clicks, dates_clicks, tickers_clicks, risk_clicks, costs_clicks, rebalancing_clicks,
        # Clicks for headers
        strat_header_clicks, date_header_clicks, tick_header_clicks, risk_header_clicks, 
        costs_header_clicks, rebal_header_clicks, summary_header_clicks,
        # States for validation
        strategy_value, strat_style, dates_style, tickers_style, risk_style, costs_style, rebalancing_style, summary_style):
        
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update

        # Get triggered input
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        logger.debug(f"Wizard trigger: {trigger_id}")
        
        # Default styles (all collapsed)
        visible_style = {"display": "block", "marginLeft": "30px", "paddingTop": "10px"}
        hidden_style = {"display": "none", "marginLeft": "30px", "paddingTop": "10px"}
        
        # Get current step number from the active panel
        current_styles = [strat_style, dates_style, tickers_style, risk_style, costs_style, rebalancing_style, summary_style]
        try:
            current_step = next(i for i, style in enumerate(current_styles) if style.get("display") == "block")
        except:
            current_step = 0  # Default to first step if none is active
        
        # Calculate next step based on the trigger
        next_step = current_step  # Default to keeping the same step
        
        # Handle Confirm button clicks (move to next step)
        if "confirm-" in trigger_id:
            # Map buttons to the next step
            next_steps = {
                "confirm-strategy": 1,
                "confirm-dates": 2,
                "confirm-tickers": 3,
                "confirm-risk": 4,
                "confirm-costs": 5,
                "confirm-rebalancing": 6
            }
            
            # Only advance if it's a valid step
            if trigger_id in next_steps:
                next_step = next_steps[trigger_id]
                
                # Do basic validation
                if trigger_id == "confirm-strategy" and not strategy_value:
                    next_step = current_step  # Stay on the same step
        
        # Handle header clicks (directly open that step)
        elif "-header" in trigger_id:
            # Map headers to their corresponding steps
            header_steps = {
                "strategy-selection-header": 0,
                "date-range-selection-header": 1,
                "tickers-selection-header": 2,
                "risk-management-header": 3,
                "trading-costs-header": 4,
                "rebalancing-rules-header": 5,
                "summary-header": 6
            }
            
            if trigger_id in header_steps:
                # If clicking on the current step's header, toggle it
                if header_steps[trigger_id] == current_step:
                    # Collapse if already expanded
                    next_step = None  # Indicates collapsing all steps
                else:
                    # Otherwise switch to the clicked step
                    next_step = header_steps[trigger_id]
        
        # Create styles list for each step's content
        styles = [hidden_style] * 7  # Start with all hidden
        
        # If next_step is valid, make that step visible
        if next_step is not None and 0 <= next_step < 7:
            styles[next_step] = visible_style
            
        # Update status classes for each step
        status_classes = []
        for i in range(7):
            if i < next_step:
                status_classes.append("step-status completed")
            elif i == next_step:
                status_classes.append("step-status current")
            else:
                status_classes.append("step-status pending")
        
        # Calculate progress percentage
        progress = ((next_step + 1) / 7) * 100 if next_step is not None else 0
        
        # Return all outputs
        return styles + status_classes + [progress]
        
    # Callback to validate strategy selection
    @app.callback(
        Output("confirm-strategy", "disabled"),
        Input("strategy-selector", "value")
    )
    def validate_strategy_selection(strategy):
        return not strategy

    # Callback to validate date range
    @app.callback(
        Output("confirm-dates", "disabled"),
        [Input("backtest-start-date", "date"),
         Input("backtest-end-date", "date")]
    )
    def validate_date_range(start_date, end_date):
        return not (start_date and end_date)

    # Callback to validate ticker selection
    @app.callback(
        Output("confirm-tickers", "disabled"),
        [Input({"type": "ticker-checkbox", "index": ALL}, "value")]
    )
    def validate_ticker_selection(values):
        if not values:
            return True
        return not any(values)

    # Callback to validate risk management
    @app.callback(
        Output("confirm-risk", "disabled"),
        [Input("risk-management-inputs", "children")]
    )
    def validate_risk_management(_):
        return False

    # Callback to validate trading costs
    @app.callback(
        Output("confirm-costs", "disabled"),
        [Input("commission-input", "value"),
         Input("slippage-input", "value")]
    )
    def validate_trading_costs(commission, slippage):
        if commission is None or slippage is None:
            return True
        return False

    # Callback to validate rebalancing settings and enable "Run Backtest" button
    @app.callback(
        [Output("confirm-rebalancing", "disabled"),
         Output("run-backtest-button", "disabled")],
        [Input("rebalancing-frequency", "value"),
         Input("rebalancing-threshold", "value")]
    )
    def validate_rebalancing(frequency, threshold):
        is_valid = frequency is not None and threshold is not None
        # Both confirm button and run button depend on the same validation
        return not is_valid, not is_valid