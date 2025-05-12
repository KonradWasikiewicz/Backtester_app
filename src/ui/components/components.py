# src/ui/components/components.py
"""
Re-export of components from the parent components module to avoid import conflicts.
"""

# Import functions from the parent ui.components module
from src.ui.components import create_metric_card as _imported_create_metric_card
from src.ui.components import create_metric_card_with_tooltip as _imported_create_metric_card_with_tooltip

# Re-export the functions
create_metric_card = _imported_create_metric_card
create_metric_card_with_tooltip = _imported_create_metric_card_with_tooltip
