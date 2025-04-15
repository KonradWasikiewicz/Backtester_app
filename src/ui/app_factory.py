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

# Import local modules
from src.core.constants import AVAILABLE_STRATEGIES
from src.core.data import DataLoader
from src.ui.callbacks.strategy_callbacks import register_strategy_callbacks
from src.ui.callbacks.backtest_callbacks import register_backtest_callbacks
from src.ui.callbacks.risk_management_callbacks import register_risk_management_callbacks
from src.ui.layouts.strategy_config import create_strategy_config_section
from src.ui.layouts.results_display import create_results_section
from src.ui.layouts.risk_management import create_risk_management_section
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

    # Configure logging
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
    Create an enhanced version display component with popover for additional details.

    Returns:
        html component: The version display component
    """
    version = get_version()
    version_info = get_version_info()

    # Create version changes list for popover
    changelog = get_changelog()
    current_version_log = changelog.get(version, changelog.get(version_info['full'], {}))

    changes_list = []
    if current_version_log:
        changes = current_version_log.get('changes', [])
        for change in changes:
            changes_list.append(html.Li(change))

    # Create version badge with popover
    version_badge = dbc.Button(
        [
            html.Span("v" + version, className="version-badge"),
            html.I(className="fas fa-info-circle ms-1")
        ],
        id="version-badge",
        color="link",
        size="sm",
        className="p-0 text-light text-decoration-none"
    )

    version_popover = dbc.Popover(
        [
            dbc.PopoverHeader(f"Backtester v{version}"),
            dbc.PopoverBody([
                html.P([
                    html.Strong("Release: "),
                    RELEASE_DATE
                ]),
                html.Hr(className="my-2"),
                html.P(
                    html.Strong("What's in this version:"),
                    className="mb-2"
                ),
                html.Ul(
                    changes_list if changes_list else [html.Li("Initial release")],
                    className="ps-3 mb-0"
                ),
                html.Hr(className="my-2"),
                html.Small([
                    html.A("View changelog", href="#", id="view-changelog", className="text-primary"),
                    " | ",
                    html.A("Report issue", href="https://github.com/", target="_blank", className="text-primary")
                ])
            ])
        ],
        target="version-badge",
        trigger="hover",
        placement="bottom",
        className="version-popover"
    )

    return html.Div([version_badge, version_popover])

def create_app_layout() -> html.Div:
    """
    Create the main app layout.

    Returns:
        html.Div: The main app layout
    """
    try:
        logger.info("Creating app layout")

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
                            create_version_display()
                        ], width="auto"),
                        dbc.Col([
                            # Add debug button
                            dbc.Button(
                                html.I(className="fas fa-bug"),
                                id="toggle-debug-btn",
                                color="link",
                                className="p-0 text-light me-3",
                                title="Toggle debug mode"
                            ),
                            html.A(
                                html.I(className="fab fa-github fa-lg"),
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
        logger.info("Registering application callbacks...") # Added log

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

        logger.info("Finished registering application callbacks.") # Added log

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

    Args:
        app: The Dash application instance
    """
    logger.debug("Registering debug callbacks...") # Added log
    from dash.dependencies import Input, Output, State

    # Create necessary layout elements only if they don't exist
    # This check is important if layout modification happens elsewhere too
    debug_container_id = 'debug-container-marker'
    if debug_container_id not in app.layout:
        logger.debug("Adding debug toast container to layout.") # Added log
        # Use a wrapper Div with an ID to check for existence
        debug_elements = html.Div([
            html.Div(id='debug-dummy-output', style={'display': 'none'}), # Keep this? Check if used.
             html.Div(
                dbc.Toast(
                    "JavaScript error logging active. Check server logs for details.", # Updated message
                    id="debug-toast",
                    header="Debug Info", # Simplified header
                    icon="info",
                    is_open=False,
                    dismissable=True,
                    duration=4000,
                    style={"position": "fixed", "top": 10, "right": 10, "zIndex": 9999}
                ),
                id='toast-container'
            )
        ], id=debug_container_id) # Add ID to the wrapper
        # Ensure app.layout is a list or Div children to append
        if isinstance(app.layout, html.Div):
             if hasattr(app.layout, 'children') and isinstance(app.layout.children, list):
                 app.layout.children.append(debug_elements)
             else:
                 # If layout children isn't a list, wrap existing layout
                 app.layout.children = [app.layout.children, debug_elements]
        elif isinstance(app.layout, list):
            app.layout.append(debug_elements)
        else:
             logger.error("Cannot add debug elements: app.layout is not a Div or list.")


    # Simple callback to show notification
    @app.callback(
        Output('debug-toast', 'is_open'),
        [Input('toggle-debug-btn', 'n_clicks')],
        [State('debug-toast', 'is_open')],
         prevent_initial_call=True # Added prevent_initial_call
    )
    def toggle_debug_toast(n_clicks, is_open):
        # n_clicks is None on first load, but prevent_initial_call handles this
        # if n_clicks is None:
        #     return dash.no_update

        # Log the event
        logger.info(f"Debug button clicked ({n_clicks} times). Toggling debug info toast.") # Updated log

        # Toggle toast state
        return not is_open
    logger.debug("Finished registering debug callbacks.") # Added log


def configure_logging(log_level=logging.INFO) -> None:
    """
    Configure logging for the application.

    Args:
        log_level: Logging level to use
    """
    # Check if root logger already has handlers to prevent duplicate setup
    if not logging.getLogger().hasHandlers():
        log_format = '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s' # Added lineno
        date_format = '%Y-%m-%d %H:%M:%S'

        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format=log_format,
            datefmt=date_format,
            handlers=[
                # Use RotatingFileHandler for backtest.log
                logging.handlers.RotatingFileHandler(
                    "backtest.log", maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
                ),
                logging.StreamHandler(sys.stdout) # Keep console output
            ]
        )
        logger.info("Root logger configured.") # Added log
    else:
        logger.debug("Root logger already configured. Skipping setup.") # Added log


    # Set level for specific loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    # Set level for dash components if needed
    # logging.getLogger('dash.dash').setLevel(logging.INFO)
    # logging.getLogger('dash.dependencies').setLevel(logging.INFO)

def get_available_tickers() -> List[str]:
    """
    Get list of available tickers from the data loader.

    Returns:
        List[str]: List of available ticker symbols
    """
    try:
        data_loader = DataLoader()
        tickers = data_loader.get_available_tickers()
        logger.debug(f"Available tickers retrieved: {len(tickers)}") # Added log
        return tickers
    except Exception as e:
        logger.error(f"Error getting available tickers: {e}", exc_info=True) # Log full traceback
        return []
