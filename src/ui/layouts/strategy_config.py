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

# Dodanie ścieżki głównego katalogu projektu do sys.path dla importów
try:
    # Próba importu z src (dla pełnej aplikacji)
    from src.core.data import DataLoader
    from src.core.constants import AVAILABLE_STRATEGIES
except ModuleNotFoundError:
    # Jeśli nie działa, dostosuj ścieżkę i zaimportuj ponownie
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
    if project_root not in sys.path:
        sys.path.append(project_root)
    
    # Ponowna próba importu
    from src.core.data import DataLoader
    from src.core.constants import AVAILABLE_STRATEGIES

def get_strategy_dropdown(available_strategies: Dict[str, Any]) -> dcc.Dropdown:
    """
    Creates a dropdown selector for available trading strategies.
    
    Args:
        available_strategies: Dictionary of strategy names and their classes
        
    Returns:
        dcc.Dropdown: A Dash dropdown component for strategy selection
    """
    return dcc.Dropdown(
        id="strategy-selector",
        options=[{"label": name, "value": name} for name in available_strategies.keys()],
        value=list(available_strategies.keys())[0] if available_strategies else None,
        className="mb-3", 
        clearable=False
    )

def generate_strategy_parameters(strategy_class) -> html.Div:
    """
    Dynamically generates form fields for a strategy's parameters.
    
    Args:
        strategy_class: The class of the selected strategy
        
    Returns:
        html.Div: Container with parameter input fields
    """
    # Handle case when no strategy is selected
    if not strategy_class:
        return html.P("Select a strategy.", className="text-muted")
    
    try:
        # Get signature of the strategy class constructor
        sig = inspect.signature(strategy_class.__init__)
        params_inputs = []
        
        # Process each parameter
        for name, param in sig.parameters.items():
            # Skip self, tickers, and special parameters
            if name in ['self', 'tickers', 'args', 'kwargs']:
                continue
            
            # Get default value or set to None if required
            default_value = param.default if param.default is not inspect.Parameter.empty else None
            
            # Initialize input attributes
            input_type = 'text'
            step = 'any'
            placeholder = str(default_value) if default_value is not None else "Required"
            required = default_value is None
            
            # Determine parameter type
            annotation = param.annotation
            if default_value is not None:
                target_type = type(default_value)
            elif annotation != inspect.Parameter.empty:
                target_type = annotation
            else:
                target_type = str
            
            # Handle boolean parameters with checkbox
            if target_type == bool:
                params_inputs.append(dbc.Row([
                    dbc.Label(name.replace('_', ' ').title(), width=6, className="small"),
                    dbc.Col(dbc.Checkbox(
                        id={'type': 'strategy-param', 'index': name}, 
                        value=bool(default_value)
                    ), width=6)
                ], className="mb-2 align-items-center"))
                continue
            
            # Handle integer parameters
            elif target_type == int:
                input_type = 'number'
                step = 1
            
            # Handle float parameters
            elif target_type == float:
                input_type = 'number'
                # Set appropriate step based on value magnitude
                step = 0.1  # default step
                if default_value is not None:
                    if abs(default_value) < 10:
                        step = 0.1
                    elif abs(default_value) < 100:
                        step = 1
                    else:
                        step = 10
            
            # Create input field for the parameter
            params_inputs.append(dbc.Row([
                dbc.Label(
                    name.replace('_', ' ').title(), 
                    width=6, 
                    className="small", 
                    html_for=str({'type': 'strategy-param', 'index': name})
                ),
                dbc.Col(dcc.Input(
                    id={'type': 'strategy-param', 'index': name},
                    type=input_type,
                    value=default_value,
                    step=step if input_type == 'number' else None,
                    placeholder=placeholder,
                    required=required,
                    className="form-control form-control-sm",
                    debounce=True
                ), width=6)
            ], className="mb-2 align-items-center"))
        
        # Handle case with no parameters
        if not params_inputs:
            return html.P("This strategy has no configurable parameters.", className="text-muted")
        
        # Return container with all parameter inputs
        return html.Div(children=params_inputs)
    
    except Exception as e:
        # Log error and return error message
        logger.error(f"Error inspecting strategy parameters: {e}", exc_info=True)
        return html.P(f"Error loading parameters: {str(e)}", className="text-danger")

def create_ticker_checklist(tickers):
    """
    Create a checklist component for selecting tickers, with search functionality.
    
    Args:
        tickers: List of available tickers
        
    Returns:
        A Dash HTML Div containing the ticker checklist component
    """
    if not tickers:
        return html.Div("No tickers available", className="text-light")
    
    # Calculate the number of columns and rows
    num_columns = 4
    max_tickers_per_column = len(tickers) // num_columns + (1 if len(tickers) % num_columns > 0 else 0)
    
    # Find the longest ticker for optimal width
    max_ticker_length = max(len(ticker) for ticker in tickers)
    ticker_width = max(70, max_ticker_length * 10)  # Minimum 70px, or 10px per character
    
    # Create checkboxes in a grid layout
    ticker_checkboxes = []
    
    for i, ticker in enumerate(tickers):
        row_idx = i % max_tickers_per_column
        col_idx = i // max_tickers_per_column
        
        if col_idx < num_columns:  # Ensure we don't exceed our column count
            ticker_checkbox = dbc.Checkbox(
                id={"type": "ticker-checkbox", "index": ticker},
                label=ticker,
                value=False,
                className="me-2 ticker-item",
                inputClassName="ticker-input",
                labelClassName="ticker-label",
            )
            
            ticker_checkboxes.append(ticker_checkbox)
    
    # Arrange checkboxes in columns
    checkbox_columns = []
    for col_idx in range(num_columns):
        start_idx = col_idx * max_tickers_per_column
        end_idx = min((col_idx + 1) * max_tickers_per_column, len(ticker_checkboxes))
        
        if start_idx < len(ticker_checkboxes):
            column = dbc.Col(
                ticker_checkboxes[start_idx:end_idx],
                width=3,
                style={"width": f"{ticker_width}px", "minWidth": f"{ticker_width}px"}
            )
            checkbox_columns.append(column)
    
    # Search input and Quick action buttons
    search_and_actions = dbc.Row([
        dbc.Col([
            dbc.InputGroup([
                dbc.InputGroupText(html.I(className="fas fa-search")),
                dbc.Input(
                    id="ticker-search",
                    placeholder="Search tickers...",
                    type="text",
                    className="mb-3"
                )
            ])
        ], width=6),
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button("Select All", id="select-all-tickers", color="secondary", size="sm", className="me-2"),
                dbc.Button("Clear All", id="clear-all-tickers", color="secondary", size="sm")
            ], className="float-end")
        ], width=6)
    ], className="mb-3")
    
    # Create the component
    return html.Div([
        search_and_actions,
        dbc.Row(checkbox_columns),
    ], 
    style={
        "maxHeight": "300px",
        "overflowY": "auto",
        "border": "1px solid #ccc",
        "borderRadius": "5px",
        "padding": "10px"
    },
    id="ticker-checklist-container")

def create_backtest_parameters() -> html.Div:
    """
    Creates a section for backtest configuration parameters.
    
    Returns:
        html.Div: Container with backtest parameter inputs
    """
    # Get available date range from data loader
    try:
        data_loader = DataLoader()
        min_date, max_date = data_loader.get_date_range()
        # Fixed start date at January 1, 2020
        default_start = pd.Timestamp('2020-01-01')
        # End date is the latest available data date
        default_end = pd.Timestamp.today() if max_date is None else max_date
        
        # Create year-based marks for the slider (only beginnings of years)
        date_marks = {}
        
        # Convert dates to Unix timestamps (milliseconds) for the RangeSlider
        fixed_start = pd.Timestamp('2020-01-01')
        if max_date is not None:
            # Get all years in the range from 2020 to max_date year
            start_year = 2020
            end_year = max_date.year
            
            for year in range(start_year, end_year + 1):
                year_start = pd.Timestamp(f"{year}-01-01")
                if year_start <= max_date:
                    date_ts = int(year_start.timestamp() * 1000)
                    date_marks[date_ts] = str(year)
    except Exception as e:
        logger.error(f"Error getting date range from DataLoader: {e}")
        default_start = pd.Timestamp('2020-01-01')
        default_end = pd.Timestamp.today()
        date_marks = {}
    
    # Convert default dates to timestamps for the slider
    default_start_ts = int(default_start.timestamp() * 1000)
    default_end_ts = int(default_end.timestamp() * 1000)
    min_date_ts = int(pd.Timestamp('2020-01-01').timestamp() * 1000)  # Fixed start at 2020-01-01
    max_date_ts = int(max_date.timestamp() * 1000) if max_date is not None else default_end_ts
    
    return html.Div(children=[
        html.Hr(className="my-3"),
        html.H5("Backtest Parameters", className="mb-3"),
        
        # Date Range Selection - nowoczesny interfejs z ulepszonym stylem
        dbc.Row(children=[
            dbc.Label("Date Range", width=4, className="col-form-label text-light"),
            dbc.Col(children=[
                html.Div(children=[
                    # Improved date range controls
                    dbc.Row([
                        # Start date
                        dbc.Col([
                            html.Div([
                                html.Span("Start Date:", className="text-light small d-block mb-1"),
                                dbc.Card(
                                    dbc.CardBody([
                                        dcc.DatePickerSingle(
                                            id='backtest-start-date',
                                            date=default_start.strftime('%Y-%m-%d'),
                                            display_format='YYYY-MM-DD',
                                            first_day_of_week=1,
                                            min_date_allowed=min_date.strftime('%Y-%m-%d') if min_date else default_start.strftime('%Y-%m-%d'),
                                            max_date_allowed=max_date.strftime('%Y-%m-%d') if max_date else default_end.strftime('%Y-%m-%d'),
                                            className="date-picker-dark"
                                        )
                                    ], className="p-2"),
                                    className="bg-dark border-primary",
                                )
                            ], className="mb-2"),
                        ], width=6),
                        
                        # End date
                        dbc.Col([
                            html.Div([
                                html.Span("End Date:", className="text-light small d-block mb-1"),
                                dbc.Card(
                                    dbc.CardBody([
                                        dcc.DatePickerSingle(
                                            id='backtest-end-date',
                                            date=default_end.strftime('%Y-%m-%d'),
                                            display_format='YYYY-MM-DD',
                                            first_day_of_week=1,
                                            min_date_allowed=min_date.strftime('%Y-%m-%d') if min_date else default_start.strftime('%Y-%m-%d'),
                                            max_date_allowed=max_date.strftime('%Y-%m-%d') if max_date else default_end.strftime('%Y-%m-%d'),
                                            className="date-picker-dark"
                                        )
                                    ], className="p-2"),
                                    className="bg-dark border-primary",
                                )
                            ], className="mb-2"),
                        ], width=6),
                    ], className="mb-2"),
                    
                    # Date range preview
                    dbc.Card(
                        dbc.CardBody([
                            html.Div(
                                id="date-range-preview",
                                children=f"Selected period: {default_start.strftime('%Y-%m-%d')} to {default_end.strftime('%Y-%m-%d')}",
                                className="text-center small"
                            )
                        ], className="py-2 px-3"),
                        className="bg-dark text-light border-secondary mb-3",
                    ),
                    
                    # Preset buttons for quick date selection
                    dbc.ButtonGroup(
                        [
                            dbc.Button("1M", id="date-range-1m", size="sm", outline=True, color="primary", className="px-2"),
                            dbc.Button("3M", id="date-range-3m", size="sm", outline=True, color="primary", className="px-2"),
                            dbc.Button("6M", id="date-range-6m", size="sm", outline=True, color="primary", className="px-2"),
                            dbc.Button("1Y", id="date-range-1y", size="sm", outline=True, color="primary", className="px-2"),
                            dbc.Button("2Y", id="date-range-2y", size="sm", outline=True, color="primary", className="px-2"),
                            dbc.Button("All", id="date-range-all", size="sm", outline=True, color="primary", className="px-2"),
                        ],
                        className="w-100 mb-2",
                    ),
                ], id="date-picker-container"),
            ], width=8)
        ], className="mb-4 align-items-start"),
        
        # Initial capital input
        dbc.Row(children=[
            dbc.Label("Initial Capital", width=4, className="col-form-label text-light"),
            dbc.Col(children=[
                dbc.Input(
                    id="backtest-capital",
                    type="number",
                    value=10000,
                    min=1,
                    step=1000,
                    className="bg-dark text-light border-secondary"
                )
            ], width=8)
        ], className="mb-3 align-items-center"),
        
        # Status indicator for the backtest
        html.Div(children=[
            html.Div(id="backtest-status", className="mt-3")
        ])
    ])

def create_strategy_config_section(tickers=None):
    """
    Creates the complete strategy configuration section with a step-by-step wizard.
    
    Args:
        tickers: List of available tickers
        
    Returns:
        html.Div: The complete strategy configuration section
    """
    try:
        # Define the progress bar for the wizard
        progress = dbc.Progress(
            value=0,
            id="wizard-progress",
            className="mb-3",
            style={"height": "4px"}
        )

        # Create all steps
        steps = [
            # Step 1: Strategy Selection
            create_wizard_step(
                "strategy-selection",
                "Step 1: Strategy Selection",
                html.Div([
                    html.Label("Select a strategy:", className="mb-2"),
                    get_strategy_dropdown(AVAILABLE_STRATEGIES),
                    dcc.Markdown(id="strategy-description", className="mb-3 mt-3"),
                    dbc.Button(
                        "Confirm",
                        id="confirm-strategy",
                        color="primary",
                        className="mt-3"
                    )
                ]),
                step_number=1
            ),
            
            # Step 2: Date Range Selection
            create_wizard_step(
                "date-range-selection",
                "Step 2: Date Range Selection",
                html.Div([
                    html.Label("Select date range:", className="mb-2"),
                    create_backtest_parameters(),
                    dbc.Button(
                        "Confirm",
                        id="confirm-dates",
                        color="primary",
                        className="mt-3"
                    )
                ]),
                is_hidden=True,
                step_number=2
            ),

            # Step 3: Tickers Selection
            create_wizard_step(
                "tickers-selection",
                "Step 3: Tickers Selection",
                html.Div([
                    html.Label("Select tickers to trade:", className="mb-2"),
                    create_ticker_checklist(tickers if tickers else []),
                    dbc.Button(
                        "Confirm",
                        id="confirm-tickers",
                        color="primary",
                        className="mt-3"
                    )
                ]),
                is_hidden=True,
                step_number=3
            ),

            # Step 4: Risk Management
            create_wizard_step(
                "risk-management",
                "Step 4: Risk Management",
                html.Div([
                    html.Label("Configure risk parameters:", className="mb-2"),
                    html.Div(id="risk-management-inputs", className="mb-3"),
                    dbc.Button(
                        "Confirm",
                        id="confirm-risk",
                        color="primary",
                        className="mt-3"
                    )
                ]),
                is_hidden=True,
                step_number=4
            ),

            # Step 5: Trading Costs and Slippage
            create_wizard_step(
                "trading-costs",
                "Step 5: Trading Costs",
                html.Div([
                    html.Label("Configure trading costs:", className="mb-2"),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Commission (%):", className="mb-2"),
                            dbc.Input(
                                id="commission-input",
                                type="number",
                                min=0,
                                max=100,
                                step=0.01,
                                value=0.1,
                                className="mb-3"
                            ),
                            html.Label("Slippage (%):", className="mb-2"),
                            dbc.Input(
                                id="slippage-input",
                                type="number",
                                min=0,
                                max=100,
                                step=0.01,
                                value=0.1,
                                className="mb-3"
                            )
                        ])
                    ]),
                    dbc.Button(
                        "Confirm",
                        id="confirm-costs",
                        color="primary",
                        className="mt-3"
                    )
                ]),
                is_hidden=True,
                step_number=5
            ),

            # Step 6: Rebalancing Rules
            create_wizard_step(
                "rebalancing-rules",
                "Step 6: Rebalancing Rules",
                html.Div([
                    html.Label("Configure rebalancing rules:", className="mb-2"),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Rebalancing Frequency:", className="mb-2"),
                            dcc.Dropdown(
                                id="rebalancing-frequency",
                                options=[
                                    {"label": "Daily", "value": "D"},
                                    {"label": "Weekly", "value": "W"},
                                    {"label": "Monthly", "value": "M"},
                                    {"label": "Quarterly", "value": "Q"},
                                    {"label": "Yearly", "value": "Y"}
                                ],
                                value="M",
                                className="mb-3"
                            ),
                            html.Label("Threshold for Rebalancing (%):", className="mb-2"),
                            dbc.Input(
                                id="rebalancing-threshold",
                                type="number",
                                min=0,
                                max=100,
                                step=0.1,
                                value=5,
                                className="mb-3"
                            )
                        ])
                    ]),
                    dbc.Button(
                        "Confirm",
                        id="confirm-rebalancing",
                        color="primary",
                        className="mt-3"
                    )
                ]),
                is_hidden=True,
                step_number=6
            ),

            # Step 7: Summary and Run Backtest
            create_wizard_step(
                "summary",
                "Step 7: Summary and Run Backtest",
                html.Div([
                    html.Label("Review your configuration:", className="mb-2"),
                    html.Div(id="wizard-summary-content", className="mb-3"),
                    dbc.Button(
                        children=[html.I(className="fas fa-play me-2"), "Run Backtest"],
                        id="run-backtest-button",
                        color="primary",
                        className="w-100 mt-3"
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
            html.H4("Error", className="text-danger"),
            html.P(str(e))
        ])

def create_wizard_step(step_id, title, content, is_hidden=False, step_number=0):
    """
    Creates a wizard step with accordion-style behavior.
    
    Args:
        step_id: Unique identifier for the step
        title: Step title
        content: Step content
        is_hidden: Whether the step should be hidden initially
        step_number: The step number (for display and status)
        
    Returns:
        html.Div: The styled wizard step
    """
    return html.Div([
        # Clickable header that's always visible
        html.Div([
            html.Div([
                html.Span(f"{step_number}", id=f"{step_id}-status", className="step-status me-2"),
                html.H5(title, className="mb-0 d-inline")
            ], id=f"{step_id}-header", className="step-header")
        ], className="mb-2", style={"cursor": "pointer"}),
        
        # Collapsible content section
        html.Div(
            content,
            id=f"{step_id}-content",
            style={"display": "none" if is_hidden else "block", "marginLeft": "30px", "paddingTop": "10px"},
        )
    ],
    id=f"{step_id}-container",
    className="wizard-step mb-3 border-bottom pb-3")

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