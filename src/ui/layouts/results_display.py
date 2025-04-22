import dash_bootstrap_components as dbc
from dash import html, dcc
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

def create_overview_metrics(metrics_ids: List[str], header: str = "Performance Overview") -> dbc.Card:
    """
    Creates overview metrics card with placeholders for key performance metrics.

    Args:
        metrics_ids: List of metric IDs to include
        header: Header title for the card

    Returns:
        dbc.Card: Card component with overview metrics
    """
    metrics_containers = []
    # Define display names, handling special cases if needed
    display_names = {
        "total-return": "Total Return",
        "cagr": "CAGR",
        "sharpe": "Sharpe Ratio",
        "max-drawdown": "Max Drawdown",
        "win-rate": "Win Rate",
        "profit-factor": "Profit Factor",
        "avg-trade": "Avg Trade P/L",
        "recovery-factor": "Recovery Factor", # Added
        "calmar-ratio": "Calmar Ratio",       # Added
        "starting-balance": "Starting Balance",
        "ending-balance": "Ending Balance",
        "signals-generated": "Signals Generated",
        "trades-count": "Trades Count",
        "unexecuted-signals": "Unexecuted Signals"
    }

    for metric_id in metrics_ids:
        display_name = display_names.get(metric_id, metric_id.replace("-", " ").title()) # Use display name map
        metrics_containers.append(
            dbc.Col(
                html.Div([
                    html.Small(display_name, className="text-muted d-block mb-1"), # Add label
                    html.Div(id=f"metric-{metric_id}", children="--", className="metric-value h5") # Add default value and class
                ]),
                # Adjusted column widths for potentially more metrics
                width=6, sm=4, md=3, lg=2, xxl=2, # Added xxl, adjusted others
                className="mb-2" # Add bottom margin
            )
        )

    return dbc.Card([
        dbc.CardHeader(header),
        dbc.CardBody([
            dbc.Row(
                metrics_containers,
                className="g-2" # Use g-2 for smaller gutters
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
                            outline=False, # Start with Value selected
                            size="sm",
                            n_clicks=0
                        ),
                        dbc.Button(
                            "Returns",
                            id="btn-chart-returns",
                            color="primary",
                            outline=True, # Others outlined
                            size="sm",
                            n_clicks=0
                        ),
                        dbc.Button(
                            "Drawdown",
                            id="btn-chart-drawdown",
                            color="primary",
                            outline=True, # Others outlined
                            size="sm",
                            n_clicks=0
                        )
                    ],
                    className="ms-auto" # Align buttons to the right
                )
            ], className="d-flex align-items-center")
        ]),
        dbc.CardBody([
            dcc.Loading(
                dcc.Graph(
                    id="portfolio-chart",
                    config={"displayModeBar": True, "scrollZoom": True},
                     # Add a default empty figure to prevent errors before first calculation
                    figure={'data': [], 'layout': {'template': 'plotly_dark', 'height': 400}}
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
                    config={"displayModeBar": False},
                    # Add a default empty figure
                    figure={'data': [], 'layout': {'template': 'plotly_dark', 'height': 350}}
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
                children=html.Div(
                    "Run a backtest to view trade history.", # Default message
                    id="trades-table-container"
                    ),
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
                html.Span("Signals & Trades", className="me-auto"), # Align left
                dbc.Select(
                    id="ticker-selector",
                    options=[], # Options populated by callback
                    value=None,
                    placeholder="Select ticker...",
                    className="ticker-select ms-2", # Add margin
                    style={"width": "150px"}
                )
            ], className="d-flex align-items-center")
        ]),
        dbc.CardBody([
            dcc.Loading(
                dcc.Graph(
                    id="signals-chart",
                    config={"displayModeBar": True, "scrollZoom": True},
                    # Add a default empty figure
                    figure={'data': [], 'layout': {'template': 'plotly_dark', 'height': 400}}
                ),
                type="circle"
            )
        ])
    ]) # Removed mb-4, let the grid handle spacing


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
    ], id="no-results-placeholder", # Added ID here
       className="text-center py-5",
       style={"display": "block"}) # Default to visible


def create_results_section() -> html.Div:
    """
    Creates the complete results display section with all visualizations.

    Returns:
        html.Div: Container with results section
    """
    return html.Div([
        html.Div(id="backtest-status", className="mb-3 text-center"),
        # Results section (initially hidden)
        html.Div(
            id="results-section",
            children=[
                # Strategy Overview
                create_overview_metrics(
                    metrics_ids=[
                        "total-return", "cagr", "sharpe", "max-drawdown", "calmar-ratio",
                        "recovery-factor", "starting-balance", "ending-balance", "signals-generated"
                    ],
                    header="Strategy Overview"
                ),
                # Trades Overview
                create_overview_metrics(
                    metrics_ids=[
                        "trades-count", "win-rate", "profit-factor", "avg-trade", "unexecuted-signals"
                    ],
                    header="Trades Overview"
                ),
                create_portfolio_charts(),

                dbc.Row([
                    dbc.Col(create_monthly_returns_heatmap(), lg=6, className="mb-4"), # Add bottom margin to cols
                    dbc.Col(create_trades_table(), lg=6, className="mb-4") # Add bottom margin to cols
                ]),

                create_signals_chart() # This takes full width row
            ],
            style={"display": "none"} # Start hidden
        ),

        # Placeholder section (initially visible)
        create_no_results_placeholder() # Changed: placeholder is now created by its own function
    ])