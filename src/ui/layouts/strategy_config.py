import dash_bootstrap_components as dbc
import inspect
from dash import html, dcc
import logging
import traceback
from typing import Dict, Any, List
import pandas as pd
import os
import sys
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Add project root to sys.path for imports
try:
    # Try import from src for full application
    from src.core.data import DataLoader
    from src.core.constants import AVAILABLE_STRATEGIES
except ModuleNotFoundError:
    # On import failure, append project root to sys.path and retry imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
    if project_root not in sys.path:
        sys.path.append(project_root)

    # Retry import after path adjustment
    from src.core.data import DataLoader
    from src.core.constants import AVAILABLE_STRATEGIES

# --- Strategy dropdown creation function ---
def get_strategy_dropdown(available_strategies: List[Dict[str, str]]) -> dcc.Dropdown: # Changed typing to list of dicts
    """
    Creates a Dash Dropdown component for selecting a strategy.

    Args:
        available_strategies (list[dict]): A list of dictionaries,
            where each dict has 'label' and 'value' keys.

    Returns:
        dcc.Dropdown: The dropdown component.
    """
    logger.debug(f"Creating strategy dropdown with strategies: {available_strategies}")
    if not isinstance(available_strategies, list):
        logger.error(f"available_strategies is not a list: {type(available_strategies)}. Using empty options.")
        options = []
    else:
        # --- Corrected logic for creating options ---
        # Assume available_strategies is a list of dicts: [{'label': 'Display Name', 'value': 'ID'}, ...]
        options = [
            {"label": strategy.get("label", "Missing Label"), "value": strategy.get("value", "Missing Value")}
            for strategy in available_strategies
            if isinstance(strategy, dict) # Ensure element is a dict
        ]
        # Check if options are empty
        if not options:
             logger.warning("Generated empty options for strategy dropdown. Check AVAILABLE_STRATEGIES structure in constants.py.")

    return dcc.Dropdown(
        id='strategy-dropdown',
        options=options,
        placeholder="Click here...",
        className="mb-3 w-100",
        clearable=False,
        style={"backgroundColor": "#1e222d", "color": "#ffffff"}
    )

# ... (rest of the helper functions: generate_strategy_parameters, create_ticker_checklist, create_backtest_parameters - no changes in logic, but ensure IDs are consistent) ...
# Example create_ticker_checklist (ensure IDs are correct)
def create_ticker_checklist(ticker_options: List[Dict[str, str]]):
    """Creates a checklist for selecting tickers, accepting pre-formatted options."""
    logger.debug(f"Creating ticker checklist with options: {ticker_options}")
    # Directly use the provided options, assuming they are already in the correct format
    # Add a check for safety
    options = []
    if isinstance(ticker_options, list) and all(isinstance(opt, dict) and 'label' in opt and 'value' in opt for opt in ticker_options):
        options = ticker_options
    elif ticker_options: # Log if the format is unexpected
        logger.warning(f"Received unexpected format for ticker options: {ticker_options}. Expected list of dicts like {{'label': 'X', 'value': 'X'}}.")

    return dcc.Checklist(
        id='ticker-input',
        options=options, # Use the already formatted options directly
        value=[], # Default to nothing selected
        labelStyle={'display': 'block'} # Display each ticker on a new line
    )

# Example create_backtest_parameters (ensure IDs are correct)
def create_backtest_parameters():
    """Creates date pickers for backtest start and end dates."""
    logger.debug("Creating date range pickers.")
    # ... (logic for fetching dates) ...
    try:
        data_loader = DataLoader()
        min_date, max_date = data_loader.get_date_range()
        default_start = pd.Timestamp('2020-01-01')
        default_end = pd.Timestamp.today() if max_date is None else max_date
    except Exception as e:
        logger.error(f"Error getting date range from DataLoader: {e}")
        min_date = pd.Timestamp('2020-01-01')
        max_date = pd.Timestamp.today()
        default_start = min_date
        default_end = max_date

    return html.Div([
        dbc.Row([
            dbc.Col(html.Div([
                html.Label('From:', className='mb-1'),
                dcc.DatePickerSingle(
                    id='backtest-start-date',
                    date=default_start.strftime('%Y-%m-%d'),
                    min_date_allowed=min_date.strftime('%Y-%m-%d') if min_date else None,
                    max_date_allowed=max_date.strftime('%Y-%m-%d') if max_date else None,
                    placeholder='Start Date',
                    display_format='YYYY-MM-DD',
                    className='mb-2'
                )
            ]), width=6),
            dbc.Col(html.Div([
                html.Label('To:', className='mb-1'),
                dcc.DatePickerSingle(
                    id='backtest-end-date',
                    date=default_end.strftime('%Y-%m-%d'),
                    min_date_allowed=min_date.strftime('%Y-%m-%d') if min_date else None,
                    max_date_allowed=max_date.strftime('%Y-%m-%d') if max_date else None,
                    placeholder='End Date',
                    display_format='YYYY-MM-DD',
                    className='mb-2'
                )
            ]), width=6)
        ])
    ])


# --- Main function creating the strategy configuration section ---
def create_strategy_config_section(tickers=None):
    """
    Creates the main layout for the strategy configuration wizard.
    Includes all steps.
    """
    logger.info("Creating strategy configuration section layout...")
    try:
        # --- Progress bar ---
        progress = dbc.Progress(id="wizard-progress", value=0, striped=True, animated=True, className="mb-4")

        # --- Definition of wizard steps ---
        steps = [
            create_wizard_step(
                "strategy-selection",
                "Step 1: Initial Capital and Strategy Selection",
                html.Div([
                    html.Label("Initial Capital (USD):", className="mb-2"),
                    dbc.Input(
                        id='initial-capital-input',
                        type='text',  # Changed to text for formatting
                        value="100 000",  # Default value formatted
                        className="mb-3 numeric-input-formatted", # Added class for JS
                        style={"backgroundColor": "#1e222d", "color": "#ffffff"} # Added style
                    ),
                    html.Label("Select a strategy:", className="mb-2"), # Added mt-3 for spacing
                    get_strategy_dropdown(AVAILABLE_STRATEGIES),
                    html.Div(id="strategy-description-output", className="mb-3 mt-3"),
                    html.Div(id='strategy-param-section', className="mt-4 mb-3"),
                    dbc.Button("Confirm", id="confirm-strategy", color="primary", className="mt-3", disabled=True)
                ]),
                step_number=1
            ),
            create_wizard_step(
                "date-range-selection",
                "Step 2: Date Range Selection",
                html.Div([
                    html.Label("Select date range:", className="mb-2"),
                    create_backtest_parameters(), # Use helper function
                    dbc.Button(
                        "Confirm",
                        id="confirm-dates", # ID consistent with callbacks
                        color="primary",
                        className="mt-3",
                        disabled=True # Initially disabled
                    )
                ]),
                is_hidden=True,
                step_number=2
            ),
            create_wizard_step(
                "tickers-selection",
                "Step 3: Tickers Selection",
                html.Div([
                    html.Label("Select tickers to trade:", className="mb-2"),
                    html.Div([
                        dbc.Button("Select All", id="select-all-tickers", color="secondary", size="sm", className="me-2"),
                        dbc.Button("Deselect All", id="deselect-all-tickers", color="secondary", size="sm")
                    ], className="mb-2"),
                    create_ticker_checklist(tickers if tickers else []),
                    dbc.Button(
                        "Confirm",
                        id="confirm-tickers",
                        color="primary",
                        className="mt-3",
                        disabled=True
                    )
                ]),
                is_hidden=True,
                step_number=3
            ),
            create_wizard_step(
                "risk-management",
                "Step 4: Risk Management",
                html.Div([
                    html.Label("Configure risk parameters:", className="mb-2"),
                    # Checklist of risk features
                    dcc.Checklist(
                        id="risk-features-checklist",
                        options=[
                            {'label': 'Position Sizing', 'value': 'position_sizing'},
                            {'label': 'Stop Loss', 'value': 'stop_loss'},
                            {'label': 'Take Profit', 'value': 'take_profit'},
                            {'label': 'Risk per Trade', 'value': 'risk_per_trade'},
                            {'label': 'Market Filter', 'value': 'market_filter'},
                            {'label': 'Drawdown Protection', 'value': 'drawdown_protection'}
                        ],
                        value=[],
                        labelStyle={'display': 'block'},
                        className="mb-3"
                    ),
                    # Panels for each risk feature, hidden by default
                    html.Div([  # Position Sizing Panel
                        dbc.Row([
                            dbc.Col([
                                html.Label("Max Position Size (%):", className="mb-1"),
                                dbc.Input(id="max-position-size", type="number", min=0, max=100, step=1, size="sm", style={"width": "100px", "backgroundColor": "#1e222d", "color": "#ffffff"}) # Added style
                            ], width="auto")
                        ], className="align-items-center ms-3 mb-3")
                    ], id="position_sizing-panel", style={"display": "none"}),

                    html.Div([  # Stop Loss Panel
                        dbc.Row([
                            dbc.Col([
                                html.Label("Type:", className="mb-1"),
                                dcc.Dropdown(id="stop-loss-type", options=[{'label':'Fixed','value':'fixed'},{'label':'Trailing','value':'trailing'}], value='fixed', clearable=False, className="mb-2 w-100")
                            ], width=5),
                            dbc.Col([
                                html.Label("Value (%):", className="mb-1"),
                                dbc.Input(id="stop-loss-value", type="number", min=0, step=0.1, size="sm", style={"width":"100px", "backgroundColor": "#1e222d", "color": "#ffffff"}) # Added style
                            ], width="auto")
                        ], className="align-items-center ms-3 mb-3")
                    ], id="stop_loss-panel", style={"display": "none"}),

                    html.Div([  # Take Profit Panel
                        dbc.Row([
                            dbc.Col([
                                html.Label("Type:", className="mb-1"),
                                dcc.Dropdown(id="take-profit-type", options=[{'label':'Fixed','value':'fixed'},{'label':'Trailing','value':'trailing'}], value='fixed', clearable=False, className="mb-2 w-100")
                            ], width=5),
                            dbc.Col([
                                html.Label("Value (%):", className="mb-1"),
                                dbc.Input(id="take-profit-value", type="number", min=0, step=0.1, size="sm", style={"width":"100px", "backgroundColor": "#1e222d", "color": "#ffffff"}) # Added style
                            ], width="auto")
                        ], className="align-items-center ms-3 mb-3")
                    ], id="take_profit-panel", style={"display": "none"}),

                    html.Div([  # Risk per Trade Panel
                        dbc.Row([
                            dbc.Col([
                                html.Label("Max Risk per Trade (%):", className="mb-1"),
                                dbc.Input(id="max-risk-per-trade", type="number", min=0, step=0.1, size="sm", style={"width":"100px", "backgroundColor": "#1e222d", "color": "#ffffff"}) # Added style
                            ], width="auto")
                        ], className="align-items-center ms-3 mb-3")
                    ], id="risk_per_trade-panel", style={"display": "none"}),

                    html.Div([  # Market Filter Panel
                        dbc.Row([
                            dbc.Col([
                                html.Label("Trend Lookback (days):", className="mb-1"),
                                dbc.Input(id="market-trend-lookback", type="number", min=1, step=1, size="sm", style={"width":"100px", "backgroundColor": "#1e222d", "color": "#ffffff"}) # Added style
                            ], width="auto")
                        ], className="align-items-center ms-3 mb-3")
                    ], id="market_filter-panel", style={"display": "none"}),

                    html.Div([  # Drawdown Protection Panel
                        dbc.Row([
                            dbc.Col([
                                html.Label("Max Drawdown (%):", className="mb-1"),
                                dbc.Input(id="max-drawdown", type="number", min=0, step=0.1, size="sm", style={"width":"100px", "backgroundColor": "#1e222d", "color": "#ffffff"}) # Added style
                            ], width="auto", className="me-4"),
                            dbc.Col([
                                html.Label("Max Daily Loss (%):", className="mb-1"),
                                dbc.Input(id="max-daily-loss", type="number", min=0, step=0.1, size="sm", style={"width":"100px", "backgroundColor": "#1e222d", "color": "#ffffff"}) # Added style
                            ], width="auto")
                        ], className="align-items-center ms-3 mb-3")
                    ], id="drawdown_protection-panel", style={"display": "none"}),

                    dbc.Button(
                        "Continue without additional risk measures",
                        id="confirm-risk",
                        color="primary",
                        className="mt-3",
                        disabled=True
                    )
                ]),
                is_hidden=True, step_number=4
            ),
            create_wizard_step(
                "trading-costs",
                "Step 5: Trading Costs",
                html.Div([
                    html.Label("Configure trading costs:", className="mb-2"),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Commission (%):", className="mb-1"),
                            dbc.Input(
                                id="commission-input", type="number", min=0, step=0.01, value=0.1,
                                size="sm", style={"width": "100px", "backgroundColor": "#1e222d", "color": "#ffffff"} # Added style
                            )
                        ], width="auto", className="d-flex flex-column align-items-start me-4"),
                        dbc.Col([
                            html.Label("Slippage (%):", className="mb-1"),
                            dbc.Input(
                                id="slippage-input", type="number", min=0, step=0.01, value=0.05,
                                size="sm", style={"width": "100px", "backgroundColor": "#1e222d", "color": "#ffffff"} # Added style
                            )
                        ], width="auto", className="d-flex flex-column align-items-start")
                    ], className="align-items-center mb-3"),
                    dbc.Button(
                        "Confirm",
                        id="confirm-costs", # ID consistent with callbacks
                        color="primary",
                        className="mt-3",
                        disabled=True # Initially disabled
                    )
                ]),
                is_hidden=True, step_number=5
            ),
             create_wizard_step(
                "rebalancing-rules",
                "Step 6: Rebalancing Rules",
                html.Div([
                    html.Label("Configure rebalancing rules:", className="mb-2"),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Frequency:", className="mb-1"),
                            dcc.Dropdown(id="rebalancing-frequency", options=[
                                {'label': 'Daily', 'value': 'D'},
                                {'label': 'Weekly', 'value': 'W'},
                                {'label': 'Monthly', 'value': 'M'},
                                {'label': 'Quarterly', 'value': 'Q'},
                                {'label': 'Annually', 'value': 'A'}, # Changed Yearly to Annually for consistency with pandas
                                {'label': 'None', 'value': 'N'}
                            ], value='M', clearable=False, className="mb-2 w-100")
                        ], width=5),
                        dbc.Col([
                            html.Label("Threshold (%):", className="mb-1"),
                            dbc.Input(id="rebalancing-threshold", type="number", min=0, step=0.1, value=5.0, size="sm", style={"width":"100px", "backgroundColor": "#1e222d", "color": "#ffffff"}) # Added style
                        ], width="auto")
                    ], className="align-items-center ms-3 mb-3"),
                    dbc.Button(
                        "Confirm",
                        id="confirm-rebalancing",  # Consistent with callback Input
                        color="primary",
                        className="mt-3",
                        disabled=True  # Initially disabled
                    )
                ]),
                is_hidden=True, step_number=6
            ),
            create_wizard_step(
                "wizard-summary",
                "Step 7: Summary and Run Backtest",
                html.Div([
                    html.H5("Review Configuration Summary", className="mb-3"),
                    html.Div([
                        html.Div([
                            html.Strong("Strategy:"),
                            html.Span(id="summary-strategy-name", className="ms-2")
                        ], className="mb-2"),
                        html.Div([
                            html.Strong("Initial Capital:"),
                            html.Span(id="summary-initial-capital", className="ms-2")
                        ], className="mb-2"),
                        # Add other summary items here if needed
                    ], id="wizard-summary-output", className="mb-3"),
                    dbc.Button(
                        "Run Backtest",
                        id="run-backtest-button",
                        color="success",
                        className="w-100 mt-3",
                        disabled=True
                    )
                ]),
                is_hidden=True,
                step_number=7
            )
        ]

        # Wrap all steps in a single container
        return html.Div([
            progress,
            html.Div(steps, id="wizard-steps-container", className="wizard-steps")
        ], id="strategy-config-container", className="strategy-wizard")

    except Exception as e:
        logger.error(f"Error creating strategy config section: {e}", exc_info=True)
        return html.Div([
            dbc.Alert(f"Error generating strategy configuration layout: {e}", color="danger")
        ])

# --- Helper function creating a wizard step ---
def create_wizard_step(step_id, title, content, is_hidden=False, step_number=0):
    """Creates a single step (card) for the wizard."""
    # Content style controlled by is_hidden initially, and by callback later
    content_style = {"display": "none"} if is_hidden else {"display": "block"}
    # Add margin consistent with previous attempts
    content_style.update({"marginLeft": "30px", "paddingTop": "10px"})

    return dbc.Card(
        [
            dbc.CardHeader(
                # Wrap H5 in an html.Div and assign the ID here
                html.Div(
                    html.H5(title, className="mb-0 fw-bold"), # Keep existing title style
                    id=f"{step_id}-header", # ID for click events moved to Div
                    style={"cursor": "pointer"} # Indicate it's clickable
                ),
                className="step-header p-2" # Use step-header class for styling
                # Removed ID from CardHeader itself
            ),
            # Assign the ID expected by the callback for content visibility control
            dbc.CardBody(
                content,
                id=f"{step_id}-content",
                style=content_style # Apply visibility style here
            )
        ],
        className="mb-3 wizard-step" # Keep class for potential CSS targeting
        # No ID or style needed on the parent Card itself
    )

def create_import_tickers_modal() -> dbc.Modal:
    """
    Creates a modal for importing tickers from a file or text.
    """
    return dbc.Modal([
        dbc.ModalHeader("Import Tickers"),
        dbc.ModalBody([
            dbc.Tabs([
                dbc.Tab([
                    html.Div([
                        dbc.Textarea(
                            id="import-tickers-text",
                            placeholder="Enter tickers, one per line",
                            className="mb-3",
                            style={"height": "200px"}
                        ),
                        dbc.Button("Import", id="import-tickers-submit", color="primary")
                    ])
                ], label="Text Input"),
                dbc.Tab([
                    html.Div([
                        dcc.Upload(
                            id="import-tickers-file",
                            children=html.Div([
                                "Drag and drop or ",
                                html.A("select a file")
                            ]),
                            style={
                                "width": "100%",
                                "height": "200px",
                                "lineHeight": "200px",
                                "borderWidth": "1px",
                                "borderStyle": "dashed",
                                "borderRadius": "5px",
                                "textAlign": "center"
                            },
                            multiple=False
                        ),
                        html.Div(id="import-tickers-file-output", className="mt-3")
                    ])
                ], label="File Upload")
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id="import-tickers-close", color="secondary")
        ])
    ], id="import-tickers-modal", size="lg")