import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
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
        app: The Dash application instance
    """
    try:
        logger.debug("Registering application callbacks...") # Demoted log

        # Register wizard navigation and validation callbacks
        register_wizard_callbacks(app)
        logger.debug("Registered wizard callbacks.")
        # Register strategy-related callbacks
        register_strategy_callbacks(app)
        logger.debug("Registered strategy callbacks.") # Added log

        # Register backtest execution and results display callbacks
        register_backtest_callbacks(app)
        logger.debug("Registered backtest callbacks.") # Added log

        # Register risk management callbacks
        register_risk_management_callbacks(app)
        logger.debug("Registered risk management callbacks.") # Added log

        # Register version and changelog callbacks
        register_version_callbacks(app)
        # Removed duplicate log here

        # Register debug mode toggle callback
        register_debug_callbacks(app)
        # Removed duplicate log here

        logger.debug("Finished registering application callbacks.") # Demoted log

    except Exception as e:
        logger.error(f"Error registering callbacks: {e}", exc_info=True)
        print(f"Error registering callbacks: {e}")
        traceback.print_exc()

def register_version_callbacks(app: dash.Dash) -> None:
    """
    Register callbacks for version-related functionality.

    Args:
        app: The Dash application instance
    """
    logger.debug("Registering version callbacks...") # Added log
    from dash.dependencies import Input, Output, State

    # Callback to show changelog modal
    @app.callback(
        Output("changelog-modal", "is_open"),
        [Input("view-changelog", "n_clicks"),
         Input("footer-version", "n_clicks"),
         Input("close-changelog", "n_clicks")],
        [State("changelog-modal", "is_open")],
        prevent_initial_call=True # Added prevent_initial_call
    )
    def toggle_changelog_modal(view_clicks, footer_clicks, close_clicks, is_open):
        ctx = dash.callback_context
        if not ctx.triggered:
            # This should not happen with prevent_initial_call=True, but good practice
            return dash.no_update # Use no_update instead of is_open

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        logger.debug(f"Changelog modal trigger: {trigger_id}") # Added log
        if trigger_id in ["view-changelog", "footer-version"]:
            return True
        elif trigger_id == "close-changelog":
            return False
        return dash.no_update # Default to no update

    # Callback to populate changelog content
    @app.callback(
        Output("changelog-content", "children"),
        [Input("changelog-modal", "is_open")],
         prevent_initial_call=True # Added prevent_initial_call
    )
    def update_changelog(is_open):
        logger.debug(f"Update changelog callback triggered. is_open: {is_open}") # Added log
        if not is_open:
            # Return no_update instead of empty list when not open
            # This prevents unnecessary updates when the modal closes
            return dash.no_update

        try:
            logger.info("Loading and formatting changelog content...") # Added log
            # Get the full changelog
            changelog = get_changelog()

            # Format the changelog for display
            changelog_content = []

            for version, details in sorted(
                changelog.items(),
                key=lambda x: [int(n) for n in x[0].split('.')],
                reverse=True
            ):
                date = details.get('date', '')
                changes = details.get('changes', [])

                version_section = [
                    html.H4(f"v{version}", className="mt-3"),
                    html.P(f"Released: {date}", className="text-muted"),
                    html.Ul([
                        html.Li(change) for change in changes
                    ]) if changes else html.P("No changes documented.")
                ]

                changelog_content.extend(version_section)

            if not changelog_content:
                logger.warning("No changelog content generated.") # Added log
                return html.P("No changelog information available.")

            logger.info("Changelog content generated successfully.") # Added log
            return changelog_content
        except Exception as e:
            logger.error(f"Error generating changelog: {e}", exc_info=True)
            return html.P(f"Error loading changelog: {str(e)}")
    logger.debug("Finished registering version callbacks.") # Added log

def register_debug_callbacks(app: dash.Dash) -> None:
    """
    Register callbacks for debug functionality.
    Simple implementation that just toggles a debug toast notification.

    Args:
        app: The Dash application instance
    """
    logger.debug("Registering debug callbacks...")
    from dash.dependencies import Input, Output, State

    # Create a simple toast for debug info
    debug_elements = html.Div(
        dbc.Toast(
            "Debug mode active",
            id="debug-toast",
            header="Debug Info",
            icon="info",
            is_open=False,
            dismissable=True,
            duration=3000,
            style={"position": "fixed", "top": 10, "right": 10, "zIndex": 9999}
        ),
        id='debug-container-marker'
    )
    
    # Add debug elements to layout if not already present
    if 'debug-container-marker' not in app.layout:
        if isinstance(app.layout, html.Div) and isinstance(app.layout.children, list):
            app.layout.children.append(debug_elements)
        else:
            logger.debug("Could not add debug elements to layout")

    # Simple callback to show notification
    @app.callback(
        Output('debug-toast', 'is_open'),
        [Input('toggle-debug-btn', 'n_clicks')],
        [State('debug-toast', 'is_open')],
        prevent_initial_call=True
    )
    def toggle_debug_toast(n_clicks, is_open):
        logger.info(f"Debug button clicked. Toggling debug info toast.")
        return not is_open

def configure_logging(log_level=logging.INFO) -> None:
    """
    Configure logging for the application.

    Args:
        log_level: Logging level to use
    """
    # Check if root logger already has handlers to prevent duplicate setup
    root_logger = logging.getLogger()
    if not root_logger.hasHandlers():
        log_format = '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'

        # Configure root logger - simplified system with single handler
        logging.basicConfig(
            level=log_level,
            format=log_format,
            datefmt=date_format,
            handlers=[
                logging.StreamHandler(sys.stdout) # Console output only
            ]
        )
        logger.info("Logger configured")

        # Add the custom filter to the handlers
        deprecation_filter = DeprecationFilter()
        for handler in root_logger.handlers:
            handler.addFilter(deprecation_filter)
            logger.debug(f"Added DeprecationFilter to handler {handler}")

    else:
        logger.debug("Logger already configured")
        # Ensure filter is added even if logger was configured elsewhere (e.g., by another module)
        deprecation_filter = DeprecationFilter()
        filter_exists = any(isinstance(f, DeprecationFilter) for h in root_logger.handlers for f in h.filters)
        if not filter_exists:
            for handler in root_logger.handlers:
                handler.addFilter(deprecation_filter)
                logger.debug(f"Added DeprecationFilter to existing handler {handler}")

    # Set logging level for external libraries
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("dash").setLevel(logging.WARNING) # Added: limit Dash logs

def get_available_tickers() -> List[str]:
    """
    Get list of available tickers from the data loader.

    Returns:
        List[str]: List of available ticker symbols
    """
    try:
        data_loader = DataLoader()
        # Ensure data is loaded before getting tickers
        # data_loader.load_data() # Assuming load_data is called elsewhere or implicitly
        tickers = data_loader.get_available_tickers()
        logger.debug(f"Available tickers retrieved: {len(tickers)}") # Added log
        if not tickers:
             logger.warning("No available tickers found. Check data source.")
        return tickers
    except Exception as e:
        logger.error(f"Error getting available tickers: {e}", exc_info=True) # Log full traceback
        return []
