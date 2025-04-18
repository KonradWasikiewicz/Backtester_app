import dash
from dash import Input, Output, State, callback_context, no_update, ClientsideFunction, ALL
import dash_bootstrap_components as dbc
from dash import html, dcc
from typing import Dict, List, Any, Optional, Tuple
import logging # Import logging
import traceback
import pandas as pd
import plotly.graph_objects as go
import json
import sys
import os

# --- PRZENIESIONA INICJALIZACJA LOGGERA ---
# Configure logging EARLY, before any potential logging calls
logger = logging.getLogger(__name__)

# Import strategy logic and constants
try:
    # --- POPRAWIONE IMPORTY ---
    from src.core.constants import DEFAULT_STRATEGY_PARAMS, STRATEGY_DESCRIPTIONS, PARAM_DESCRIPTIONS # Importuj domyślne parametry i opisy
    from src.core.data import DataLoader
    # --- USUNIĘTO BŁĘDNY IMPORT 'generate_strategy_parameters' ---
except ImportError:
    # Handle potential import errors if running script directly or structure changes
    # Teraz logger jest już zdefiniowany
    logger.error("Critical import error in strategy_callbacks.py", exc_info=True)
    # Definiuj puste stałe jako fallback
    DEFAULT_STRATEGY_PARAMS = {}
    STRATEGY_DESCRIPTIONS = {}
    PARAM_DESCRIPTIONS = {}
    # Możesz też rzucić wyjątek lub zakończyć działanie

# --- Funkcja pomocnicza do generowania inputów parametrów ---
def _generate_parameter_inputs(strategy_value: str) -> List[Any]:
    """Generates input components based on the selected strategy."""
    if not strategy_value or strategy_value not in DEFAULT_STRATEGY_PARAMS:
        logger.debug(f"Cannot generate params for invalid strategy: {strategy_value}")
        return [html.P("Select a valid strategy to see its parameters.", className="text-muted")]

    params = DEFAULT_STRATEGY_PARAMS.get(strategy_value, {})
    descriptions = PARAM_DESCRIPTIONS.get(strategy_value, {})  # get tooltip texts
    if not params:
        logger.warning(f"No default parameters found for strategy: {strategy_value}")
        return [html.P(f"No parameters defined for strategy: {strategy_value}", className="text-warning")]

    inputs = []
    logger.debug(f"Generating inputs for strategy '{strategy_value}' with params: {params}")

    sorted_param_keys = sorted(params.keys())

    for param_name in sorted_param_keys:
        default_value = params[param_name]
        input_id = {"type": "strategy-param", "strategy": strategy_value, "param": param_name}
        tooltip_id = f"tooltip-{strategy_value}-{param_name}"

        # Tooltip Icon
        tooltip_icon = html.Span(
            html.I(className="fas fa-info-circle"),
            id=tooltip_id,
            style={'cursor': 'help', 'color': '#0d6efd'}
        )

        # Create display label, ensuring acronym uppercase for this strategy
        parts = param_name.split('_')
        if parts[0].upper() == strategy_value:
            display_label = ' '.join([strategy_value] + [p.title() for p in parts[1:]])
        else:
            display_label = param_name.replace('_', ' ').title()
        label_text = html.Label(display_label, htmlFor=json.dumps(input_id), className="ms-1 me-2 text-white")

        # Input component styled like dropdown
        input_component = dbc.Input(
            id=input_id,
            type="number",
            value=default_value,
            step=1 if isinstance(default_value, int) else 0.01,
            min=0,
            size="sm",
            style={"width": "100px"}, # Fixed width
            className="Select-control"  # Match dropdown color scheme
        )

        # Tooltip for parameter description
        tooltip = dbc.Tooltip(
            descriptions.get(param_name, ""),
            target=tooltip_id,
            placement="left" # Changed placement to left
        )

        # Arrange components in a row using Bootstrap grid
        param_row = dbc.Row(
            [
                dbc.Col(tooltip_icon, width="auto", className="d-flex align-items-center"),
                dbc.Col(label_text, width="auto", className="d-flex align-items-center"),
                dbc.Col(input_component, width="auto"),
                dbc.Col(tooltip) # Tooltip doesn't need a column definition, it attaches to target
            ],
            className="mb-3 align-items-center" # Added vertical alignment for items in the row
        )

        inputs.append(param_row) # Append the whole row

    return inputs

# --- Rejestracja callbacków ---
def register_strategy_callbacks(app: dash.Dash) -> None:
    """
    Register callbacks related to strategy selection and configuration.

    Args:
        app: The Dash application instance
    """
    logger.info("Registering strategy callbacks...")

    @app.callback(
        Output('strategy-description-output', 'children'),
        Input('strategy-dropdown', 'value')
    )
    def update_strategy_description(selected_strategy: Optional[str]) -> html.P:
        """Update the strategy description text when a strategy is selected."""
        if not selected_strategy:
            return html.P("Select a strategy to see its description.")
        description = STRATEGY_DESCRIPTIONS.get(selected_strategy, "No description available.")
        return html.P(description)

    @app.callback(
        [Output('strategy-param-section', 'children'), Output('confirm-strategy', 'disabled')],
        Input('strategy-dropdown', 'value')
    )
    def update_strategy_parameters(selected_strategy: Optional[str]):
        logger.info(f"Strategy selected: {selected_strategy}. Updating parameter inputs.")
        if not selected_strategy:
            # Clear section and disable confirm
            return [], True
        # Build section: header + generated inputs
        inputs = []
        try:
            inputs = _generate_parameter_inputs(selected_strategy)
        except Exception as e:
            logger.error(f"Error generating parameters for strategy {selected_strategy}: {e}", exc_info=True)
            inputs = [dbc.Alert(f"Error loading parameters: {e}", color="danger")]
        # Enable confirm when strategy selected (defaults assumed valid)
        return inputs, False

    @app.callback(
        Output("strategy-config-store", "data"),
        [
            Input({"type": "strategy-param", "strategy": ALL, "param": ALL}, "value"),
            Input("commission-input", "value"),
            Input("slippage-input", "value"),
            Input("rebalancing-frequency", "value"),
            Input("rebalancing-threshold", "value")
        ],
        [
            State("strategy-config-store", "data"),
            State('strategy-dropdown', 'value')
        ],
        prevent_initial_call=True
    )
    def update_config_store_from_inputs(*args):
        ctx = callback_context
        if not ctx.triggered or not ctx.inputs_list:
            logger.debug("Config store update: No trigger.")
            return no_update

        current_config = args[5] or {}
        selected_strategy = args[6]
        updated_config = json.loads(json.dumps(current_config))
        triggered_prop_id_str = ctx.triggered[0]['prop_id']
        triggered_value = ctx.triggered[0]['value']
        logger.debug(f"Config store update triggered by: {triggered_prop_id_str} = {triggered_value}")

        if "parameters" not in updated_config: updated_config["parameters"] = {}
        if "trading_costs" not in updated_config: updated_config["trading_costs"] = {}
        if "rebalancing" not in updated_config: updated_config["rebalancing"] = {}
        if "strategy_name" not in updated_config or updated_config.get("strategy_name") != selected_strategy:
             updated_config["strategy_name"] = selected_strategy

        try:
            prop_id_dict_str = triggered_prop_id_str.split(".")[0]
            is_pattern_match = prop_id_dict_str.startswith('{') and prop_id_dict_str.endswith('}')

            if is_pattern_match:
                prop_id_dict = json.loads(prop_id_dict_str)
                if prop_id_dict.get("type") == "strategy-param":
                    param_name = prop_id_dict.get("param")
                    trigger_strategy = prop_id_dict.get("strategy")
                    if param_name and trigger_strategy == selected_strategy:
                        updated_config["parameters"][param_name] = triggered_value
                        logger.debug(f"Updated param '{param_name}' for strategy '{selected_strategy}' to {triggered_value}")
                    else:
                        logger.warning(f"Ignoring param update trigger for mismatched strategy. Trigger ID: {prop_id_dict}, Selected: {selected_strategy}")
                else:
                     logger.warning(f"Unhandled pattern-matching trigger ID type: {prop_id_dict.get('type')}")

            elif prop_id_dict_str == "commission-input":
                 try: updated_config["trading_costs"]["commission_value"] = float(triggered_value) if triggered_value is not None else None
                 except (ValueError, TypeError): logger.warning(f"Invalid commission value: {triggered_value}")
                 logger.debug(f"Updated commission_value to {updated_config['trading_costs'].get('commission_value')}")
            elif prop_id_dict_str == "slippage-input":
                 try: updated_config["trading_costs"]["slippage_value"] = float(triggered_value) if triggered_value is not None else None
                 except (ValueError, TypeError): logger.warning(f"Invalid slippage value: {triggered_value}")
                 logger.debug(f"Updated slippage_value to {updated_config['trading_costs'].get('slippage_value')}")
            elif prop_id_dict_str == "rebalancing-frequency":
                 updated_config["rebalancing"]["frequency"] = triggered_value
                 logger.debug(f"Updated rebalancing frequency to {triggered_value}")
            elif prop_id_dict_str == "rebalancing-threshold":
                 try: updated_config["rebalancing"]["threshold"] = float(triggered_value) if triggered_value is not None else None
                 except (ValueError, TypeError): logger.warning(f"Invalid rebalancing threshold: {triggered_value}")
                 logger.debug(f"Updated rebalancing threshold to {updated_config['rebalancing'].get('threshold')}")
            else:
                logger.warning(f"Unhandled simple trigger ID in config store update: {prop_id_dict_str}")

        except (json.JSONDecodeError, AttributeError, KeyError, IndexError) as e:
            logger.error(f"Error processing triggered ID or updating config: {e} | ID: {triggered_prop_id_str}", exc_info=True)
            return no_update

        if updated_config != current_config:
            logger.info(f"Updated strategy-config-store: {json.dumps(updated_config)}")
            return updated_config
        else:
            logger.debug("Config store update: No change detected.")
            return no_update

    logger.info("Strategy callbacks registered.")