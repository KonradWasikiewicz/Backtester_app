import dash
# --- UPDATED IMPORT LINE ---
from dash import Input, Output, State, callback_context, no_update, ClientsideFunction, ALL
import dash_bootstrap_components as dbc
from dash import html, dcc
from typing import Dict, List, Any, Optional
import logging
import traceback
import pandas as pd
import plotly.graph_objects as go
import json

# Import strategy logic and constants
try:
    from src.core.constants import AVAILABLE_STRATEGIES, STRATEGY_DESCRIPTIONS
    from src.core.data import DataService
    from src.ui.layouts.strategy_config import create_strategy_parameters_layout, create_trading_costs_layout, create_rebalancing_layout
except ImportError:
    # Handle potential import errors if running script directly or structure changes
    import sys, os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.core.constants import AVAILABLE_STRATEGIES, STRATEGY_DESCRIPTIONS
    from src.core.data import DataService
    from src.ui.layouts.strategy_config import create_strategy_parameters_layout, create_trading_costs_layout, create_rebalancing_layout

# Configure logging
logger = logging.getLogger(__name__)

def register_strategy_callbacks(app: dash.Dash) -> None:
    """
    Register callbacks related to strategy selection and configuration.

    Args:
        app: The Dash application instance
    """
    logger.info("Registering strategy callbacks...")

    # Callback to update strategy description
    @app.callback(
        Output("strategy-description", "children"),
        Input("strategy-selector", "value"),
         prevent_initial_call=True # Don't update on initial load
    )
    def update_strategy_description(strategy_name: Optional[str]) -> List[html.P]:
        """
        Updates the strategy description area based on the selected strategy.

        Args:
            strategy_name: The name of the selected strategy.

        Returns:
            A list of html.P components containing the description.
        """
        if not strategy_name:
            logger.debug("No strategy selected, clearing description.")
            return [html.P("Select a strategy to see its description.")]

        description = STRATEGY_DESCRIPTIONS.get(strategy_name, "No description available.")
        logger.debug(f"Displaying description for strategy: {strategy_name}")
        # Simple formatting: split by newline and wrap each line in P
        return [html.P(line) for line in description.split('\n')]

    # Callback to update the parameter, costs, and rebalancing sections based on selected strategy
    @app.callback(
        [
            Output("strategy-parameters-content", "children"),
            Output("trading-costs-content", "children"),
            Output("rebalancing-rules-content", "children"),
            Output("strategy-config-store", "data") # Store the full config
        ],
        Input("strategy-selector", "value"),
        # --- REMOVED Input('summary-strategy', 'children') ---
        # This Input was causing the "nonexistent object" error.
        # State("strategy-config-store", "data"), # Keep state if needed for merging later
         prevent_initial_call=True # Important: Run only when strategy changes
    )
    def update_config_sections(strategy_name: Optional[str]): # removed current_config
        """
        Updates the configuration sections (parameters, costs, rebalancing)
        when a new strategy is selected. Stores the default config for the strategy.

        Args:
            strategy_name: The name of the selected strategy.
            # current_config: The existing configuration from the store (if needed).

        Returns:
            Tuple containing the new layouts for parameters, costs, rebalancing,
            and the default configuration data for the selected strategy.
        """
        if not strategy_name:
            logger.debug("No strategy selected, clearing config sections.")
            # Return empty layouts and empty config
            return [], [], [], {}

        logger.info(f"Updating config sections for strategy: {strategy_name}")
        try:
            strategy_class = AVAILABLE_STRATEGIES.get(strategy_name)
            if not strategy_class:
                logger.warning(f"Strategy class not found for {strategy_name}")
                return [], [], [], {}

            # Instantiate the strategy to get default parameters
            strategy_instance = strategy_class()
            default_params = strategy_instance.get_parameters()

            # Create layouts based on default parameters
            params_layout = create_strategy_parameters_layout(strategy_name, default_params)
            costs_layout = create_trading_costs_layout() # Assuming defaults are handled here
            rebalancing_layout = create_rebalancing_layout() # Assuming defaults are handled here

            # Prepare default config for the store
            # Combine defaults from all sections
            default_config = {
                "strategy_name": strategy_name,
                "parameters": default_params,
                "trading_costs": { # Add default cost values
                    "commission_type": "percentage",
                    "commission_value": 0.001, # Example: 0.1%
                    "slippage_type": "percentage",
                    "slippage_value": 0.0005 # Example: 0.05%
                },
                "rebalancing": { # Add default rebalancing values
                    "frequency": "monthly",
                    "threshold": 0.05 # Example: 5%
                }
            }
            logger.debug(f"Generated default config for {strategy_name}: {default_config}")

            return params_layout, costs_layout, rebalancing_layout, default_config

        except Exception as e:
            logger.error(f"Error updating config sections for {strategy_name}: {e}", exc_info=True)
            # Return error message in layouts and empty config
            error_msg = f"Error loading config for {strategy_name}."
            return html.P(error_msg, className="text-danger"), \
                   html.P(error_msg, className="text-danger"), \
                   html.P(error_msg, className="text-danger"), \
                   {}


    # Callback to update strategy config store when individual parameters change
    # This uses MATCH for dynamic parameter inputs
    @app.callback(
        Output("strategy-config-store", "data", allow_duplicate=True), # allow_duplicate is crucial here
        [
            # Inputs for parameters (dynamic)
            Input({"type": "strategy-param", "strategy": ALL, "param": ALL}, "value"),
            # Inputs for trading costs
            Input("commission-type-selector", "value"),
            Input("commission-value-input", "value"),
            Input("slippage-type-selector", "value"),
            Input("slippage-value-input", "value"),
            # Inputs for rebalancing
            Input("rebalancing-frequency-selector", "value"),
            Input("rebalancing-threshold-input", "value")
        ],
        State("strategy-config-store", "data"), # Get the current config
        prevent_initial_call=True
    )
    def update_config_store_from_inputs(*args):
        """
        Updates the strategy-config-store whenever any individual
        configuration input (parameter, cost, rebalancing) changes.

        Args:
            *args: All input values followed by the current store data state.

        Returns:
            The updated configuration dictionary for the store.
        """
        ctx = callback_context
        if not ctx.triggered or not ctx.inputs_list:
            logger.debug("Config store update: No trigger.")
            return no_update

        # The last argument is the State (current store data)
        current_config = args[-1] or {}
        # All preceding arguments are the Input values
        input_values = args[:-1]

        # Deep copy to avoid modifying the original state directly
        updated_config = json.loads(json.dumps(current_config))

        # Get triggered component info
        triggered_prop_id_str = ctx.triggered[0]['prop_id']
        triggered_value = ctx.triggered[0]['value']
        logger.debug(f"Config store update triggered by: {triggered_prop_id_str} = {triggered_value}")

        # Check if the trigger is a dynamic parameter
        if ".value" in triggered_prop_id_str:
            try:
                prop_id_dict = json.loads(triggered_prop_id_str.split(".")[0])
                if prop_id_dict.get("type") == "strategy-param":
                    param_name = prop_id_dict.get("param")
                    strategy_name = prop_id_dict.get("strategy") # Get strategy from ID

                    # Ensure strategy name matches the one in store (or initialize if needed)
                    if updated_config.get("strategy_name") == strategy_name and param_name:
                        if "parameters" not in updated_config:
                            updated_config["parameters"] = {}
                        updated_config["parameters"][param_name] = triggered_value
                        logger.debug(f"Updated param '{param_name}' to {triggered_value}")
                    else:
                         logger.warning(f"Strategy mismatch or param_name missing. Trigger: {prop_id_dict}, Store: {updated_config.get('strategy_name')}")


                # --- Handle specific cost and rebalancing inputs ---
                elif prop_id_dict == "commission-type-selector":
                     if "trading_costs" not in updated_config: updated_config["trading_costs"] = {}
                     updated_config["trading_costs"]["commission_type"] = triggered_value
                elif prop_id_dict == "commission-value-input":
                     if "trading_costs" not in updated_config: updated_config["trading_costs"] = {}
                     updated_config["trading_costs"]["commission_value"] = triggered_value
                elif prop_id_dict == "slippage-type-selector":
                     if "trading_costs" not in updated_config: updated_config["trading_costs"] = {}
                     updated_config["trading_costs"]["slippage_type"] = triggered_value
                elif prop_id_dict == "slippage-value-input":
                     if "trading_costs" not in updated_config: updated_config["trading_costs"] = {}
                     updated_config["trading_costs"]["slippage_value"] = triggered_value
                elif prop_id_dict == "rebalancing-frequency-selector":
                     if "rebalancing" not in updated_config: updated_config["rebalancing"] = {}
                     updated_config["rebalancing"]["frequency"] = triggered_value
                elif prop_id_dict == "rebalancing-threshold-input":
                     if "rebalancing" not in updated_config: updated_config["rebalancing"] = {}
                     updated_config["rebalancing"]["threshold"] = triggered_value

            except (json.JSONDecodeError, AttributeError, KeyError) as e:
                logger.error(f"Error parsing triggered ID or updating config: {e} | ID: {triggered_prop_id_str}")
                return no_update # Avoid corrupting the store

        # Compare if config actually changed before returning
        if updated_config != current_config:
            logger.debug(f"Updated strategy-config-store: {updated_config}")
            return updated_config
        else:
            logger.debug("Config store update: No actual change detected.")
            return no_update


    # Callback to control accordion visibility/expansion (Example)
    # This needs to be adapted based on your actual accordion structure
    # Assuming you have dbc.Accordion with items having item_id like "config-item-params", etc.
    @app.callback(
        Output("config-accordion", "active_item"), # Assuming accordion ID is "config-accordion"
        Input("confirm-strategy", "n_clicks"),
        Input("confirm-parameters", "n_clicks"), # Need button for this
        Input("confirm-tickers", "n_clicks"),    # Need button for this
        Input("confirm-risk", "n_clicks"),
        Input("confirm-costs", "n_clicks"),
        Input("confirm-rebalancing", "n_clicks"), # Need button for this
        prevent_initial_call=True
    )
    def control_accordion_steps(strat_clicks, param_clicks, ticker_clicks, risk_clicks, cost_clicks, rebal_clicks):
        ctx = callback_context
        if not ctx.triggered:
            return "config-item-strategy" # Start with strategy open

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Define the order of accordion items
        steps = {
            "confirm-strategy": "config-item-tickers", # Next is tickers
            "confirm-tickers": "config-item-parameters", # Next is params
            "confirm-parameters": "config-item-risk", # Next is risk
            "confirm-risk": "config-item-costs",
            "confirm-costs": "config-item-rebalancing",
            "confirm-rebalancing": None # Stay on last step or collapse all?
            # Add logic for going back if needed
        }

        next_item = steps.get(trigger_id)
        logger.debug(f"Accordion trigger: {trigger_id}, next item: {next_item}")
        if next_item:
            return next_item
        elif trigger_id == "confirm-rebalancing":
             # Decide what happens after the last step
             return "config-item-rebalancing" # Stay open
             # return None # Collapse all
        else:
            return no_update # Or return current active item using State

    logger.info("Strategy callbacks registered.")

# Note: The accordion callback above is a basic example.
# You need corresponding dbc.Accordion and dbc.AccordionItem components in your layout
# (likely in src/ui/layouts/strategy_config.py) with matching IDs like:
# dbc.Accordion(id="config-accordion", active_item="config-item-strategy", children=[
#     dbc.AccordionItem(..., title="Step 1: Strategy Selection", item_id="config-item-strategy"),
#     dbc.AccordionItem(..., title="Step 2: Tickers", item_id="config-item-tickers"),
#     dbc.AccordionItem(..., title="Step 3: Parameters", item_id="config-item-parameters"),
#     dbc.AccordionItem(..., title="Step 4: Risk Management", item_id="config-item-risk"),
#     dbc.AccordionItem(..., title="Step 5: Trading Costs", item_id="config-item-costs"),
#     dbc.AccordionItem(..., title="Step 6: Rebalancing", item_id="config-item-rebalancing"),
# ])
# You also need the corresponding "Confirm" buttons within each accordion item.