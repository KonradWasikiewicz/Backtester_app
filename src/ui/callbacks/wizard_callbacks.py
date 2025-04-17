import dash
from dash import html, dcc, Input, Output, State, ALL, MATCH, ctx, no_update
import logging
# Make sure logging is configured appropriately elsewhere (e.g., in app_factory or main app.py)
# from ...config.logging_config import setup_logging
from src.core.constants import STRATEGY_DESCRIPTIONS # Poprawna ścieżka do stałych
from src.core.constants import DEFAULT_STRATEGY_PARAMS  # added import for default params

logger = logging.getLogger(__name__)

def register_wizard_callbacks(app):
    """
    Register callbacks for the wizard interface, including step transitions and validation.
    """
    logger.info("Registering wizard callbacks...")

    # Removed duplicate strategy description callback (registered in strategy_callbacks)

    # --- Consolidated Step Transition Callback ---
    @app.callback(
        [
            # Step Content Visibility
            Output("strategy-selection-content", "style"),
            Output("date-range-selection-content", "style"),
            Output("tickers-selection-content", "style"),
            Output("risk-management-content", "style"),
            Output("trading-costs-content", "style"),
            Output("rebalancing-rules-content", "style"),
            Output("wizard-summary-content", "style"),
            # Header class toggles for each step
            Output("strategy-selection-header", "className"),
            Output("date-range-selection-header", "className"),
            Output("tickers-selection-header", "className"),
            Output("risk-management-header", "className"),
            Output("trading-costs-header", "className"),
            Output("rebalancing-rules-header", "className"),
            Output("wizard-summary-header", "className"),
            # Progress Bar
            Output("wizard-progress", "value")
        ],
        [
            # Confirm Buttons (Inputs) - Verify these IDs
            Input("confirm-strategy", "n_clicks"),
            Input("confirm-dates", "n_clicks"),
            Input("confirm-tickers", "n_clicks"),
            Input("confirm-risk", "n_clicks"),
            Input("confirm-costs", "n_clicks"),
            Input("confirm-rebalancing", "n_clicks"),
            # Step Headers (Inputs) - Verify these IDs
            Input("strategy-selection-header", "n_clicks"),
            Input("date-range-selection-header", "n_clicks"),
            Input("tickers-selection-header", "n_clicks"),
            Input("risk-management-header", "n_clicks"),
            Input("trading-costs-header", "n_clicks"),
            Input("rebalancing-rules-header", "n_clicks"),
            Input("wizard-summary-header", "n_clicks")
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

        # Define step indices
        steps = [
            "strategy-selection", "date-range-selection", "tickers-selection",
            "risk-management", "trading-costs", "rebalancing-rules", "wizard-summary"
        ]
        num_steps = len(steps)
        target_step_index = 0 # Default to the first step

        try:
            if "confirm-" in trigger_id:
                confirm_map = {
                    "confirm-strategy": 1, "confirm-dates": 2, "confirm-tickers": 3,
                    "confirm-risk": 4, "confirm-costs": 5, "confirm-rebalancing": 6
                }
                target_step_index = confirm_map.get(trigger_id)
                if target_step_index is None:
                    logger.error(f"Unknown confirm button ID: {trigger_id}")
                    return no_update
                logger.info(f"Confirm button '{trigger_id}' clicked. Target step index: {target_step_index}")

            elif "-header" in trigger_id:
                header_map = {
                    "strategy-selection-header": 0, "date-range-selection-header": 1,
                    "tickers-selection-header": 2, "risk-management-header": 3,
                    "trading-costs-header": 4, "rebalancing-rules-header": 5, "wizard-summary-header": 6
                }
                target_step_index = header_map.get(trigger_id)
                if target_step_index is None:
                    logger.error(f"Unknown header ID: {trigger_id}")
                    return no_update
                logger.info(f"Header '{trigger_id}' clicked. Target step index: {target_step_index}")
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

            logger.debug(f"Returning styles: {step_styles}")
            logger.debug(f"Returning statuses: {status_classes}")
            logger.debug(f"Returning progress: {progress}")

            return step_styles + status_classes + [progress]

        except Exception as e:
            logger.error(f"Error in handle_step_transition callback: {e}", exc_info=True)
            return no_update # Prevent app crash

    # --- Validation Callbacks (Crucial for enabling Confirm buttons) ---

    @app.callback(
        Output("confirm-strategy", "disabled"),
        Input("strategy-dropdown", "value"),
        prevent_initial_call=False
    )
    def validate_strategy_selection(strategy_value):
        # Enable Confirm as soon as a strategy is selected; default params assumed valid
        is_disabled = not bool(strategy_value)
        logger.debug(f"Strategy selected: {strategy_value}. Confirm button disabled: {is_disabled}")
        return is_disabled

    @app.callback(
        Output("confirm-dates", "disabled"),
        [Input("backtest-start-date", "date"), # Verify these IDs
         Input("backtest-end-date", "date")]
    )
    def validate_date_range(start_date, end_date):
        is_disabled = not (start_date and end_date)
        logger.debug(f"Dates selected: Start={start_date}, End={end_date}. Confirm Dates button disabled: {is_disabled}")
        return is_disabled

    @app.callback(
        Output("confirm-tickers", "disabled"),
        Input("ticker-input", "value") # Verify this ID (or the correct component for ticker selection)
    )
    def validate_ticker_selection(tickers):
        # Add more robust validation if needed (e.g., check format)
        is_disabled = not bool(tickers)
        logger.debug(f"Tickers selected: {tickers}. Confirm Tickers button disabled: {is_disabled}")
        return is_disabled

    @app.callback(
        Output("confirm-costs", "disabled"),
        [Input("commission-input", "value"), Input("slippage-input", "value")]
    )
    def validate_costs(commission, slippage):
        ok = commission is not None and slippage is not None
        logger.debug(f"Costs inputs: commission={commission}, slippage={slippage}, valid: {ok}")
        return not ok

    @app.callback(
        Output("confirm-rebalancing", "disabled"),
        [Input("rebalancing-frequency", "value"), Input("rebalancing-threshold", "value")]
    )
    def validate_rebalancing(frequency, threshold):
        ok = bool(frequency) and threshold is not None
        logger.debug(f"Rebalancing inputs: freq={frequency}, thresh={threshold}, valid: {ok}")
        return not ok

    logger.info("Wizard callbacks registered successfully.")

# Remember to ensure this function is called during app setup, e.g., in create_app()