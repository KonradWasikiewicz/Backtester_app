import dash
from dash import Dash, html, dcc, Input, Output, State, ALL, MATCH, ctx, no_update
from dash.exceptions import PreventUpdate # Added import
import logging
# Make sure logging is configured appropriately elsewhere (e.g., in app_factory or main app.py)
# from ...config.logging_config import setup_logging
from src.core.constants import STRATEGY_DESCRIPTIONS # Poprawna ścieżka do stałych
from src.core.constants import DEFAULT_STRATEGY_PARAMS  # added import for default params
from src.core.constants import AVAILABLE_STRATEGIES # Ensure this is imported
from src.ui.ids import WizardIDs, StrategyConfigIDs  # Import the centralized IDs and StrategyConfigIDs
from src.ui.components.stepper import create_wizard_stepper  # Import for updating the stepper

logger = logging.getLogger(__name__)

def register_wizard_callbacks(app: Dash):
    """
    Register callbacks for the wizard interface, including step transitions and validation.
    """
    logger.info("Registering wizard and main page run button callbacks...")

    # --- Consolidated Step Transition Callback ---
    @app.callback(
        [
            # Step Content Visibility
            Output(WizardIDs.step_content("strategy-selection"), "style"),
            Output(WizardIDs.step_content("date-range-selection"), "style"),
            Output(WizardIDs.step_content("tickers-selection"), "style"),
            Output(WizardIDs.step_content("risk-management"), "style"),
            Output(WizardIDs.step_content("trading-costs"), "style"),
            Output(WizardIDs.step_content("rebalancing-rules"), "style"),
            Output(WizardIDs.step_content("wizard-summary"), "style"),
            # Header class toggles for each step
            Output(WizardIDs.step_header("strategy-selection"), "className"),
            Output(WizardIDs.step_header("date-range-selection"), "className"),
            Output(WizardIDs.step_header("tickers-selection"), "className"),
            Output(WizardIDs.step_header("risk-management"), "className"),
            Output(WizardIDs.step_header("trading-costs"), "className"),
            Output(WizardIDs.step_header("rebalancing-rules"), "className"),
            Output(WizardIDs.step_header("wizard-summary"), "className"),
            # --- UPDATED Progress Bar Output ID ---
            Output(WizardIDs.PROGRESS_BAR, "value"),
            # --- ADDED Progress Bar Style Output ---
            Output(WizardIDs.PROGRESS_BAR, "style"),
            # --- ADDED Stepper Output ---
            Output(WizardIDs.WIZARD_STEPPER, "children")
        ],
        [
            # Confirm Buttons (Inputs) - Using centralized IDs for all wizard confirm buttons
            Input(WizardIDs.CONFIRM_STRATEGY_BUTTON, "n_clicks"),
            Input(WizardIDs.CONFIRM_DATES_BUTTON, "n_clicks"),
            Input(WizardIDs.CONFIRM_TICKERS_BUTTON, "n_clicks"),
            Input(WizardIDs.CONFIRM_RISK_BUTTON, "n_clicks"),
            Input(WizardIDs.CONFIRM_COSTS_BUTTON, "n_clicks"),
            Input(WizardIDs.CONFIRM_REBALANCING_BUTTON, "n_clicks"),
            # Step Headers (Inputs) - Using WizardID helper methods
            Input(WizardIDs.step_header("strategy-selection"), "n_clicks"),
            Input(WizardIDs.step_header("date-range-selection"), "n_clicks"),
            Input(WizardIDs.step_header("tickers-selection"), "n_clicks"),
            Input(WizardIDs.step_header("risk-management"), "n_clicks"),
            Input(WizardIDs.step_header("trading-costs"), "n_clicks"),
            Input(WizardIDs.step_header("rebalancing-rules"), "n_clicks"),
            Input(WizardIDs.step_header("wizard-summary"), "n_clicks"),
            # --- ADDED Step Indicator Inputs ---
            Input(WizardIDs.step_indicator(1), "n_clicks"),
            Input(WizardIDs.step_indicator(2), "n_clicks"),
            Input(WizardIDs.step_indicator(3), "n_clicks"),
            Input(WizardIDs.step_indicator(4), "n_clicks"),
            Input(WizardIDs.step_indicator(5), "n_clicks"),
            Input(WizardIDs.step_indicator(6), "n_clicks"),
            Input(WizardIDs.step_indicator(7), "n_clicks")
        ],
        prevent_initial_call=True
    )
    def handle_step_transition(*args):
        """Handles navigation between wizard steps based on button or header clicks."""
        if not ctx.triggered:
            logger.warning("Step transition callback triggered without context.")
            return no_update

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        logger.info(f"Step transition triggered by: {trigger_id}")

        # Define step indices and names
        steps = [
            "strategy-selection", "date-range-selection", "tickers-selection",
            "risk-management", "trading-costs", "rebalancing-rules", "wizard-summary"
        ]
        step_names = [
            "Strategy",
            "Date Range",
            "Tickers",
            "Risk",
            "Costs",
            "Rebalancing",
            "Summary"
        ]
        num_steps = len(steps)
        target_step_index = 0 # Default to the first step

        # --- Determine if trigger is a header click ---
        is_header_click = "-header" in trigger_id

        try:
            # Check if trigger is one of the centralized confirm buttons
            if trigger_id == WizardIDs.CONFIRM_STRATEGY_BUTTON:
                target_step_index = 1  # Move to date selection
                logger.info(f"Confirm strategy button clicked. Target step index: {target_step_index}")
            elif trigger_id == WizardIDs.CONFIRM_DATES_BUTTON:
                target_step_index = 2  # Move to ticker selection
                logger.info(f"Confirm dates button clicked. Target step index: {target_step_index}")
            elif trigger_id == WizardIDs.CONFIRM_TICKERS_BUTTON:
                target_step_index = 3  # Move to risk management
                logger.info(f"Confirm tickers button clicked. Target step index: {target_step_index}")
            elif trigger_id == WizardIDs.CONFIRM_RISK_BUTTON:
                target_step_index = 4  # Move to trading costs
                logger.info(f"Confirm risk button clicked. Target step index: {target_step_index}")
            elif trigger_id == WizardIDs.CONFIRM_COSTS_BUTTON:
                target_step_index = 5  # Move to rebalancing
                logger.info(f"Confirm costs button clicked. Target step index: {target_step_index}")
            elif trigger_id == WizardIDs.CONFIRM_REBALANCING_BUTTON:
                target_step_index = 6  # Move to summary
                logger.info(f"Confirm rebalancing button clicked. Target step index: {target_step_index}")
            elif "-header" in trigger_id:
                header_map = {
                    WizardIDs.step_header("strategy-selection"): 0, 
                    WizardIDs.step_header("date-range-selection"): 1,
                    WizardIDs.step_header("tickers-selection"): 2, 
                    WizardIDs.step_header("risk-management"): 3,
                    WizardIDs.step_header("trading-costs"): 4, 
                    WizardIDs.step_header("rebalancing-rules"): 5, 
                    WizardIDs.step_header("wizard-summary"): 6
                }
                target_step_index = header_map.get(trigger_id)
                if target_step_index is None:
                    logger.error(f"Unknown header ID: {trigger_id}")
                    return no_update
                logger.info(f"Header '{trigger_id}' clicked. Target step index: {target_step_index}")
            # --- ADDED: Step Indicator Click Handler ---
            elif trigger_id.startswith("step-indicator-"):
                try:
                    # Extract step number from the indicator ID (1-based)
                    step_number = int(trigger_id.split("-")[-1])
                    target_step_index = step_number - 1  # Convert to 0-based index
                    logger.info(f"Step indicator {step_number} clicked. Target step index: {target_step_index}")
                except ValueError:
                    logger.error(f"Invalid step indicator ID format: {trigger_id}")
                    return no_update
            else:
                logger.error(f"Unhandled trigger ID in step transition: {trigger_id}")
                return no_update

            # --- Generate Outputs ---
            visible_style = {"display": "block", "marginLeft": "30px", "paddingTop": "10px"}
            hidden_style = {"display": "none", "marginLeft": "30px", "paddingTop": "10px"}
            step_styles = [hidden_style] * num_steps
            status_classes = ["step-status"] * num_steps # Base class

            if 0 <= target_step_index < num_steps:
                step_styles[target_step_index] = visible_style
                for i in range(num_steps):
                    if i < target_step_index: status_classes[i] += " completed"
                    elif i == target_step_index: status_classes[i] += " current"
                    else: status_classes[i] += " pending"
            else:
                logger.error(f"Invalid target_step_index calculated: {target_step_index}. Defaulting to step 0.")
                step_styles[0] = visible_style # Fallback to first step
                status_classes[0] += " current"
                for i in range(1, num_steps): status_classes[i] += " pending"

            progress = ((target_step_index + 1) / num_steps) * 100

            # --- Determine strategy progress bar style ---
            # Show if a header was clicked, otherwise no_update (run_backtest callback will hide it)
            progress_bar_style = {'display': 'block'} if is_header_click else no_update

            logger.debug(f"Returning statuses: {status_classes}")
            logger.debug(f"Returning progress: {progress}")
            logger.debug(f"Returning progress bar style: {progress_bar_style}")

            # Create updated stepper component
            updated_stepper = create_wizard_stepper(target_step_index, step_names).children

            # Return styles, classes, progress value, progress bar style, and stepper
            return step_styles + status_classes + [progress, progress_bar_style, updated_stepper]

        except Exception as e:
            logger.error(f"Error in handle_step_transition callback: {e}", exc_info=True)
            # Ensure the number of no_update matches the number of outputs
            return [no_update] * (num_steps * 2 + 3) # 7 styles + 7 classes + value + style + stepper
