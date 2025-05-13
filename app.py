import sys
import logging
import traceback
from pathlib import Path
import os
import pandas as pd
from flask import request, jsonify

# --- Set Pandas Option for Future Behavior ---
# pd.set_option('future.no_silent_downcasting', True) # Removed: Option not available in pandas 1.5.3
# --- End Set Option ---

# Ensure src is in the path
APP_ROOT = Path(__file__).resolve().parent
ASSETS_DIR = APP_ROOT / "assets" # Define assets directory path
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
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s') # Changed level to DEBUG
logger = logging.getLogger(__name__)
# Only log application start once, after the reloader has initialized main process
if __name__ == '__main__' and os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    logger.info("--- Application Start ---")


try:
    # Create the Dash application using the factory function
    # create_app is responsible for:
    # 1. Instantiating Dash
    # 2. Configuring logging (via configure_logging)
    # 3. Setting the layout (via create_app_layout)
    # 4. Registering all necessary callbacks (via register_callbacks)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        logger.info("Creating Dash application via create_app...")
    # Pass ASSETS_DIR to create_app
    app = create_app(suppress_callback_exceptions=True, assets_dir=str(ASSETS_DIR))
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        logger.info("Dash application created successfully.")

    # --- Explicitly Configure Flask Static Files ---
    # This might be redundant now, but let's keep it for safety
    app.server.static_folder = str(ASSETS_DIR)
    app.server.static_url_path = '/assets'
    logger.info(f"Flask static_folder explicitly set to: {app.server.static_folder}")
    logger.info(f"Flask static_url_path explicitly set to: {app.server.static_url_path}")
    # --- End Explicit Configuration ---


    # --- Endpoint for Client-Side Errors ---
    @app.server.route('/log-client-errors', methods=['POST'])
    def log_client_errors():
        """Logs errors/warnings received from the client-side JavaScript."""
        data = request.get_json()
        if not data:
            logger.warning("Received empty request to /log-client-errors")
            return jsonify(status="bad request"), 400

        errors = data.get('errors', [])
        warnings = data.get('warnings', [])
        logs = data.get('logs', []) # Optional: capture console.log if needed

        log_prefix = "[Client-Side]"
        if errors:
            for error in errors:
                logger.error(f"{log_prefix} Error: {error}")
        if warnings:
            for warning in warnings:
                logger.warning(f"{log_prefix} Warning: {warning}")
        if logs:
            for log_msg in logs:
                logger.info(f"{log_prefix} Log: {log_msg}") # Log client logs as info

        return jsonify(status="received"), 200
    # --- END Endpoint ---

    # --- NEW: Log confirmation of endpoint registration ---
    # This log will appear when the app starts IF the route is successfully registered.
    logger.info("Successfully registered /log-client-errors endpoint")
    # --- END NEW Log ---


    # --- Run Server ---
    if __name__ == '__main__':
        # Only log server start in the reloaded process, not in the initial checker process
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            logger.info("Starting Dash server (Debug Mode ON, Explicit Assets Path)...")  # Fixed: Debug Mode ON
        else:
            # Silence logs in the initial process - using correct logger name for Werkzeug
            logging.getLogger('werkzeug').setLevel(logging.ERROR)
            # Also silence other loggers during initial load
            logging.getLogger('dash').setLevel(logging.ERROR)
            logging.getLogger('flask').setLevel(logging.ERROR)
        
        # Keep debug=True
        app.run(debug=True,
                use_reloader=True)

except Exception as e:
    # Catch any exceptions during the app setup process
    logger.critical(f"CRITICAL ERROR during application initialization: {e}", exc_info=True)
    # Print to stderr as a fallback if logging somehow failed
    print(f"CRITICAL ERROR initializing application: {e}", file=sys.stderr)
    traceback.print_exc()
    logging.shutdown() # Ensure all log messages are flushed
    sys.exit(1) # Exit with error code  