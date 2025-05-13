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

# Import centralized IDs
from src.ui.ids import WizardIDs, StrategyConfigIDs # MODIFIED: Added StrategyConfigIDs

# --- MOVED LOGGER INITIALIZATION ---
# Configure logging EARLY, before any potential logging calls
logger = logging.getLogger(__name__)

# Import strategy logic and constants
try:
    # --- CORRECTED IMPORTS ---
    from src.core.constants import DEFAULT_STRATEGY_PARAMS, STRATEGY_DESCRIPTIONS, PARAM_DESCRIPTIONS # Import default parameters and descriptions
    # --- REMOVED DIRECT CORE IMPORT ---
    # from src.core.data import DataLoader 
    # --- ADDED SERVICE LAYER IMPORT ---
    from src.services.data_service import DataService 
    # --- REMOVED INCORRECT IMPORT 'generate_strategy_parameters' ---
except ImportError:
    # Handle potential import errors if running script directly or structure changes
    # Logger is now defined here
    logger.error("Critical import error in strategy_callbacks.py", exc_info=True)
    # Define empty constants as fallback
    DEFAULT_STRATEGY_PARAMS = {}
    STRATEGY_DESCRIPTIONS = {}
    PARAM_DESCRIPTIONS = {}
    # You might also raise an exception or exit

# --- Helper function to generate parameter inputs ---
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
        
        # Use a custom div for the label with fixed width for alignment
        label_container = html.Div(
            [tooltip_icon, html.Label(display_label, htmlFor=json.dumps(input_id), className="ms-1")],
            className="param-label"  # Apply our new CSS class for fixed-width labels
        )

        # Input component styled like dropdown
        input_component = dbc.Input(
            id=input_id,
            type="number",
            value=default_value,
            step=1 if isinstance(default_value, int) else 0.01,
            min=0,
            size="sm",
            style={"width": "100px"}, # Fixed width
            className="Select-control param-input"  # Added our new CSS class
        )

        # Tooltip for parameter description
        tooltip = dbc.Tooltip(
            descriptions.get(param_name, ""),
            target=tooltip_id,
            placement="left"
        )

        # Use our custom CSS classes for consistent alignment
        param_row = html.Div(
            [label_container, input_component, tooltip],
            className="param-row"  # Use our custom CSS class for rows
        )

        inputs.append(param_row)

    return inputs

# --- Register callbacks ---
def register_strategy_callbacks(app: dash.Dash) -> None:
    """
    Register callbacks related to strategy selection and configuration.

    Args:
        app: The Dash application instance
    """
    logger.info("Registering strategy callbacks...")
    
    # --- Instantiate DataService (assuming it's lightweight or managed elsewhere if heavy) ---
    # If DataService requires complex setup, this might need to be passed in or accessed differently.
    data_service = DataService()    # @app.callback(
    #     Output(WizardIDs.STRATEGY_DESCRIPTION_OUTPUT, 'children'),
    #     Input(WizardIDs.STRATEGY_DROPDOWN, 'value')
    # )
    # def update_strategy_description(selected_strategy: Optional[str]) -> html.P:
    #     """Update the strategy description text when a strategy is selected."""
    #     if not selected_strategy:
    #         return html.P("Select a strategy to see its description.")
    #     description = STRATEGY_DESCRIPTIONS.get(selected_strategy, "No description available.")
    #     return html.P(description)
    # This callback was removed because it was causing a duplicate with wizard_callbacks.py
    # Parameters inputs are now handled by wizard_callbacks.py

    logger.info("Strategy callbacks registered.")