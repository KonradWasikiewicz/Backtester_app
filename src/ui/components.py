import dash_bootstrap_components as dbc
from dash import html

def create_metric_card(title, value, prefix="", suffix=""):
    """Create a styled metric card component with dark theme"""
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-subtitle text-muted"),
            html.H4(f"{prefix}{value}{suffix}", className="card-title text-info")
        ]),
        className="mb-3 bg-dark"
    )

def create_metric_card_with_tooltip(title, value, tooltip_text="", text_color=None):
    """Create a metric card with tooltip"""
    value_style = {}
    if text_color:
        value_style = {"color": text_color, "fontWeight": "bold"}
        
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Span(title, className="metric-title d-inline-block"),
                html.Span([
                    html.I(className="fas fa-info-circle ms-1 text-muted")
                ], id={"type": "tooltip", "index": title.replace(" ", "-").lower()})
            ]),
            html.Div(value, className="metric-value", style=value_style)
        ], className="p-2")  # Reduced padding
    ], className="h-100 metric-card border-0 shadow-sm"),
    dbc.Tooltip(
        tooltip_text,
        target={"type": "tooltip", "index": title.replace(" ", "-").lower()},
        placement="top"
    )
