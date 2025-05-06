import logging
from dash import html, dcc
import dash_bootstrap_components as dbc
from typing import List, Dict, Any
import pandas as pd
from src.core.data import DataLoader
from src.core.constants import AVAILABLE_STRATEGIES
from src.ui.ids import WizardIDs  # Import the centralized IDs

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
        id=WizardIDs.step_header(step_id),  # Use the method to generate header ID
        className="wizard-step-header mb-2",
        style={"cursor": "pointer"}
        ),
        html.Div(
            content,
            id=WizardIDs.step_content(step_id),  # Use the method to generate content ID
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
    progress = dbc.Progress(id=WizardIDs.PROGRESS_BAR, value=0, striped=True, animated=True, className="mb-4")

    # Steps
    steps = [
        create_wizard_step(
            "strategy-selection",
            "Step 1: Initial Capital and Strategy Selection",
            html.Div([
                # moved initial capital above strategy selection
                html.Label("Initial Capital (USD):", className="mb-2", htmlFor=WizardIDs.INITIAL_CAPITAL_INPUT),
                dbc.Input(
                    id=WizardIDs.INITIAL_CAPITAL_INPUT,
                    type='number',
                    value=100000,  # Default value
                    min=1000,      # Minimum value
                    step=1000,     # Step increment
                    className="mb-3",
                    # Add formatting or validation if needed later
                ),
                html.Label("Select a strategy:", className="mb-2", htmlFor=WizardIDs.STRATEGY_DROPDOWN),
                dcc.Dropdown(
                    id=WizardIDs.STRATEGY_DROPDOWN,
                    options=[{'label': s['label'], 'value': s['value']} for s in AVAILABLE_STRATEGIES],
                    placeholder="Select a strategy...",
                    className="mb-3",
                    clearable=False
                ),
                html.Div(id=WizardIDs.STRATEGY_DESCRIPTION_OUTPUT, className="mb-3 mt-3"),
                html.H6("Strategy Parameters:", className="mt-4 mb-2"),
                html.Div(id=WizardIDs.STRATEGY_PARAM_INPUTS_CONTAINER, className="mb-3"),
                dbc.Button("Confirm", id=WizardIDs.CONFIRM_STRATEGY_BUTTON, color="primary", className="mt-3", disabled=True)
            ])
        ),
        # Step 2: Date Range Selection (placeholder)
        create_wizard_step(
            "date-range-selection",
            "Step 2: Date Range Selection",
            html.Div([
                html.Label("Start Date:", className="mb-2", htmlFor=WizardIDs.DATE_RANGE_START_PICKER),
                dcc.DatePickerSingle(
                    id=WizardIDs.DATE_RANGE_START_PICKER,
                    min_date_allowed="2019-01-01",
                    max_date_allowed="2025-12-31",
                    initial_visible_month="2023-01-01",
                    className="mb-3"
                ),
                html.Label("End Date:", className="mb-2", htmlFor=WizardIDs.DATE_RANGE_END_PICKER),
                dcc.DatePickerSingle(
                    id=WizardIDs.DATE_RANGE_END_PICKER,
                    min_date_allowed="2019-01-01",
                    max_date_allowed="2025-12-31",
                    initial_visible_month="2023-12-31",
                    className="mb-3"
                ),
                dbc.Button("Confirm", id=WizardIDs.CONFIRM_DATES_BUTTON, color="primary", className="mt-3", disabled=True)
            ]),
            is_hidden=True
        ),
        # Step 3: Ticker Selection (placeholder)
        create_wizard_step(
            "tickers-selection",
            "Step 3: Tickers Selection",
            html.Div([
                html.Label("Select tickers:", className="mb-2", htmlFor=WizardIDs.TICKER_DROPDOWN),
                dcc.Dropdown(
                    id=WizardIDs.TICKER_DROPDOWN,
                    multi=True,
                    placeholder="Select tickers...",
                    className="mb-3"
                ),
                html.Div([
                    dbc.Button("Select All", id="select-all-tickers", color="secondary", className="me-2"),
                    dbc.Button("Deselect All", id="deselect-all-tickers", color="secondary")
                ], className="d-flex justify-content-start mb-3"),
                dbc.Button("Confirm", id=WizardIDs.CONFIRM_TICKERS_BUTTON, color="primary", className="mt-3", disabled=True)
            ]),
            is_hidden=True
        ),
        # Step 4: Risk Management (placeholder - simplified)
        create_wizard_step(
            "risk-management",
            "Step 4: Risk Management",
            html.Div([
                # Simplified version of your risk management UI
                html.Div(id='risk-features-checklist', className="mb-3"),
                html.Div([
                    # Risk management parameters would go here
                    dbc.Input(id='max-position-size', type='number', placeholder="Max Position Size %", className="mb-2"),
                    dbc.Input(id='stop-loss-value', type='number', placeholder="Stop Loss %", className="mb-2"),
                    dbc.Select(id='stop-loss-type', options=[
                        {"label": "Fixed", "value": "fixed"},
                        {"label": "Trailing", "value": "trailing"}
                    ], placeholder="Stop Loss Type", className="mb-2"),
                    # Additional risk management inputs...
                ]),
                dbc.Button("Confirm", id=WizardIDs.CONFIRM_RISK_BUTTON, color="primary", className="mt-3")
            ]),
            is_hidden=True
        ),
        # Step 5: Trading Costs
        create_wizard_step(
            "trading-costs",
            "Step 5: Trading Costs",
            html.Div([
                html.Label("Commission (%):", className="mb-2", htmlFor=WizardIDs.COMMISSION_INPUT),
                dbc.Input(
                    id=WizardIDs.COMMISSION_INPUT,
                    type="number",
                    min=0,
                    max=10,
                    step=0.01,
                    value=0.1,
                    className="mb-3"
                ),
                html.Label("Slippage (%):", className="mb-2", htmlFor=WizardIDs.SLIPPAGE_INPUT),
                dbc.Input(
                    id=WizardIDs.SLIPPAGE_INPUT,
                    type="number",
                    min=0,
                    max=5,
                    step=0.01,
                    value=0.05,
                    className="mb-3"
                ),
                dbc.Button("Confirm", id=WizardIDs.CONFIRM_COSTS_BUTTON, color="primary", className="mt-3")
            ]),
            is_hidden=True
        ),
        # Step 6: Rebalancing Rules - Added with proper IDs
        create_wizard_step(
            "rebalancing-rules",
            "Step 6: Rebalancing Rules",
            html.Div([
                html.Label("Rebalancing Frequency:", className="mb-2", htmlFor=WizardIDs.REBALANCING_FREQUENCY_DROPDOWN),
                dcc.Dropdown(
                    id=WizardIDs.REBALANCING_FREQUENCY_DROPDOWN,
                    options=[
                        {'label': 'Daily', 'value': 'D'},
                        {'label': 'Weekly', 'value': 'W'},
                        {'label': 'Monthly', 'value': 'M'},
                        {'label': 'Quarterly', 'value': 'Q'},
                        {'label': 'Annually', 'value': 'A'},
                        {'label': 'None', 'value': 'N'}
                    ],
                    value='M',  # Default to Monthly
                    clearable=False,
                    className="mb-3"
                ),
                html.Label("Rebalancing Threshold (%):", className="mb-2", htmlFor=WizardIDs.REBALANCING_THRESHOLD_INPUT),
                dbc.Input(
                    id=WizardIDs.REBALANCING_THRESHOLD_INPUT,
                    type="number",
                    min=0,
                    max=100,
                    step=1,
                    value=5,  # Default 5%
                    className="mb-3"
                ),
                dbc.Button("Confirm", id=WizardIDs.CONFIRM_REBALANCING_BUTTON, color="primary", className="mt-3")
            ]),
            is_hidden=True
        ),
        # Step 7: Summary (placeholder)
        create_wizard_step(
            "wizard-summary",
            "Step 7: Summary and Run Backtest",
            html.Div([
                html.Div(id=WizardIDs.SUMMARY_OUTPUT_CONTAINER, className="mb-4"),
                dbc.Button(
                    "Run Backtest",
                    id=WizardIDs.RUN_BACKTEST_BUTTON_WIZARD,
                    color="success",
                    size="lg",
                    className="mt-3 w-100",
                    disabled=True
                )
            ]),
            is_hidden=True
        )
    ]

    return html.Div([
        progress,
        html.Div(steps, id=WizardIDs.STEPS_CONTAINER, className="wizard-steps")
    ], id=WizardIDs.STRATEGY_CONFIG_CONTAINER, className="strategy-wizard")
