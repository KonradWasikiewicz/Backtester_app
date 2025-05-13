import dash
from dash import Dash, html, dcc, Input, Output, State, ALL, MATCH, ctx, no_update
import dash_bootstrap_components as dbc  # Import Bootstrap components
from dash.exceptions import PreventUpdate # Added import
import logging
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
        step_content_styles = []
        step_header_classes = []
        step_count = 7  # We have 7 steps in total
        
        # Default display style for hidden step content
        hidden_style = {"display": "none"}
        visible_style = {"display": "block"}
        
        # Preset all steps as hidden initially
        for _ in range(step_count):
            step_content_styles.append(hidden_style.copy())
            step_header_classes.append("wizard-step-header")
        
        # Default to the first step if no other trigger
        current_step = 1
        
        # Callback context and parameters
        trigger = ctx.triggered_id
        
        # Extract relevant states
        # Subtract all inputs to get to the first state index
        first_state_index = len(ctx.inputs)  # All inputs length
        
        # Extract states for each step
        strategy_value = args[first_state_index]
        initial_capital = args[first_state_index + 1]
        date_start = args[first_state_index + 2]
        date_end = args[first_state_index + 3]
        selected_tickers_value = args[first_state_index + 4]  # MODIFIED: Was selected_tickers, now from dropdown value
        max_position_size = args[first_state_index + 5]
        commission_value = args[first_state_index + 6]
        slippage_value = args[first_state_index + 7]
        rebalancing_freq = args[first_state_index + 8]
        rebalancing_threshold = args[first_state_index + 9]
        
        # Track completed steps based on required inputs
        if strategy_value and initial_capital:
            completed_steps.add(1)
        if date_start and date_end:
            completed_steps.add(2)
        # MODIFIED: Check selected_tickers_value (list of strings from dropdown)
        if selected_tickers_value and isinstance(selected_tickers_value, list) and len(selected_tickers_value) > 0:
            completed_steps.add(3)
        if max_position_size is not None:  # This might need a more comprehensive check depending on risk requirements
            completed_steps.add(4)
        if commission_value is not None and slippage_value is not None:  # This might need a more comprehensive check
            completed_steps.add(5)
        if rebalancing_freq and rebalancing_threshold is not None:  # This might need a more comprehensive check
            completed_steps.add(6)
        
        # Handle different trigger types
        if isinstance(trigger, str):
            # Handle button clicks
            if trigger == WizardIDs.CONFIRM_STRATEGY_BUTTON and 1 in completed_steps:
                current_step = 2
            elif trigger == WizardIDs.CONFIRM_DATES_BUTTON and 2 in completed_steps:
                current_step = 3
            elif trigger == WizardIDs.CONFIRM_TICKERS_BUTTON and 3 in completed_steps:
                current_step = 4
            elif trigger == WizardIDs.CONFIRM_RISK_BUTTON and 4 in completed_steps:
                current_step = 5
            elif trigger == WizardIDs.CONFIRM_COSTS_BUTTON and 5 in completed_steps:
                current_step = 6
            elif trigger == WizardIDs.CONFIRM_REBALANCING_BUTTON and 6 in completed_steps:
                current_step = 7
            # Handle step header clicks for navigation
            elif trigger.endswith("-header"):
                # Extract step number from header ID
                step_name = trigger.replace("-header", "")
                if step_name == "strategy-selection":
                    current_step = 1
                elif step_name == "date-range-selection" and 1 in completed_steps:
                    current_step = 2
                elif step_name == "tickers-selection" and 2 in completed_steps:
                    current_step = 3
                elif step_name == "risk-management" and 3 in completed_steps:
                    current_step = 4
                elif step_name == "trading-costs" and 4 in completed_steps:
                    current_step = 5
                elif step_name == "rebalancing-rules" and 5 in completed_steps:
                    current_step = 6
                elif step_name == "wizard-summary" and 6 in completed_steps:
                    current_step = 7
            # --- ADDED: Handle step indicator clicks ---
            elif trigger.startswith("step-indicator-"):
                # Extract step number from indicator ID
                indicator_step = int(trigger.split("-")[-1])
                
                # Only allow navigation to completed steps or the next incomplete step
                if indicator_step in completed_steps or indicator_step == 1 or indicator_step == max(completed_steps) + 1:
                    current_step = indicator_step
        
        # Mark the current step content as visible and header as active
        if 1 <= current_step <= step_count:
            step_content_styles[current_step - 1] = visible_style
            step_header_classes[current_step - 1] = "wizard-step-header active"
            
            # Also mark completed steps with a different style
            for completed_step in completed_steps:
                if completed_step != current_step and 1 <= completed_step <= step_count:
                    step_header_classes[completed_step - 1] = "wizard-step-header completed"
        
        # Calculate progress percentage - one-indexed
        progress_percentage = (len(completed_steps) / step_count) * 100
        
        # Set progress bar color based on completion
        progress_bar_style = {
            "transition": "width 0.5s ease",
            "backgroundColor": "#4CAF50" if progress_percentage >= 100 else "#375a7f"
        }
        
        # Create or update the stepper
        current_stepper = create_wizard_stepper(current_step, completed_steps)
        
        return (
            *step_content_styles,
            *step_header_classes,
            progress_percentage,
            progress_bar_style,
            current_stepper
        )

    # --- Callback for Strategy Dropdown to Update Description ---
    @app.callback(
        Output(WizardIDs.STRATEGY_DESCRIPTION_OUTPUT, "children"),
        Input(WizardIDs.STRATEGY_DROPDOWN, "value")
    )
    def update_strategy_description(selected_strategy):
        """
        Updates the strategy description text based on the selected strategy.
        """
        if not selected_strategy:
            # Return a default message if no strategy is selected
            return html.P("Please select a strategy to see its description.")
        
        # Get the description for the selected strategy from our constants
        description = STRATEGY_DESCRIPTIONS.get(selected_strategy, "No description available.")
        
        # Return formatted description
        return html.Div([
            html.P(description),            # You could add more details, parameters, or examples here if needed
        ])
        
    # --- Callback to Update Strategy Parameter Inputs ---    
    @app.callback(
        Output(WizardIDs.STRATEGY_PARAM_INPUTS_CONTAINER, "children"),
        Input(WizardIDs.STRATEGY_DROPDOWN, "value")
    )
    def update_strategy_parameters(selected_strategy):
        """
        Dynamically generate parameter input fields based on the selected strategy.
        """
        if not selected_strategy or selected_strategy not in DEFAULT_STRATEGY_PARAMS:
            return []  # Return empty list if no strategy selected or no parameters defined
        
        # Get the parameters for the selected strategy
        params = DEFAULT_STRATEGY_PARAMS[selected_strategy]
        
        # Create input fields for each parameter
        parameter_inputs = []
        
        # Sort parameters for consistent display order
        sorted_param_keys = sorted(params.keys())
        
        for param_name in sorted_param_keys:
            param_value = params[param_name]
            # Check if param_value is a dictionary (for advanced configuration) or a simple value
            if isinstance(param_value, dict):
                # Extract parameter configuration from dictionary
                default_value = param_value.get("default", 0)
                min_value = param_value.get("min", None)
                max_value = param_value.get("max", None)
                step = param_value.get("step", 1)
                description = param_value.get("description", f"Parameter: {param_name}")
            else:
                # Use the simple value directly
                default_value = param_value
                min_value = None
                max_value = None
                step = 1 if isinstance(default_value, int) else 0.1
                # Get description from PARAM_DESCRIPTIONS if available
                description = f"Parameter: {param_name}"
                if selected_strategy in PARAM_DESCRIPTIONS and param_name in PARAM_DESCRIPTIONS[selected_strategy]:
                    description = PARAM_DESCRIPTIONS[selected_strategy][param_name]
            
            # Create a formatted display label (following same pattern as strategy_callbacks)
            parts = param_name.split('_')
            if parts[0].upper() == selected_strategy:
                display_label = ' '.join([selected_strategy] + [p.title() for p in parts[1:]])
            else:
                display_label = param_name.replace('_', ' ').title()
              # Create tooltip ID
            tooltip_id = f"tooltip-{selected_strategy}-{param_name}"
            
            # Tooltip icon for parameter description
            tooltip_icon = html.Span(
                html.I(className="fas fa-info-circle"),
                id=tooltip_id,
                style={'cursor': 'help', 'color': '#0d6efd'}
            )
            
            # Label container with fixed width for alignment
            # Remove the htmlFor attribute since we can't directly reference pattern-matching IDs this way
            label_container = html.Div(
                [tooltip_icon, html.Label(display_label, className="ms-1")],
                className="param-label"
            )
            
            # Input component styled like other app inputs
            input_component = dbc.Input(
                id={"type": "strategy-param", "name": param_name},
                type="number",
                value=default_value,
                min=min_value,
                max=max_value,
                step=step,
                size="sm",
                style={"width": "100px"}, # Fixed width for consistent layout
                className="param-input"
            )
            
            # Tooltip for parameter description
            tooltip = dbc.Tooltip(
                description,
                target=tooltip_id,
                placement="left"
            )
              # Create parameter input row with proper styling
            param_row = html.Div(
                [label_container, input_component, tooltip],
                className="param-row"
            )
            
            parameter_inputs.append(param_row)
        
        # Wrap all inputs in a container with styling
        return html.Div([
            html.H6("Strategy Parameters", className="mb-2 mt-1"),
            html.Div(parameter_inputs, className="params-container")
        ])
        
    # --- Additional callbacks for the wizard would follow here ---
    
    # For example, callbacks to:
    # - Validate inputs for each step
    # - Add/remove tickers from the selected list
    # - Update date ranges based on available data
    # - Toggle risk management features
    
    # To avoid making this file too long, implementation details for these additional callbacks
    # can be added as needed, or potentially split into separate modules.

    # --- Collect selected strategy parameters for the summary ---    
    @app.callback(
        Output(WizardIDs.SUMMARY_STRATEGY_PARAMETERS, "children"),
        [Input(WizardIDs.STRATEGY_DROPDOWN, "value")],
        [State({"type": "strategy-param", "name": ALL}, "id"),
         State({"type": "strategy-param", "name": ALL}, "value")]
    )
    def update_strategy_parameters_summary(selected_strategy, param_ids, param_values):
        """Collect and format strategy parameters for the summary screen."""
        if not selected_strategy:
            return html.P("No strategy selected.")
        
        if not param_ids or not param_values:
            return html.P(f"Strategy: {selected_strategy} (using default parameters)")
        
        # Create a summary of selected parameters
        param_summary_items = []
        
        # Get strategy description
        strategy_description = STRATEGY_DESCRIPTIONS.get(selected_strategy, "No description available.")
        
        # Sort parameters by name to ensure consistent display order
        param_data = sorted(zip(param_ids, param_values), key=lambda x: x[0]["name"])
        
        for param_id, param_value in param_data:
            param_name = param_id["name"]
            
            # Create a formatted display label like in the input fields
            parts = param_name.split('_')
            if parts[0].upper() == selected_strategy:
                display_label = ' '.join([selected_strategy] + [p.title() for p in parts[1:]])
            else:
                display_label = param_name.replace('_', ' ').title()
            
            # Format parameter row with Bootstrap styling
            param_summary_items.append(
                dbc.Row([
                    dbc.Col(html.Span(display_label, className="fw-bold"), width=6),
                    dbc.Col(html.Span(str(param_value)), width=6)
                ], className="mb-1")
            )
        
        # Return a more structured and styled summary
        return html.Div([
            html.H5(f"Strategy: {selected_strategy}", className="mt-2 mb-2"),
            html.P(strategy_description, className="text-muted mb-3"),
            html.H6("Parameters:", className="mb-2"),
            html.Div(param_summary_items, className="ps-3 pe-3 pb-2 pt-1 border-start border-light")
        ], className="summary-section")

    # --- Summary page updates ---
    @app.callback(
        [Output(WizardIDs.SUMMARY_STRATEGY_DETAILS, "children"),
         Output(WizardIDs.SUMMARY_DATES_DETAILS, "children"),
         Output(WizardIDs.SUMMARY_TICKERS_DETAILS, "children"),
         Output(WizardIDs.SUMMARY_RISK_DETAILS, "children"),
         Output(WizardIDs.SUMMARY_COSTS_DETAILS, "children"),
         Output(WizardIDs.SUMMARY_REBALANCING_DETAILS, "children")],
        [Input(WizardIDs.step_header(WizardIDs.SUMMARY_CONTAINER), "n_clicks")],
        [State(WizardIDs.STRATEGY_DROPDOWN, "value"),
         State(WizardIDs.INITIAL_CAPITAL_INPUT, "value"),
         State(WizardIDs.DATE_RANGE_START_PICKER, "date"),
         State(WizardIDs.DATE_RANGE_END_PICKER, "date"),
         State(WizardIDs.TICKER_DROPDOWN, "value"),  # MODIFIED: Was TICKER_LIST_CONTAINER
         State(WizardIDs.MAX_POSITION_SIZE_INPUT, "value"),
         State(WizardIDs.STOP_LOSS_INPUT, "value"),
         State(WizardIDs.TAKE_PROFIT_INPUT, "value"),
         State(WizardIDs.COMMISSION_INPUT, "value"),
         State(WizardIDs.SLIPPAGE_INPUT, "value"),
         State(WizardIDs.REBALANCING_FREQUENCY_DROPDOWN, "value"),
         State(WizardIDs.REBALANCING_THRESHOLD_INPUT, "value")]
    )
    def update_wizard_summary(n_clicks, strategy, initial_capital, start_date, end_date, 
                             selected_tickers_dropdown_value, max_position, stop_loss, take_profit, 
                             commission, slippage, rebalancing_freq, rebalancing_threshold):
        """Update the wizard summary page with all selected configurations."""
        if n_clicks is None:
            # Don't update on initial load
            raise PreventUpdate
            
        # Format strategy summary
        strategy_summary = html.Div([
            html.P(f"Strategy: {strategy}"),
            html.P(f"Initial Capital: ${initial_capital:,.2f}")
        ])
        
        # Format date range summary
        date_summary = html.Div([
            html.P(f"Backtest Period: {start_date} to {end_date}")
        ])
        
        # MODIFIED: Extract ticker names directly from the dropdown value
        ticker_names = selected_tickers_dropdown_value if selected_tickers_dropdown_value else []
        
        # Format ticker summary
        ticker_summary = html.Div([
            html.P(f"Selected Tickers: {', '.join(ticker_names) if ticker_names else 'None'}")
        ])
        
        # Format risk management summary
        risk_summary = html.Div([
            html.P(f"Maximum Position Size: {max_position}%"),
            html.P(f"Stop Loss: {stop_loss}%"),
            html.P(f"Take Profit: {take_profit}%")
        ])
          # Format trading costs summary
        costs_summary = html.Div([
            html.P(f"Commission: {commission}%"),
            html.P(f"Slippage: {slippage}%")
        ])
          # Format rebalancing summary
        rebalancing_summary = html.Div([
            html.P(f"Rebalancing Frequency: {rebalancing_freq}"),
            html.P(f"Rebalancing Threshold: {rebalancing_threshold}%")
        ])
        
        return (strategy_summary, date_summary, ticker_summary, 
                risk_summary, costs_summary, rebalancing_summary)                
    # --- Enable/disable Strategy Confirm button based on selection ---
    @app.callback(
        Output(WizardIDs.CONFIRM_STRATEGY_BUTTON, "disabled"),
        [Input(WizardIDs.STRATEGY_DROPDOWN, "value"),
         Input(WizardIDs.INITIAL_CAPITAL_INPUT, "value")]
    )
    def toggle_strategy_confirm_button(selected_strategy, initial_capital):
        """Enable the confirm button when both a strategy is selected and initial capital is provided"""
        if not selected_strategy:
            return True  # Keep button disabled if no strategy selected
            
        # Handle text input that might contain spaces or other formatting
        if initial_capital is not None:
            try:
                # Remove spaces and convert to float
                if isinstance(initial_capital, str):
                    initial_capital = float(initial_capital.replace(" ", ""))
                else:
                    initial_capital = float(initial_capital)
                
                if initial_capital > 0:
                    return False  # Enable button
            except (ValueError, TypeError):
                pass  # If conversion fails, keep the button disabled
                
        return True  # Keep button disabled in all other cases

    # --- Update Selected Tickers List ---
    @app.callback(
        [Output(WizardIDs.TICKER_LIST_CONTAINER, "children"),
         Output(WizardIDs.CONFIRM_TICKERS_BUTTON, "disabled")],
        [Input(WizardIDs.TICKER_DROPDOWN, "value"),
         Input(WizardIDs.SELECT_ALL_TICKERS_BUTTON, "n_clicks"),
         Input(WizardIDs.DESELECT_ALL_TICKERS_BUTTON, "n_clicks")],
        [State(WizardIDs.TICKER_DROPDOWN, "options")]
    )
    def update_selected_tickers(selected_tickers, select_all_clicks, deselect_all_clicks, available_options):
        """
        Update the selected tickers container and enable/disable the confirm button.
        """
        trigger = ctx.triggered_id
        
        # Handle Select All / Deselect All actions
        if trigger == WizardIDs.SELECT_ALL_TICKERS_BUTTON and available_options:
            selected_tickers = [option["value"] for option in available_options] if available_options else []
        elif trigger == WizardIDs.DESELECT_ALL_TICKERS_BUTTON:
            selected_tickers = []
        
        # No tickers selected
        if not selected_tickers:
            return html.Div("No tickers selected. Please select at least one ticker."), True
        
        # Create ticker badges
        ticker_badges = []
        for ticker in selected_tickers:
            badge = html.Div(
                ticker,
                className="badge bg-primary me-2 mb-2 p-2"
            )
            ticker_badges.append(badge)
        
        # Enable confirm button if at least one ticker is selected
        button_disabled = len(ticker_badges) == 0
        
        return html.Div(ticker_badges, className="mt-2"), button_disabled

    # --- Populate ticker dropdown options ---
    @app.callback(
        Output(WizardIDs.TICKER_DROPDOWN, "options"),
        Input(WizardIDs.step_content("tickers-selection"), "style"),
    )
    def populate_ticker_dropdown(style):
        """
        Populate the ticker dropdown with available tickers.
        This runs when the ticker selection step becomes visible.
        """
        if style is None or style.get("display") == "none":
            raise PreventUpdate
            
        try:
            # Use DataLoader to get the list of available tickers
            data_loader = DataLoader()
            available_tickers = data_loader.get_available_tickers()
            
            # Format tickers for dropdown options
            return [{"label": ticker, "value": ticker} for ticker in available_tickers]
        except Exception as e:
            logger.error(f"Error loading ticker options: {e}")
            # Return some default tickers in case of error
            default_tickers = ["AAPL", "MSFT", "GOOG", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "WMT"]
            return [{"label": ticker, "value": ticker} for ticker in default_tickers]