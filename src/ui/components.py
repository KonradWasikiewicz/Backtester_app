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

def create_metric_card_with_tooltip(title, value, tooltip_text):
    """Create a metric card with tooltip"""
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.H6(title, className="card-subtitle text-muted d-inline-block me-2"),
                html.I(
                    className="fas fa-info-circle",
                    id=f"tooltip-{title.lower().replace(' ', '-')}",
                    style={'color': '#6c757d', 'fontSize': '14px'}
                ),
                dbc.Tooltip(
                    tooltip_text,
                    target=f"tooltip-{title.lower().replace(' ', '-')}",
                    placement="top"
                )
            ]),
            html.H4(value, className="card-title text-info")
        ]),
        className="mb-3 bg-dark"
    )
