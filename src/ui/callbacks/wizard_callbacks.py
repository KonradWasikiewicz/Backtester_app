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
            State(WizardIDs.TICKER_LIST_CONTAINER, "children"),  # From step 3
            # Risk management states (step 4) - Using any applicable state from the risk step
            State(WizardIDs.MAX_POSITION_SIZE_INPUT, "value"),  # Example from step 4
            # Trading costs states (step 5) - Using any applicable state from the costs step
            State("wizard-commission-input", "value"),  # Example from step 5
            # Rebalancing states (step 6) - Using any applicable state from the rebalancing step
            State("wizard-rebalancing-freq-dropdown", "value"),  # Example from step 6
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
        selected_tickers = args[first_state_index + 4]
        max_position_size = args[first_state_index + 5]
        commission_value = args[first_state_index + 6]
        rebalancing_freq = args[first_state_index + 7]
        
        # Track completed steps based on required inputs
        if strategy_value and initial_capital:
            completed_steps.add(1)
        if date_start and date_end:
            completed_steps.add(2)
        if selected_tickers and isinstance(selected_tickers, list) and len(selected_tickers) > 0:
            completed_steps.add(3)
        if max_position_size is not None:  # This might need a more comprehensive check depending on risk requirements
            completed_steps.add(4)
        if commission_value is not None:  # This might need a more comprehensive check
            completed_steps.add(5)
        if rebalancing_freq:  # This might need a more comprehensive check
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
            html.P(description),
            # You could add more details, parameters, or examples here if needed
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
        
        for param_name, param_config in params.items():
            # Extract parameter configuration
            default_value = param_config.get("default", 0)
            min_value = param_config.get("min", None)
            max_value = param_config.get("max", None)
            step = param_config.get("step", 1)
            description = param_config.get("description", f"Parameter: {param_name}")
            
            # Create parameter input container
            param_container = html.Div([
                html.Label(description),
                # Generate different input types based on parameter configuration
                dcc.Input(
                    id={"type": "strategy-param", "name": param_name},
                    type="number",
                    value=default_value,
                    min=min_value,
                    max=max_value,
                    step=step,
                    className="wizard-parameter-input"
                )
            ], className="wizard-parameter-container")
            
            parameter_inputs.append(param_container)
        
        return parameter_inputs
        
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
        Output("wizard-strategy-parameters-summary", "children"),
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
        
        for param_id, param_value in zip(param_ids, param_values):
            param_name = param_id["name"]
            # Get parameter description if available
            param_desc = "Unknown parameter"
            
            if selected_strategy in DEFAULT_STRATEGY_PARAMS and param_name in DEFAULT_STRATEGY_PARAMS[selected_strategy]:
                param_desc = DEFAULT_STRATEGY_PARAMS[selected_strategy][param_name].get("description", param_name)
            
            param_summary_items.append(
                html.Li(f"{param_desc}: {param_value}")
            )
        
        return html.Div([
            html.P(f"Strategy: {selected_strategy}", className="summary-title"),
            html.P("Parameters:"),
            html.Ul(param_summary_items, className="summary-list")
        ])

    # --- Summary page updates ---
    @app.callback(
        [Output("wizard-summary-strategy", "children"),
         Output("wizard-summary-dates", "children"),
         Output("wizard-summary-tickers", "children"),
         Output("wizard-summary-risk", "children"),
         Output("wizard-summary-costs", "children"),
         Output("wizard-summary-rebalancing", "children")],
        [Input(WizardIDs.step_header("wizard-summary"), "n_clicks")],
        [State(WizardIDs.STRATEGY_DROPDOWN, "value"),
         State(WizardIDs.INITIAL_CAPITAL_INPUT, "value"),
         State(WizardIDs.DATE_RANGE_START_PICKER, "date"),
         State(WizardIDs.DATE_RANGE_END_PICKER, "date"),
         State(WizardIDs.TICKER_LIST_CONTAINER, "children"),
         State(WizardIDs.MAX_POSITION_SIZE_INPUT, "value"),
         State(WizardIDs.STOP_LOSS_INPUT, "value"),
         State(WizardIDs.TAKE_PROFIT_INPUT, "value"),
         State("wizard-commission-input", "value"),
         State("wizard-slippage-input", "value"),
         State("wizard-rebalancing-freq-dropdown", "value")]
    )
    def update_wizard_summary(n_clicks, strategy, initial_capital, start_date, end_date, 
                             ticker_children, max_position, stop_loss, take_profit,
                             commission, slippage, rebalancing_freq):
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
        
        # Extract ticker names from the ticker container children
        ticker_names = []
        if ticker_children and isinstance(ticker_children, list):
            for child in ticker_children:
                if isinstance(child, dict) and child.get('props', {}).get('children'):
                    ticker_text = child['props']['children']
                    if isinstance(ticker_text, str) and ticker_text.strip():
                        ticker_names.append(ticker_text.strip())
        
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
            html.P(f"Rebalancing Frequency: {rebalancing_freq}")
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