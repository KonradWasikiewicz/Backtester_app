"""
Simplified validation callbacks for wizard interface - works with existing button state management.
This only provides essential validation without feedback components.
"""

import logging
from datetime import datetime, date
from dash import Input, Output, State, callback
from dash.exceptions import PreventUpdate

from src.ui.ids import WizardIDs

logger = logging.getLogger(__name__)

# Validation constants
MIN_INITIAL_CAPITAL = 1000
MAX_INITIAL_CAPITAL = 100000000  # 100 million

def register_validation_callbacks(app):
    """Register minimal validation callbacks that work with existing wizard system."""
    logger.info("Registering wizard validation callbacks...")
    
    # Simple validation for initial capital input - just provide valid/invalid states
    @app.callback(
        [
            Output(WizardIDs.INITIAL_CAPITAL_INPUT, "valid"),
            Output(WizardIDs.INITIAL_CAPITAL_INPUT, "invalid")
        ],
        [Input(WizardIDs.INITIAL_CAPITAL_INPUT, "value")],
        prevent_initial_call=True
    )
    def validate_initial_capital(capital_value):
        """Simple validation for initial capital."""
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

    logger.info("Wizard validation callbacks registered successfully.")
