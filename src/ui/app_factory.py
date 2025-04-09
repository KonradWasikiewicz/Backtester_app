import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
import logging
import os
from pathlib import Path
import sys
from typing import Dict, Any, List
import traceback

# Configure logging
logger = logging.getLogger(__name__)

# Import local modules
from src.core.constants import AVAILABLE_STRATEGIES
from src.core.data import DataLoader
from src.ui.callbacks.strategy_callbacks import register_strategy_callbacks
from src.ui.callbacks.backtest_callbacks import register_backtest_callbacks
from src.ui.callbacks.risk_management_callbacks import register_risk_management_callbacks
from src.ui.layouts.strategy_config import create_strategy_config_section
from src.ui.layouts.results_display import create_results_section
from src.ui.layouts.risk_management import create_risk_management_section

def create_app(debug: bool = False, suppress_callback_exceptions: bool = True) -> dash.Dash:
    """
    Creates and configures the Dash application.
    
    Args:
        debug: Whether to run the app in debug mode
        suppress_callback_exceptions: Whether to suppress callback exceptions
        
    Returns:
        dash.Dash: Configured Dash application instance
    """
    # Initialize the Dash app with Bootstrap components
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            dbc.themes.DARKLY,  # Using Darkly for dark theme
            "https://use.fontawesome.com/releases/v6.0.0/css/all.css"  # Font Awesome icons
        ],
        suppress_callback_exceptions=suppress_callback_exceptions,
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"}
        ]
    )
    
    # Add custom CSS for datepickers in dark mode
    app.index_string = '''
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <style>
                /* Custom styles for date pickers */
                .DateInput_input {
                    background-color: #1e222d !important;
                    color: #ffffff !important;
                    border-radius: 4px !important;
                    border: 1px solid #444 !important;
                    font-size: 14px !important;
                }
                
                .CalendarMonth_caption {
                    color: #ffffff !important;
                }
                
                .DayPicker_weekHeader {
                    color: #ffffff !important;
                }
                
                .CalendarDay__default {
                    background-color: #2a2e39 !important;
                    border-color: #444 !important;
                    color: #ffffff !important;
                }
                
                .CalendarDay__selected, 
                .CalendarDay__selected:hover {
                    background-color: #375a7f !important;
                    border-color: #375a7f !important;
                    color: white !important;
                }
                
                .CalendarDay__hovered_span,
                .CalendarDay__selected_span {
                    background-color: #4d6f94 !important;
                    color: white !important;
                }
                
                .DayPickerNavigation_button {
                    background-color: #1e222d !important;
                    border-color: #444 !important;
                }
                
                .DayPickerNavigation_svg {
                    fill: #ffffff !important;
                }
                
                .DateRangePicker, .SingleDatePicker {
                    background-color: transparent !important;
                }
                
                .DateRangePickerInput, .SingleDatePickerInput {
                    background-color: #1e222d !important;
                    border-color: #444 !important;
                }
                
                .DayPicker {
                    background-color: #2a2e39 !important;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5) !important;
                }
                
                /* Additional styles for complete dark mode */
                .CalendarMonth, .CalendarMonthGrid {
                    background-color: #2a2e39 !important;
                }
                
                .DayPicker_weekHeaders {
                    background-color: #2a2e39 !important;
                }
                
                .CalendarDay__blocked_out_of_range {
                    color: #666 !important;
                    background-color: #222 !important;
                }
                
                .DateInput, .DateInput_1 {
                    background-color: transparent !important;
                }
                
                .DateRangePickerInput_arrow {
                    color: white !important;
                }
                
                /* Fix select dropdown styling */
                .Select-control, .Select.is-focused>.Select-control {
                    background-color: #1e222d !important;
                    color: white !important;
                    border-color: #444 !important;
                }
                
                .Select-menu-outer {
                    background-color: #2a2e39 !important;
                    color: white !important;
                    border-color: #444 !important;
                }
                
                .Select-option {
                    background-color: #2a2e39 !important;
                    color: white !important;
                }
                
                .Select-option.is-focused {
                    background-color: #375a7f !important;
                }
                
                .Select-value-label {
                    color: white !important;
                }
                
                .has-value.Select--single>.Select-control .Select-value .Select-value-label {
                    color: white !important;
                }
                
                .Select-placeholder, .Select--single>.Select-control .Select-value {
                    color: #ccc !important;
                }
                
                /* Fix for overlapping callbacks error */
                .error-container {
                    display: none !important;
                }
            </style>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    '''
    
    # Set app title
    app.title = "Financial Backtester"
    
    # Configure logging
    configure_logging()
    
    # Get available tickers
    available_tickers = get_available_tickers()
    
    # Create the app layout
    app.layout = dbc.Container([
        # App title
        html.H1("Backtester", className="text-center mb-4 text-light"),
        
        # Main content row
        dbc.Row([
            # Left column - Configuration sections
            dbc.Col([
                # Strategy Configuration
                create_strategy_config_section(available_tickers),
                html.Div(className="mb-3"),  # Spacer
                # Risk Management
                create_risk_management_section(available_tickers)
            ], width=3, className="pe-3"),
            
            # Right column - Results
            dbc.Col([
                create_results_section()
            ], width=9)
        ], className="g-0"),
        
        # Store components
        dcc.Store(id='strategy-store'),
        dcc.Store(id='risk-management-store'),
        dcc.Store(id='results-store')
    ], fluid=True, className="py-4")
    
    # Register callbacks
    register_callbacks(app)
    
    return app

def create_app_layout() -> html.Div:
    """
    Create the main application layout structure.
    
    Returns:
        html.Div: The main application layout
    """
    try:
        logger.info("Creating application layout")
        
        # Load available tickers from the data loader
        try:
            data_loader = DataLoader()
            available_tickers = data_loader.get_available_tickers()
            logger.info(f"Loaded {len(available_tickers)} available tickers")
        except Exception as e:
            logger.error(f"Error loading available tickers: {e}")
            available_tickers = []
        
        # UWAGA: Ta funkcja nie jest faktycznie używana w aplikacji
        # Główny layout jest definiowany bezpośrednio w create_app
        layout = html.Div([
            # Navbar
            dbc.Navbar(
                dbc.Container([
                    dbc.Row([
                        dbc.Col([
                            html.I(className="fas fa-chart-line me-2"),
                            html.Span("Trading Strategy Backtester", className="ms-2 fw-bold")
                        ], width="auto"),
                    ], align="center", className="flex-grow-1"),
                    dbc.Row([
                        dbc.Col([
                            html.A(
                                dbc.Button([
                                    html.I(className="fab fa-github me-1"),
                                    "GitHub"
                                ], color="light", outline=True, size="sm"),
                                href="https://github.com/",
                                target="_blank"
                            )
                        ], width="auto")
                    ])
                ], fluid=True),
                color="dark",
                dark=True,
                className="mb-4"
            ),
            
            # Main content
            dbc.Container([
                dbc.Row([
                    # Left panel: Strategy configuration
                    dbc.Col([
                        create_strategy_config_section(available_tickers),
                        # Spacer
                        html.Div(className="my-4")
                        # Risk management section jest już zdefiniowany w create_app
                    ], md=4, lg=3),
                    
                    # Right panel: Results display
                    dbc.Col([
                        create_results_section()
                    ], md=8, lg=9)
                ])
            ], fluid=True),
            
            # Footer
            html.Footer(
                dbc.Container([
                    html.P([
                        "© 2024 Trading Strategy Backtester | ",
                        html.A("Terms", href="#", className="text-light"),
                        " | ",
                        html.A("Privacy", href="#", className="text-light")
                    ], className="text-center text-muted")
                ], fluid=True),
                className="py-3 mt-5",
                style={"backgroundColor": "#1a1a1a"}
            )
        ])
        
        return layout
    
    except Exception as e:
        logger.error(f"Error creating app layout: {e}", exc_info=True)
        return html.Div([
            html.H3("Error initializing application layout", className="text-danger"),
            html.P(f"Details: {str(e)}")
        ])

def register_callbacks(app: dash.Dash) -> None:
    """
    Register all application callbacks.
    
    Args:
        app: The Dash application
    """
    try:
        logger.info("Registering application callbacks")
        
        # Register strategy-related callbacks
        register_strategy_callbacks(app)
        
        # Register backtest execution and results display callbacks
        register_backtest_callbacks(app)
        
        # Register risk management callbacks
        register_risk_management_callbacks(app)
        
    except Exception as e:
        logger.error(f"Error registering callbacks: {e}", exc_info=True)
        print(f"Error registering callbacks: {e}")
        traceback.print_exc()

def configure_logging(log_level=logging.INFO) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level to use
    """
    log_format = '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler("backtest.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set level for some verbose libraries
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

def get_available_tickers() -> List[str]:
    """
    Get list of available tickers from the data loader.
    
    Returns:
        List[str]: List of available ticker symbols
    """
    try:
        data_loader = DataLoader()
        return data_loader.get_available_tickers()
    except Exception as e:
        logger.error(f"Error getting available tickers: {e}")
        return []