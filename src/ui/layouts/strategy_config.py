import dash_bootstrap_components as dbc
import inspect
from dash import html, dcc
import logging
import traceback
from typing import Dict, Any, List
import pandas as pd
import os
import sys

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

def create_ticker_checklist(available_tickers: List[str] = None) -> html.Div:
    """
    Creates a checklist component for ticker selection with optimized layout.
    
    Args:
        available_tickers: List of available ticker symbols
        
    Returns:
        html.Div: A container with the ticker selection interface
    """
    if not available_tickers:
        available_tickers = []
    
    # Calculate number of columns and rows for the grid
    num_columns = 4
    num_rows = (len(available_tickers) + num_columns - 1) // num_columns
    
    # Find the longest ticker for column width
    max_ticker_length = max(len(ticker) for ticker in available_tickers) if available_tickers else 0
    ticker_col_width = f"{max_ticker_length * 0.8}em"  # Adjust multiplier based on font size
    
    # Create grid layout
    grid_items = []
    for i in range(num_rows):
        row_items = []
        for j in range(num_columns):
            idx = i * num_columns + j
            if idx < len(available_tickers):
                ticker = available_tickers[idx]
                row_items.append(
                    dbc.Col([
                        html.Div([
                            html.Span(ticker, style={
                                "width": ticker_col_width,
                                "display": "inline-block",
                                "vertical-align": "middle",
                                "line-height": "1.5"
                            }),
                            dbc.Checkbox(
                                id={"type": "ticker-checkbox", "index": ticker},
                                value=False,
                                className="ms-2",
                                style={"transform": "scale(1.2)"}  # Make checkbox larger
                            )
                        ], className="d-flex align-items-center", style={"min-height": "2em"})
                    ], width="auto", className="px-2")
                )
            else:
                row_items.append(dbc.Col(width="auto", className="px-2"))
        grid_items.append(dbc.Row(row_items, className="mb-2"))
    
    return html.Div(children=[
        html.Label("Select Tickers", className="form-label"),
        
        # Search input
        dbc.Input(
            id="ticker-search",
            type="text",
            placeholder="Search tickers...",
            className="mb-2",
            debounce=True
        ),
        
        # Ticker grid
        html.Div(grid_items, className="ticker-grid mb-3", style={
            "max-height": "300px",
            "overflow-y": "auto",  # Only allow vertical scroll
            "overflow-x": "hidden", # Hide horizontal scroll
            "padding": "0.5rem"
        }),
        
        # Quick actions
        html.Div([
            dbc.Button("Select All", id="select-all-tickers", color="primary", size="sm", className="me-2"),
            dbc.Button("Clear All", id="clear-all-tickers", color="secondary", size="sm"),
        ], className="mt-2"),
        
        html.Small(
            "Select one or more tickers to include in the backtest. Use search to filter tickers.",
            className="text-muted d-block mt-1"
        )
    ], className="mb-3")

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

def create_strategy_config_section(available_tickers: List[str] = None) -> dbc.Card:
    """
    Creates the strategy configuration section of the UI.
    
    Args:
        available_tickers: List of available ticker symbols
        
    Returns:
        dbc.Card: A card component containing the strategy configuration UI
    """
    if not available_tickers:
        available_tickers = []
    
    # Strategy descriptions for tooltips
    strategy_descriptions = {
        'MA': {
            'name': 'Moving Average Crossover',
            'description': [
                'Uses crossing of two moving averages to generate signals',
                'Buy when fast MA crosses above slow MA',
                'Sell when fast MA crosses below slow MA',
                'Effective in trending markets'
            ]
        },
        'RSI': {
            'name': 'Relative Strength Index',
            'description': [
                'Uses overbought/oversold conditions to generate signals',
                'Buy when RSI crosses above oversold threshold',
                'Sell when RSI crosses below overbought threshold',
                'Effective in ranging markets'
            ]
        },
        'BB': {
            'name': 'Bollinger Bands',
            'description': [
                'Uses price movement relative to volatility bands',
                'Buy when price touches lower band and starts rising',
                'Sell when price touches upper band and starts falling',
                'Adapts to changing market volatility'
            ]
        }
    }
    
    # Create strategy dropdown with full names
    strategy_dropdown = dcc.Dropdown(
        id="strategy-selector",
        options=[
            {"label": strategy_descriptions[key]['name'], "value": key} 
            for key in AVAILABLE_STRATEGIES.keys()
        ],
        value=list(AVAILABLE_STRATEGIES.keys())[0] if AVAILABLE_STRATEGIES else None,
        style={
            'backgroundColor': '#1e222d',
            'color': '#ffffff',
            'border': '1px solid #444'
        },
        className="w-100"
    )
    
    # Create strategy description div
    strategy_description = html.Div(
        id="strategy-description",
        className="mt-2 px-2 py-2",
        style={'backgroundColor': '#2a2e39', 'borderRadius': '5px'}
    )
    
    return dbc.Card([
        dbc.CardHeader("Strategy Configuration", className="bg-dark text-light"),
        dbc.CardBody([
            # Strategy Selection
            dbc.Row([
                dbc.Col([
                    dbc.Label("Select Strategy", html_for="strategy-selector", className="text-light"),
                    strategy_dropdown,
                    strategy_description
                ], width=12)
            ], className="mb-3"),
            
            # Date Range Selection
            dbc.Row([
                dbc.Col([
                    dbc.Label("Start Date", html_for="slider-start-date-picker", className="text-light"),
                    dcc.DatePickerSingle(
                        id="slider-start-date-picker",
                        date=pd.Timestamp('2020-01-01'),
                        display_format='YYYY-MM-DD',
                        first_day_of_week=1,
                        min_date_allowed=pd.Timestamp('2010-01-01'),
                        max_date_allowed=pd.Timestamp.today(),
                        initial_visible_month=pd.Timestamp('2020-01-01'),
                        className="w-100",
                        style={'backgroundColor': '#1e222d', 'color': '#ffffff', 'borderRadius': '5px'},
                        calendar_orientation='vertical'
                    )
                ], width=6),
                dbc.Col([
                    dbc.Label("End Date", html_for="slider-end-date-picker", className="text-light"),
                    dcc.DatePickerSingle(
                        id="slider-end-date-picker",
                        date=pd.Timestamp.today(),
                        display_format='YYYY-MM-DD',
                        first_day_of_week=1,
                        min_date_allowed=pd.Timestamp('2010-01-01'),
                        max_date_allowed=pd.Timestamp.today(),
                        initial_visible_month=pd.Timestamp.today(),
                        className="w-100",
                        style={'backgroundColor': '#1e222d', 'color': '#ffffff', 'borderRadius': '5px'},
                        calendar_orientation='vertical'
                    )
                ], width=6)
            ], className="mb-3"),
            
            # Ticker Selection
            create_ticker_checklist(available_tickers),
            
            # Strategy Parameters
            html.Div(id="strategy-parameters", className="mt-3"),
            
            # Run Backtest Button
            dbc.Button(
                "Run Backtest",
                id="run-backtest-button",
                color="primary",
                className="w-100 mt-3"
            ),
            
            # Status indicator
            html.Div(id="backtest-status", className="mt-2")
        ], className="bg-dark")
    ], className="border-secondary")

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