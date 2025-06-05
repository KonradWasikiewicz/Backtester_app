import dash_bootstrap_components as dbc
from dash import html, dcc # Import dcc for potential future components
import logging
from typing import Dict, Tuple, Optional, List, Any

logger = logging.getLogger(__name__)

# Import visualization configuration for consistent colors/styles
try:
    from src.core.constants import VISUALIZATION_CONFIG as VIZ_CFG
except ImportError:
    logger.warning("Could not import VISUALIZATION_CONFIG in components. Using fallback colors.")
    # Basic fallback settings for colors
    VIZ_CFG = { "colors": { "card_background": "#1e222d", "text_color": "#dee2e6", "text_muted": "#6c757d", "primary": "#0d6efd"} }


def create_metric_card(title: str, value: str, card_classname: str = "mb-2", value_classname: str = "text-primary") -> dbc.Card:
    """
    Creates a simple Bootstrap Card to display a single metric.
    (Less used now that we have a tooltip version).

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
            html.H6(title, className="card-subtitle text-muted small mb-1"), # Smaller title
            html.H4(value, className=f"card-title metric-value {value_classname}") # Use metric-value class
        ], className="p-2"), # Reduced padding
        className=f"h-100 {card_classname}", # h-100 for equal height in row
        style={"backgroundColor": VIZ_CFG['colors']['card_background']} # Set background
    )


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
    value_style = {"color": text_color} if text_color else {"color": VIZ_CFG['colors'].get('primary', '#0d6efd')} # Default to primary color

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
                style={'cursor': 'help'}
            )
        )

    card_content = dbc.Card(
        dbc.CardBody([
            html.Div(title_elements, className="d-flex justify-content-between align-items-center mb-1"), # Flexbox for title and icon
            html.Div(value, className="metric-value", style=value_style)
        ], className="p-2"), # Reduced padding
        className="h-100 border-0", # h-100 for equal height, no border
        style={"backgroundColor": VIZ_CFG['colors']['card_background']} # Card background
    )

    # Create tooltip only if tooltip_text is provided
    tooltip_component = dbc.Tooltip(
            tooltip_text,
            target=tooltip_target_id,
            placement="top",
            # Custom classes for tooltips can be added if needed
            # className="custom-tooltip bs-tooltip-top",
            # style={"backgroundColor": "rgba(42, 46, 57, 0.95)", "color": "#fff"} # Custom tooltip style
        ) if tooltip_text else None

    # Return Div containing the card and tooltip (if exists)
    children = [card_content]
    if tooltip_component:
        children.append(tooltip_component)

    # Return wrapper Div that takes full column height
    return html.Div(children, className=f"metric-wrapper {card_classname}", style={'height': '100%'})

# Future reusable UI components can be added here, e.g.:
# - Function to create a card header section
# - Custom dropdown component
# - Icon button component


def create_metrics_table(rows: List[Tuple[str, Any, Optional[Any]]]) -> dbc.Table:
    """Create a simple metrics table.

    Args:
        rows: List of tuples (label, strategy_value, benchmark_value or None).

    Returns:
        dbc.Table component representing the metrics.
    """
    show_benchmark = any(len(r) > 2 and r[2] is not None for r in rows)

    header_cells = [html.Th("Metric"), html.Th("Strategy")]
    if show_benchmark:
        header_cells.append(html.Th("Benchmark"))

    body_rows = []
    for row in rows:
        label = row[0]
        strat_val = row[1]
        bench_val = row[2] if len(row) > 2 else None

        def _fmt(val):
            if isinstance(val, (int, float)):
                return f"{val:.2f}"
            return "" if val is None else str(val)

        cells = [html.Td(label), html.Td(_fmt(strat_val))]
        if show_benchmark:
            cells.append(html.Td(_fmt(bench_val)))

        body_rows.append(html.Tr(cells))

    table = dbc.Table(
        [html.Thead(html.Tr(header_cells)), html.Tbody(body_rows)],
        bordered=True,
        size="sm",
        className="w-100",
    )
    return table
