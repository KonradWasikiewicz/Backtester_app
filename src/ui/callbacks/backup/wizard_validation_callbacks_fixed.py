"""
Fixed validation callbacks for wizard interface - comprehensive button state management.
This system properly validates step requirements and controls button states.
"""

import logging
from datetime import datetime, date
from dash import Input, Output, State, callback, no_update
from dash.exceptions import PreventUpdate

from src.ui.ids import WizardIDs

logger = logging.getLogger(__name__)

# Validation constants
MIN_INITIAL_CAPITAL = 1000
MAX_INITIAL_CAPITAL = 100000000  # 100 million

def register_validation_callbacks(app):
    """Register comprehensive validation callbacks that properly control button states."""
    logger.info("Registering comprehensive wizard validation callbacks...")
    
    # Simple validation for initial capital input styling
    @app.callback(
        [
            Output(WizardIDs.INITIAL_CAPITAL_INPUT, "valid"),
            Output(WizardIDs.INITIAL_CAPITAL_INPUT, "invalid")
        ],
        [Input(WizardIDs.INITIAL_CAPITAL_INPUT, "value")],
        prevent_initial_call=True
    )
    def validate_initial_capital_styling(capital_value):
        """Simple validation for initial capital styling."""
        if capital_value is None:
            return False, False
        
        try:
            clean_value = str(capital_value).replace(" ", "").replace(",", "")
            capital = float(clean_value)
            if MIN_INITIAL_CAPITAL <= capital <= MAX_INITIAL_CAPITAL:
                return True, False
            else:
                return False, True
        except (ValueError, TypeError):
            return False, True

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
        
        return button_states

    # Validation for Run Backtest button (Step 7)
    @app.callback(
        Output(WizardIDs.RUN_BACKTEST_BUTTON_WIZARD, "disabled", allow_duplicate=True),
        [
            Input(WizardIDs.CONFIRMED_STEPS_STORE, "data"),
            Input(WizardIDs.step_content("wizard-summary"), "style"),
        ],
        [
            State(WizardIDs.STRATEGY_DROPDOWN, "value"),
            State(WizardIDs.INITIAL_CAPITAL_INPUT, "value"),
            State(WizardIDs.TICKER_DROPDOWN, "value"),
        ],
        prevent_initial_call=True
    )
    def update_run_backtest_button(confirmed_steps, summary_style, strategy, initial_capital, tickers):
        """Control Run Backtest button state."""
        
        # Must be on summary page
        if not summary_style or summary_style.get("display") != "block":
            return True
        
        # Check if critical steps are valid
        step1_valid = validate_step_1(strategy, initial_capital)
        step3_valid = validate_step_3(tickers)  # Critical: must have tickers
        
        # Must have valid strategy, capital, and tickers
        if not (step1_valid and step3_valid):
            return True
        
        # Check if essential steps are confirmed (steps 1-6)
        if confirmed_steps is None:
            confirmed_steps = []
        
        required_steps = [1, 2, 3, 4, 5, 6]
        steps_confirmed = all(step in confirmed_steps for step in required_steps)
        
        return not steps_confirmed

    logger.info("Comprehensive wizard validation callbacks registered successfully.")
