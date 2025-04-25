import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, no_update
import logging
import os
from pathlib import Path
import sys
from typing import Dict, Any, List
import traceback
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)

# --- Custom Log Filter ---
class DeprecationFilter(logging.Filter):
    """Filter out specific deprecation warnings."""
    def filter(self, record):
        # Check if the message contains the specific deprecation warning text
        if "is deprecated and will change in a future version" in record.getMessage():
            return False  # Do not log this message
        return True # Log other messages

# Import local modules
from src.core.constants import AVAILABLE_STRATEGIES
from src.core.data import DataLoader
from src.ui.callbacks.strategy_callbacks import register_strategy_callbacks
from src.ui.callbacks.backtest_callbacks import register_backtest_callbacks
from src.ui.callbacks.risk_management_callbacks import register_risk_management_callbacks
from src.ui.callbacks.wizard_callbacks import register_wizard_callbacks
from src.ui.layouts.strategy_config import create_strategy_config_section  # Use full wizard layout with all steps
from src.ui.layouts.results_display import create_results_section
from src.version import get_version, get_version_info, RELEASE_DATE, get_changelog  # Import version info

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
            dbc.themes.DARKLY,  # Using dark Bootstrap theme
            "https://use.fontawesome.com/releases/v6.0.0/css/all.css"  # Font Awesome icons
        ],
        suppress_callback_exceptions=suppress_callback_exceptions,
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"}
        ]
    )

    # Add custom CSS for dark mode
    app.index_string = '''
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <style>
                body {
                    background-color: #121212 !important;
                    color: #ffffff !important;
                    min-height: 100vh;
                }

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

                /* --- NEW: Style dbc.Select --- */
                .form-select {
                    background-color: #1e222d !important;
                    color: white !important;
                    border-color: #444 !important;
                }
                /* Style options within dbc.Select */
                .form-select option {
                    background-color: #2a2e39 !important; /* Match dropdown menu */
                    color: white !important;
                }
                /* --- END NEW --- */

                /* Fix for overlapping callbacks error */
                .error-container {
                    background-color: #1e222d !important;
                    color: #ffffff !important;
                    border: 1px solid #2a2e39 !important;
                    padding: 10px;
                    margin: 10px 0;
                    border-radius: 4px;
                }

                /* Version badge styling */
                .version-badge {
                    background-color: #375a7f !important;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 12px;
                    font-weight: 600;
                    color: white !important;
                }

                .version-popover {
                    background-color: #1e222d !important;
                    color: #ffffff !important;
                    border-color: #2a2e39 !important;
                    max-width: 350px;
                }

                /* Additional dark mode styles */
                .nav-link {
                    color: #ffffff !important;
                }

                .nav-link:hover {
                    color: #4d6f94 !important;
                }

                .navbar {
                    background-color: #1e222d !important;
                    border-bottom: 1px solid #2a2e39 !important;
                }

                .dropdown-menu {
                    background-color: #1e222d !important;
                    border-color: #2a2e39 !important;
                }

                .dropdown-item {
                    color: #ffffff !important;
                }

                .dropdown-item:hover {
                    background-color: #2a2e39 !important;
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

    # Configure logging (demoted to debug in detailed steps)
    configure_logging()

    # Create the app layout using the function
    app.layout = create_app_layout()

    # Register all application callbacks
    register_callbacks(app)

    # --- REMOVED the @app.server.route('/log-client-errors', ...) block ---
    # This route is now registered only once in app.py via log_client_errors_endpoint(app)

    return app

def create_version_display():
    """
    Create an enhanced version display component without a popover.

    Returns:
        html component: The version display component
    """
    version = get_version()

    # Create version badge without popover icon
    version_badge = dbc.Button(
        [
            html.Span("v" + version, className="version-badge"),
        ],
        id="version-badge",
        color="link",
        size="sm",
        className="p-0 text-light text-decoration-none"
    )

    return html.Div([version_badge])

def create_app_layout() -> html.Div:
    """
    Create the main app layout.

    Returns:
        html.Div: The main app layout
    """
    try:
        logger.debug("Creating app layout")

        # Get available tickers for the strategy configuration
        available_tickers = get_available_tickers()

        # Create the application layout
        layout = html.Div([
            # Store for app state
            dcc.Store(id="app-state", data={}),

            # --- ADDED: Store to signal backtest completion ---
            dcc.Store(id='backtest-results-store'),

            # Changelog modal
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Backtester Changelog")),
                    dbc.ModalBody(
                        html.Div(id="changelog-content")
                    ),
                    dbc.ModalFooter(
                        dbc.Button("Close", id="close-changelog", className="ms-auto")
                    ),
                ],
                id="changelog-modal",
                size="lg",
                is_open=False,
            ),

            # App header
            dbc.Navbar(
                dbc.Container([
                    dbc.Row(
                        [
                            dbc.Col(
                                html.H3("Trading Strategy Backtester", className="text-center mb-0 text-light"),
                                className="text-center"
                            ),
                        ],
                        className="w-100",
                    ),
                    dbc.Row([

                        dbc.Col([
                            create_version_display(), # Version display
                            # GitHub icon moved here
                            html.A(
                                html.I(className="fab fa-github fa-lg ms-2"), # Added margin-start
                                href="https://github.com/KonradWasikiewicz/Backtester_app", # Updated URL
                                target="_blank",
                                className="text-light text-decoration-none" # Added classes for styling
                            )
                        ], width="auto", className="d-flex align-items-center"), # Use flexbox for alignment
                    ], justify="end") # Justify content to the end (right)
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
                        # Add the backtest status message container here
                        html.Div(id="backtest-status", className="mb-3 text-center"),
                        # Spacer
                        html.Div(className="my-4")
                    ], md=4, className="mb-4"), # Added column width and margin

                    # Right panel: Results display
                    dbc.Col([
                        create_results_section() # Use the function that includes the loader
                    ], md=8)
                ])
            ], fluid=True),

            # Footer
            html.Footer(
                dbc.Container([
                    html.P([
                        "© 2025 Trading Strategy Backtester | ",
                        html.A("Terms", href="#", className="text-light"),
                        " | ",
                        html.A("Privacy", href="#", className="text-light"),
                        " | ",
                        # Add version again in the footer
                        html.Span([
                            "Version: ",
                            html.A(
                                f"v{get_version()}",
                                href="#",
                                id="footer-version",
                                className="text-light fw-bold"
                            )
                        ])
                    ], className="text-center text-muted")
                ], fluid=True),
                className="py-3 mt-5",
                style={"backgroundColor": "#1a1a1a"}
            )
        ])

        logger.debug("App layout created")
        return layout

    except Exception as e:
        logger.error(f"Error creating app layout: {e}", exc_info=True)
        # Return a simple error message layout
        return html.Div([html.H1("Error creating application layout"), html.P(str(e))])

def configure_logging(log_level=logging.INFO) -> None:
    """
    Configures the application's logging.
    Uses console output only, suppresses external library logs,
    and prevents duplicate handler registration.
    """
    # Check if root logger already has handlers to prevent duplicate setup
    root_logger = logging.getLogger()
    if not root_logger.hasHandlers():
        log_format = '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'

        # Configure root logger with console output only
        logging.basicConfig(
            level=log_level,
            format=log_format,
            datefmt=date_format,
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        logger.info(f"Root logger configured with level {logging.getLevelName(log_level)}")

        # Add the custom filter to the root logger
        deprecation_filter = DeprecationFilter()
        root_logger.addFilter(deprecation_filter)
        logger.info("DeprecationFilter added to root logger.")

    else:
        logger.debug("Root logger already has handlers. Skipping basicConfig.")
        # Ensure level is set even if handlers exist
        root_logger.setLevel(log_level)

    # Limit external library logs
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("dash").setLevel(logging.WARNING)
    logging.getLogger("plotly").setLevel(logging.WARNING) # Added plotly
    logger.debug("External library log levels set to WARNING.")

def register_callbacks(app: dash.Dash) -> None:
    """
    Register all application callbacks.

    Args:
        app: The Dash application instance
    """
    logger.debug("Registering callbacks...")
    try:
        register_strategy_callbacks(app)
        register_backtest_callbacks(app)
        register_risk_management_callbacks(app)
        register_wizard_callbacks(app)

        # --- Register Changelog Modal Callbacks ---
        @app.callback(
            Output("changelog-modal", "is_open"),
            [Input("version-badge", "n_clicks"), Input("close-changelog", "n_clicks")],
            [State("changelog-modal", "is_open")],
            prevent_initial_call=True,
        )
        def toggle_changelog_modal(n_badge, n_close, is_open):
            if n_badge or n_close:
                return not is_open
            return is_open

        @app.callback(
            Output("changelog-content", "children"),
            Input("version-badge", "n_clicks"),
            prevent_initial_call=True,
        )
        def load_changelog_content(n_clicks):
            if n_clicks:
                try:
                    changelog_md = get_changelog()
                    # Convert markdown to HTML components
                    return dcc.Markdown(changelog_md, dangerously_allow_html=True)
                except Exception as e:
                    logger.error(f"Error loading changelog: {e}")
                    return html.P(f"Error loading changelog: {e}")
            return no_update

        logger.info("All callbacks registered successfully.")
    except Exception as e:
        logger.error(f"Error during callback registration: {e}", exc_info=True)
        raise # Re-raise the exception to prevent the app from starting incorrectly

def get_available_tickers() -> List[Dict[str, str]]:
    """
    Get a list of available tickers from the data directory.

    Returns:
        List[Dict[str, str]]: List of dictionaries for dropdown options.
    """
    try:
        data_loader = DataLoader()
        tickers = data_loader.get_available_tickers()
        # Format for dbc.Select or dcc.Checklist options
        return [{'label': ticker, 'value': ticker} for ticker in tickers]
    except Exception as e:
        logger.error(f"Error getting available tickers: {e}", exc_info=True)
        return [] # Return empty list on error
