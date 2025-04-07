import dash_bootstrap_components as dbc
import inspect
from dash import html, dcc
import logging
import traceback
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger(__name__)

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
    if not strategy_class:
        return html.P("Select a strategy.", className="text-muted")
    
    try:
        sig = inspect.signature(strategy_class.__init__)
        params_inputs = []
        
        for name, param in sig.parameters.items():
            # Skip self, tickers, *args, **kwargs parameters
            if name in ['self', 'tickers', 'args', 'kwargs']: 
                continue
                
            default_value = param.default if param.default is not inspect.Parameter.empty else None
            input_type, step, placeholder = 'text', 'any', str(default_value) if default_value is not None else "Required"
            required = default_value is None
            
            annotation = param.annotation
            target_type = type(default_value) if default_value is not None else (
                annotation if annotation != inspect.Parameter.empty else str)

            if target_type == bool:
                # Boolean checkbox for boolean parameters
                params_inputs.append(dbc.Row([
                    dbc.Label(name.replace('_', ' ').title(), width=6, className="small"),
                    dbc.Col(dbc.Checkbox(
                        id={'type': 'strategy-param', 'index': name}, 
                        value=bool(default_value)
                    ), width=6)
                ], className="mb-2 align-items-center"))
                continue
            
            elif target_type == int: 
                # Integer input
                input_type, step = 'number', 1
                
            elif target_type == float:
                # Float input with appropriate step size
                input_type = 'number'
                step = 0.1 if abs(default_value or 0.0) < 10 else (
                    1 if abs(default_value or 0.0) < 100 else 10)

            # General text/number input
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

        if not params_inputs:
            return html.P("This strategy has no configurable parameters.", className="text-muted")
            
        return html.Div(params_inputs)
        
    except Exception as e:
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
    
    return html.Div([
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
    return html.Div([
        html.Hr(className="my-3"),
        html.H5("Backtest Parameters", className="mb-3"),
        
        # Date Range input
        dbc.Row([
            dbc.Label("Date Range", width=4, className="col-form-label"),
            dbc.Col([
                dcc.DatePickerRange(
                    id="backtest-daterange",
                    start_date_placeholder_text="Start Date",
                    end_date_placeholder_text="End Date",
                    className="w-100"
                )
            ], width=8)
        ], className="mb-3 align-items-center"),
        
        # Initial capital input
        dbc.Row([
            dbc.Label("Initial Capital", width=4, className="col-form-label"),
            dbc.Col([
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
            [html.I(className="fas fa-play me-2"), "Run Backtest"],
            id="run-backtest-button",  # Zmieniono id z "run-backtest" na "run-backtest-button"
            color="primary",
            className="w-100 mt-2"
        ),
        
        # Status indicator for the backtest
        html.Div([
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
    return dbc.Card([
        dbc.CardHeader("Strategy Configuration"),
        dbc.CardBody([
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