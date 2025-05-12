# src/ui/components/metric_cards.py
"""
Metric card components for the backtester application.
This file re-exports the metric card components from the parent module.
"""

# Import the metric card functions from the parent module
from src.ui.components import create_metric_card as _parent_create_metric_card

# Re-export the functions
create_metric_card = _parent_create_metric_card
