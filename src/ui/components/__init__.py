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
from typing import Optional

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

# Implementing the tooltip version of the metric card
def create_metric_card_with_tooltip(title: str,
                                    value: str,
                                    tooltip_text: str = "",
                                    text_color: Optional[str] = None,
                                    card_classname: str = "mb-2") -> html.Div:
    """
    Creates a Bootstrap Card for a metric, including an info icon with a tooltip.

    Args:
        title (str): The title/label for the metric.
        value (str): The formatted value of the metric.
        tooltip_text (str): Text to display in the tooltip. If empty, no icon/tooltip is shown.
        text_color (Optional[str]): Specific CSS color for the value text (e.g., '#28a745' for green).
        card_classname (str): Additional CSS classes for the outer html.Div container.

    Returns:
        html.Div: A Div containing the Card and its Tooltip.
    """
    value_style = {"color": text_color} if text_color else {}

    # Use a dictionary for ID to avoid collisions and enable easier CSS/JS targeting
    tooltip_target_id = {'type': 'metric-tooltip-target', 'index': title.replace(" ", "-").lower()}

    # Title elements and icon (if tooltip is provided)
    title_elements = [html.Span(title, className="metric-title me-1")] # Add margin after title
    if tooltip_text:
        title_elements.append(
             html.Span(
                html.I(className="fas fa-info-circle fa-xs"), # FontAwesome info icon, fa-xs for smaller size
                id=tooltip_target_id,
                className="text-muted tooltip-icon", # Class for icon styling
             )
        )

    # Card component with the metric
    card = dbc.Card(
        dbc.CardBody([
            html.Div(title_elements, className="d-flex align-items-center mb-1"),
            html.H5(value, style=value_style)
        ]),
        className=card_classname
    )

    # Only create the tooltip if tooltip text is provided
    if tooltip_text:
        tooltip = dbc.Tooltip(
            tooltip_text,
            target=tooltip_target_id,
            placement="top"
        )
        return html.Div([card, tooltip])
    else:
        return html.Div([card])
