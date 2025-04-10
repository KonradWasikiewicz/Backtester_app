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
                    # Slider do wyboru zakresu dat
                    dcc.RangeSlider(
                        id="backtest-date-slider",
                        min=min_date_ts,
                        max=max_date_ts,
                        value=[default_start_ts, default_end_ts],
                        marks=date_marks,
                        allowCross=False,
                        className="mt-1 mb-3"
                    ),
                    
                    # Eleganckie wyświetlanie wybranych dat
                    dbc.Row([
                        # Data początkowa
                        dbc.Col([
                            html.Div([
                                html.Span("Start Date:", className="text-light small d-block mb-1"),
                                dbc.Card(
                                    children=[
                                        html.Div(
                                            id="selected-start-date",
                                            children=default_start.strftime('%Y-%m-%d'),
                                            className="text-center py-2 fw-bold"
                                        ),
                                    ],
                                    className="bg-dark border-primary",
                                    style={"cursor": "pointer"}
                                ),
                            ], className="mb-2"),
                        ], width=6),
                        
                        # Data końcowa
                        dbc.Col([
                            html.Div([
                                html.Span("End Date:", className="text-light small d-block mb-1"),
                                dbc.Card(
                                    children=[
                                        html.Div(
                                            id="selected-end-date",
                                            children=default_end.strftime('%Y-%m-%d'),
                                            className="text-center py-2 fw-bold"
                                        ),
                                    ],
                                    className="bg-dark border-primary",
                                    style={"cursor": "pointer"}
                                ),
                            ], className="mb-2"),
                        ], width=6),
                    ], className="mb-2"),
                    
                    # Ukryte pola do wyboru daty
                    html.Div([
                        # Picker daty początkowej z poprawionym stylem
                        dcc.DatePickerSingle(
                            id='slider-start-date-picker',
                            date=default_start.strftime('%Y-%m-%d'),
                            display_format='YYYY-MM-DD',
                            first_day_of_week=1,  # Monday as first day
                            min_date_allowed=min_date.strftime('%Y-%m-%d') if min_date else default_start.strftime('%Y-%m-%d'),
                            max_date_allowed=max_date.strftime('%Y-%m-%d') if max_date else default_end.strftime('%Y-%m-%d'),
                            style={"display": "none"},  # Ukryty - będzie używany tylko jako backend
                        ),
                        
                        # Picker daty końcowej z poprawionym stylem
                        dcc.DatePickerSingle(
                            id='slider-end-date-picker',
                            date=default_end.strftime('%Y-%m-%d'),
                            display_format='YYYY-MM-DD',
                            first_day_of_week=1,  # Monday as first day
                            min_date_allowed=min_date.strftime('%Y-%m-%d') if min_date else default_start.strftime('%Y-%m-%d'),
                            max_date_allowed=max_date.strftime('%Y-%m-%d') if max_date else default_end.strftime('%Y-%m-%d'),
                            style={"display": "none"},  # Ukryty - będzie używany tylko jako backend
                        ),
                    ]),
                    
                    # Przyciski szybkiego wyboru zakresów dat
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
                ], id="date-slider-container"),
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
        
        # Run backtest button
        dbc.Button(
            children=[html.I(className="fas fa-play me-2"), "Run Backtest"],
            id="run-backtest-button",
            color="primary",
            className="w-100 mt-3"
        ),
        
        # Status indicator for the backtest
        html.Div(children=[
            html.Div(id="backtest-status", className="mt-3")
        ])
    ])

def create_strategy_config_section(tickers=None):
    """
    Create the strategy configuration section of the interface.
    
    Args:
        tickers: List of available tickers to display (optional)
        
    Returns:
        A Dash HTML Div containing the strategy configuration UI
    """
    # If tickers not provided, load available tickers
    if tickers is None:
        tickers = loader.get_available_tickers()
    
    # Create a wizard interface with multiple steps
    return html.Div([
        # Hidden store for wizard state
        dcc.Store(id="wizard-state", data={}),
        
        # Wizard progress bar
        dbc.Progress(
            id="wizard-progress",
            value=0,
            className="mb-4",
            style={"height": "10px"}
        ),
        
        # Step 1: Strategy and Asset Selection
        create_wizard_step(
            step_id="step1",
            title="Step 1: Strategy and Asset Selection",
            content=[
                # Strategy Selection
                dbc.Row([
                    dbc.Col([
                        html.Label("Select Strategy", className="text-light"),
                        dcc.Dropdown(
                            id='strategy-selector',
                            options=[
                                {'label': 'Moving Average (MA)', 'value': 'MA'},
                                {'label': 'Relative Strength Index (RSI)', 'value': 'RSI'},
                                {'label': 'Bollinger Bands (BB)', 'value': 'BB'},
                            ],
                            placeholder="Select a strategy",
                            className="mb-3"
                        ),
                        html.Div(id="strategy-description", className="mb-3"),
                        html.Div(id="strategy-parameters", className="mb-3")
                    ], md=6),
                    
                    # Date Range Selection
                    dbc.Col([
                        html.Label("Select Date Range", className="text-light"),
                        dcc.DatePickerRange(
                            id='slider-start-date-picker',
                            min_date_allowed=datetime(2015, 1, 1),
                            max_date_allowed=datetime.now(),
                            initial_visible_month=datetime(2020, 1, 1),
                            start_date=datetime(2020, 1, 1),
                            end_date=datetime(2022, 12, 31),
                            className="mb-3 w-100"
                        ),
                    ], md=6)
                ]),
                
                # Ticker Selection Section
                dbc.Row([
                    dbc.Col([
                        html.Label("Select Tickers", className="text-light"),
                        create_ticker_checklist(tickers),
                    ])
                ]),
                
                # Step 1 Confirmation Button
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            "Confirm Selection", 
                            id="confirm-step1-btn", 
                            color="success", 
                            className="mt-3"
                        )
                    ], className="d-flex justify-content-end")
                ])
            ]
        ),
        
        # Step 2: Risk Management
        create_wizard_step(
            step_id="step2",
            title="Step 2: Risk Management",
            content=[
                dbc.Row([
                    dbc.Col([
                        html.Label("Risk Management Features", className="text-light"),
                        dbc.Checklist(
                            id="risk-features-checklist",
                            options=[
                                {"label": "Position Sizing", "value": "position_sizing"},
                                {"label": "Stop Loss", "value": "stop_loss"},
                                {"label": "Take Profit", "value": "take_profit"},
                                {"label": "Market Filter", "value": "market_filter"},
                                {"label": "Drawdown Protection", "value": "drawdown_protection"}
                            ],
                            value=[],
                            className="mb-3"
                        )
                    ], md=6),
                    
                    dbc.Col([
                        html.Label("Stop Loss Configuration", className="text-light"),
                        dbc.RadioItems(
                            id="stop-loss-type",
                            options=[
                                {"label": "Percentage", "value": "percent"},
                                {"label": "ATR Multiple", "value": "atr"},
                                {"label": "Trailing Stop", "value": "trailing"}
                            ],
                            value="percent",
                            className="mb-2"
                        ),
                        dcc.Slider(
                            id="stop-loss-value",
                            min=1,
                            max=10,
                            step=0.5,
                            value=2,
                            marks={i: str(i) for i in range(1, 11)},
                            className="mb-3"
                        ),
                    ], md=6)
                ]),
                
                # Step 2 Confirmation Button
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            "Confirm Risk Settings", 
                            id="confirm-step2-btn", 
                            color="success", 
                            className="mt-3"
                        )
                    ], className="d-flex justify-content-end")
                ])
            ]
        ),
        
        # Step 3: Run and Summary
        create_wizard_step(
            step_id="step3",
            title="Step 3: Confirm and Run",
            content=[
                dbc.Card([
                    dbc.CardHeader("Summary of Configuration", className="text-white bg-primary"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H6("Strategy:", className="text-muted mb-1"),
                                html.P(id="summary-strategy", className="lead mb-3"),
                                
                                html.H6("Date Range:", className="text-muted mb-1"),
                                html.P(id="summary-date-range", className="lead mb-3"),
                            ], md=6),
                            dbc.Col([
                                html.H6("Tickers:", className="text-muted mb-1"),
                                html.P(id="summary-tickers", className="lead mb-3"),
                                
                                html.H6("Risk Management:", className="text-muted mb-1"),
                                html.P(id="summary-risk", className="lead mb-3"),
                            ], md=6)
                        ]),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    "Run Backtest", 
                                    id="run-backtest-button", 
                                    color="primary", 
                                    size="lg",
                                    className="mt-3",
                                    disabled=True
                                )
                            ], className="d-flex justify-content-center")
                        ])
                    ])
                ])
            ]
        )
    ], className="strategy-config-section py-3")

def create_wizard_step(step_id, title, content):
    """
    Create a collapsible wizard step component
    
    Args:
        step_id: The ID prefix for the step
        title: The title of the step
        content: The content to display in the step
        
    Returns:
        A Dash component representing the step
    """
    header_card = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H5([
                        html.Span(id=f"{step_id}-status", className="me-2"),
                        title
                    ], className="mb-0")
                ]),
                dbc.Col([
                    html.Div(id=f"{step_id}-summary", className="text-end small text-muted")
                ], width="auto")
            ])
        ], className="py-2")
    ], id=f"{step_id}-header-card", className="mb-2", style={"cursor": "pointer"})
    
    return html.Div([
        header_card,
        # Summary collapse - this shows when step is completed
        dbc.Collapse(
            dbc.Card(dbc.CardBody(id=f"{step_id}-summary")),
            id=f"{step_id}-summary-collapse",
            is_open=False,
            className="mb-3"
        ),
        # Content collapse - this shows the step content
        dbc.Collapse(
            dbc.Card(dbc.CardBody(content)),
            id=f"{step_id}-collapse",
            is_open=step_id == "step1",  # First step is open by default
            className="mb-3"
        )
    ])

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