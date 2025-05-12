# src/ui/components/__init__.py
"""
UI components package for the backtester application.
"""

# Import stepper components
from src.ui.components.stepper import create_wizard_stepper, create_step_indicator

# Import necessary modules for create_metric_card
import dash_bootstrap_components as dbc
from dash import html
import logging

logger = logging.getLogger(__name__)

# Directly implement create_metric_card in the components package
# This avoids import issues while ensuring the function is available
def create_metric_card(title: str, value: str, card_classname: str = "mb-2", value_classname: str = "text-primary") -> dbc.Card:
    """
    Creates a simple Bootstrap Card to display a single metric.
    
    Args:
        title (str): The title or label for the metric.
        value (str): The formatted value of the metric to display.
        card_classname (str): Additional CSS classes for the dbc.Card.
        value_classname(str): Additional CSS classes for the metric value (e.g., text-success, text-danger).
    
    Returns:
        dbc.Card: A Dash Bootstrap Card component.
    """
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-subtitle text-muted"),
            html.H5(value, className=value_classname)
        ]),
        className=card_classname
    )
