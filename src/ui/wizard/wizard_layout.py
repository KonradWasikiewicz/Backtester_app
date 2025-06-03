"""
Wizard layout module for the step-by-step backtesting configuration interface.
This module creates the complete wizard interface with all 6 steps.
"""

import logging
from dash import html, dcc
import dash_bootstrap_components as dbc
from typing import List, Dict, Any
import pandas as pd
from src.core.data import DataLoader
from src.core.constants import AVAILABLE_STRATEGIES
from src.ui.ids import WizardIDs
from src.ui.wizard.layout import create_wizard_layout

logger = logging.getLogger(__name__)

def get_wizard_layout():
    """Get the complete wizard layout."""
    return create_wizard_layout()
