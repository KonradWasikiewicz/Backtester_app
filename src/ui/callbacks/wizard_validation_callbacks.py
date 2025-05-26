"""
Real-time input validation callbacks for the wizard interface.
Provides immediate feedback for invalid inputs using dbc.FormFeedback components.
"""

import logging
from datetime import datetime, date
from dash import Input, Output, State, callback, clientside_callback, ClientsideFunction
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from src.ui.ids import WizardIDs

logger = logging.getLogger(__name__)

# Validation constants
MIN_INITIAL_CAPITAL = 1000
MAX_INITIAL_CAPITAL = 100000000  # 100 million
MIN_PERCENTAGE = 0
MAX_PERCENTAGE = 100
MIN_LOOKBACK_DAYS = 1
MAX_LOOKBACK_DAYS = 1000

def register_validation_callbacks(app):
    """Register all real-time validation callbacks for the wizard."""
    logger.info("Registering wizard validation callbacks...")
    # Step 1: Initial Capital Validation
    @app.callback(
        [
            Output(WizardIDs.INITIAL_CAPITAL_INPUT, "valid"),
            Output(WizardIDs.INITIAL_CAPITAL_INPUT, "invalid"),
            Output(WizardIDs.INITIAL_CAPITAL_FEEDBACK, "children"),
            Output(WizardIDs.INITIAL_CAPITAL_FEEDBACK, "style")
        ],
        [Input(WizardIDs.INITIAL_CAPITAL_INPUT, "value")],
        [State(WizardIDs.INITIAL_CAPITAL_INPUT, "id")]  # Use state to track if user interacted
    )
    def validate_initial_capital(capital_value, input_id):
        """Validate initial capital input in real-time."""
        # Don't validate if it's the default value and user hasn't interacted
        if capital_value is None or str(capital_value).strip() == "":
            return False, False, "", {"display": "none"}
        
        # Don't show validation for default values until user changes them
        if str(capital_value) == "100000" or str(capital_value) == "100 000":
            return True, False, "", {"display": "none"}
        
        try:
            # Remove formatting (spaces, commas) for validation
            clean_value = str(capital_value).replace(" ", "").replace(",", "")
            capital = float(clean_value)
            if capital < MIN_INITIAL_CAPITAL:
                return False, True, f"Initial capital must be at least ${MIN_INITIAL_CAPITAL:,}", {"display": "block"}
            elif capital > MAX_INITIAL_CAPITAL:
                return False, True, f"Initial capital cannot exceed ${MAX_INITIAL_CAPITAL:,}", {"display": "block"}
            else:
                return True, False, "", {"display": "none"}
        except (ValueError, TypeError):
            return False, True, "Please enter a valid number", {"display": "block"}    # Step 1: Strategy Selection Validation
    @app.callback(
        [
            Output(WizardIDs.STRATEGY_VALIDATION_FEEDBACK, "children"),
            Output(WizardIDs.STRATEGY_VALIDATION_FEEDBACK, "style")
        ],
        [Input(WizardIDs.STRATEGY_DROPDOWN, "value")],
        [State(WizardIDs.CONFIRM_STRATEGY_BUTTON, "n_clicks")]  # Only show error after user tries to confirm
    )
    def validate_strategy_selection(strategy_value, confirm_clicks):
        """Validate strategy selection."""
        # Don't show validation error until user tries to confirm or has selected something first
        if strategy_value is None and (confirm_clicks is None or confirm_clicks == 0):
            return "", {"display": "none"}
        elif strategy_value is None:
            return "Please select a strategy", {"display": "block"}
        return "", {"display": "none"}

    # Step 1: Validation on Confirm Button Click
    @app.callback(
        [
            Output(WizardIDs.STRATEGY_VALIDATION_FEEDBACK, "children", allow_duplicate=True),
            Output(WizardIDs.STRATEGY_VALIDATION_FEEDBACK, "style", allow_duplicate=True),
            Output(WizardIDs.INITIAL_CAPITAL_FEEDBACK, "children", allow_duplicate=True),
            Output(WizardIDs.INITIAL_CAPITAL_FEEDBACK, "style", allow_duplicate=True)
        ],
        [Input(WizardIDs.CONFIRM_STRATEGY_BUTTON, "n_clicks")],
        [
            State(WizardIDs.STRATEGY_DROPDOWN, "value"),
            State(WizardIDs.INITIAL_CAPITAL_INPUT, "value")
        ],
        prevent_initial_call=True
    )
    def validate_step1_on_confirm(n_clicks, strategy_value, capital_value):
        """Show validation errors when user tries to confirm Step 1."""
        if n_clicks is None or n_clicks == 0:
            return "", {"display": "none"}, "", {"display": "none"}
        
        strategy_feedback = ""
        strategy_style = {"display": "none"}
        capital_feedback = ""
        capital_style = {"display": "none"}
        
        # Validate strategy selection
        if strategy_value is None:
            strategy_feedback = "Please select a strategy"
            strategy_style = {"display": "block"}
        
        # Validate capital input
        if capital_value is None or str(capital_value).strip() == "":
            capital_feedback = "Please enter initial capital"
            capital_style = {"display": "block"}
        else:
            try:
                clean_value = str(capital_value).replace(" ", "").replace(",", "")
                capital = float(clean_value)
                if capital < MIN_INITIAL_CAPITAL:
                    capital_feedback = f"Initial capital must be at least ${MIN_INITIAL_CAPITAL:,}"
                    capital_style = {"display": "block"}
                elif capital > MAX_INITIAL_CAPITAL:
                    capital_feedback = f"Initial capital cannot exceed ${MAX_INITIAL_CAPITAL:,}"
                    capital_style = {"display": "block"}
            except (ValueError, TypeError):
                capital_feedback = "Please enter a valid number"
                capital_style = {"display": "block"}
        
        return strategy_feedback, strategy_style, capital_feedback, capital_style    # Step 2: Date Range Validation
    @app.callback(
        [
            Output(WizardIDs.DATE_START_FEEDBACK, "children"),
            Output(WizardIDs.DATE_START_FEEDBACK, "style"),
            Output(WizardIDs.DATE_END_FEEDBACK, "children"),
            Output(WizardIDs.DATE_END_FEEDBACK, "style"),
            Output(WizardIDs.DATE_RANGE_FEEDBACK, "children"),
            Output(WizardIDs.DATE_RANGE_FEEDBACK, "style")
        ],
        [
            Input(WizardIDs.DATE_RANGE_START_PICKER, "date"),
            Input(WizardIDs.DATE_RANGE_END_PICKER, "date")
        ],
        [State(WizardIDs.CONFIRM_DATES_BUTTON, "n_clicks")]
    )
    def validate_date_range(start_date, end_date, confirm_clicks):
        """Validate date range selection."""
        start_feedback = ""
        start_style = {"display": "none"}
        end_feedback = ""
        end_style = {"display": "none"}
        range_feedback = ""
        range_style = {"display": "none"}
        
        # Only validate if dates are missing and user tried to confirm
        if start_date is None and confirm_clicks and confirm_clicks > 0:
            start_feedback = "Please select a start date"
            start_style = {"display": "block"}
        
        if end_date is None and confirm_clicks and confirm_clicks > 0:
            end_feedback = "Please select an end date"
            end_style = {"display": "block"}
          # Validate date range relationship only if both dates are selected
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                
                if start_dt >= end_dt:
                    range_feedback = "End date must be after start date"
                    range_style = {"display": "block"}
                elif (end_dt - start_dt).days < 30:
                    range_feedback = "Date range should be at least 30 days"
                    range_style = {"display": "block"}
            except (ValueError, TypeError):
                range_feedback = "Invalid date format"
                range_style = {"display": "block"}
        
        return (start_feedback, start_style, end_feedback, end_style, 
                 range_feedback, range_style)

    # Step 3: Ticker Selection Validation
    @app.callback(
        [
            Output(WizardIDs.TICKER_DROPDOWN_FEEDBACK, "children"),
            Output(WizardIDs.TICKER_DROPDOWN_FEEDBACK, "style")
        ],
        [Input(WizardIDs.TICKER_DROPDOWN, "value")],
        prevent_initial_call=True
    )
    def validate_ticker_selection(ticker_values):
        """Validate ticker selection with immediate feedback."""
        if not ticker_values or len(ticker_values) == 0:
            return "Please select at least one ticker", {"display": "block"}
        elif len(ticker_values) > 50:  # Reasonable limit
            return "Too many tickers selected (maximum 50)", {"display": "block"}
        return "", {"display": "none"}

    # Step 4: Risk Management Validation
    @app.callback(
        [
            Output(WizardIDs.MAX_POSITION_SIZE_FEEDBACK, "children"),
            Output(WizardIDs.MAX_POSITION_SIZE_FEEDBACK, "style")
        ],
        [Input(WizardIDs.MAX_POSITION_SIZE_INPUT, "value")]
    )
    def validate_max_position_size(position_size):
        """Validate maximum position size."""
        if position_size is None:
            return "", {"display": "none"}
        
        try:
            size = float(position_size)
            if size < 0:
                return "Position size cannot be negative", {"display": "block"}
            elif size > 100:
                return "Position size cannot exceed 100%", {"display": "block"}
            elif size == 0:
                return "Position size should be greater than 0", {"display": "block"}
            return "", {"display": "none"}
        except (ValueError, TypeError):
            return "Please enter a valid number", {"display": "block"}

    @app.callback(
        [
            Output(WizardIDs.STOP_LOSS_FEEDBACK, "children"),
            Output(WizardIDs.STOP_LOSS_FEEDBACK, "style")
        ],
        [Input(WizardIDs.STOP_LOSS_INPUT, "value")]
    )
    def validate_stop_loss(stop_loss_value):
        """Validate stop loss percentage."""
        if stop_loss_value is None:
            return "", {"display": "none"}
        
        try:
            value = float(stop_loss_value)
            if value < 0:
                return "Stop loss cannot be negative", {"display": "block"}
            elif value > 50:
                return "Stop loss seems very high (>50%)", {"display": "block"}
            return "", {"display": "none"}
        except (ValueError, TypeError):
            return "Please enter a valid percentage", {"display": "block"}

    @app.callback(
        [
            Output(WizardIDs.TAKE_PROFIT_FEEDBACK, "children"),
            Output(WizardIDs.TAKE_PROFIT_FEEDBACK, "style")
        ],
        [Input(WizardIDs.TAKE_PROFIT_INPUT, "value")]
    )
    def validate_take_profit(take_profit_value):
        """Validate take profit percentage."""
        if take_profit_value is None:
            return "", {"display": "none"}
        
        try:
            value = float(take_profit_value)
            if value < 0:
                return "Take profit cannot be negative", {"display": "block"}
            elif value > 1000:
                return "Take profit seems very high (>1000%)", {"display": "block"}
            return "", {"display": "none"}
        except (ValueError, TypeError):
            return "Please enter a valid percentage", {"display": "block"}

    @app.callback(
        [
            Output(WizardIDs.MAX_RISK_PER_TRADE_FEEDBACK, "children"),
            Output(WizardIDs.MAX_RISK_PER_TRADE_FEEDBACK, "style")
        ],
        [Input(WizardIDs.MAX_RISK_PER_TRADE_INPUT, "value")]
    )
    def validate_max_risk_per_trade(risk_value):
        """Validate maximum risk per trade."""
        if risk_value is None:
            return "", {"display": "none"}
        
        try:
            value = float(risk_value)
            if value < 0:
                return "Risk per trade cannot be negative", {"display": "block"}
            elif value > 10:
                return "Risk per trade seems very high (>10%)", {"display": "block"}
            return "", {"display": "none"}
        except (ValueError, TypeError):
            return "Please enter a valid percentage", {"display": "block"}

    @app.callback(
        [
            Output(WizardIDs.MARKET_TREND_LOOKBACK_FEEDBACK, "children"),
            Output(WizardIDs.MARKET_TREND_LOOKBACK_FEEDBACK, "style")
        ],
        [Input(WizardIDs.MARKET_TREND_LOOKBACK_INPUT, "value")]
    )
    def validate_market_trend_lookback(lookback_value):
        """Validate market trend lookback period."""
        if lookback_value is None:
            return "", {"display": "none"}
        
        try:
            value = int(lookback_value)
            if value < MIN_LOOKBACK_DAYS:
                return f"Lookback period must be at least {MIN_LOOKBACK_DAYS} day", {"display": "block"}
            elif value > MAX_LOOKBACK_DAYS:
                return f"Lookback period cannot exceed {MAX_LOOKBACK_DAYS} days", {"display": "block"}
            return "", {"display": "none"}
        except (ValueError, TypeError):
            return "Please enter a valid number of days", {"display": "block"}

    @app.callback(
        [
            Output(WizardIDs.MAX_DRAWDOWN_FEEDBACK, "children"),
            Output(WizardIDs.MAX_DRAWDOWN_FEEDBACK, "style")
        ],
        [Input(WizardIDs.MAX_DRAWDOWN_INPUT, "value")]
    )
    def validate_max_drawdown(drawdown_value):
        """Validate maximum drawdown percentage."""
        if drawdown_value is None:
            return "", {"display": "none"}
        
        try:
            value = float(drawdown_value)
            if value < 0:
                return "Maximum drawdown cannot be negative", {"display": "block"}
            elif value > 99:
                return "Maximum drawdown cannot exceed 99%", {"display": "block"}
            return "", {"display": "none"}
        except (ValueError, TypeError):
            return "Please enter a valid percentage", {"display": "block"}

    @app.callback(
        [
            Output(WizardIDs.MAX_DAILY_LOSS_FEEDBACK, "children"),
            Output(WizardIDs.MAX_DAILY_LOSS_FEEDBACK, "style")
        ],
        [Input(WizardIDs.MAX_DAILY_LOSS_INPUT, "value")]
    )
    def validate_max_daily_loss(daily_loss_value):
        """Validate maximum daily loss percentage."""
        if daily_loss_value is None:
            return "", {"display": "none"}
        
        try:
            value = float(daily_loss_value)
            if value < 0:
                return "Maximum daily loss cannot be negative", {"display": "block"}
            elif value > 50:
                return "Maximum daily loss seems very high (>50%)", {"display": "block"}
            return "", {"display": "none"}
        except (ValueError, TypeError):
            return "Please enter a valid percentage", {"display": "block"}

    # Step 5: Trading Costs Validation
    @app.callback(
        [
            Output(WizardIDs.COMMISSION_FEEDBACK, "children"),
            Output(WizardIDs.COMMISSION_FEEDBACK, "style")
        ],
        [Input(WizardIDs.COMMISSION_INPUT, "value")]
    )
    def validate_commission(commission_value):
        """Validate commission percentage."""
        if commission_value is None:
            return "", {"display": "none"}
        
        try:
            value = float(commission_value)
            if value < 0:
                return "Commission cannot be negative", {"display": "block"}
            elif value > 5:
                return "Commission seems very high (>5%)", {"display": "block"}
            return "", {"display": "none"}
        except (ValueError, TypeError):
            return "Please enter a valid percentage", {"display": "block"}

    @app.callback(
        [
            Output(WizardIDs.SLIPPAGE_FEEDBACK, "children"),
            Output(WizardIDs.SLIPPAGE_FEEDBACK, "style")
        ],
        [Input(WizardIDs.SLIPPAGE_INPUT, "value")]
    )
    def validate_slippage(slippage_value):
        """Validate slippage percentage."""
        if slippage_value is None:
            return "", {"display": "none"}
        
        try:
            value = float(slippage_value)
            if value < 0:
                return "Slippage cannot be negative", {"display": "block"}
            elif value > 2:
                return "Slippage seems very high (>2%)", {"display": "block"}
            return "", {"display": "none"}
        except (ValueError, TypeError):
            return "Please enter a valid percentage", {"display": "block"}

    # Step 6: Rebalancing Validation
    @app.callback(
        [
            Output(WizardIDs.REBALANCING_THRESHOLD_FEEDBACK, "children"),
            Output(WizardIDs.REBALANCING_THRESHOLD_FEEDBACK, "style")
        ],
        [Input(WizardIDs.REBALANCING_THRESHOLD_INPUT, "value")]
    )
    def validate_rebalancing_threshold(threshold_value):
        """Validate rebalancing threshold percentage."""
        if threshold_value is None:
            return "", {"display": "none"}
        
        try:
            value = float(threshold_value)
            if value < 0:
                return "Rebalancing threshold cannot be negative", {"display": "block"}
            elif value > 100:
                return "Rebalancing threshold cannot exceed 100%", {"display": "block"}
            return "", {"display": "none"}
        except (ValueError, TypeError):
            return "Please enter a valid percentage", {"display": "block"}

    # Validation state aggregator - updates the validation store
    @app.callback(
        Output(WizardIDs.VALIDATION_STATE_STORE, "data"),
        [
            # Step 1: Initial Capital
            Input(WizardIDs.INITIAL_CAPITAL_INPUT, "value"),
            # Step 2: Strategy
            Input(WizardIDs.STRATEGY_DROPDOWN, "value"),
            # Step 3: Dates
            Input(WizardIDs.DATE_RANGE_START_PICKER, "date"),
            Input(WizardIDs.DATE_RANGE_END_PICKER, "date"),
            # Step 4: Tickers
            Input(WizardIDs.TICKER_DROPDOWN, "value"),
            # Step 5: Risk Management (simplified - just one key field)
            Input(WizardIDs.MAX_POSITION_SIZE_INPUT, "value"),
            # Step 6: Trading Costs (simplified)
            Input(WizardIDs.COMMISSION_INPUT, "value"),
            # Step 7: Rebalancing (simplified)
            Input(WizardIDs.REBALANCING_FREQUENCY_DROPDOWN, "value"),
        ],
        prevent_initial_call=True
    )
    def update_validation_state(initial_capital, strategy, start_date, end_date, 
                               tickers, max_position, commission, rebalancing_freq):
        """Update validation state for all steps."""
        validation_state = {
            1: True,  # Step 1: Initial Capital - default valid
            2: True,  # Step 2: Strategy - default valid  
            3: True,  # Step 3: Dates - default valid
            4: True,  # Step 4: Tickers - default valid
            5: True,  # Step 5: Risk Management - default valid
            6: True,  # Step 6: Trading Costs - default valid
            7: True,  # Step 7: Rebalancing - default valid
        }
        
        # Step 1: Initial Capital validation
        if initial_capital is not None:
            try:
                clean_value = str(initial_capital).replace(" ", "").replace(",", "")
                capital = float(clean_value)
                validation_state[1] = MIN_INITIAL_CAPITAL <= capital <= MAX_INITIAL_CAPITAL
            except (ValueError, TypeError):
                validation_state[1] = False
        else:
            validation_state[1] = False
            
        # Step 2: Strategy validation
        validation_state[2] = strategy is not None and strategy != ""
        
        # Step 3: Date validation
        if start_date and end_date:
            try:
                from datetime import datetime
                start_dt = datetime.fromisoformat(start_date)
                end_dt = datetime.fromisoformat(end_date)
                validation_state[3] = start_dt < end_dt and (end_dt - start_dt).days >= 30
            except (ValueError, TypeError):
                validation_state[3] = False
        else:
            validation_state[3] = False
            
        # Step 4: Ticker validation
        validation_state[4] = tickers is not None and len(tickers) > 0
        
        # Step 5: Risk Management validation
        if max_position is not None:
            try:
                size = float(max_position)
                validation_state[5] = 0 < size <= 100
            except (ValueError, TypeError):
                validation_state[5] = False
        else:
            validation_state[5] = False
            
        # Step 6: Trading Costs validation
        if commission is not None:
            try:
                comm = float(commission)
                validation_state[6] = 0 <= comm <= 1  # 0-1% commission
            except (ValueError, TypeError):
                validation_state[6] = False
        else:
            validation_state[6] = False
            
        # Step 7: Rebalancing validation
        validation_state[7] = rebalancing_freq is not None and rebalancing_freq != ""
        
        return validation_state

    # Confirm Button States Based on Validation
    @app.callback(
        [
            Output(WizardIDs.CONFIRM_STRATEGY_BUTTON, "disabled", allow_duplicate=True),
            Output(WizardIDs.CONFIRM_DATES_BUTTON, "disabled", allow_duplicate=True),
            Output(WizardIDs.CONFIRM_TICKERS_BUTTON, "disabled", allow_duplicate=True),
            Output(WizardIDs.CONFIRM_RISK_BUTTON, "disabled", allow_duplicate=True),
            Output(WizardIDs.CONFIRM_COSTS_BUTTON, "disabled", allow_duplicate=True),
            Output(WizardIDs.CONFIRM_REBALANCING_BUTTON, "disabled", allow_duplicate=True),
        ],
        [Input(WizardIDs.VALIDATION_STATE_STORE, "data")],
        prevent_initial_call=True
    )
    def update_confirm_button_states(validation_state):
        """Update confirm button states based on validation."""
        if not validation_state:
            # If no validation state, disable all buttons
            return [True] * 6
            
        # Map step numbers to button disable states (invert validation state)
        button_states = [
            not validation_state.get(1, False),  # Strategy button (step 1)
            not validation_state.get(3, False),  # Dates button (step 3) 
            not validation_state.get(4, False),  # Tickers button (step 4)
            not validation_state.get(5, False),  # Risk button (step 5)
            not validation_state.get(6, False),  # Costs button (step 6)
            not validation_state.get(7, False),  # Rebalancing button (step 7)
        ]
        
        return button_states

    logger.info("Wizard validation callbacks registered successfully.")
