import dash_bootstrap_components as dbc
import inspect
from dash import html, dcc
import logging
import traceback
from typing import Dict, Any, List
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)

# Import DataLoader
from src.core.data import DataLoader

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
    Creates a checklist component for ticker selection.
    
    Args:
        available_tickers: List of available ticker symbols
        
    Returns:
        html.Div: A container with the ticker selection checklist
    """
    if not available_tickers:
        available_tickers = []
    
    return html.Div(children=[
        html.Label("Select Tickers", className="form-label"),
        dcc.Checklist(
            id="ticker-checklist",
            options=[{"label": ticker, "value": ticker} for ticker in available_tickers],
            value=[],  # Default: no tickers selected
            className="ticker-checklist",
            labelStyle={"display": "block", "margin-bottom": "5px"}
        ),
        html.Small(
            "Select one or more tickers to include in the backtest.",
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
        
        # Date Range Slider (default method)
        dbc.Row(children=[
            dbc.Label("Date Range", width=4, className="col-form-label"),
            dbc.Col(children=[
                html.Div(children=[
                    # Uproszczony komponent wyboru zakresu dat
                    html.Div(children=[
                        # Slider do wyboru zakresu dat
                        dcc.RangeSlider(
                            id="backtest-date-slider",
                            min=min_date_ts,
                            max=max_date_ts,
                            value=[default_start_ts, default_end_ts],
                            marks=date_marks,
                            allowCross=False,
                            className="mt-1 mb-3",
                            updatemode="drag",
                        ),
                        
                        # Wyświetlanie wybranych dat i przyciski do wywołania kalendarza
                        html.Div(children=[
                            # Data początkowa
                            dbc.Button(
                                id="selected-start-date", 
                                outline=True,
                                color="primary",
                                size="sm",
                                className="me-2",
                                style={"min-width": "115px"}
                            ),
                            
                            # Separator
                            html.Span(" do ", className="text-muted mx-2"),
                            
                            # Data końcowa
                            dbc.Button(
                                id="selected-end-date", 
                                outline=True,
                                color="primary",
                                size="sm",
                                className="ms-2",
                                style={"min-width": "115px"}
                            ),
                        ], className="d-flex justify-content-center align-items-center mb-4"),
                        
                        # Ukryte pola do wyboru daty - wyświetlane tylko po kliknięciu przycisku
                        html.Div(
                            children=[
                                dcc.DatePickerSingle(
                                    id='slider-start-date-picker',
                                    date=default_start.strftime('%Y-%m-%d'),
                                    display_format='YYYY-MM-DD',
                                    className='d-none',
                                    with_portal=True,
                                ),
                                dcc.DatePickerSingle(
                                    id='slider-end-date-picker',
                                    date=default_end.strftime('%Y-%m-%d'),
                                    display_format='YYYY-MM-DD',
                                    className='d-none',
                                    with_portal=True,
                                ),
                            ]
                        ),
                    ], id="date-slider-container"),
                
                    # Manual date picker (initially hidden)
                    html.Div(children=[
                        dcc.DatePickerRange(
                            id="backtest-daterange",
                            start_date=default_start.strftime('%Y-%m-%d'),
                            end_date=default_end.strftime('%Y-%m-%d'),
                            start_date_placeholder_text="Start Date",
                            end_date_placeholder_text="End Date",
                            className="w-100"
                        )
                    ], id="manual-date-container", style={"display": "none"})
                ]),
            ], width=8)
        ], className="mb-3 align-items-center"),
        
        # Initial capital input
        dbc.Row(children=[
            dbc.Label("Initial Capital", width=4, className="col-form-label"),
            dbc.Col(children=[
                dbc.Input(
                    id="backtest-capital",
                    type="number",
                    value=10000,
                    min=1,
                    step=1000
                )
            ], width=8)
        ], className="mb-3 align-items-center"),
        
        # Run backtest button
        dbc.Button(
            children=[html.I(className="fas fa-play me-2"), "Run Backtest"],
            id="run-backtest-button",
            color="primary",
            className="w-100 mt-2"
        ),
        
        # Status indicator for the backtest
        html.Div(children=[
            html.Div(id="backtest-status", className="mt-2")
        ])
    ])

def create_strategy_section(available_strategies: Dict[str, Any], available_tickers: List[str] = None) -> dbc.Card:
    """
    Creates the strategy configuration UI section.
    
    Args:
        available_strategies: Dictionary of available trading strategies
        available_tickers: List of available ticker symbols
        
    Returns:
        dbc.Card: A card component containing the strategy selection and configuration UI
    """
    return dbc.Card(children=[
        dbc.CardHeader("Strategy Configuration"),
        dbc.CardBody(children=[
            html.Label("Strategy", className="form-label"),
            get_strategy_dropdown(available_strategies),
            
            # Ticker selection with checklist instead of text input
            create_ticker_checklist(available_tickers),
            
            html.Label("Strategy Parameters", className="form-label"),
            html.Div(id="strategy-parameters"),
            
            # Add backtest parameters section with Run Backtest button
            create_backtest_parameters()
        ])
    ])