from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import logging
from typing import List, Dict, Any
import os
import sys

# Ensure src directory is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import the main layout factory
print("--- app_factory.py: Attempting to import create_layout from src.ui.layouts ---")
try:
    from src.ui.layouts import create_layout
    print("--- app_factory.py: Successfully imported create_layout from src.ui.layouts ---")
except ImportError as e:
    print(f"--- app_factory.py: FAILED to import create_layout from src.ui.layouts: {e} ---")
    # If this fails, define a placeholder to allow the rest of the script to be parsed
    def create_layout(*args, **kwargs):
        print("--- app_factory.py: USING PLACEHOLDER create_layout ---")
        return html.Div("Error: Main layout could not be loaded.")

# Comment out other callback imports for now to isolate the issue
# from src.ui.callbacks.wizard_callbacks import register_wizard_callbacks
# ... other callback imports

print("--- app_factory.py: EXECUTING MODULE ---")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_available_tickers() -> List[Dict[str, str]]:
    """
    Get a list of available tickers.
    Placeholder function.
    """
    print("--- app_factory.py: get_available_tickers CALLED (placeholder) ---")
    return [{'label': 'AAPL', 'value': 'AAPL'}, {'label': 'MSFT', 'value': 'MSFT'}]

def create_app(**kwargs: Any) -> Dash: # Added **kwargs to match app.py call
    print("--- app_factory.py: create_app CALLED ---")
    try:
        app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
        
        # Call create_layout - it might need tickers
        try:
            tickers = get_available_tickers()
            app.layout = create_layout(tickers=tickers) # Pass tickers if needed by your actual create_layout
            print("--- app_factory.py: app.layout ASSIGNED ---")
        except Exception as e_layout:
            print(f"--- app_factory.py: ERROR calling create_layout or assigning to app.layout: {e_layout} ---")
            logger.error(f"Error in create_layout: {e_layout}", exc_info=True)
            app.layout = html.Div(f"Layout Error: {e_layout}") # Display error in UI

        register_callbacks(app)
        print("--- app_factory.py: create_app RETURNING ---")
        return app
    except Exception as e_create_app:
        print(f"--- app_factory.py: CRITICAL ERROR in create_app: {e_create_app} ---")
        logger.error(f"Critical error during app creation: {e_create_app}", exc_info=True)
        # Fallback app if creation fails catastrophically
        app = Dash(__name__)
        app.layout = html.Div([
            html.H1("Application Initialization Failed"),
            html.P(f"Error: {e_create_app}")
        ])
        return app

def register_callbacks(app: Dash) -> None:
    print("--- app_factory.py: register_callbacks CALLED ---")
    try:
        # Import and register all callbacks
        # We import them all from the callbacks package to ensure proper dependency resolution
        from src.ui.callbacks import register_wizard_callbacks, register_backtest_callbacks, register_run_backtest_callback
        
        # Register wizard callbacks first (UI interaction)
        print("--- app_factory.py: Registering wizard callbacks ---")
        register_wizard_callbacks(app)
        print("--- app_factory.py: Wizard callbacks registered ---")
        
        # Register backtest callbacks next (backtest execution)
        print("--- app_factory.py: Registering backtest callbacks ---")
        register_backtest_callbacks(app)
        print("--- app_factory.py: Backtest callbacks registered ---")
        
        # Register run backtest callback last (validation before running backtest)
        print("--- app_factory.py: Registering run backtest callback ---")
        register_run_backtest_callback(app)
        print("--- app_factory.py: Run backtest callback registered ---")

    except ImportError as e_import:
        print(f"--- app_factory.py: ImportError in register_callbacks: {e_import} ---")
        logger.error(f"ImportError in register_callbacks: {e_import}", exc_info=True)
    except Exception as e_general:
        print(f"--- app_factory.py: General Exception during import or registration in register_callbacks: {e_general} ---")
        logger.error(f"General Exception in register_callbacks: {e_general}", exc_info=True)
    
    # Comment out other registrations
    # print("--- app_factory.py: Attempting to register other callbacks (commented out) ---")
    # try:
    #     register_wizard_callbacks(app)
    #     # ... other callback registrations
    #     print("--- app_factory.py: Other callbacks would be registered here ---")
    # except Exception as e_other_cb:
    #     print(f"--- app_factory.py: Exception during other (commented out) callback registration: {e_other_cb} ---")
    #     logger.error(f"Error registering other (commented out) callbacks: {e_other_cb}", exc_info=True)
        
    print("--- app_factory.py: register_callbacks COMPLETE ---")

print("--- app_factory.py: MODULE EXECUTION COMPLETE ---")

# This is usually in app.py or a run.py, not in the factory itself.
# if __name__ == '__main__':
#     app_instance = create_app()
#     app_instance.run_server(debug=True)
