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
        Output('strategy-description-output', 'children'), # Zmień ID, jeśli jest inne
        Input('strategy-dropdown', 'value')               # Zmień ID, jeśli jest inne
    )
    def update_strategy_description(selected_strategy):
        """Updates the strategy description text based on the dropdown selection."""
        # Pobierz opis ze słownika, użyj domyślnego tekstu, jeśli strategia nie została znaleziona lub nie wybrano żadnej
        description_text = STRATEGY_DESCRIPTIONS.get(selected_strategy, "Select a strategy to see its description.")
        # Zwróć komponent HTML (np. akapit) z tekstem opisu
        return html.P(description_text)

    # Callback to handle step transitions
    @app.callback(
        [Output(f"{step}-container", "style") for step in [
            "strategy-selection", "date-range-selection", "tickers-selection",
            "risk-management", "trading-costs", "rebalancing-rules"
        ]],
        Output("wizard-progress", "value"),
        [Input("confirm-strategy", "n_clicks"),
         Input("confirm-dates", "n_clicks"),
         Input("confirm-tickers", "n_clicks"),
         Input("confirm-risk", "n_clicks"),
         Input("confirm-costs", "n_clicks")],
        [State("strategy-selector", "value")],
        prevent_initial_call=True
    )
    def handle_step_transition(strategy_clicks, dates_clicks, tickers_clicks, 
                             risk_clicks, costs_clicks, strategy_value):
        ctx = dash.callback_context
        if not ctx.triggered:
            return [{"display": "block" if i == 0 else "none"} for i in range(6)], 0
            
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # Map buttons to next steps
        step_mapping = {
            "confirm-strategy": 1,
            "confirm-dates": 2,
            "confirm-tickers": 3,
            "confirm-risk": 4,
            "confirm-costs": 5
        }
        
        next_step = step_mapping.get(trigger, 0)
        
        # Validate transitions
        if trigger == "confirm-strategy" and not strategy_value:
            next_step = 0
        
        # Update step visibility
        step_styles = []
        for i in range(6):
            if i == next_step:
                step_styles.append({"display": "block"})
            else:
                step_styles.append({"display": "none"})
        
        progress = (next_step / 6) * 100
        return step_styles, progress

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

    # Callback to enable/disable start backtest button
    @app.callback(
        Output("start-backtest", "disabled"),
        [Input("rebalancing-frequency", "value"),
         Input("rebalancing-threshold", "value")]
    )
    def validate_rebalancing(frequency, threshold):
        if frequency is None or threshold is None:
            return True
        return False