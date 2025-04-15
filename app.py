import sys
import logging
import traceback
from pathlib import Path
import os

# Ensure src is in the path
APP_ROOT = Path(__file__).resolve().parent
sys.path.append(str(APP_ROOT))

# Import factory functions and Dash components
try:
    from src.ui.app_factory import (
        create_app,
        # Logging configuration is handled within create_app
    )
except ImportError as e:
    # Use basic print for critical import errors as logging might not be set up
    print(f"CRITICAL: Error importing core modules: {e}")
    traceback.print_exc()
    sys.exit(1) # Exit if essential imports fail

# Basic logging configuration for the main application entry point
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.info("--- Application Start ---")


try:
    # Create the Dash application using the factory function
    # create_app is responsible for:
    # 1. Instantiating Dash
    # 2. Configuring logging (via configure_logging)
    # 3. Setting the layout (via create_app_layout)
    # 4. Registering all necessary callbacks (via register_callbacks)
    logger.info("Creating Dash application via create_app...")
    app = create_app(suppress_callback_exceptions=True) 
    logger.info("Dash application created successfully.")

    # Callback registration is handled within create_app
    # Layout is set within create_app

    # --- Run Server ---
    if __name__ == '__main__':
        logger.info("Starting Dash development server...")
        # debug=True enables Dash Dev Tools (error reporting, callback graph)
        # dev_tools_hot_reload=False prevents automatic browser refresh on code changes
        app.run(debug=True, dev_tools_hot_reload=False)

except Exception as e:
    # Catch any exceptions during the app setup process
    logger.critical(f"CRITICAL ERROR during application initialization: {e}", exc_info=True)
    # Print to stderr as a fallback if logging somehow failed
    print(f"CRITICAL ERROR initializing application: {e}", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1) # Exit with error code