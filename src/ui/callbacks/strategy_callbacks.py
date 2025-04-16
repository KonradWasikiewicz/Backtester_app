import dash
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
    from src.core.constants import AVAILABLE_STRATEGIES
    from src.core.data import DataLoader # Corrected from DataService previously
    # --- CORRECTED IMPORT: generate_strategy_parameters ---
    # --- REMOVED create_trading_costs_layout, create_rebalancing_layout ---
    from src.ui.layouts.strategy_config import generate_strategy_parameters
except ImportError:
    # Handle potential import errors if running script directly or structure changes
    import sys, os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.core.constants import AVAILABLE_STRATEGIES
    from src.core.data import DataLoader # Corrected from DataService previously
    # --- CORRECTED IMPORT: generate_strategy_parameters ---
    # --- REMOVED create_trading_costs_layout, create_rebalancing_layout ---
    from src.ui.layouts.strategy_config import generate_strategy_parameters

# Configure logging
logger = logging.getLogger(__name__)

def register_strategy_callbacks(app: dash.Dash) -> None:
    """
    Register callbacks related to strategy selection and configuration.

    Args:
        app: The Dash application instance
    """
    logger.info("Registering strategy callbacks...")

    # Callback to update strategy description (Should be correct now)
    @app.callback(
        Output("strategy-description", "children"),
        Input("strategy-selector", "value"),
         prevent_initial_call=True
    )
    def update_strategy_description(strategy_name: Optional[str]) -> List[html.P]:
        """ Updates strategy description based on docstring. """
        if not strategy_name:
            logger.debug("No strategy selected, clearing description.")
            return [html.P("Select a strategy to see its description.")]
        try:
            strategy_class = AVAILABLE_STRATEGIES.get(strategy_name)
            if strategy_class and strategy_class.__doc__:
                description = strategy_class.__doc__.strip()
                logger.debug(f"Displaying description for strategy: {strategy_name}")
                bullets = [html.Li(line.strip().lstrip('*').strip()) for line in description.split('\n') if line.strip()]
                return [html.H6("Description:"), html.Ul(bullets, className="list-unstyled ps-3")]
            else:
                logger.warning(f"No description (docstring) found for strategy: {strategy_name}")
                return [html.P("No description available.")]
        except Exception as e:
            logger.error(f"Error getting strategy description for {strategy_name}: {e}", exc_info=True)
            return [html.P("Error loading description.", className="text-danger")]


    # Callback to update the PARAMETER section and config store based on selected strategy
    # --- UPDATED OUTPUTS ---
    @app.callback(
        [
            Output("strategy-parameters-content", "children"), # Only update params content
            Output("strategy-config-store", "data") # Update the store with defaults
        ],
        Input("strategy-selector", "value"),
         prevent_initial_call=True
    )
    def update_parameter_section_and_store(strategy_name: Optional[str]):
        """
        Updates the strategy parameters section and stores the default config
        when a new strategy is selected.
        """
        if not strategy_name:
            logger.debug("No strategy selected, clearing params section and store.")
            # Return empty layout and empty config
            return [], {} # Updated return

        logger.info(f"Updating params section and store for strategy: {strategy_name}")
        try:
            strategy_class = AVAILABLE_STRATEGIES.get(strategy_name)
            if not strategy_class:
                logger.warning(f"Strategy class not found for {strategy_name}")
                return [], {} # Updated return

            # --- Use the correct function name ---
            params_layout = generate_strategy_parameters(strategy_class)

            # Prepare default config for the store (including params, costs, rebalancing)
            strategy_instance = strategy_class() # Instantiate to get defaults if needed
            default_params = strategy_instance.get_parameters() # Assuming this method exists

            default_config = {
                "strategy_name": strategy_name,
                "parameters": default_params,
                 # Keep defaults for costs and rebalancing in the store, even if layout isn't dynamic here
                "trading_costs": {
                    "commission_type": "percentage", "commission_value": 0.001,
                    "slippage_type": "percentage", "slippage_value": 0.0005
                },
                "rebalancing": {"frequency": "monthly", "threshold": 0.05}
            }
            logger.debug(f"Generated default config for {strategy_name}: {default_config}")

            # --- UPDATED RETURN ---
            # Return only the params layout and the config data
            return params_layout, default_config

        except Exception as e:
            logger.error(f"Error updating params section/store for {strategy_name}: {e}", exc_info=True)
            # Return error message in layout and empty config
            error_msg = f"Error loading config for {strategy_name}."
            # --- UPDATED RETURN ---
            return html.P(error_msg, className="text-danger"), {}


    # Callback to update strategy config store when individual inputs change (Should be correct)
    @app.callback(
        Output("strategy-config-store", "data", allow_duplicate=True),
        [
            Input({"type": "strategy-param", "strategy": ALL, "param": ALL}, "value"),
            Input("commission-type-selector", "value"), # Assuming these IDs exist in strategy_config.py layout
            Input("commission-value-input", "value"),   # Assuming these IDs exist in strategy_config.py layout
            Input("slippage-type-selector", "value"),   # Assuming these IDs exist in strategy_config.py layout
            Input("slippage-value-input", "value"),     # Assuming these IDs exist in strategy_config.py layout
            Input("rebalancing-frequency-selector", "value"), # Assuming these IDs exist in strategy_config.py layout
            Input("rebalancing-threshold-input", "value")     # Assuming these IDs exist in strategy_config.py layout
        ],
        State("strategy-config-store", "data"),
        prevent_initial_call=True
    )
    def update_config_store_from_inputs(*args):
        """ Updates the strategy-config-store based on individual input changes. """
        ctx = callback_context
        if not ctx.triggered or not ctx.inputs_list: return no_update
        current_config = args[-1] or {}
        input_values = args[:-1]
        updated_config = json.loads(json.dumps(current_config)) # Deep copy
        triggered_prop_id_str = ctx.triggered[0]['prop_id']
        triggered_value = ctx.triggered[0]['value']
        logger.debug(f"Config store update triggered by: {triggered_prop_id_str} = {triggered_value}")

        if ".value" in triggered_prop_id_str:
            try:
                # Attempt to parse ID as JSON (for pattern-matching IDs)
                try:
                    prop_id_dict = json.loads(triggered_prop_id_str.split(".")[0])
                except json.JSONDecodeError:
                    # If not JSON, treat it as a simple string ID
                    prop_id_dict = triggered_prop_id_str.split(".")[0]

                # Handle dynamic parameters
                if isinstance(prop_id_dict, dict) and prop_id_dict.get("type") == "strategy-param":
                    param_name = prop_id_dict.get("param")
                    strategy_name = prop_id_dict.get("strategy")
                    if updated_config.get("strategy_name") == strategy_name and param_name:
                        if "parameters" not in updated_config: updated_config["parameters"] = {}
                        updated_config["parameters"][param_name] = triggered_value
                        logger.debug(f"Updated param '{param_name}' to {triggered_value}")
                    else:
                         logger.warning(f"Strategy mismatch or param_name missing. Trigger: {prop_id_dict}, Store: {updated_config.get('strategy_name')}")
                # Handle simple string IDs for costs/rebalancing
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
                else:
                    logger.warning(f"Unhandled trigger ID in config store update: {prop_id_dict}")

            except (AttributeError, KeyError) as e:
                logger.error(f"Error processing triggered ID or updating config: {e} | ID: {triggered_prop_id_str}")
                return no_update

        if updated_config != current_config:
            logger.debug(f"Updated strategy-config-store: {updated_config}")
            return updated_config
        else:
            logger.debug("Config store update: No actual change detected.")
            return no_update


    # DISABLED: This callback was competing with handle_step_transition in wizard_callbacks.py
    # Removing this resolves the step transition issue
    # @app.callback(
    #     [
    #         Output("strategy-selection-container", "style"),
    #         Output("date-range-selection-container", "style"),
    #         Output("tickers-selection-container", "style"),
    #         Output("risk-management-container", "style"),
    #         Output("trading-costs-container", "style"),
    #         Output("rebalancing-rules-container", "style"),
    #         Output("wizard-progress", "value") # Update progress bar
    #     ],
    #     [
    #         Input("confirm-strategy", "n_clicks"),
    #         Input("confirm-dates", "n_clicks"),
    #         Input("confirm-tickers", "n_clicks"),
    #         Input("confirm-risk", "n_clicks"),
    #         Input("confirm-costs", "n_clicks"),
    #         Input("confirm-rebalancing", "n_clicks"),  # Add Step 6 confirm button
    #     ],
    #     [
    #         State("strategy-selector", "value"),
    #     ],
    #     prevent_initial_call=True
    # )
    # def control_wizard_steps(confirm_strat, confirm_dates, confirm_tickers, confirm_risk, confirm_costs, confirm_rebalancing, strategy_value):
    #     # This functionality is now handled by handle_step_transition in wizard_callbacks.py
    #     pass

    logger.info("Strategy callbacks registered.")
