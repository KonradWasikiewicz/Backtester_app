"""
Real-time input validation callbacks for the wizard interface.
Provides immediate feedback for invalid inputs using dbc.FormFeedback components.
Also controls button states based on validation state.
"""

import logging
from datetime import datetime, date
from dash import Input, Output, State, callback, no_update
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

# Core validation logic for button states
def validate_step_1(strategy, initial_capital):
    """Validate Step 1: Strategy + Initial Capital"""
    # Strategy must be selected
    if not strategy:
        return False
    
    # Initial capital must be valid
    if initial_capital is None:
        return False
        
    try:
        clean_value = str(initial_capital).replace(" ", "").replace(",", "")
        capital = float(clean_value)
        return MIN_INITIAL_CAPITAL <= capital <= MAX_INITIAL_CAPITAL
    except (ValueError, TypeError):
        return False

def validate_step_2(start_date, end_date):
    """Validate Step 2: Date Range (can use defaults)"""
    # Dates are optional - can use defaults
    if not start_date or not end_date:
        return True  # Allow defaults
    
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        return start_dt < end_dt and (end_dt - start_dt).days >= 30
    except (ValueError, TypeError):
        return True  # Allow defaults if invalid

def validate_step_3(tickers):
    """Validate Step 3: Tickers - CRITICAL REQUIREMENT"""
    # At least one ticker must be selected
    return tickers is not None and len(tickers) > 0

def validate_step_4(max_position_size, stop_loss, take_profit):
    """Validate Step 4: Risk Management (can use defaults)"""
    # These are optional - can use defaults
    try:
        if max_position_size is not None:
            size = float(max_position_size)
            if not (0 < size <= 100):
                return False
        
        if stop_loss is not None:
            sl = float(stop_loss)
            if sl < 0:
                return False
                
        if take_profit is not None:
            tp = float(take_profit)
            if tp < 0:
                return False
                
        return True
    except (ValueError, TypeError):
        return True  # Allow defaults

def validate_step_5(commission, slippage):
    """Validate Step 5: Trading Costs (can use defaults)"""
    try:
        if commission is not None:
            comm = float(commission)
            if comm < 0 or comm > 5:
                return False
                
        if slippage is not None:
            slip = float(slippage)
            if slip < 0 or slip > 2:
                return False
                
        return True
    except (ValueError, TypeError):
        return True  # Allow defaults

def validate_step_6(rebalancing_freq, rebalancing_threshold):
    """Validate Step 6: Rebalancing (can use defaults)"""
    try:
        if rebalancing_threshold is not None:
            threshold = float(rebalancing_threshold)
            if threshold < 0 or threshold > 100:
                return False
                
        return True
    except (ValueError, TypeError):
        return True  # Allow defaults

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
            return False, True, "Please enter a valid number", {"display": "block"}

    # Step 1: Strategy Selection Validation
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
        
        return strategy_feedback, strategy_style, capital_feedback, capital_style

    # Step 2: Date Range Validation
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

    # Step 2: Validation on Confirm Button Click
    @app.callback(
        [
            Output(WizardIDs.DATE_START_FEEDBACK, "children", allow_duplicate=True),
            Output(WizardIDs.DATE_START_FEEDBACK, "style", allow_duplicate=True),
            Output(WizardIDs.DATE_END_FEEDBACK, "children", allow_duplicate=True),
            Output(WizardIDs.DATE_END_FEEDBACK, "style", allow_duplicate=True),
            Output(WizardIDs.DATE_RANGE_FEEDBACK, "children", allow_duplicate=True),
            Output(WizardIDs.DATE_RANGE_FEEDBACK, "style", allow_duplicate=True)
        ],
        [Input(WizardIDs.CONFIRM_DATES_BUTTON, "n_clicks")],
        [
            State(WizardIDs.DATE_RANGE_START_PICKER, "date"),
            State(WizardIDs.DATE_RANGE_END_PICKER, "date")
        ],
        prevent_initial_call=True
    )
    def validate_step2_on_confirm(n_clicks, start_date, end_date):
        """Show validation errors when user tries to confirm Step 2."""
        if n_clicks is None or n_clicks == 0:
            return ("", {"display": "none"}, "", {"display": "none"}, 
                    "", {"display": "none"})
        
        start_feedback = ""
        start_style = {"display": "none"}
        end_feedback = ""
        end_style = {"display": "none"}
        range_feedback = ""
        range_style = {"display": "none"}
        
        # Validate start date
        if start_date is None:
            start_feedback = "Please select a start date"
            start_style = {"display": "block"}
        
        # Validate end date
        if end_date is None:
            end_feedback = "Please select an end date"
            end_style = {"display": "block"}
        
        # Validate date range relationship if both dates are provided
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

    # Step 3: Validation on Confirm Button Click
    @app.callback(
        [
            Output(WizardIDs.TICKER_DROPDOWN_FEEDBACK, "children", allow_duplicate=True),
            Output(WizardIDs.TICKER_DROPDOWN_FEEDBACK, "style", allow_duplicate=True)
        ],
        [Input(WizardIDs.CONFIRM_TICKERS_BUTTON, "n_clicks")],
        [State(WizardIDs.TICKER_DROPDOWN, "value")],
        prevent_initial_call=True
    )
    def validate_step3_on_confirm(n_clicks, tickers):
        """Show validation errors when user tries to confirm Step 3."""
        if n_clicks is None or n_clicks == 0:
            return "", {"display": "none"}
        
        feedback = ""
        style = {"display": "none"}
        
        # Validate ticker selection
        if not tickers or len(tickers) == 0:
            feedback = "Please select at least one ticker"
            style = {"display": "block"}
        elif len(tickers) > 50:  # Reasonable limit
            feedback = "Too many tickers selected (maximum 50)"
            style = {"display": "block"}
        
        return feedback, style

    # Step 4: Validation on Confirm Button Click
    @app.callback(
        [
            Output(WizardIDs.MAX_POSITION_SIZE_FEEDBACK, "children", allow_duplicate=True),
            Output(WizardIDs.MAX_POSITION_SIZE_FEEDBACK, "style", allow_duplicate=True),
            Output(WizardIDs.STOP_LOSS_FEEDBACK, "children", allow_duplicate=True),
            Output(WizardIDs.STOP_LOSS_FEEDBACK, "style", allow_duplicate=True),
            Output(WizardIDs.TAKE_PROFIT_FEEDBACK, "children", allow_duplicate=True),
            Output(WizardIDs.TAKE_PROFIT_FEEDBACK, "style", allow_duplicate=True)
        ],
        [Input(WizardIDs.CONFIRM_RISK_BUTTON, "n_clicks")],
        [
            State(WizardIDs.MAX_POSITION_SIZE_INPUT, "value"),
            State(WizardIDs.STOP_LOSS_INPUT, "value"),
            State(WizardIDs.TAKE_PROFIT_INPUT, "value")
        ],
        prevent_initial_call=True
    )
    def validate_step4_on_confirm(n_clicks, max_position_size, stop_loss, take_profit):
        """Show validation errors when user tries to confirm Step 4."""
        if n_clicks is None or n_clicks == 0:
            return ("", {"display": "none"}, "", {"display": "none"}, 
                    "", {"display": "none"})
        
        position_feedback = ""
        position_style = {"display": "none"}
        sl_feedback = ""
        sl_style = {"display": "none"}
        tp_feedback = ""
        tp_style = {"display": "none"}
        
        # Validate max position size
        if max_position_size is not None:
            try:
                size = float(max_position_size)
                if size < 0:
                    position_feedback = "Position size cannot be negative"
                    position_style = {"display": "block"}
                elif size > 100:
                    position_feedback = "Position size cannot exceed 100%"
                    position_style = {"display": "block"}
                elif size == 0:
                    position_feedback = "Position size should be greater than 0"
                    position_style = {"display": "block"}
            except (ValueError, TypeError):
                position_feedback = "Please enter a valid number"
                position_style = {"display": "block"}
        
        # Validate stop loss
        if stop_loss is not None:
            try:
                sl = float(stop_loss)
                if sl < 0:
                    sl_feedback = "Stop loss cannot be negative"
                    sl_style = {"display": "block"}
                elif sl > 50:
                    sl_feedback = "Stop loss seems very high (>50%)"
                    sl_style = {"display": "block"}
            except (ValueError, TypeError):
                sl_feedback = "Please enter a valid percentage"
                sl_style = {"display": "block"}
        
        # Validate take profit
        if take_profit is not None:
            try:
                tp = float(take_profit)
                if tp < 0:
                    tp_feedback = "Take profit cannot be negative"
                    tp_style = {"display": "block"}
                elif tp > 1000:
                    tp_feedback = "Take profit seems very high (>1000%)"
                    tp_style = {"display": "block"}
            except (ValueError, TypeError):
                tp_feedback = "Please enter a valid percentage"
                tp_style = {"display": "block"}
        
        return (position_feedback, position_style, sl_feedback, sl_style,
                tp_feedback, tp_style)

    # Step 5: Validation on Confirm Button Click
    @app.callback(
        [
            Output(WizardIDs.COMMISSION_FEEDBACK, "children", allow_duplicate=True),
            Output(WizardIDs.COMMISSION_FEEDBACK, "style", allow_duplicate=True),
            Output(WizardIDs.SLIPPAGE_FEEDBACK, "children", allow_duplicate=True),
            Output(WizardIDs.SLIPPAGE_FEEDBACK, "style", allow_duplicate=True)
        ],
        [Input(WizardIDs.CONFIRM_COSTS_BUTTON, "n_clicks")],
        [
            State(WizardIDs.COMMISSION_INPUT, "value"),
            State(WizardIDs.SLIPPAGE_INPUT, "value")
        ],
        prevent_initial_call=True
    )
    def validate_step5_on_confirm(n_clicks, commission, slippage):
        """Show validation errors when user tries to confirm Step 5."""
        if n_clicks is None or n_clicks == 0:
            return ("", {"display": "none"}, "", {"display": "none"})
        
        commission_feedback = ""
        commission_style = {"display": "none"}
        slippage_feedback = ""
        slippage_style = {"display": "none"}
        
        # Validate commission
        if commission is not None:
            try:
                comm = float(commission)
                if comm < 0:
                    commission_feedback = "Commission cannot be negative"
                    commission_style = {"display": "block"}
                elif comm > 5:
                    commission_feedback = "Commission seems very high (>5%)"
                    commission_style = {"display": "block"}
            except (ValueError, TypeError):
                commission_feedback = "Please enter a valid percentage"
                commission_style = {"display": "block"}
        
        # Validate slippage
        if slippage is not None:
            try:
                slip = float(slippage)
                if slip < 0:
                    slippage_feedback = "Slippage cannot be negative"
                    slippage_style = {"display": "block"}
                elif slip > 2:
                    slippage_feedback = "Slippage seems very high (>2%)"
                    slippage_style = {"display": "block"}
            except (ValueError, TypeError):
                slippage_feedback = "Please enter a valid percentage"
                slippage_style = {"display": "block"}
        
        return (commission_feedback, commission_style, slippage_feedback, slippage_style)

    # Step 6: Validation on Confirm Button Click
    @app.callback(
        [
            Output(WizardIDs.REBALANCING_THRESHOLD_FEEDBACK, "children", allow_duplicate=True),
            Output(WizardIDs.REBALANCING_THRESHOLD_FEEDBACK, "style", allow_duplicate=True)
        ],
        [Input(WizardIDs.CONFIRM_REBALANCING_BUTTON, "n_clicks")],
        [
            State(WizardIDs.REBALANCING_FREQUENCY_DROPDOWN, "value"),
            State(WizardIDs.REBALANCING_THRESHOLD_INPUT, "value")
        ],
        prevent_initial_call=True
    )
    def validate_step6_on_confirm(n_clicks, rebalancing_freq, rebalancing_threshold):
        """Show validation errors when user tries to confirm Step 6."""
        if n_clicks is None or n_clicks == 0:
            return "", {"display": "none"}
        
        feedback = ""
        style = {"display": "none"}
        
        # Validate rebalancing frequency (required)
        if not rebalancing_freq:
            feedback = "Please select a rebalancing frequency"
            style = {"display": "block"}
          # Validate rebalancing threshold if provided
        if rebalancing_threshold is not None:
            try:
                threshold = float(rebalancing_threshold)
                if threshold < 0:
                    feedback = "Rebalancing threshold cannot be negative"
                    style = {"display": "block"}
                elif threshold > 100:
                    feedback = "Rebalancing threshold cannot exceed 100%"
                    style = {"display": "block"}
            except (ValueError, TypeError):
                if not feedback:  # Don't override frequency validation error
                    feedback = "Please enter a valid percentage"
                    style = {"display": "block"}
        
        return feedback, style

    # Main validation callback that controls all button states
    @app.callback(
        [
            # Button disabled states for steps 1-6
            Output(WizardIDs.CONFIRM_STRATEGY_BUTTON, "disabled", allow_duplicate=True),
            Output(WizardIDs.CONFIRM_DATES_BUTTON, "disabled", allow_duplicate=True),
            Output(WizardIDs.CONFIRM_TICKERS_BUTTON, "disabled", allow_duplicate=True),
            Output(WizardIDs.CONFIRM_RISK_BUTTON, "disabled", allow_duplicate=True),
            Output(WizardIDs.CONFIRM_COSTS_BUTTON, "disabled", allow_duplicate=True),
            Output(WizardIDs.CONFIRM_REBALANCING_BUTTON, "disabled", allow_duplicate=True),
        ],
        [
            # Watch all relevant inputs for changes
            Input(WizardIDs.STRATEGY_DROPDOWN, "value"),
            Input(WizardIDs.INITIAL_CAPITAL_INPUT, "value"),
            Input(WizardIDs.DATE_RANGE_START_PICKER, "date"),
            Input(WizardIDs.DATE_RANGE_END_PICKER, "date"),
            Input(WizardIDs.TICKER_DROPDOWN, "value"),
            Input(WizardIDs.MAX_POSITION_SIZE_INPUT, "value"),
            Input(WizardIDs.STOP_LOSS_INPUT, "value"),
            Input(WizardIDs.TAKE_PROFIT_INPUT, "value"),
            Input(WizardIDs.COMMISSION_INPUT, "value"),
            Input(WizardIDs.SLIPPAGE_INPUT, "value"),
            Input(WizardIDs.REBALANCING_FREQUENCY_DROPDOWN, "value"),
            Input(WizardIDs.REBALANCING_THRESHOLD_INPUT, "value"),
            # Also watch confirmed steps to handle already confirmed states
            Input(WizardIDs.CONFIRMED_STEPS_STORE, "data"),
        ],
        prevent_initial_call=True
    )
    def update_button_states(strategy, initial_capital, start_date, end_date, tickers,
                           max_position_size, stop_loss, take_profit, commission, slippage, 
                           rebalancing_freq, rebalancing_threshold, confirmed_steps):
        """Update button disabled states based on step validation."""
        
        # Get confirmed steps (default to empty list)
        if confirmed_steps is None:
            confirmed_steps = []
        
        # Validate each step
        step1_valid = validate_step_1(strategy, initial_capital)
        step2_valid = validate_step_2(start_date, end_date)
        step3_valid = validate_step_3(tickers)
        step4_valid = validate_step_4(max_position_size, stop_loss, take_profit)
        step5_valid = validate_step_5(commission, slippage)
        step6_valid = validate_step_6(rebalancing_freq, rebalancing_threshold)
        
        # Button states: disabled if invalid OR already confirmed
        button_states = [
            not step1_valid or 1 in confirmed_steps,  # Strategy button
            not step2_valid or 2 in confirmed_steps,  # Dates button
            not step3_valid or 3 in confirmed_steps,  # Tickers button
            not step4_valid or 4 in confirmed_steps,  # Risk button
            not step5_valid or 5 in confirmed_steps,  # Costs button
            not step6_valid or 6 in confirmed_steps,  # Rebalancing button
        ]
        
        return button_states    # Button state management system working correctly
    logger.info("Wizard validation callbacks registered successfully")
