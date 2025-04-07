import dash_bootstrap_components as dbc
import inspect
from dash import html, dcc
import logging
import traceback
from typing import Dict, Any

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

def create_strategy_section(available_strategies: Dict[str, Any]) -> dbc.Card:
    """
    Creates the complete strategy selection and configuration section.
    
    Args:
        available_strategies: Dictionary of strategy names and their classes
        
    Returns:
        dbc.Card: A card component containing strategy selection and configuration
    """
    return dbc.Card([
        dbc.CardHeader("Configuration"),
        dbc.CardBody([
            html.H6("Select Strategy", className="mb-2"),
            get_strategy_dropdown(available_strategies),
            
            html.H6("Strategy Parameters", className="mt-3 mb-2"),
            html.Div(
                id="strategy-parameters-container", 
                className="mb-3 border rounded p-2 bg-secondary", 
                style={'minHeight': '80px'}
            ),
            
            html.H6("Tickers & Risk Management", className="mt-3 mb-2"),
            html.Div(id="risk-management-container")
        ])
    ], className="mb-4")