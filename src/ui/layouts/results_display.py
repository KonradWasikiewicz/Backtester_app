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
        "recovery-factor": "Recovery Factor",
        "calmar-ratio": "Calmar Ratio",
        "starting-balance": "Starting Balance",
        "ending-balance": "Ending Balance",
        "signals-generated": "Total Entry Signals", # Updated name
        "trades-count": "Executed Trades", # Updated name
        # Add new rejection metric display names
        "rejected-signals-total": "Rejected Signals (Total)",
        "rejected-signals-cash": "Rejected: Insufficient Cash",
        "rejected-signals-risk": "Rejected: Risk/Size Rules",
        "rejected-signals-maxpos": "Rejected: Max Positions",
        "rejected-signals-exists": "Rejected: Position Exists",
        "rejected-signals-filter": "Rejected: Market Filter",
        "rejected-signals-other": "Rejected: Other Reasons"
    }

    for metric_id in metrics_ids:
        display_name = display_names.get(metric_id, metric_id.replace("-", " ").title()) # Use display name map
        metrics_containers.append(
            dbc.Col(
                html.Div([
                    html.Small(display_name, className="text-muted d-block mb-1"), # Add label
                    # Ensure the ID matches the callback output format: metric-<id>
                    html.Div(id=f"metric-{metric_id}", children="--", className="metric-value h5") 
                ]),
                # Use slightly wider columns for potentially longer labels
                width=6, sm=4, md=4, lg=3, xxl=2, # Adjusted widths
                className="mb-2" # Add bottom margin
            )
        )

    return dbc.Card([
        dbc.CardHeader(header),
        dbc.CardBody([
            dbc.Row(
                metrics_containers,
                className="g-3" # Slightly larger gutters
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
        # Results section (initially hidden)
        html.Div(
            id="results-section",
            children=[
                # Strategy Overview
                create_overview_metrics(
                    metrics_ids=[
                        "total-return", "cagr", "sharpe", "max-drawdown", "calmar-ratio",
                        "recovery-factor", "starting-balance", "ending-balance"
                    ],
                    header="Strategy Performance Overview"
                ),
                # Trades & Signals Overview
                create_overview_metrics(
                    metrics_ids=[
                        "signals-generated", # Total entry signals
                        "trades-count",      # Executed trades
                        "rejected-signals-total", # Total rejected
                        "win-rate", 
                        "profit-factor", 
                        "avg-trade",
                        # Detailed Rejection Reasons
                        "rejected-signals-cash",
                        "rejected-signals-risk",
                        "rejected-signals-maxpos",
                        "rejected-signals-exists",
                        "rejected-signals-filter",
                        "rejected-signals-other"
                    ],
                    header="Trade & Signal Execution Overview"
                ),
                create_portfolio_charts(), # Portfolio chart remains full width

                # Move heatmap above trades table, both full width
                dbc.Row([
                    dbc.Col(create_monthly_returns_heatmap(), width=12, className="mb-4"),
                ]),
                dbc.Row([
                     dbc.Col(create_trades_table(), width=12, className="mb-4") # Trades table full width
                ]),

                create_signals_chart() # Signals chart remains full width
            ],
            style={"display": "none"} # Start hidden
        ),

        # Placeholder section (initially visible)
        create_no_results_placeholder()
    ])