import sys
import logging
import traceback
from pathlib import Path
import os
import re

# Ensure src is in the path
APP_ROOT = Path(__file__).resolve().parent
sys.path.append(str(APP_ROOT))

# Import factory functions
try:
    from src.ui.app_factory import (
        create_app,
        configure_logging,
        create_app_layout,
        register_callbacks,
        # Removed register_version_callbacks, register_debug_callbacks as they are called within register_callbacks
    )
    from dash import html, dcc
    # Import the server-side logger endpoint function
    from server_logger import initialize_logger, log_client_errors_endpoint
except ImportError as e:
    print(f"Error importing modules: {e}")
    traceback.print_exc()
    sys.exit(1)

# Initialize the enhanced logging system
logging_result = initialize_logger()
if logging_result["status"] == "error":
    print(f"Failed to initialize logging: {logging_result['message']}")
    sys.exit(1)

# Configure application logging
configure_logging()
logger = logging.getLogger(__name__)

# --- Removed apply_format_patches and scan_for_format_issues ---
# These functions seemed experimental or potentially unused.
# If they are necessary, they can be added back, but let's simplify first.
# def apply_format_patches(): ...
# def scan_for_format_issues(): ...

try:
    # Create the Dash application
    # suppress_callback_exceptions=True can hide underlying issues.
    # Consider setting to False during debugging if problems persist after fixing duplicates.
    app = create_app(suppress_callback_exceptions=True)

    # Register the single client error logging endpoint
    # This MUST be called before register_callbacks if clientside.js uses it immediately.
    log_client_errors_endpoint(app)
    logger.info("Registered client error endpoint /log-client-errors")

    # Register all application callbacks (includes strategy, backtest, risk, version, debug)
    register_callbacks(app)
    logger.info("Registered core application callbacks")

    # Register wizard callbacks (if still used, called separately)
    # Check if src.ui.callbacks.wizard_callbacks is still relevant.
    try:
        from src.ui.callbacks.wizard_callbacks import register_wizard_callbacks
        register_wizard_callbacks(app)
        logger.info("Registered wizard callbacks")
    except ImportError:
        logger.warning("Wizard callbacks module not found or failed to import.")
    except Exception as e_wiz:
        logger.error(f"Error registering wizard callbacks: {e_wiz}", exc_info=True)


    # Get the original layout
    original_layout = create_app_layout()

    # Add error logging components to the original layout
    # These seem related to a different error handling mechanism, might be removable later.
    app.layout = html.Div([
        # Error logging components (Consider removing if assets/clientside.js handles everything)
        # html.Div([
        #     dcc.Store(id='error-store', storage_type='local'),
        #     html.Div(id='error-notifier', style={'display': 'none'}),
        # ]),

        # Original layout
        original_layout
    ])
    logger.info("Application layout created")

    # --- Removed configure_client_side_logging() and add_browser_storage_reader(app) calls ---
    # Relying on assets/clientside.js for client-side logging

    if __name__ == '__main__':
        # debug=True enables the Dash dev tools (like the error popup)
        # dev_tools_hot_reload=False is often recommended for stability
        app.run(debug=True, dev_tools_hot_reload=False)

except Exception as e:
    logger.critical(f"CRITICAL ERROR initializing application: {e}", exc_info=True)
    print(f"CRITICAL ERROR initializing application: {e}")
    traceback.print_exc()
    sys.exit(1) # Exit if app fails to initialize
