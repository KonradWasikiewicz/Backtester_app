import dash_bootstrap_components as dbc
from dash import html, dcc
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

def create_overview_metrics(metrics_ids: List[str]) -> dbc.Card:
    """
    Creates overview metrics card with placeholders for key performance metrics.
    
    Args:
        metrics_ids: List of metric IDs to include
        
    Returns:
        dbc.Card: Card component with overview metrics
    """
    metrics_containers = []
    for metric_id in metrics_ids:
        display_name = metric_id.replace("-", " ").title()
        metrics_containers.append(
            dbc.Col(
                html.Div(
                    id=f"metric-{metric_id}",
                    className="metric-container"
                ),
                width={"size": 3, "sm": 4, "md": 3, "lg": 2}
            )
        )
    
    return dbc.Card([
        dbc.CardHeader("Performance Overview"),
        dbc.CardBody([
            dbc.Row(
                metrics_containers,
                className="metrics-row g-2"
            )
        ])
    ], className="mb-4")


def create_portfolio_charts() -> dbc.Card:
    """
    Creates card with portfolio performance charts.
    
    Returns:
        dbc.Card: Card component with portfolio charts
    """
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.Span("Portfolio Performance", className="me-2"),
                dbc.ButtonGroup(
                    [
                        dbc.Button(
                            "Value", 
                            id="btn-chart-value",
                            color="primary", 
                            outline=False,
                            size="sm",
                            n_clicks=0
                        ),
                        dbc.Button(
                            "Returns", 
                            id="btn-chart-returns",
                            color="primary", 
                            outline=True,
                            size="sm",
                            n_clicks=0
                        ),
                        dbc.Button(
                            "Drawdown", 
                            id="btn-chart-drawdown",
                            color="primary", 
                            outline=True,
                            size="sm",
                            n_clicks=0
                        )
                    ],
                    className="ms-2"
                )
            ], className="d-flex align-items-center")
        ]),
        dbc.CardBody([
            dcc.Loading(
                dcc.Graph(
                    id="portfolio-chart",
                    config={"displayModeBar": True, "scrollZoom": True}
                ),
                type="circle"
            )
        ])
    ], className="mb-4")


def create_monthly_returns_heatmap() -> dbc.Card:
    """
    Creates card with monthly returns heatmap.
    
    Returns:
        dbc.Card: Card component with monthly returns heatmap
    """
    return dbc.Card([
        dbc.CardHeader("Monthly Returns"),
        dbc.CardBody([
            dcc.Loading(
                dcc.Graph(
                    id="monthly-returns-heatmap",
                    config={"displayModeBar": False}
                ),
                type="circle"
            )
        ])
    ], className="mb-4")


def create_trades_table() -> dbc.Card:
    """
    Creates card with trades table.
    
    Returns:
        dbc.Card: Card component with trades data table
    """
    return dbc.Card([
        dbc.CardHeader("Trade History"),
        dbc.CardBody([
            dcc.Loading(
                id="trades-table-loading",
                children=html.Div(id="trades-table-container"),
                type="circle"
            )
        ])
    ], className="mb-4")


def create_signals_chart() -> dbc.Card:
    """
    Creates card with signals overlay chart.
    
    Returns:
        dbc.Card: Card component with signals chart
    """
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.Span("Signals & Trades", className="me-2"),
                dbc.Select(
                    id="ticker-selector",
                    options=[],
                    value=None,
                    placeholder="Select a ticker...",
                    className="ticker-select ms-2",
                    style={"width": "150px"}
                )
            ], className="d-flex align-items-center")
        ]),
        dbc.CardBody([
            dcc.Loading(
                dcc.Graph(
                    id="signals-chart",
                    config={"displayModeBar": True, "scrollZoom": True}
                ),
                type="circle"
            )
        ])
    ])


def create_no_results_placeholder() -> html.Div:
    """
    Creates placeholder to display when no results are available.
    
    Returns:
        html.Div: Placeholder component
    """
    return html.Div([
        html.I(className="fas fa-chart-line fa-3x text-muted mb-3"),
        html.H4("No Backtest Results", className="text-muted"),
        html.P("Configure and run a backtest to see results here.", className="text-muted")
    ], className="text-center py-5")


def create_results_section() -> html.Div:
    """
    Creates the complete results display section with all visualizations.
    
    Returns:
        html.Div: Container with results section
    """
    metrics_ids = [
        "total-return", "cagr", "sharpe", "max-drawdown", 
        "win-rate", "profit-factor", "avg-trade"
    ]
    
    return html.Div([
        html.Div(
            id="results-section",
            children=[
                create_overview_metrics(metrics_ids),
                create_portfolio_charts(),
                
                dbc.Row([
                    dbc.Col(
                        create_monthly_returns_heatmap(),
                        lg=6
                    ),
                    dbc.Col(
                        create_trades_table(),
                        lg=6
                    )
                ]),
                
                create_signals_chart()
            ],
            style={"display": "none"}
        ),
        
        html.Div(
            id="no-results-placeholder",
            children=create_no_results_placeholder(),
            style={"display": "block"}
        )
    ])