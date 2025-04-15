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
        register_callbacks, # This function should handle all core callback registrations
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

# Configure application logging (will be called again in create_app, but safe due to check)
# Consider configuring logging only *once* before create_app if preferred.
configure_logging()
logger = logging.getLogger(__name__)


try:
    # Create the Dash application
    app = create_app(suppress_callback_exceptions=True) # create_app calls configure_logging and register_callbacks internally

    # Register the single client error logging endpoint
    # This needs to happen after app is created but before app.run
    log_client_errors_endpoint(app)
    logger.info("Registered client error endpoint /log-client-errors")

    # --- REMOVED registration of wizard_callbacks ---
    # This seems to be the source of the duplicate "strategy-description" output
    # and potentially contributing to confusion.
    # try:
    #     from src.ui.callbacks.wizard_callbacks import register_wizard_callbacks
    #     register_wizard_callbacks(app)
    #     logger.info("Registered wizard callbacks") # This line indicated it was being called
    # except ImportError:
    #     logger.warning("Wizard callbacks module not found or failed to import.")
    # except Exception as e_wiz:
    #     logger.error(f"Error registering wizard callbacks: {e_wiz}", exc_info=True)
    logger.info("Skipped registration of wizard_callbacks.")


    # Set the layout (create_app already sets app.layout internally)
    # Re-setting it here is redundant if create_app does it. Let's rely on create_app.
    # app.layout = create_app_layout()
    logger.info("Application layout created by create_app.")


    if __name__ == '__main__':
        # debug=True enables the Dash dev tools (like the error popup)
        app.run(debug=True, dev_tools_hot_reload=False)

except Exception as e:
    logger.critical(f"CRITICAL ERROR initializing application: {e}", exc_info=True)
    print(f"CRITICAL ERROR initializing application: {e}")
    traceback.print_exc()
    sys.exit(1) # Exit if app fails to initialize