import dash
from dash import Dash, html, dcc, Input, Output, State, ALL, MATCH, ctx, no_update
import dash_bootstrap_components as dbc  # Import Bootstrap components
from dash.exceptions import PreventUpdate # Added import
import logging
from datetime import date  # Import for date validation
# Make sure logging is configured appropriately elsewhere (e.g., in app_factory or main app.py)
# from ...config.logging_config import setup_logging
from src.core.constants import STRATEGY_DESCRIPTIONS # Poprawna ścieżka do stałych
from src.core.constants import DEFAULT_STRATEGY_PARAMS  # added import for default params
from src.core.constants import AVAILABLE_STRATEGIES # Ensure this is imported
from src.core.constants import PARAM_DESCRIPTIONS  # added import for parameter descriptions
from src.ui.ids import WizardIDs, StrategyConfigIDs  # Import the centralized IDs and StrategyConfigIDs
from src.ui.components.stepper import create_wizard_stepper  # Import for updating the stepper
from src.core.data import DataLoader  # Import for ticker data

logger = logging.getLogger(__name__)

def register_wizard_callbacks(app: Dash):
    """
    Register callbacks for the wizard interface, including step transitions and validation.
    """
    logger.info("Registering wizard and main page run button callbacks...")
