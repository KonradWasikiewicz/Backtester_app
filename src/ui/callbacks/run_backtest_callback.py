# filepath: x:\GitHub\Backtester_app\src\ui\callbacks\run_backtest_callback.py

import logging
from dash import Dash, Input, Output, State, ctx
from dash.exceptions import PreventUpdate

# Import IDs - import from ids module, not from specific componets
from src.ui.ids import WizardIDs, SharedComponentIDs

# Set up logging
logger = logging.getLogger(__name__)

print("--- Executing: src/ui/callbacks/run_backtest_callback.py ---")

def register_run_backtest_callback(app: Dash):
    """
    Registers callbacks for the run backtest functionality.
    This function specifically handles the validation of steps before allowing 
    the user to run a backtest.
    """
    print("--- register_run_backtest_callback function defined ---")
    
    @app.callback(
        # Output for the trigger store that will initiate backtest
        Output(SharedComponentIDs.RUN_BACKTEST_TRIGGER_STORE, "data"),
        # Output for error message when steps aren't completed
        Output(WizardIDs.RUN_BACKTEST_ERROR_MESSAGE, "children"),
        Output(WizardIDs.RUN_BACKTEST_ERROR_MESSAGE, "style"),
        
        # Inputs
        Input(WizardIDs.RUN_BACKTEST_BUTTON_WIZARD, "n_clicks"),
        
        # States
        State(WizardIDs.CONFIRMED_STEPS_STORE, "data"),
        State(SharedComponentIDs.RUN_BACKTEST_TRIGGER_STORE, "data"),
    )
    def handle_run_backtest_click(n_clicks, confirmed_steps, current_trigger_data):
        """
        Handles clicks on the Run Backtest button, validating that all steps are completed first.
        """
        if n_clicks is None or n_clicks == 0:
            raise PreventUpdate("No button click detected")
            
        # Default values
        error_message = ""
        error_style = {"color": "red", "marginTop": "10px", "display": "none"}
        trigger_data = current_trigger_data or {}
        
        # Update timestamp to trigger the backtest if we proceed
        trigger_data["timestamp"] = ctx.triggered_timestamp
            
        # Check if all 6 required steps are confirmed
        required_steps = list(range(1, 7))  # Steps 1-6
        
        # Check which steps are missing
        if confirmed_steps:
            missing_steps = [str(s) for s in required_steps if s not in confirmed_steps]
            
            if missing_steps:
                # Some steps are missing - show error and don't trigger backtest
                error_message = f"Before running the backtest, please complete steps: {', '.join(missing_steps)}."
                error_style["display"] = "block"
                logger.warning(f"Backtest attempted but missing steps: {missing_steps}")
                # Don't update trigger data, so backtest won't run
                return current_trigger_data, error_message, error_style
        else:
            # No steps confirmed at all
            error_message = "Please complete all configuration steps before running the backtest."
            error_style["display"] = "block"
            logger.warning("Backtest attempted but no steps confirmed")
            return current_trigger_data, error_message, error_style
            
        # All required steps confirmed, can run backtest
        logger.info("All steps validated, triggering backtest")
        return trigger_data, "", {"display": "none"}

    print("--- register_run_backtest_callback successfully registered callbacks ---")

print("--- src/ui/callbacks/run_backtest_callback.py finished execution ---")
