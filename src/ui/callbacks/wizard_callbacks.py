import dash
from dash import Dash, html, dcc, Input, Output, State, ALL, MATCH, ctx, no_update
import dash_bootstrap_components as dbc  # Import Bootstrap components
from dash.exceptions import PreventUpdate # Added import
import logging
from datetime import date  # Import for date validation
# Make sure logging is configured appropriately elsewhere (e.g., in app_factory or main app.py)
# from ...config.logging_config import setup_logging
from src.core.constants import STRATEGY_DESCRIPTIONS # Poprawna ścieżka do stałych
from src.core.constants import DEFAULT_STRATEGY_PARAMS  # added import for default params
from src.core.constants import AVAILABLE_STRATEGIES # Ensure this is imported
from src.core.constants import PARAM_DESCRIPTIONS  # added import for parameter descriptions
from src.ui.ids import WizardIDs, StrategyConfigIDs  # Import the centralized IDs and StrategyConfigIDs
from src.ui.components.stepper import create_wizard_stepper  # Import for updating the stepper
from src.core.data import DataLoader  # Import for ticker data

logger = logging.getLogger(__name__)

def register_wizard_callbacks(app: Dash):
    """
    Register callbacks for the wizard interface, including step transitions and validation.
    """
    logger.info("Registering wizard and main page run button callbacks...")
    
    # Track the completion status of each step
    completed_steps = set()

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
        [
            # State variables to verify steps are complete before allowing navigation
            State(WizardIDs.STRATEGY_DROPDOWN, "value"),  # From step 1
            State(WizardIDs.INITIAL_CAPITAL_INPUT, "value"),  # From step 1
            State(WizardIDs.DATE_RANGE_START_PICKER, "date"),  # From step 2
            State(WizardIDs.DATE_RANGE_END_PICKER, "date"),  # From step 2
            State(WizardIDs.TICKER_DROPDOWN, "value"),  # MODIFIED: Was TICKER_LIST_CONTAINER, "children"
            # Risk management states (step 4) - Using any applicable state from the risk step
            State(WizardIDs.MAX_POSITION_SIZE_INPUT, "value"),  # Example from step 4
            # Trading costs states (step 5) - Using any applicable state from the costs step
            State(WizardIDs.COMMISSION_INPUT, "value"),  # Example from step 5
            State(WizardIDs.SLIPPAGE_INPUT, "value"),   # Example from step 5
            # Rebalancing states (step 6) - Using any applicable state from the rebalancing step
            State(WizardIDs.REBALANCING_FREQUENCY_DROPDOWN, "value"),  # Corrected ID
            State(WizardIDs.REBALANCING_THRESHOLD_INPUT, "value")  # Example from step 6
        ],
        prevent_initial_call=True
    )
    def handle_step_transition(*args):
        """
        Handles transitions between wizard steps, updating visibility and styles accordingly.
        """
        # Initialize outputs
        step_content_styles = [{"display": "none"}] * 7
        step_header_classes = []
        step_count = 7  # We have 7 steps in total

        # Default to the first step if no other trigger or on initial load (though prevent_initial_call=True)
        active_step_from_trigger = 1  # Default to step 1

        trigger = ctx.triggered_id

        # --- Extract states for validation (values are passed in *args after all inputs) ---
        num_inputs = sum(1 for i in ctx.inputs_list[0] if i)  # Count actual inputs

        strategy_value = args[num_inputs]
        initial_capital = args[num_inputs + 1]
        date_start = args[num_inputs + 2]
        date_end = args[num_inputs + 3]
        selected_tickers_value = args[num_inputs + 4]

        # --- Determine current step based on trigger ---
        if isinstance(trigger, str):
            if trigger == WizardIDs.CONFIRM_STRATEGY_BUTTON:
                completed_steps.add(1)
                active_step_from_trigger = 2
            elif trigger == WizardIDs.CONFIRM_DATES_BUTTON:
                completed_steps.add(2)
                active_step_from_trigger = 3
            elif trigger == WizardIDs.CONFIRM_TICKERS_BUTTON:
                completed_steps.add(3)
                active_step_from_trigger = 4
            elif trigger == WizardIDs.CONFIRM_RISK_BUTTON:
                completed_steps.add(4)
                active_step_from_trigger = 5
            elif trigger == WizardIDs.CONFIRM_COSTS_BUTTON:
                completed_steps.add(5)
                active_step_from_trigger = 6
            elif trigger == WizardIDs.CONFIRM_REBALANCING_BUTTON:
                completed_steps.add(6)
                active_step_from_trigger = 7
            elif trigger.endswith("-header"):
                step_name = trigger.replace("-header", "")
                header_to_step_map = {
                    "strategy-selection": 1, "date-range-selection": 2, "tickers-selection": 3,
                    "risk-management": 4, "trading-costs": 5, "rebalancing-rules": 6, "wizard-summary": 7
                }
                clicked_step = header_to_step_map.get(step_name, 1)
                if clicked_step == 1 or clicked_step in completed_steps or \
                   (completed_steps and clicked_step == max(completed_steps) + 1 and clicked_step <= step_count) or \
                   (not completed_steps and clicked_step == 1):
                    active_step_from_trigger = clicked_step
                else:
                    active_step_from_trigger = max(completed_steps) + 1 if completed_steps and max(completed_steps) < step_count else (1 if not completed_steps else step_count)
            elif trigger.startswith("step-indicator-"):
                indicator_step = int(trigger.split("-")[-1])
                if indicator_step == 1 or indicator_step in completed_steps or \
                   (completed_steps and indicator_step == max(completed_steps) + 1 and indicator_step <= step_count) or \
                   (not completed_steps and indicator_step == 1):
                    active_step_from_trigger = indicator_step
                else:
                    active_step_from_trigger = max(completed_steps) + 1 if completed_steps and max(completed_steps) < step_count else (1 if not completed_steps else step_count)
        else:
            active_step_from_trigger = 1
            if completed_steps:
                active_step_from_trigger = min(max(completed_steps) + 1, step_count)

        current_step = max(1, min(active_step_from_trigger, step_count))

        step_content_styles = [{"display": "block"} if (i + 1) == current_step else {"display": "none"} for i in range(step_count)]

        for i in range(step_count):
            step_num_loop = i + 1
            if step_num_loop == current_step:
                step_header_classes.append("wizard-step-header-current")
            elif step_num_loop in completed_steps:
                step_header_classes.append("wizard-step-header-completed")
            else:
                step_header_classes.append("wizard-step-header-pending")

        progress_percentage = (len(completed_steps) / step_count) * 100
        progress_bar_style = {
            "transition": "width 0.5s ease",
            "backgroundColor": "#4CAF50" if progress_percentage >= 100 else "#375a7f"
        }
        current_stepper = create_wizard_stepper(current_step, completed_steps)

        return (
            *step_content_styles,
            *step_header_classes,
            progress_percentage,
            progress_bar_style,
            current_stepper
        )

    @app.callback(
        Output(WizardIDs.CONFIRM_DATES_BUTTON, "disabled"),
        [
            Input(WizardIDs.DATE_RANGE_START_PICKER, "date"),
            Input(WizardIDs.DATE_RANGE_END_PICKER, "date"),
        ],
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
        Output(WizardIDs.CONFIRM_STRATEGY_BUTTON, "disabled"),
        [
            Input(WizardIDs.STRATEGY_DROPDOWN, "value"),
            Input(WizardIDs.INITIAL_CAPITAL_INPUT, "value")
        ]
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
        Output(WizardIDs.CONFIRM_RISK_BUTTON, "disabled"),
        [Input(WizardIDs.step_content("risk-management"), "style")]
    )
    def toggle_confirm_risk_button(risk_content_style):
        if risk_content_style and risk_content_style.get("display") == "block":
            logger.debug("Enabling CONFIRM_RISK_BUTTON as Step 4 is visible.")
            return False
        logger.debug("Disabling CONFIRM_RISK_BUTTON as Step 4 is not visible.")
        return True

    # --- Enable/disable Costs Confirm button ---
    @app.callback(
        Output(WizardIDs.CONFIRM_COSTS_BUTTON, "disabled"),
        [Input(WizardIDs.COMMISSION_INPUT, "value"),
         Input(WizardIDs.SLIPPAGE_INPUT, "value")]
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
        Output(WizardIDs.CONFIRM_REBALANCING_BUTTON, "disabled"),
        [Input(WizardIDs.REBALANCING_FREQUENCY_DROPDOWN, "value"),
         Input(WizardIDs.REBALANCING_THRESHOLD_INPUT, "value")]
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
        Output(WizardIDs.RUN_BACKTEST_BUTTON_WIZARD, "disabled"),
        [Input(WizardIDs.step_content("wizard-summary"), "style")]
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
        [Output(WizardIDs.TICKER_DROPDOWN, "value"), # ADDED Output
         Output(WizardIDs.TICKER_LIST_CONTAINER, "children"),
         Output(WizardIDs.CONFIRM_TICKERS_BUTTON, "disabled")],
        [Input(WizardIDs.TICKER_DROPDOWN, "value"),
         Input(WizardIDs.SELECT_ALL_TICKERS_BUTTON, "n_clicks"),
         Input(WizardIDs.DESELECT_ALL_TICKERS_BUTTON, "n_clicks")],
        [State(WizardIDs.TICKER_DROPDOWN, "options")]
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