import dash # Added dash back
from dash import Dash, html, dcc, Input, Output, State, ALL, MATCH, ctx, no_update, callback_context # Added callback_context
import logging
from datetime import date  # Import for date validation
# Make sure logging is configured appropriately elsewhere (e.g., in app_factory or main app.py)
# from ...config.logging_config import setup_logging
from src.core.constants import STRATEGY_DESCRIPTIONS # Poprawna ścieżka do stałych
from src.core.constants import DEFAULT_STRATEGY_PARAMS  # added import for default params
from src.core.constants import AVAILABLE_STRATEGIES # Ensure this is imported
from src.core.constants import PARAM_DESCRIPTIONS  # added import for parameter descriptions
from src.ui.ids import WizardIDs, StrategyConfigIDs # Removed PageIDs and GeneralIDs
from src.ui.components.stepper import create_wizard_stepper  # Import for updating the stepper
from src.core.data import DataLoader  # Import for ticker data
from dash.exceptions import PreventUpdate # Added PreventUpdate
import dash_bootstrap_components as dbc # Added dbc
from typing import List, Tuple, Dict # Added Dict

logger = logging.getLogger(__name__)

TOTAL_STEPS = 7

# CSS class names (ensure these are defined in style.css)
# For Stepper Indicators
STEPPER_COMPLETED_CLASS = "step-completed"
STEPPER_ACTIVE_CLASS = "current" # Changed from "step-active"
STEPPER_PENDING_CLASS = "step-pending"
# For Step Headers
HEADER_COMPLETED_CLASS = "wizard-step-header-completed"
HEADER_ACTIVE_CLASS = "wizard-step-header-current"
HEADER_PENDING_CLASS = "wizard-step-header-pending"


def register_wizard_callbacks(app: Dash): # Make sure Dash is imported if not already
    """
    Register callbacks for the wizard interface, including step transitions and validation.
    """
    logger.info("Registering wizard and main page run button callbacks...")
    
    # Track the completion status of each step - THIS IS NOW HANDLED BY THE STORE
    # completed_steps = set() 

    # Define the explicit list of confirm button IDs for steps 1-6
    confirm_button_ids_list = [
        WizardIDs.CONFIRM_STRATEGY_BUTTON,
        WizardIDs.CONFIRM_DATES_BUTTON,
        WizardIDs.CONFIRM_TICKERS_BUTTON,
        WizardIDs.CONFIRM_RISK_BUTTON,
        WizardIDs.CONFIRM_COSTS_BUTTON,
        WizardIDs.CONFIRM_REBALANCING_BUTTON
    ]

    # Define the list of step name identifiers used for headers and content areas
    STEP_NAME_IDENTIFIERS = [
        "strategy-selection", 
        "date-range-selection", 
        "tickers-selection", 
        "risk-management", 
        "trading-costs", 
        "rebalancing-rules", 
        "wizard-summary"
    ]
    # Ensure TOTAL_STEPS matches the length of STEP_NAME_IDENTIFIERS
    if TOTAL_STEPS != len(STEP_NAME_IDENTIFIERS):
        logger.error(f"TOTAL_STEPS ({TOTAL_STEPS}) does not match STEP_NAME_IDENTIFIERS length ({len(STEP_NAME_IDENTIFIERS)})")
        # Potentially raise an error or handle this mismatch, for now, logging it.

    # --- Consolidated Step Transition Callback ---
    # @app.callback( # Start of old handle_step_transition
    #     [
    #         # Step Content Visibility
    #         Output(WizardIDs.step_content("strategy-selection"), "style"),
    #         Output(WizardIDs.step_content("date-range-selection"), "style"),
    #         Output(WizardIDs.step_content("tickers-selection"), "style"),
    #         Output(WizardIDs.step_content("risk-management"), "style"),
    #         Output(WizardIDs.step_content("trading-costs"), "style"),
    #         Output(WizardIDs.step_content("rebalancing-rules"), "style"),
    #         Output(WizardIDs.step_content("wizard-summary"), "style"),
    #         # Header class toggles for each step
    #         Output(WizardIDs.step_header("strategy-selection"), "className"),
    #         Output(WizardIDs.step_header("date-range-selection"), "className"),
    #         Output(WizardIDs.step_header("tickers-selection"), "className"),
    #         Output(WizardIDs.step_header("risk-management"), "className"),
    #         Output(WizardIDs.step_header("trading-costs"), "className"),
    #         Output(WizardIDs.step_header("rebalancing-rules"), "className"),
    #         Output(WizardIDs.step_header("wizard-summary"), "className"),
    #         # --- UPDATED Progress Bar Output ID ---
    #         Output(WizardIDs.PROGRESS_BAR, "value"),
    #         # --- ADDED Progress Bar Style Output ---
    #         Output(WizardIDs.PROGRESS_BAR, "style", allow_duplicate=True),
    #         # --- ADDED Stepper Output ---
    #         Output(WizardIDs.WIZARD_STEPPER, "children")
    #     ],
    #     [
    #         # Confirm Buttons (Inputs) - Using centralized IDs for all wizard confirm buttons
    #         Input(WizardIDs.CONFIRM_STRATEGY_BUTTON, "n_clicks"),
    #         Input(WizardIDs.CONFIRM_DATES_BUTTON, "n_clicks"),
    #         Input(WizardIDs.CONFIRM_TICKERS_BUTTON, "n_clicks"),
    #         Input(WizardIDs.CONFIRM_RISK_BUTTON, "n_clicks"),
    #         Input(WizardIDs.CONFIRM_COSTS_BUTTON, "n_clicks"),
    #         Input(WizardIDs.CONFIRM_REBALANCING_BUTTON, "n_clicks"),
    #         # Step Headers (Inputs) - Using WizardID helper methods
    #         Input(WizardIDs.step_header("strategy-selection"), "n_clicks"),
    #         Input(WizardIDs.step_header("date-range-selection"), "n_clicks"),
    #         Input(WizardIDs.step_header("tickers-selection"), "n_clicks"),
    #         Input(WizardIDs.step_header("risk-management"), "n_clicks"),
    #         Input(WizardIDs.step_header("trading-costs"), "n_clicks"),
    #         Input(WizardIDs.step_header("rebalancing-rules"), "n_clicks"),
    #         Input(WizardIDs.step_header("wizard-summary"), "n_clicks"),
    #         # --- ADDED Step Indicator Inputs ---
    #         Input(WizardIDs.step_indicator(1), "n_clicks"),
    #         Input(WizardIDs.step_indicator(2), "n_clicks"),
    #         Input(WizardIDs.step_indicator(3), "n_clicks"),
    #         Input(WizardIDs.step_indicator(4), "n_clicks"),
    #         Input(WizardIDs.step_indicator(5), "n_clicks"),
    #         Input(WizardIDs.step_indicator(6), "n_clicks"),
    #         Input(WizardIDs.step_indicator(7), "n_clicks")
    #     ],
    #     [
    #         # State variables to verify steps are complete before allowing navigation
    #         State(WizardIDs.STRATEGY_DROPDOWN, "value"),  # From step 1
    #         State(WizardIDs.INITIAL_CAPITAL_INPUT, "value"),  # From step 1
    #         State(WizardIDs.DATE_RANGE_START_PICKER, "date"),  # From step 2
    #         State(WizardIDs.DATE_RANGE_END_PICKER, "date"),  # From step 2
    #         State(WizardIDs.TICKER_DROPDOWN, "value"),  # MODIFIED: Was TICKER_LIST_CONTAINER, "children"
    #         # Risk management states (step 4) - Using any applicable state from the risk step
    #         State(WizardIDs.MAX_POSITION_SIZE_INPUT, "value"),  # Example from step 4
    #         # Trading costs states (step 5) - Using any applicable state from the costs step
    #         State(WizardIDs.COMMISSION_INPUT, "value"),  # Example from step 5
    #         State(WizardIDs.SLIPPAGE_INPUT, "value"),   # Example from step 5
    #         # Rebalancing states (step 6) - Using any applicable state from the rebalancing step
    #         State(WizardIDs.REBALANCING_FREQUENCY_DROPDOWN, "value"),  # Corrected ID
    #         State(WizardIDs.REBALANCING_THRESHOLD_INPUT, "value")  # Example from step 6
    #     ],
    #     prevent_initial_call=True
    # )
    # def handle_step_transition(*args):
    #     """
    #     Handles transitions between wizard steps, updating visibility and styles accordingly.
    #     THIS CALLBACK IS NOW REPLACED BY update_wizard_state_and_ui
    #     """
    #     pass # Commented out

    @app.callback(
        Output(WizardIDs.CONFIRM_DATES_BUTTON, "disabled", allow_duplicate=True), # Added allow_duplicate
        [
            Input(WizardIDs.DATE_RANGE_START_PICKER, "date"),
            Input(WizardIDs.DATE_RANGE_END_PICKER, "date"),
        ],
        prevent_initial_call=True # Added prevent_initial_call for consistency if it was missing
    )
    def toggle_confirm_dates_button(start_date_str: str | None, end_date_str: str | None) -> bool:
        logger.debug(
            "Callback 'toggle_confirm_dates_button' triggered with start_date: %s, end_date: %s",
            start_date_str,
            end_date_str,
        )
        if not start_date_str or not end_date_str:
            logger.debug("Disabling CONFIRM_DATES_BUTTON because one or both dates are not selected.")
            return True
        try:
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
        except ValueError:
            logger.error(
                "Invalid date format received for date pickers. start_date: %s, end_date: %s",
                start_date_str,
                end_date_str,
                exc_info=True,
            )
            return True
        if start_date > end_date:
            logger.debug(
                "Disabling CONFIRM_DATES_BUTTON because start_date (%s) is after end_date (%s).",
                start_date,
                end_date,
            )
            return True
        logger.debug(
            "Enabling CONFIRM_DATES_BUTTON. Start date: %s, End date: %s",
            start_date,
            end_date,
        )
        return False

    # --- Enable/disable Strategy Step 1 Confirm button ---
    @app.callback(
        Output(WizardIDs.CONFIRM_STRATEGY_BUTTON, "disabled", allow_duplicate=True), # Added allow_duplicate
        [
            Input(WizardIDs.STRATEGY_DROPDOWN, "value"),
            Input(WizardIDs.INITIAL_CAPITAL_INPUT, "value")
        ],
        prevent_initial_call=True # Added prevent_initial_call
    )
    def toggle_confirm_strategy_button(strategy, initial_capital):
        """
        Enable the Step 1 confirm button only when a strategy is selected and valid initial capital is provided.
        """
        logger.info(
            "Callback 'toggle_confirm_strategy_button' triggered with strategy: %s, initial_capital: %s",
            strategy,
            initial_capital
        )
        
        # Check if strategy and initial capital are provided
        if not strategy:
            logger.info("Disabling CONFIRM_STRATEGY_BUTTON because strategy is not selected.")
            return True
            
        if initial_capital is None:
            logger.info("Disabling CONFIRM_STRATEGY_BUTTON because initial capital is not provided.")
            return True
        
        # Check if initial capital is a valid number and greater than minimum
        try:
            # Remove spaces and any non-numeric except dot and minus
            sanitized_capital = (
                initial_capital.replace(' ', '') if isinstance(initial_capital, str) else initial_capital
            )
            capital_value = float(sanitized_capital)
            if capital_value < 1000:  # Matches the min value in the UI
                logger.info("Disabling CONFIRM_STRATEGY_BUTTON because initial capital is less than minimum required.")
                return True
        except (ValueError, TypeError):
            logger.info("Disabling CONFIRM_STRATEGY_BUTTON due to invalid initial capital type.")
            return True
        
        # All validation passed
        logger.info(
            "Enabling CONFIRM_STRATEGY_BUTTON. Strategy: %s, Initial capital: %s",
            strategy,
            initial_capital
        )
        return False

    # --- Enable/disable Risk Confirm button ---
    @app.callback(
        Output(WizardIDs.CONFIRM_RISK_BUTTON, "disabled", allow_duplicate=True), # Added allow_duplicate
        [Input(WizardIDs.step_content("risk-management"), "style")],
        prevent_initial_call=True # Added prevent_initial_call
    )
    def toggle_confirm_risk_button(risk_content_style):
        if risk_content_style and risk_content_style.get("display") == "block":
            logger.debug("Enabling CONFIRM_RISK_BUTTON as Step 4 is visible.")
            return False
        logger.debug("Disabling CONFIRM_RISK_BUTTON as Step 4 is not visible.")
        return True

    # --- Enable/disable Costs Confirm button ---
    @app.callback(
        Output(WizardIDs.CONFIRM_COSTS_BUTTON, "disabled", allow_duplicate=True), # Added allow_duplicate
        [Input(WizardIDs.COMMISSION_INPUT, "value"),
         Input(WizardIDs.SLIPPAGE_INPUT, "value")],
        prevent_initial_call=True # Added prevent_initial_call
    )
    def toggle_confirm_costs_button(commission, slippage):
        if commission is not None and slippage is not None:
            try:
                if float(commission) >= 0 and float(slippage) >= 0:
                    logger.debug("Enabling CONFIRM_COSTS_BUTTON.")
                    return False
            except (ValueError, TypeError):
                logger.debug("Disabling CONFIRM_COSTS_BUTTON due to invalid input type.")
                return True
        logger.debug("Disabling CONFIRM_COSTS_BUTTON due to missing inputs.")
        return True

    # --- Enable/disable Rebalancing Confirm button ---
    @app.callback(
        Output(WizardIDs.CONFIRM_REBALANCING_BUTTON, "disabled", allow_duplicate=True), # Added allow_duplicate
        [Input(WizardIDs.REBALANCING_FREQUENCY_DROPDOWN, "value"),
         Input(WizardIDs.REBALANCING_THRESHOLD_INPUT, "value")],
        prevent_initial_call=True # Added prevent_initial_call
    )
    def toggle_confirm_rebalancing_button(frequency, threshold):
        if frequency is not None and threshold is not None:
            try:
                if float(threshold) >= 0:
                    logger.debug("Enabling CONFIRM_REBALANCING_BUTTON.")
                    return False
            except (ValueError, TypeError):
                logger.debug("Disabling CONFIRM_REBALANCING_BUTTON due to invalid threshold type.")
                return True
        logger.debug("Disabling CONFIRM_REBALANCING_BUTTON due to missing inputs.")
        return True

    # --- Enable/disable Run Backtest button on Summary Page ---
    @app.callback(
        Output(WizardIDs.RUN_BACKTEST_BUTTON_WIZARD, "disabled", allow_duplicate=True), # Added allow_duplicate
        [Input(WizardIDs.step_content("wizard-summary"), "style")], # This input might need review if summary visibility is also controlled by new callback
        prevent_initial_call=True # Added prevent_initial_call
    )
    def toggle_run_backtest_button(summary_content_style):
        if summary_content_style and summary_content_style.get("display") == "block":
            logger.debug("Enabling RUN_BACKTEST_BUTTON_WIZARD as Step 7 is visible.")
            return False
        logger.debug("Disabling RUN_BACKTEST_BUTTON_WIZARD as Step 7 is not visible.")
        return True

    # --- Callback for Strategy Dropdown to Update Description ---
    @app.callback(
        Output(WizardIDs.STRATEGY_DESCRIPTION_OUTPUT, "children"),
        Input(WizardIDs.STRATEGY_DROPDOWN, "value")
    )
    def update_strategy_description(selected_strategy):
        if not selected_strategy:
            return html.P("Please select a strategy to see its description.")
        description = STRATEGY_DESCRIPTIONS.get(selected_strategy, "No description available.")
        return html.Div([
            html.P(description),
        ])

    # --- Callback to Update Strategy Parameter Inputs ---    
    @app.callback(
        Output(WizardIDs.STRATEGY_PARAM_INPUTS_CONTAINER, "children"),
        Input(WizardIDs.STRATEGY_DROPDOWN, "value")
    )
    def update_strategy_parameters(selected_strategy):
        if not selected_strategy or selected_strategy not in DEFAULT_STRATEGY_PARAMS:
            return []
        params = DEFAULT_STRATEGY_PARAMS[selected_strategy]
        parameter_inputs = []
        sorted_param_keys = sorted(params.keys())
        for param_name in sorted_param_keys:
            param_value = params[param_name]
            if isinstance(param_value, dict):
                default_value = param_value.get("default", 0)
                min_value = param_value.get("min", None)
                max_value = param_value.get("max", None)
                step = param_value.get("step", 1)
                description = param_value.get("description", f"Parameter: {param_name}")
            else:
                default_value = param_value
                min_value = None
                max_value = None
                step = 1 if isinstance(default_value, int) else 0.1
                description = f"Parameter: {param_name}"
                if selected_strategy in PARAM_DESCRIPTIONS and param_name in PARAM_DESCRIPTIONS[selected_strategy]:
                    description = PARAM_DESCRIPTIONS[selected_strategy][param_name]
            parts = param_name.split('_')
            if parts[0].upper() == selected_strategy:
                display_label = ' '.join([selected_strategy] + [p.title() for p in parts[1:]])
            else:
                display_label = param_name.replace('_', ' ').title()
            tooltip_id = f"tooltip-{selected_strategy}-{param_name}"
            tooltip_icon = html.Span(
                html.I(className="fas fa-info-circle"),
                id=tooltip_id,
                style={'cursor': 'help', 'color': '#0d6efd'}
            )
            label_container = html.Div(
                [tooltip_icon, html.Label(display_label, className="ms-1")],
                className="param-label"
            )
            
            input_component = dbc.Input(
                id={"type": "strategy-parameter", "index": param_name},
                type="number",
                value=default_value,
                min=min_value,
                max=max_value,
                step=step,
                size="sm",
                style={"width": "100px"},
                className="param-input"
            )
            tooltip = dbc.Tooltip(
                description,
                target=tooltip_id,
                placement="left"
            )
            param_row = html.Div(
                [label_container, input_component, tooltip],
                className="param-row"
            )
            parameter_inputs.append(param_row)
        return html.Div([
            html.H6("Strategy Parameters", className="mb-2 mt-1"),
            html.Div(parameter_inputs, className="params-container")
        ])

    # --- Collect Strategy Parameters ---
    @app.callback(
        Output(WizardIDs.STRATEGY_PARAMS_STORE, "data"),
        [Input(WizardIDs.STRATEGY_DROPDOWN, "value"),
         Input({"type": "strategy-parameter", "index": ALL}, "value")],
        [State({"type": "strategy-parameter", "index": ALL}, "id")]
    )
    def update_strategy_params(strategy_type, param_values, param_ids):
        """
        Collect all strategy-specific parameters into the STRATEGY_PARAMS_STORE.
        This store will later be used to update the main configuration.
        """
        if not strategy_type or not param_ids or not param_values:
            logger.debug("update_strategy_params: No strategy selected or no parameters to collect")
            return {}
            
        # Build a dictionary of parameter names and values
        params = {}
        for param_id, param_value in zip(param_ids, param_values):
            if param_value is not None:  # Only include parameters with values
                param_name = param_id["index"]
                params[param_name] = param_value
                
        logger.debug(f"update_strategy_params: Collected parameters for {strategy_type}: {params}")
        return params

    # --- Collect selected strategy parameters for the summary ---    
    @app.callback(
        Output(WizardIDs.SUMMARY_STRATEGY_PARAMETERS, "children"),
        [Input(WizardIDs.STRATEGY_DROPDOWN, "value")],
        [State({"type": "strategy-param", "name": ALL}, "id"),
         State({"type": "strategy-param", "name": ALL}, "value")]
    )
    def update_strategy_parameters_summary(selected_strategy, param_ids, param_values):
        if not selected_strategy:
            return html.P("No strategy selected.")
        
        strategy_description = STRATEGY_DESCRIPTIONS.get(selected_strategy, "No description available.")
          # The parent Div (with ID WizardIDs.SUMMARY_STRATEGY_PARAMETERS) will be styled by CSS.
        # No conflicting className here.
        if not param_ids or not param_values:
            # Use H6 with summary-subtitle class for consistency with other summary items
            return html.Div([
                html.H6("Strategy:", className="summary-subtitle mt-2 mb-1"),
                html.P(f"{selected_strategy} (using default parameters)"),
                html.P(strategy_description, className="text-muted")
            ], className="summary-item")

        param_summary_items = []
        param_data = sorted(zip(param_ids, param_values), key=lambda x: x[0]["name"])
        for param_id, param_value in param_data:
            param_name = param_id["name"]
            parts = param_name.split('_')
            if parts[0].upper() == selected_strategy:
                display_label = ' '.join([selected_strategy] + [p.title() for p in parts[1:]])
            else:
                display_label = param_name.replace('_', ' ').title()
            param_summary_items.append(
                dbc.Row([
                    dbc.Col(html.Span(display_label, className="fw-bold"), width=6),
                    dbc.Col(html.Span(str(param_value)), width=6)
                ], className="mb-0") # mb-0 for tight parameter rows, CSS will handle font
            )
          # Use consistent heading styles with other summary items
        return html.Div([
            html.H6("Strategy:", className="summary-subtitle mt-2 mb-1"),
            html.P(f"{selected_strategy}"),
            html.P(strategy_description, className="text-muted"),
            html.H6("Parameters:", className="summary-subtitle mt-2 mb-1"),
            html.Div(param_summary_items, className="strategy-params-list") # Specific class for this list
        ], className="summary-item")

    # --- Summary page updates ---
    @app.callback(
        [Output(WizardIDs.SUMMARY_STRATEGY_DETAILS, "children"),  # This will now be for Initial Capital
         Output(WizardIDs.SUMMARY_DATES_DETAILS, "children"),
         Output(WizardIDs.SUMMARY_TICKERS_DETAILS, "children"),
         Output(WizardIDs.SUMMARY_RISK_DETAILS, "children"),
         Output(WizardIDs.SUMMARY_COSTS_DETAILS, "children"),
         Output(WizardIDs.SUMMARY_REBALANCING_DETAILS, "children")],
        [Input(WizardIDs.step_content("wizard-summary"), "style")],
        [State(WizardIDs.STRATEGY_DROPDOWN, "value"), # Keep strategy state for context if needed, though not directly displayed here
         State(WizardIDs.INITIAL_CAPITAL_INPUT, "value"),
         State(WizardIDs.DATE_RANGE_START_PICKER, "date"),
         State(WizardIDs.DATE_RANGE_END_PICKER, "date"),
         State(WizardIDs.TICKER_DROPDOWN, "value"),
         State(WizardIDs.MAX_POSITION_SIZE_INPUT, "value"),
         State(WizardIDs.STOP_LOSS_INPUT, "value"),
         State(WizardIDs.TAKE_PROFIT_INPUT, "value"),
         State(WizardIDs.COMMISSION_INPUT, "value"),
         State(WizardIDs.SLIPPAGE_INPUT, "value"),
         State(WizardIDs.REBALANCING_FREQUENCY_DROPDOWN, "value"),
         State(WizardIDs.REBALANCING_THRESHOLD_INPUT, "value")]
    )
    def update_summary_display(style, strategy_value, initial_capital, start_date, end_date, tickers, 
                               max_position_size, stop_loss, take_profit, commission, slippage, 
                               rebalancing_freq, rebalancing_threshold):
        # If summary step is not visible, prevent update
        if style is None or style.get("display") == "none":
            raise PreventUpdate
        
        # Prepare summary components for each section
        # Sanitize initial_capital for formatting
        sanitized_capital = (
            str(initial_capital).replace(' ', '') if isinstance(initial_capital, str) else initial_capital
        )
        try:
            capital_value = float(sanitized_capital)
        except (ValueError, TypeError):
            capital_value = 0.0
        strategy_summary = html.Div([
            html.H5("Strategy Configuration", className="summary-section-title"),
            html.P(f"Strategy Type: {strategy_value or 'Not selected'}"),
            html.P(f"Initial Capital: ${capital_value:,.2f}")
        ])
        
        date_summary = html.Div([
            html.H5("Date Range", className="summary-section-title"),
            html.P(f"Start Date: {start_date or 'Not selected'}"),
            html.P(f"End Date: {end_date or 'Not selected'}")
        ])
        
        ticker_items = []
        if tickers:
            ticker_items = [html.Li(ticker) for ticker in tickers]
        else:
            ticker_items = [html.Li("No tickers selected")]
        
        ticker_summary = html.Div([
            html.H5("Selected Tickers", className="summary-section-title"),
            html.Ul(ticker_items)
        ])
        
        risk_summary = html.Div([
            html.H5("Risk Management", className="summary-section-title"),
            html.P(f"Max Position Size: {max_position_size or 0}%"),
            html.P(f"Stop Loss: {stop_loss or 0}%"),
            html.P(f"Take Profit: {take_profit or 0}%")
        ])
        
        costs_summary = html.Div([
            html.H5("Trading Costs", className="summary-section-title"),
            html.P(f"Commission: {commission or 0} bps"),
            html.P(f"Slippage: {slippage or 0} bps")
        ])
        
        rebalancing_summary = html.Div([
            html.H5("Rebalancing Rules", className="summary-section-title"),
            html.P(f"Frequency: {rebalancing_freq or 'Not selected'}"),
            html.P(f"Threshold: {rebalancing_threshold or 0}%")
        ])
        
        return strategy_summary, date_summary, ticker_summary, risk_summary, costs_summary, rebalancing_summary

    # --- Update Main Configuration Store when reaching summary page ---
    @app.callback(
        Output(StrategyConfigIDs.STRATEGY_CONFIG_STORE_MAIN, "data"),
        Input(WizardIDs.step_content("wizard-summary"), "style"),
        [
            State(WizardIDs.STRATEGY_DROPDOWN, "value"),
            State(WizardIDs.INITIAL_CAPITAL_INPUT, "value"),
            State(WizardIDs.DATE_RANGE_START_PICKER, "date"),
            State(WizardIDs.DATE_RANGE_END_PICKER, "date"),
            State(WizardIDs.TICKER_DROPDOWN, "value"),
            State(WizardIDs.MAX_POSITION_SIZE_INPUT, "value"),
            State(WizardIDs.STOP_LOSS_INPUT, "value"),
            State(WizardIDs.TAKE_PROFIT_INPUT, "value"),
            State(WizardIDs.COMMISSION_INPUT, "value"),
            State(WizardIDs.SLIPPAGE_INPUT, "value"),
            State(WizardIDs.REBALANCING_FREQUENCY_DROPDOWN, "value"),
            State(WizardIDs.REBALANCING_THRESHOLD_INPUT, "value"),
            # Include the parameters store to get the strategy-specific parameters
            State(WizardIDs.STRATEGY_PARAMS_STORE, "data"),
            # Include the current config data to preserve any additional fields not set by the wizard
            State(StrategyConfigIDs.STRATEGY_CONFIG_STORE_MAIN, "data"),
        ],
        prevent_initial_call=True
    )
    def update_main_config_store(summary_style, strategy_type, initial_capital, start_date, end_date, 
                                tickers, max_position_size, stop_loss, take_profit, commission, 
                                slippage, rebalancing_frequency, rebalancing_threshold, 
                                strategy_params, current_config):
        """
        Update the main configuration store when the wizard summary is shown.
        This ensures the main configuration is ready when the Run Backtest button is clicked.
        """
        # If the summary is not visible, don't update
        if summary_style is None or summary_style.get("display") == "none":
            logger.debug("update_main_config_store: Summary not visible, not updating main config store")
            return dash.no_update
        
        # Start with the current config if it exists (to preserve any fields)
        config_data = current_config or {}
        
        # Update with the wizard values
        config_data.update({
            "strategy_type": strategy_type,
            "initial_capital": initial_capital,
            "start_date": start_date,
            "end_date": end_date,
            "tickers": tickers,
            "risk_management": {
                "max_position_size": max_position_size,
                "stop_loss": stop_loss,
                "take_profit": take_profit
            },
            "trading_costs": {
                "commission_bps": commission,
                "slippage_bps": slippage
            },
            "rebalancing": {
                "frequency": rebalancing_frequency,
                "threshold_pct": rebalancing_threshold
            }
        })
        
        # Add strategy-specific parameters if they exist
        if strategy_params:
            config_data["strategy_params"] = strategy_params
        
        logger.info(f"Updated main configuration store with wizard data: {config_data}")
        return config_data

    # --- Update Selected Tickers List ---
    @app.callback(
        [Output(WizardIDs.TICKER_DROPDOWN, "value"),
         Output(WizardIDs.TICKER_LIST_CONTAINER, "children"),
         Output(WizardIDs.CONFIRM_TICKERS_BUTTON, "disabled", allow_duplicate=True)], # Added allow_duplicate
        [Input(WizardIDs.TICKER_DROPDOWN, "value"),
         Input(WizardIDs.SELECT_ALL_TICKERS_BUTTON, "n_clicks"),
         Input(WizardIDs.DESELECT_ALL_TICKERS_BUTTON, "n_clicks")],
        [State(WizardIDs.TICKER_DROPDOWN, "options")],
        prevent_initial_call=True # Added prevent_initial_call=True
    )
    def update_selected_tickers(current_selected_tickers, select_all_clicks, deselect_all_clicks, available_options):
        trigger = ctx.triggered_id
        
        # Determine the new list of selected_tickers based on the trigger
        if trigger == WizardIDs.SELECT_ALL_TICKERS_BUTTON and available_options:
            new_selected_tickers = [option["value"] for option in available_options]
        elif trigger == WizardIDs.DESELECT_ALL_TICKERS_BUTTON:
            new_selected_tickers = []
        else:
            # This branch handles direct interaction with the dropdown
            new_selected_tickers = current_selected_tickers if current_selected_tickers is not None else []

        if not new_selected_tickers:
            return [], html.Div("No tickers selected. Please select at least one ticker."), True
            
        ticker_badges = []
        for ticker in new_selected_tickers:
            badge = html.Div(
                ticker,
                className="badge bg-primary me-2 mb-2 p-2"
            )
            ticker_badges.append(badge)
            
        button_disabled = len(ticker_badges) == 0
        return new_selected_tickers, html.Div(ticker_badges, className="mt-2"), button_disabled

    # --- Populate ticker dropdown options ---
    @app.callback(
        Output(WizardIDs.TICKER_DROPDOWN, "options"),
        Input(WizardIDs.step_content("tickers-selection"), "style"),
    )
    def populate_ticker_dropdown(style):
        if style is None or style.get("display") == "none":
            raise PreventUpdate
        try:
            data_loader = DataLoader()
            available_tickers = data_loader.get_available_tickers()
            return [{"label": ticker, "value": ticker} for ticker in available_tickers]
        except Exception as e:
            logger.error(f"Error loading ticker options: {e}")
            default_tickers = ["AAPL", "MSFT", "GOOG", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "WMT"]
            return [{"label": ticker, "value": ticker} for ticker in default_tickers]

    # --- The new comprehensive callback:
    @app.callback(
        [
            Output(WizardIDs.ACTIVE_STEP_STORE, "data"),
            Output(WizardIDs.CONFIRMED_STEPS_STORE, "data"),
            Output(WizardIDs.ALL_STEPS_COMPLETED_STORE, "data"),
            # Stepper indicator classNames (7 outputs) - Use WizardIDs.step_indicator
            *[Output(WizardIDs.step_indicator(i), "className") for i in range(1, TOTAL_STEPS + 1)],
            # Step header classNames (7 outputs) - Use WizardIDs.step_header with STEP_NAME_IDENTIFIERS
            *[Output(WizardIDs.step_header(STEP_NAME_IDENTIFIERS[i-1]), "className") for i in range(1, TOTAL_STEPS + 1)],
            # Step content styles (7 outputs) - Use WizardIDs.step_content with STEP_NAME_IDENTIFIERS
            *[Output(WizardIDs.step_content(STEP_NAME_IDENTIFIERS[i-1]), "style") for i in range(1, TOTAL_STEPS + 1)],
            # Confirm button disabled states (6 outputs for steps 1-6) - using explicit IDs
            *[Output(id, "disabled", allow_duplicate=True) for id in confirm_button_ids_list],
            # Run backtest button disabled state (1 output)
            Output(WizardIDs.RUN_BACKTEST_BUTTON_WIZARD, "disabled", allow_duplicate=True),
            # Progress Bar Outputs
            Output(WizardIDs.PROGRESS_BAR, "value", allow_duplicate=True),
            Output(WizardIDs.PROGRESS_BAR, "style", allow_duplicate=True),
        ],
        [
            Input(WizardIDs.ACTIVE_STEP_STORE, "data"),
            Input(WizardIDs.CONFIRMED_STEPS_STORE, "data"),
            Input(WizardIDs.ALL_STEPS_COMPLETED_STORE, "data"),
            # Stepper indicator n_clicks - Use WizardIDs.step_indicator
            *[Input(WizardIDs.step_indicator(i), "n_clicks") for i in range(1, TOTAL_STEPS + 1)],
            # Step header n_clicks - Use WizardIDs.step_header with STEP_NAME_IDENTIFIERS
            *[Input(WizardIDs.step_header(STEP_NAME_IDENTIFIERS[i-1]), "n_clicks") for i in range(1, TOTAL_STEPS + 1)],
            # Confirm button n_clicks (6 inputs) - using explicit IDs
            *[Input(id, "n_clicks") for id in confirm_button_ids_list],
            Input(WizardIDs.RUN_BACKTEST_BUTTON_WIZARD, "n_clicks"),
        ],
        prevent_initial_call=True # Changed from False to True
    )
    def update_wizard_state_and_ui(*args: Tuple[any, ...]) -> Tuple[any, ...]:
        ctx = callback_context
        # Ensure callback_context is imported: from dash import callback_context
        triggered_input_info = ctx.triggered[0]
        triggered_prop_id = triggered_input_info["prop_id"]
        
        # Argument unpacking based on new Input list
        # Stores (3) + Stepper Indicators (7) + Step Headers (7) + Confirm Buttons (6) + Run Backtest (1) = 24 args before *args
        # current_active_step = args[0]
        # current_confirmed_steps = args[1]
        # current_all_steps_completed = args[2]
        
        # Simpler: direct access based on input structure
        input_values = ctx.inputs
        current_active_step = input_values[WizardIDs.ACTIVE_STEP_STORE + ".data"]
        current_confirmed_steps = input_values[WizardIDs.CONFIRMED_STEPS_STORE + ".data"]
        current_all_steps_completed = input_values[WizardIDs.ALL_STEPS_COMPLETED_STORE + ".data"]
        
        # Initialize states if None
        if current_active_step is None: current_active_step = 1
        if current_confirmed_steps is None: current_confirmed_steps = []
        if not isinstance(current_confirmed_steps, list): current_confirmed_steps = [] # Ensure it's a list
        if current_all_steps_completed is None: current_all_steps_completed = False
        
        new_active_step = current_active_step
        new_confirmed_steps = list(current_confirmed_steps) # Make a mutable copy
        new_all_steps_completed = current_all_steps_completed

        store_outputs: List[any] = [no_update] * 3 # For the 3 dcc.Store components
        
        is_n_clicks_trigger = ".n_clicks" in triggered_prop_id
        
        if not ctx.triggered or not is_n_clicks_trigger or triggered_prop_id == ".":
            # Initial load or external store update, or non-n_clicks trigger
            store_outputs = [current_active_step, current_confirmed_steps, current_all_steps_completed]
        else:
            triggered_id_str = triggered_prop_id.split(".")[0]
            # If triggered_id_str is a dict-like string (e.g., from pattern-matching IDs), parse it
            # For now, assuming simple string IDs from the explicit list or get_... methods
            
            interaction_handled = False

            # Stepper indicator clicks
            # Corrected loop and ID generation
            for step_num_clicked in range(1, TOTAL_STEPS + 1): # step_num_clicked is 1-based
                expected_indicator_id = WizardIDs.step_indicator(step_num_clicked)
                if triggered_id_str == expected_indicator_id:
                    new_active_step = step_num_clicked
                    interaction_handled = True
                    break
            
            # Step header clicks
            # Corrected loop and ID generation
            if not interaction_handled:
                for i_idx, step_id_str_from_list in enumerate(STEP_NAME_IDENTIFIERS): # iIdx is 0-based
                    step_num_clicked = i_idx + 1 # 1-based
                    expected_header_id = WizardIDs.step_header(step_id_str_from_list)
                    if triggered_id_str == expected_header_id:
                        new_active_step = step_num_clicked
                        interaction_handled = True
                        break

            # Confirm button clicks (steps 1-6)
            if not interaction_handled:
                for idx, confirm_button_id_str in enumerate(confirm_button_ids_list):
                    if triggered_id_str == confirm_button_id_str:
                        step_num_confirmed = idx + 1 # step_num_confirmed is 1-based
                        if step_num_confirmed not in new_confirmed_steps:
                            new_confirmed_steps.append(step_num_confirmed)
                            new_confirmed_steps.sort()
                        
                        # Activate next step if current is not the last confirmable step
                        if step_num_confirmed < TOTAL_STEPS: # If step 1-6 confirmed, and it's not step 7 itself
                           # Only advance if it's not the last step (step 7 is run backtest)
                           if step_num_confirmed < TOTAL_STEPS -1: # If step 1-5 confirmed
                               new_active_step = step_num_confirmed + 1
                           elif step_num_confirmed == TOTAL_STEPS -1: # If step 6 is confirmed
                               new_active_step = TOTAL_STEPS # Activate summary (step 7)
                        else: # Should not happen here as confirm_button_ids_list is for steps 1-6
                            new_active_step = step_num_confirmed

                        interaction_handled = True
                        break
            
            # Run Backtest button click (Step 7 confirmation)
            if not interaction_handled and triggered_id_str == WizardIDs.RUN_BACKTEST_BUTTON_WIZARD:
                # Check if all prerequisites (steps 1-6) are confirmed
                prerequisites_met = all(s in new_confirmed_steps for s in range(1, TOTAL_STEPS))
                if prerequisites_met:
                    if TOTAL_STEPS not in new_confirmed_steps: # Confirm step 7
                        new_confirmed_steps.append(TOTAL_STEPS)
                        new_confirmed_steps.sort()
                    
                    # Assuming backtest run is successful upon click for this UI logic
                    new_all_steps_completed = True 
                    # Ensure all steps are marked confirmed if all_steps_completed is true
                    new_confirmed_steps = list(range(1, TOTAL_STEPS + 1))
                    new_active_step = TOTAL_STEPS # Keep step 7 active or make it active
                else:
                    # Prerequisites not met, ideally button should be disabled, but handle defensively
                    # No change in active step or confirmed steps here, button should not have been clickable
                    pass 
                interaction_handled = True

            # Determine if store outputs need to be updated
            if (interaction_handled or
               new_active_step != current_active_step or
               set(new_confirmed_steps) != set(current_confirmed_steps) or
               new_all_steps_completed != current_all_steps_completed):
                store_outputs = [new_active_step, new_confirmed_steps, new_all_steps_completed]
            # else: stores remain no_update if no relevant change occurred


        final_active_step = store_outputs[0] if store_outputs[0] is not no_update else current_active_step
        final_confirmed_steps = store_outputs[1] if store_outputs[1] is not no_update else current_confirmed_steps
        final_all_steps_completed = store_outputs[2] if store_outputs[2] is not no_update else current_all_steps_completed
        
        if final_confirmed_steps is None: final_confirmed_steps = []

        stepper_indicator_classes: List[str] = []
        step_header_classes: List[str] = []
        step_content_styles: List[Dict[str, str]] = []
        confirm_button_disabled_states: List[bool] = [False] * len(confirm_button_ids_list) # Initialize

        for i in range(1, TOTAL_STEPS + 1):
            is_confirmed = i in final_confirmed_steps
            is_active = (i == final_active_step)
            base_stepper_class = "step-indicator" # Added base class

            # Stepper and Header classes
            if final_all_steps_completed:
                stepper_indicator_classes.append(f"{base_stepper_class} {STEPPER_COMPLETED_CLASS}")
                step_header_classes.append(HEADER_COMPLETED_CLASS)
            elif is_active:
                stepper_indicator_classes.append(f"{base_stepper_class} {STEPPER_ACTIVE_CLASS}")
                step_header_classes.append(HEADER_ACTIVE_CLASS)
            elif is_confirmed:
                stepper_indicator_classes.append(f"{base_stepper_class} {STEPPER_COMPLETED_CLASS}")
                step_header_classes.append(HEADER_COMPLETED_CLASS)
            else:
                stepper_indicator_classes.append(f"{base_stepper_class} {STEPPER_PENDING_CLASS}")
                step_header_classes.append(HEADER_PENDING_CLASS)

            # Content visibility
            step_content_styles.append({'display': 'block'} if is_active else {'display': 'none'})

            # Confirm button disabled states (for steps 1-6)
            if i <= len(confirm_button_ids_list): # Steps 1 through 6
                # This callback part makes it disabled if confirmed or all completed.
                # Other specific validation callbacks might also disable it.
                confirm_button_disabled_states[i-1] = is_confirmed or final_all_steps_completed

        # Run backtest button (Step 7) disabled state
        prerequisites_for_run_backtest = list(range(1, TOTAL_STEPS)) # Steps 1-6 must be confirmed
        all_prerequisites_met = all(s in final_confirmed_steps for s in prerequisites_for_run_backtest)
        run_backtest_disabled = not all_prerequisites_met or final_all_steps_completed

        # Progress bar calculation
        progress_percentage = (len(final_confirmed_steps) / TOTAL_STEPS) * 100
        progress_bar_style = {
            "width": f"{progress_percentage}%", # Ensure width is set for dbc.Progress
            "transition": "width 0.5s ease", # Smooth transition
            # dbc.Progress uses 'color' prop for bar color, or 'bar_style' for direct style
            # For simplicity, we'll assume direct style manipulation if 'color' prop isn't used or for more control
            # However, dbc.Progress typically uses 'value' and its 'color' prop ('success', 'info')
            # Let's stick to value and style for now, assuming style overrides default color behavior if needed.
            # If using dbc.Progress with 'color' prop, this style might be less effective for bar color.
        }
        # For dbc.Progress, the color is often set by the 'color' property (e.g., "success", "info")
        # If we want to set a custom background color via style, it might need to target an inner element.
        # For now, this style sets the width. The color might be green if progress_percentage is 100 via a class,
        # or we might need another output for the 'color' prop of dbc.Progress.
        # The old callback used backgroundColor. If dbc.Progress, it's better to use its 'color' prop.
        # Let's assume for now the CSS handles the color based on value or a class.
        # The old style was: "backgroundColor": "#4CAF50" if progress_percentage >= 100 else "#375a7f"
        # This can be added to progress_bar_style if it works with dbc.Progress.

        outputs_tuple: List[any] = []
        outputs_tuple.extend(store_outputs)
        outputs_tuple.extend(stepper_indicator_classes)
        outputs_tuple.extend(step_header_classes)
        outputs_tuple.extend(step_content_styles)
        outputs_tuple.extend(confirm_button_disabled_states)
        outputs_tuple.append(run_backtest_disabled)
        outputs_tuple.append(progress_percentage) # For dbc.Progress 'value'
        outputs_tuple.append(progress_bar_style)   # For dbc.Progress 'style' or 'bar_style'
        
        return tuple(outputs_tuple)

    logger.info("Wizard callbacks registered.")