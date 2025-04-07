import sys
import logging
import traceback
from pathlib import Path

# Ensure src is in the path
APP_ROOT = Path(__file__).resolve().parent
sys.path.append(str(APP_ROOT))

# Import factory functions
try:
    from src.ui.app_factory import create_app, configure_logging
except ImportError as e:
    print(f"Error importing modules: {e}")
    traceback.print_exc()
    sys.exit(1)

# Configure application logging
configure_logging()
logger = logging.getLogger(__name__)

# Create the Dash application
try:
    logger.info("Initializing Backtester application")
    app = create_app(debug=True)
    
    # Application entry point
    if __name__ == "__main__":
        logger.info("Starting Backtester application")
        app.run_server(debug=True, port=8050)
except Exception as e:
    logger.error(f"Failed to initialize application: {e}", exc_info=True)
    print(f"ERROR: Failed to initialize application: {e}")
    traceback.print_exc()
