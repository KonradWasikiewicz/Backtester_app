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

# Import centralized IDs
from src.ui.ids.ids import WizardIDs, StrategyConfigIDs, AppStructureIDs

# Import the stepper component
from src.ui.components.stepper import create_wizard_stepper

# Add project root to sys.path for imports
try:
    # Try import from src for full application
    from src.services.data_service import DataService
    from src.core.constants import AVAILABLE_STRATEGIES
except ModuleNotFoundError:
    # On import failure, append project root to sys.path and retry imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
    if project_root not in sys.path:
        sys.path.append(project_root)

    # Retry import after path adjustment
    from src.services.data_service import DataService
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
        id=WizardIDs.STRATEGY_DROPDOWN,  # Updated to use centralized ID
        options=options,
        placeholder="Click here...",
        className="mb-3 w-100",
        clearable=False,
        style={"position": "relative", "zIndex": "1050"} # Higher z-index to appear above all other content
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
        id=StrategyConfigIDs.TICKER_INPUT_LEGACY,
        options=options, # Use the already formatted options directly
        value=[], # Default to nothing selected
        labelStyle={'display': 'block'} # Display each ticker on a new line
    )

# Example create_backtest_parameters (ensure IDs are correct)
def create_backtest_parameters():
    """Creates date pickers for backtest start and end dates."""
    logger.debug("Creating date range pickers.")
    try:
        # --- USE DATASERVICE --- 
        data_service = DataService()
        min_date, max_date = data_service.get_date_range()
        
        # Ensure minimum date is not earlier than Jan 1, 2020
        absolute_min_date = pd.Timestamp('2020-01-01')
        if min_date is None or min_date < absolute_min_date:
            min_date = absolute_min_date
            
        # Use latest data date as max
        default_end = max_date if max_date is not None else pd.Timestamp.today()
        default_start = min_date
        
        logger.debug(f"Date range set: Min={min_date.strftime('%Y-%m-%d')}, Max={max_date.strftime('%Y-%m-%d') if max_date else 'today'}")
    except Exception as e:
        logger.error(f"Error getting date range from DataService: {e}")
        min_date = pd.Timestamp('2020-01-01')
        max_date = pd.Timestamp.today()
        default_start = min_date
        default_end = max_date

    # Common date picker styling to center text
    date_picker_style = {
        "textAlign": "center",  # Center the date text
        "width": "150px"       # Fixed width for consistent layout
    }

    return html.Div([
        dbc.Row([
            dbc.Col(html.Div([
                html.Div([
                    html.Label('From:', className='mb-1', htmlFor=StrategyConfigIDs.BACKTEST_START_DATE_LEGACY),
                    html.Div(style={"width": "60px", "display": "inline-block"}),  # Spacer div 
                    dcc.DatePickerSingle(
                        id=StrategyConfigIDs.BACKTEST_START_DATE_LEGACY,
                        date=default_start.strftime('%Y-%m-%d'),
                        min_date_allowed=min_date.strftime('%Y-%m-%d'),
                        max_date_allowed=max_date.strftime('%Y-%m-%d') if max_date else None,
                        placeholder='Start Date',
                        display_format='YYYY-MM-DD',
                        className='mb-1', # Reduced margin
                        style=date_picker_style
                    )
                ], style={"display": "flex", "alignItems": "center"})
            ]), width=6),
            dbc.Col(html.Div([
                html.Div([
                    html.Label('To:', className='mb-1', htmlFor=StrategyConfigIDs.BACKTEST_END_DATE_LEGACY),
                    html.Div(style={"width": "60px", "display": "inline-block"}),  # Spacer div
                    dcc.DatePickerSingle(
                        id=StrategyConfigIDs.BACKTEST_END_DATE_LEGACY,
                        date=default_end.strftime('%Y-%m-%d'),
                        min_date_allowed=min_date.strftime('%Y-%m-%d'),
                        max_date_allowed=max_date.strftime('%Y-%m-%d') if max_date else None,
                        placeholder='End Date',
                        display_format='YYYY-MM-DD',
                        className='mb-1', # Reduced margin
                        style=date_picker_style
                    )
                ], style={"display": "flex", "alignItems": "center"})
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
        # --- Fetch tickers using DataService if not provided ---
        if tickers is None:
            try:
                data_service = DataService()
                tickers = data_service.get_available_tickers()
                # Format tickers for checklist: [{'label': 'TICKER', 'value': 'TICKER'}, ...]
                tickers = [{'label': t, 'value': t} for t in tickers]
            except Exception as e:
                logger.error(f"Error fetching tickers via DataService: {e}")
                tickers = [] # Fallback to empty list

        # --- Define step names for the stepper ---
        step_names = [
            "Strategy",
            "Date Range",
            "Tickers",
            "Risk",
            "Costs",
            "Rebalancing",
            "Summary"
        ]
        
        # --- Create stepper components (NEW WAY) ---
        # Get the initial list of indicator components
        initial_stepper_indicators = create_wizard_stepper(current_step_index=1, completed_steps=set())

        # This is the html.Div that will contain the step indicators.
        # Its 'children' property will be updated by the handle_step_transition callback.
        wizard_stepper_div = html.Div(
            children=initial_stepper_indicators, # Initial children
            id=WizardIDs.WIZARD_STEPPER,
            className="wizard-stepper progress-style mb-2" # CSS class for the stepper bar itself
        )
        
        # --- Keep the original progress bar but hide it initially ---
        # This is kept for compatibility with existing callbacks if any still use it, though it's hidden.
        progress_bar = dbc.Progress(
            id=WizardIDs.PROGRESS_BAR, 
            value=0, 
            striped=True, 
            animated=True, 
            className="d-none",  # Hide it by default
            style={"display": "none"}
        )

        # This is the outer container that gets sticky styling.
        # It holds the wizard_stepper_div (which contains the actual step indicators) and the hidden progress_bar.
        progress_container_for_stepper = html.Div([
            wizard_stepper_div,    # The Div that groups the step indicators
            progress_bar           # The hidden progress bar
        ], id=WizardIDs.PROGRESS_CONTAINER, className="wizard-stepper-container") # Class for sticky behavior

        # --- Definition of wizard steps ---
        steps = [
            create_wizard_step(
                "strategy-selection",
                "Step 1: Initial Capital and Strategy Selection",
                html.Div([
                    html.Label("Initial Capital (USD):", className="mb-1", htmlFor=WizardIDs.INITIAL_CAPITAL_INPUT), 
                    dbc.Input(
                        id=WizardIDs.INITIAL_CAPITAL_INPUT,
                        type='text',  
                        value="100 000",  
                        className="mb-2 numeric-input-formatted", 
                    ),
                    html.Label("Select a strategy:", className="mb-1", htmlFor=WizardIDs.STRATEGY_DROPDOWN), 
                    get_strategy_dropdown(AVAILABLE_STRATEGIES),
                    html.Div(id=WizardIDs.STRATEGY_DESCRIPTION_OUTPUT, className="mb-2 mt-2"), 
                    html.Div(id=WizardIDs.STRATEGY_PARAM_INPUTS_CONTAINER, className="mt-3 mb-2"), 
                    dbc.Button("Confirm", id=WizardIDs.CONFIRM_STRATEGY_BUTTON, color="primary", className="mt-2", disabled=True) 
                ]),
                step_number=1
            ),
            create_wizard_step(
                "date-range-selection",
                "Step 2: Selection",
                html.Div([
                    html.Label("Select date range:", className="mb-1"), 
                    html.Div([
                        dbc.Row([
                            dbc.Col(html.Div([
                                html.Div([
                                    html.Label('From:', className='mb-1', htmlFor=WizardIDs.DATE_RANGE_START_PICKER),
                                    html.Div(style={"width": "60px", "display": "inline-block"}),
                                    dcc.DatePickerSingle(
                                        id=WizardIDs.DATE_RANGE_START_PICKER,
                                        date=pd.Timestamp('2020-01-01').strftime('%Y-%m-%d'),
                                        min_date_allowed=pd.Timestamp('2020-01-01').strftime('%Y-%m-%d'),
                                        max_date_allowed=pd.Timestamp.today().strftime('%Y-%m-%d'),
                                        placeholder='Start Date',
                                        display_format='YYYY-MM-DD',
                                        className='mb-1',
                                        style={"textAlign": "center", "width": "150px"}
                                    )
                                ], style={"display": "flex", "alignItems": "center"})
                            ]), width=6),
                            dbc.Col(html.Div([
                                html.Div([
                                    html.Label('To:', className='mb-1', htmlFor=WizardIDs.DATE_RANGE_END_PICKER),
                                    html.Div(style={"width": "60px", "display": "inline-block"}),
                                    dcc.DatePickerSingle(
                                        id=WizardIDs.DATE_RANGE_END_PICKER,
                                        date=pd.Timestamp.today().strftime('%Y-%m-%d'),
                                        min_date_allowed=pd.Timestamp('2020-01-01').strftime('%Y-%m-%d'),
                                        max_date_allowed=pd.Timestamp.today().strftime('%Y-%m-%d'),
                                        placeholder='End Date',
                                        display_format='YYYY-MM-DD',
                                        className='mb-1',
                                        style={"textAlign": "center", "width": "150px"}
                                    )
                                ], style={"display": "flex", "alignItems": "center"})
                            ]), width=6)
                        ])
                    ]),
                    dbc.Button(
                        "Confirm",
                        id=WizardIDs.CONFIRM_DATES_BUTTON,
                        color="primary",
                        className="mt-2",
                        disabled=True
                    )
                ]),
                is_hidden=True,
                step_number=2
            ),
            create_wizard_step(
                "tickers-selection",
                "Step 3: Tickers Selection",
                html.Div([
                    html.Label("Select tickers to trade:", className="mb-1", htmlFor=WizardIDs.TICKER_DROPDOWN), 
                    html.Div([
                        dbc.Button("Select All", id=WizardIDs.SELECT_ALL_TICKERS_BUTTON, color="secondary", size="sm", className="me-2"),
                        dbc.Button("Deselect All", id=WizardIDs.DESELECT_ALL_TICKERS_BUTTON, color="secondary", size="sm")
                    ], className="mb-1"),
                    dcc.Dropdown(
                        id=WizardIDs.TICKER_DROPDOWN,
                        options=tickers if tickers else [],
                        multi=True,
                        placeholder="Select tickers...",
                        className="mb-2 w-100"
                    ),
                    html.Div(id=WizardIDs.TICKER_LIST_CONTAINER, className="mt-2"), # ADDED: Container for selected ticker badges
                    dbc.Button(
                        "Confirm",
                        id=WizardIDs.CONFIRM_TICKERS_BUTTON,
                        color="primary",
                        className="mt-2",
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
                    html.Label("Configure risk parameters:", className="mb-1", htmlFor=WizardIDs.RISK_FEATURES_CHECKLIST),
                    dcc.Checklist(
                        id=WizardIDs.RISK_FEATURES_CHECKLIST,
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
                        className="mb-2"
                    ),
                    # Panels for each risk feature, hidden by default
                    html.Div([  # Position Sizing Panel
                        dbc.Row([
                            dbc.Col([
                                html.Label("Max Position Size (%):", className="mb-1", htmlFor=WizardIDs.MAX_POSITION_SIZE_INPUT),
                                dbc.Input(id=WizardIDs.MAX_POSITION_SIZE_INPUT, type="number", min=0, max=100, step=1, size="sm")
                            ], width="auto")
                        ], className="align-items-center ms-3 mb-3")
                    ], id=WizardIDs.RISK_PANEL_POSITION_SIZING, style={"display": "none"}),

                    html.Div([  # Stop Loss Panel
                        dbc.Row([
                            dbc.Col([
                                html.Label("Type:", className="mb-1", htmlFor=WizardIDs.STOP_LOSS_TYPE_SELECT),
                                dcc.Dropdown(id=WizardIDs.STOP_LOSS_TYPE_SELECT, options=[{'label':'Fixed','value':'fixed'},{'label':'Trailing','value':'trailing'}], value='fixed', clearable=False, className="mb-2 w-100")
                            ], width=5),
                            dbc.Col([
                                html.Label("Value (%):", className="mb-1", htmlFor=WizardIDs.STOP_LOSS_INPUT),
                                dbc.Input(id=WizardIDs.STOP_LOSS_INPUT, type="number", min=0, step=0.1, size="sm")
                            ], width="auto")
                        ], className="align-items-center ms-3 mb-3")
                    ], id=WizardIDs.RISK_PANEL_STOP_LOSS, style={"display": "none"}),

                    html.Div([  # Take Profit Panel
                        dbc.Row([
                            dbc.Col([
                                html.Label("Type:", className="mb-1", htmlFor=WizardIDs.TAKE_PROFIT_TYPE_SELECT),
                                dcc.Dropdown(id=WizardIDs.TAKE_PROFIT_TYPE_SELECT, options=[{'label':'Fixed','value':'fixed'},{'label':'Trailing','value':'trailing'}], value='fixed', clearable=False, className="mb-2 w-100")
                            ], width=5),
                            dbc.Col([
                                html.Label("Value (%):", className="mb-1", htmlFor=WizardIDs.TAKE_PROFIT_INPUT),
                                dbc.Input(id=WizardIDs.TAKE_PROFIT_INPUT, type="number", min=0, step=0.1, size="sm")
                            ], width="auto")
                        ], className="align-items-center ms-3 mb-3")
                    ], id=WizardIDs.RISK_PANEL_TAKE_PROFIT, style={"display": "none"}),

                    html.Div([  # Risk per Trade Panel
                        dbc.Row([
                            dbc.Col([
                                html.Label("Max Risk per Trade (%):", className="mb-1", htmlFor=WizardIDs.MAX_RISK_PER_TRADE_INPUT),
                                dbc.Input(id=WizardIDs.MAX_RISK_PER_TRADE_INPUT, type="number", min=0, step=0.1, size="sm")
                            ], width="auto")
                        ], className="align-items-center ms-3 mb-3")
                    ], id=WizardIDs.RISK_PANEL_RISK_PER_TRADE, style={"display": "none"}),

                    html.Div([  # Market Filter Panel
                        dbc.Row([
                            dbc.Col([
                                html.Label("Trend Lookback (days):", className="mb-1", htmlFor=WizardIDs.MARKET_TREND_LOOKBACK_INPUT),
                                dbc.Input(id=WizardIDs.MARKET_TREND_LOOKBACK_INPUT, type="number", min=1, step=1, size="sm")
                            ], width="auto")
                        ], className="align-items-center ms-3 mb-3")
                    ], id=WizardIDs.RISK_PANEL_MARKET_FILTER, style={"display": "none"}),

                    html.Div([  # Drawdown Protection Panel
                        dbc.Row([
                            dbc.Col([
                                html.Label("Max Drawdown (%):", className="mb-1", htmlFor=WizardIDs.MAX_DRAWDOWN_INPUT),
                                dbc.Input(id=WizardIDs.MAX_DRAWDOWN_INPUT, type="number", min=0, step=0.1, size="sm")
                            ], width="auto", className="me-4"),
                            dbc.Col([
                                html.Label("Max Daily Loss (%):", className="mb-1", htmlFor=WizardIDs.MAX_DAILY_LOSS_INPUT),
                                dbc.Input(id=WizardIDs.MAX_DAILY_LOSS_INPUT, type="number", min=0, step=0.1, size="sm")
                            ], width="auto")
                        ], className="align-items-center ms-3 mb-3")
                    ], id=WizardIDs.RISK_PANEL_DRAWDOWN_PROTECTION, style={"display": "none"}),

                    dbc.Button(
                        "Continue without additional risk measures",
                        id=WizardIDs.CONFIRM_RISK_BUTTON,
                        color="primary",
                        className="mt-2",
                        disabled=True
                    )
                ]),
                is_hidden=True, step_number=4
            ),
            create_wizard_step(
                "trading-costs",
                "Step 5: Trading Costs",
                html.Div([
                    html.Label("Configure trading costs:", className="mb-1"), 
                    dbc.Row([
                        dbc.Col([
                            html.Label("Commission (%):", className="mb-1", htmlFor=WizardIDs.COMMISSION_INPUT),
                            dbc.Input(
                                id=WizardIDs.COMMISSION_INPUT, 
                                type="number", 
                                min=0, 
                                step=0.01, 
                                value=0.1,
                                size="sm"
                            )
                        ], width="auto", className="d-flex flex-column align-items-start me-4"),
                        dbc.Col([
                            html.Label("Slippage (%):", className="mb-1", htmlFor=WizardIDs.SLIPPAGE_INPUT),
                            dbc.Input(
                                id=WizardIDs.SLIPPAGE_INPUT, 
                                type="number", 
                                min=0, 
                                step=0.01, 
                                value=0.05,
                                size="sm"
                            )
                        ], width="auto", className="d-flex flex-column align-items-start")
                    ], className="align-items-center mb-2"),
                    dbc.Button(
                        "Confirm",
                        id=WizardIDs.CONFIRM_COSTS_BUTTON,
                        color="primary",
                        className="mt-2",
                        disabled=True
                    )
                ]),
                is_hidden=True, step_number=5
            ),
             create_wizard_step(
                "rebalancing-rules",
                "Step 6: Rebalancing Rules",
                html.Div([
                    html.Label("Configure rebalancing rules:", className="mb-1"), 
                    dbc.Row([
                        dbc.Col([
                            html.Label("Frequency:", className="mb-1", htmlFor=WizardIDs.REBALANCING_FREQUENCY_DROPDOWN),
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
                                value='M', 
                                clearable=False, 
                                className="mb-2 w-100"
                            )
                        ], width=5),
                        dbc.Col([
                            html.Label("Threshold (%):", className="mb-1", htmlFor=WizardIDs.REBALANCING_THRESHOLD_INPUT),
                            dbc.Input(
                                id=WizardIDs.REBALANCING_THRESHOLD_INPUT, 
                                type="number", 
                                min=0, 
                                step=0.1, 
                                value=5.0, 
                                size="sm"
                            )
                        ], width="auto")
                    ], className="align-items-center ms-3 mb-2"),
                    dbc.Button(
                        "Confirm",
                        id=WizardIDs.CONFIRM_REBALANCING_BUTTON,
                        color="primary",
                        className="mt-2",
                        disabled=True
                    )
                ]),
                is_hidden=True, step_number=6
            ),
            create_wizard_step(
                "wizard-summary",
                "Step 7: Summary and Run Backtest",
                html.Div([
                    html.H5("Strategy Configuration Summary", className="mb-3 text-center"),
                    html.Div([
                        html.Div(id=WizardIDs.SUMMARY_STRATEGY_DETAILS, className="summary-section"),
                        html.Div(id=WizardIDs.SUMMARY_STRATEGY_PARAMETERS, className="summary-section"),
                        html.Div(id=WizardIDs.SUMMARY_DATES_DETAILS, className="summary-section"),
                        html.Div(id=WizardIDs.SUMMARY_TICKERS_DETAILS, className="summary-section"),
                        html.Div(id=WizardIDs.SUMMARY_RISK_DETAILS, className="summary-section"),
                        html.Div(id=WizardIDs.SUMMARY_COSTS_DETAILS, className="summary-section"),
                        html.Div(id=WizardIDs.SUMMARY_REBALANCING_DETAILS, className="summary-section")
                    ], id=WizardIDs.SUMMARY_OUTPUT_CONTAINER, className="mb-3"),
                    dbc.Button(
                        "Run Backtest",
                        id=WizardIDs.RUN_BACKTEST_BUTTON_WIZARD,
                        color="success",
                        className="w-100 mt-2",
                        disabled=True
                    )
                ]),
                is_hidden=True,
                step_number=7
            )
        ]        # Wrap all steps in a single container
        return html.Div([
            progress_container_for_stepper, # MODIFIED: Use the new container for the stepper
            html.Div(steps, id=WizardIDs.STEPS_CONTAINER, className="wizard-steps"),
            dcc.Store(id=WizardIDs.RISK_MANAGEMENT_STORE_WIZARD),
            dcc.Store(id=WizardIDs.STRATEGY_PARAMS_STORE)  # Add store for strategy-specific parameters
        ], id=WizardIDs.STRATEGY_CONFIG_CONTAINER, className="strategy-wizard")

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
    # Add padding for spacing
    content_style.update({"paddingTop": "10px"})
    # Default to pending state for initial display
    initial_header_class = "wizard-step-header-pending" if step_number > 0 else "wizard-step-header-current"
      # Set overflow style for the card body based on step_id
    # For strategy step, allow overflow visible to show dropdown
    overflow_style = {"overflow": "visible"} if step_id == "strategy-selection" else {}
    
    return dbc.Card(
        [
            dbc.CardHeader(
                # Wrap H5 in an html.Div and assign the ID here - this div gets the header class for coloring
                html.Div(
                    html.H6(title, className="mb-0 fw-bold text-white"), # Changed H5 to H6 for more compact sizing
                    id=WizardIDs.step_header(step_id), # ID for click events moved to Div
                    className=initial_header_class, # Apply initial coloring to the div directly
                    style={"cursor": "pointer", "width": "100%", "padding": "2px"} # Further reduced padding
                ),
                className="step-header p-0" # Remove padding from header, apply to div inside
                # Removed ID from CardHeader itself
            ),
            # Assign the ID expected by the callback for content visibility control
            dbc.CardBody(
                content,
                id=WizardIDs.step_content(step_id),
                style={**content_style, **overflow_style}, # Apply visibility and overflow styles
                className="px-2 py-1" # Reduced vertical padding further
            )
        ],
        className="mb-0 wizard-step", # Changed from mb-1 to mb-0 to minimize spacing between steps
        style={"marginBottom": "2px", "overflow": "visible"} # Corrected: "margin-bottom" to "marginBottom"
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
                            id=AppStructureIDs.IMPORT_TICKERS_TEXT_INPUT,
                            placeholder="Enter tickers, one per line",
                            className="mb-3",
                            style={"height": "200px"}
                        ),
                        dbc.Button("Import", id=AppStructureIDs.IMPORT_TICKERS_SUBMIT_BUTTON, color="primary")
                    ])
                ], label="Text Input"),
                dbc.Tab([
                    html.Div([
                        dcc.Upload(
                            id=AppStructureIDs.IMPORT_TICKERS_FILE_UPLOAD,
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
                        html.Div(id=AppStructureIDs.IMPORT_TICKERS_FILE_OUTPUT, className="mt-3")
                    ])
                ], label="File Upload")
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id=AppStructureIDs.IMPORT_TICKERS_CLOSE_BUTTON, color="secondary")
        ])
    ], id=AppStructureIDs.IMPORT_TICKERS_MODAL, size="lg")