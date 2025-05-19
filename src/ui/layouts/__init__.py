# Package init file that provides unified access to layout functions

from dash import html, dcc
import dash_bootstrap_components as dbc
from typing import List, Dict

# Import layout components from various modules
from src.ui.wizard.layout import create_strategy_config_section # Wizard layout
# from src.ui.layouts.strategy_config import create_strategy_config_layout # Placeholder, if needed elsewhere
# from src.ui.layouts.risk_management import create_risk_management_layout # Placeholder
from src.ui.layouts.results_display import create_main_results_area as create_results_display_layout # For the right panel, aliased for consistency

from src.ui.ids import PageIDs, ComponentIDs, WizardIDs, ResultsIDs # Import necessary IDs

def create_layout(tickers: List[Dict[str, str]] = None) -> html.Div:
    """
    Main layout factory function that combines various components
    to create the application's three-panel layout.

    Args:
        tickers: List of stock tickers available in the application

    Returns:
        A Dash layout object
    """
    print("--- layouts/__init__.py: create_layout CALLED (Restored Version) ---")

    if tickers is None:
        tickers = []

    return html.Div(
        id=PageIDs.MAIN_CONTAINER,
        children=[
            dcc.Store(id=WizardIDs.ACTIVE_STEP_STORE), # Store for wizard state (CHANGED from WIZARD_STATE_STORE)
            dcc.Store(id=ComponentIDs.BACKTEST_RESULTS_STORE), # Store for backtest results
            dcc.Store(id=ComponentIDs.HISTORICAL_DATA_STORE), # Store for historical price data
            dcc.Store(id=ComponentIDs.STRATEGY_PARAMS_STORE), # Store for strategy parameters
            dcc.Store(id=ComponentIDs.RISK_PARAMS_STORE), # Store for risk parameters
            dcc.Store(id=ComponentIDs.TRADING_COSTS_STORE), # Store for trading costs
            dcc.Store(id=ComponentIDs.REBALANCING_RULES_STORE), # Store for rebalancing rules
            dcc.Store(id=ComponentIDs.SELECTED_TICKERS_STORE), # Store for selected tickers
            dcc.Store(id=ComponentIDs.DATE_RANGE_STORE), # Store for selected date range
            dcc.Store(id=ComponentIDs.INITIAL_CAPITAL_STORE), # Store for initial capital

            # Header
            dbc.Navbar(
                dbc.Container(
                    [
                        dbc.NavbarBrand("Advanced Backtester App", href="/", className="ms-2", style={'fontSize': '1.5rem', 'fontWeight': 'bold'}),
                        # Add any other navbar components here if needed
                    ],
                    fluid=True, # Use fluid container for full width
                ),
                color="dark", # Dark theme for navbar
                dark=True,
                sticky="top", # Make navbar sticky
                className="mb-0 p-2", # Reduced bottom margin and padding
            ),

            # Main Content Area with Three Panels
            dbc.Container(
                [
                    dbc.Row(
                        [                            # Left Panel: Strategy Configuration Wizard
                            dbc.Col(
                                create_strategy_config_section(tickers=tickers),
                                id=ResultsIDs.LEFT_PANEL_COLUMN, # Using centralized ID from ResultsIDs
                                width=12, lg=4, # Full width on small screens, 1/3 on large
                                className="mb-3 mb-lg-0", # Margin bottom on small screens
                                style={'paddingTop': '0.5rem'} # Reduced top padding
                            ),# Center Panel: Data Visualization / Charts
                            dbc.Col(
                                [
                                    html.Div(id=ComponentIDs.CHART_CONTAINER_MAIN, children=[
                                        html.H4("Price Chart", className="text-center mb-2"),
                                        dcc.Graph(id=ComponentIDs.PRICE_CHART, style={'height': '350px'}), # Reduced height
                                        html.H4("Performance Metrics", className="text-center mt-3 mb-2"),
                                        dcc.Graph(id=ComponentIDs.PERFORMANCE_CHART, style={'height': '300px'}) # Reduced height
                                    ])
                                ],
                                id=ResultsIDs.CENTER_PANEL_COLUMN, # Using centralized ID from ResultsIDs
                                width=12, lg=5, # Full width on small screens, 5/12 on large
                                className="mb-3 mb-lg-0",
                                style={'paddingTop': '0.5rem'} # Reduced top padding
                            ),                            # Right Panel: Backtest Results and Logs
                            dbc.Col(
                                create_results_display_layout(), # Use the dedicated layout function
                                id=ResultsIDs.RIGHT_PANEL_COLUMN, # Using centralized ID from ResultsIDs
                                width=12, lg=3, # Full width on small screens, 1/4 on large
                                style={'paddingTop': '0.5rem'} # Reduced top padding
                            ),
                        ],
                        className="g-2", # Reduced gutter between columns
                        align="start" # Align items to the start (top)
                    )
                ],
                fluid=True, # Use fluid container for full width content
                className="p-2", # Reduced padding for the main content container
                style={'backgroundColor': '#121212'} # Match body background
            ),

            # Footer (Optional, can be removed or styled)
            html.Footer(
                dbc.Container(
                    html.P("Backtester App - © 2025 - Advanced Version", className="text-center text-muted small"),
                    fluid=True
                ),
                className="mt-auto py-2 bg-dark text-light", # Ensure footer is at the bottom, dark theme
                style={'fontSize': '0.8rem'}
            )
        ],
        style={'minHeight': '100vh', 'display': 'flex', 'flexDirection': 'column', 'backgroundColor': '#121212'}
    )

print("--- layouts/__init__.py: MODULE LOADED (Restored Version) ---")
