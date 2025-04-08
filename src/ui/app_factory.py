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
from src.ui.layouts.strategy_config import create_strategy_config_section
from src.ui.layouts.results_display import create_results_section
from src.ui.layouts.risk_management import create_risk_management_section

def create_app(debug: bool = False) -> dash.Dash:
    """
    Creates and configures the Dash application.
    
    Args:
        debug: Whether to run the app in debug mode
        
    Returns:
        dash.Dash: Configured Dash application instance
    """
    # Initialize the Dash app with Bootstrap components
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.DARKLY],
        suppress_callback_exceptions=True,
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"}
        ]
    )
    
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
        
        # Create risk management section first to ensure it's initialized
        risk_management = create_risk_management_section()
        
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
                        create_strategy_section(AVAILABLE_STRATEGIES, available_tickers),
                        html.Div(className="my-4"),  # Add spacing
                        risk_management  # Use the pre-created risk management section
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