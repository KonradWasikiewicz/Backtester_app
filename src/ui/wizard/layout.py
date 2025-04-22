import logging
from dash import html, dcc
import dash_bootstrap_components as dbc
from typing import List, Dict, Any
import pandas as pd
from src.core.data import DataLoader
from src.core.constants import AVAILABLE_STRATEGIES

logger = logging.getLogger(__name__)

# --- Helper function creating a wizard step ---
def create_wizard_step(step_id: str, title: str, content: Any, is_hidden: bool = False, step_number: int = 0) -> html.Div:
    """
    Creates a wizard step container with header and content.
    """
    logger.debug(f"Creating wizard step: {step_id}, Hidden: {is_hidden}")
    content_style = {"display": "none"} if is_hidden else {"display": "block"}
    content_style.update({"marginLeft": "30px", "paddingTop": "10px"})

    return html.Div([
        html.Div([
            html.H5(title, className="mb-0 d-inline")
        ],
        id=f"{step_id}-header",
        className="wizard-step-header mb-2",
        style={"cursor": "pointer"}
        ),
        html.Div(
            content,
            id=f"{step_id}-content",
            style=content_style
        ),
        html.Hr(className="my-3")
    ], className="wizard-step mb-3")

# --- Main function creating the strategy configuration section ---
def create_strategy_config_section(tickers: List[str] = None) -> html.Div:
    """
    Creates the layout for the strategy configuration wizard.
    """
    logger.info("Creating strategy configuration section layout...")
    if tickers is None:
        tickers = []
    # Progress bar
    progress = dbc.Progress(id="wizard-progress", value=0, striped=True, animated=True, className="mb-4")

    # Steps
    steps = [
        create_wizard_step(
            "strategy-selection",
            "Step 1: Strategy Selection",
            html.Div([
                html.Label("Select a strategy:", className="mb-2"),
                dcc.Dropdown(
                    id='strategy-dropdown',
                    options=[{'label': s['label'], 'value': s['value']} for s in AVAILABLE_STRATEGIES],
                    placeholder="Select a strategy...",
                    className="mb-3",
                    clearable=False
                ),
                # Add Initial Capital Input Field
                html.Label("Initial Capital (USD):", className="mb-2"),
                dbc.Input(
                    id='initial-capital-input',
                    type='number',
                    value=100000,  # Default value
                    min=1000,      # Minimum value
                    step=1000,     # Step increment
                    className="mb-3",
                    # Add formatting or validation if needed later
                ),
                html.Div(id="strategy-description-output", className="mb-3 mt-3"),
                html.H6("Strategy Parameters:", className="mt-4 mb-2"),
                html.Div(id='strategy-param-inputs', className="mb-3"),
                dbc.Button("Confirm", id="confirm-strategy", color="primary", className="mt-3", disabled=True)
            ])
        ),
        # Additional steps (date-range, tickers, risk, costs, rebalancing, summary)
        # ... existing step definitions ...
    ]

    return html.Div([
        progress,
        html.Div(steps, id="wizard-steps-container", className="wizard-steps")
    ], id="strategy-config-container", className="strategy-wizard")
