import dash_bootstrap_components as dbc
from dash import dcc, html
from typing import List
import logging

# Import centralized IDs
from src.ui import ids as app_ids
from src.ui.ids.ids import SharedComponentIDs

logger = logging.getLogger(__name__)

# Keep individual chart/table creation functions as they are used to build panels


def create_portfolio_value_returns_chart() -> dbc.Card:
    """
    Creates the card containing the portfolio value/returns chart and toggle buttons."""
    logger.debug(
        "Creating portfolio value/returns chart card structure with Row/Col and flex-nowrap."
    )
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            html.H4(
                                "Portfolio Value",
                                className="card-title mb-0",
                            ),
                            width="auto",
                            className="d-flex align-items-center",
                        ),
                        dbc.Col(
                            dbc.Button(
                                html.I(className="fas fa-cog"),
                                id=app_ids.ResultsIDs.PORTFOLIO_SETTINGS_BUTTON,
                                color="primary",
                                outline=False,
                                size="sm",
                                className="gear-btn",
                            ),
                            width="auto",
                        ),
                    ],
                    align="center",  # Vertically aligns items (columns) within the Row
                    justify="between",  # Distributes space between title (left) and buttons (right)
                    className="gx-2 flex-nowrap",  # gx-2 for horizontal gutters, flex-nowrap to prevent wrapping
                )
            ),
            dbc.Popover(
                dbc.PopoverBody(
                    className="settings-popover-body",
                    [
                        dbc.Row(
                            [
                                dbc.Col("Y axis in", width="auto"),
                                dbc.Col(
                                    dbc.Button(
                                        "USD",
                                        id=app_ids.ResultsIDs.PORTFOLIO_VALUE_CURRENCY_USD,
                                        color="primary",
                                        outline=False,
                                        size="sm",
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "%",
                                        id=app_ids.ResultsIDs.PORTFOLIO_VALUE_CURRENCY_PERCENT,
                                        color="primary",
                                        outline=True,
                                        size="sm",
                                    ),
                                    width="auto",
                                ),
                            ],
                            className="g-1",
                        ),
                        dbc.Row(
                            [
                                dbc.Col("Scale", width="auto"),
                                dbc.Col(
                                    dbc.Button(
                                        "Linear",
                                        id=app_ids.ResultsIDs.PORTFOLIO_SCALE_LINEAR_BTN,
                                        color="primary",
                                        outline=False,
                                        size="sm",
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Log",
                                        id=app_ids.ResultsIDs.PORTFOLIO_SCALE_LOG_BTN,
                                        color="primary",
                                        outline=True,
                                        size="sm",
                                    ),
                                    width="auto",
                                ),
                            ],
                            className="g-1 mt-1",
                        ),
                    ]
                ),
                id=app_ids.ResultsIDs.PORTFOLIO_SETTINGS_POPOVER,
                target=app_ids.ResultsIDs.PORTFOLIO_SETTINGS_BUTTON,
                placement="bottom-end",
                trigger="legacy",
                autohide=False,
                is_open=False,
            ),
            dbc.CardBody(
                [
                    dcc.Loading(
                        id=app_ids.ResultsIDs.PORTFOLIO_CHART_LOADING,
                        children=[dcc.Graph(id=app_ids.ResultsIDs.PORTFOLIO_CHART)],
                        type="circle",
                    )
                ]
            ),
            dcc.Store(
                id=app_ids.ResultsIDs.PORTFOLIO_SETTINGS_STORE,
                data={"y_axis": "usd", "scale": "linear"},
            ),
        ],
        className="mb-1",
    )


def create_drawdown_chart() -> dbc.Card:
    """
    Creates the card containing the drawdown chart.
    Now uses the dedicated drawdown chart from VisualizationService.
    """
    logger.debug("Creating drawdown chart card structure.")
 return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            html.H4(
                                "Drawdown",
                                className="card-title mb-0",
                            ),
                            width="auto",
                            className="d-flex align-items-center",
                        ),
                        dbc.Col(
                            dbc.Button(
                                html.I(className="fas fa-cog"),
                                id=app_ids.ResultsIDs.DRAWDOWN_SETTINGS_BUTTON,
                                color="primary",
                                outline=False,
                                size="sm",
                                className="gear-btn",
                            ),
                            width="auto",
                        ),
                    ],
                    justify="between",
                    align="center",
                    className="gx-2 flex-nowrap",
                )
            ),
            dbc.Popover(
                dbc.PopoverBody(
                    className="settings-popover-body",
                    [
                        dbc.Row(
                            [
                                dbc.Col("Y axis in", width="auto"),
                                dbc.Col(
                                    dbc.Button(
                                        "USD",
                                        id=app_ids.ResultsIDs.DRAWDOWN_YAXIS_USD_BTN,
                                        color="primary",
                                        outline=True,
                                        size="sm",
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "%",
                                        id=app_ids.ResultsIDs.DRAWDOWN_YAXIS_PERCENT_BTN,
                                        color="primary",
                                        outline=False,
                                        size="sm",
                                    ),
                                    width="auto",
                                ),
                            ],
                            className="g-1",
                        ),
                        dbc.Row(
                            [
                                dbc.Col("Scale", width="auto"),
                                dbc.Col(
                                    dbc.Button(
                                        "Linear",
                                        id=app_ids.ResultsIDs.DRAWDOWN_SCALE_LINEAR_BTN,
                                        color="primary",
                                        outline=False,
                                        size="sm",
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Log",
                                        id=app_ids.ResultsIDs.DRAWDOWN_SCALE_LOG_BTN,
                                        color="primary",
                                        outline=True,
                                        size="sm",
                                    ),
                                    width="auto",
                                ),
                            ],
                            className="g-1 mt-1",
                        ),
                    ]
                ),
                id=app_ids.ResultsIDs.DRAWDOWN_SETTINGS_POPOVER,
                target=app_ids.ResultsIDs.DRAWDOWN_SETTINGS_BUTTON,
                placement="bottom-end",
                trigger="legacy",
                autohide=False,
                is_open=False,
            ),
            dbc.CardBody(
                [
                    dcc.Loading(
                        id=app_ids.ResultsIDs.DRAWDOWN_CHART_LOADING,
                        children=dcc.Graph(
                            id=app_ids.ResultsIDs.DRAWDOWN_CHART,  # This ID will be targeted by a callback that sets the figure
                        ),
                        type="circle",
                    )
                ]
            ),
            dcc.Store(
                id=app_ids.ResultsIDs.DRAWDOWN_SETTINGS_STORE,
                data={"y_axis": "percent", "scale": "linear"},
            ),
        ],
        className="mb-1",
    )


def create_monthly_returns_heatmap() -> dbc.Card:
    """
    Creates the card containing the monthly returns heatmap.
    """
    logger.debug("Creating monthly returns heatmap card structure.")
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H4("Monthly Returns Heatmap", className="card-title mb-0")
            ),
            dbc.CardBody(
                [
                    dcc.Loading(
                        id=app_ids.ResultsIDs.MONTHLY_RETURNS_HEATMAP_LOADING,  # Corrected ID
                        children=dcc.Graph(
                            id=app_ids.ResultsIDs.MONTHLY_RETURNS_HEATMAP,
                        ),
                        type="circle",
                    )
                ]
            ),
        ],
        className="mb-1",
    )  # Use mb-1


def create_trades_table() -> dbc.Card:
    """
    Creates card with a container for the trades table (dash_table.DataTable).
    The table itself will be generated by a callback.
    """
    logger.debug("Creating trades table card structure.")
    return dbc.Card(
        [
            dbc.CardHeader(html.H4("Trade History", className="card-title mb-0")),
            dbc.CardBody(
                [
                    dcc.Loading(
                        id=app_ids.ResultsIDs.TRADES_TABLE_LOADING,  # Corrected ID
                        # Container for the DataTable, populated by the callback
                        children=html.Div(
                            id=app_ids.ResultsIDs.TRADES_TABLE_CONTAINER,
                            children=[
                                # Initial placeholder message
                                html.Div("Run a backtest to view trade history.")
                            ],
                        ),
                        type="circle",
                    )
                ]
            ),
        ],
        className="mb-1",
    )  # Use mb-1


def create_signals_chart() -> dbc.Card:
    """
    Creates the card containing the signals chart and ticker selector.
    """
    logger.debug("Creating signals chart card structure.")
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            html.H4(
                                "Signals & Price Action", className="card-title mb-0"
                            ),
                            width="auto",
                        ),
                        dbc.Col(
                            dbc.Select(
                                id=app_ids.ResultsIDs.SIGNALS_TICKER_SELECTOR,
                                options=[],
                                placeholder="Select Ticker...",
                                size="sm",
                            ),
                            width=4,
                        ),
                        dbc.Col(
                            dbc.Checklist(
                                id=app_ids.ResultsIDs.SIGNALS_INDICATOR_CHECKLIST,
                                options=[
                                    {"label": "SMA50", "value": "sma50"},
                                    {"label": "SMA200", "value": "sma200"},
                                ],
                                value=[],
                                inline=True,
                                switch=True,
                            ),
                            width="auto",
                        ),
                    ],
                    justify="between",
                    align="center",
                )
            ),
            dbc.CardBody(
                [
                    dcc.Loading(
                        id=app_ids.ResultsIDs.SIGNALS_CHART_LOADING,
                        children=dcc.Graph(
                            id=app_ids.ResultsIDs.SIGNALS_CHART,
                        ),
                        type="circle",
                    )
                ]
            ),
        ],
        className="mb-1",
    )  # Use mb-1


# Removed create_status_and_progress_bar - moved to loading_overlay.py


# --- NEW: Center Panel Layout ---
def create_center_panel_layout() -> html.Div:
    """
    Creates the layout for the center panel containing all charts and the table.
    Arranges components vertically as requested.
    """
    logger.debug("Creating center panel layout.")
    return html.Div(
        [
            # New div to wrap actual results
            html.Div(
                id=app_ids.ResultsIDs.RESULTS_AREA_WRAPPER,
                children=[
                    create_portfolio_value_returns_chart(),
                    create_drawdown_chart(),
                    create_monthly_returns_heatmap(),
                    create_signals_chart(),
                    create_trades_table(),
                ],
                style={"display": "none"},
            )  # Initially hidden
        ]
    )


# --- NEW: Right Panel Layout ---
def create_right_panel_layout() -> html.Div:
    """
    Creates the layout for the right panel containing performance and trade metrics.
    Uses two cards with specific IDs for callback targeting.
    """
    logger.debug("Creating right panel layout.")
    return html.Div(
        [
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H4("Performance Overview", className="card-title mb-0")
                    ),
                    dbc.CardBody(
                        # Container for performance metrics, populated by callback
                        # Use g-2 for smaller gutters between metric cards
                        dbc.Row(
                            id=app_ids.ResultsIDs.PERFORMANCE_METRICS_CONTAINER,
                            className="g-2",
                        )
                    ),
                ],
                className="mb-1",
                id=app_ids.ResultsIDs.PERFORMANCE_OVERVIEW_CARD,
                style={"display": "none"},
            ),
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H4("Trade Statistics", className="card-title mb-0")
                    ),
                    dbc.CardBody(
                        # Container for trade statistics, populated by callback
                        # Use g-2 for smaller gutters between metric cards
                        dbc.Row(
                            id=app_ids.ResultsIDs.TRADE_METRICS_CONTAINER,
                            className="g-2",
                        )
                    ),
                ],
                className="mb-1",
                id=app_ids.ResultsIDs.TRADE_STATISTICS_CARD,
                style={"display": "none"},
            ),
        ]
    )


def create_main_results_area() -> html.Div:
    """
    Creates the main area where all results (charts, tables, metrics) will be displayed.
    """
    logger.debug("Creating main results display area.")
    return html.Div(
        id=app_ids.ResultsIDs.RESULTS_AREA_WRAPPER,  # Corrected: Access via ResultsIDs class
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        create_center_panel_layout(),
                        id=app_ids.ResultsIDs.CENTER_PANEL_COLUMN,
                        width=12,
                        lg=8,
                        className="mb-3 mb-lg-0",
                    ),
                    dbc.Col(
                        create_right_panel_layout(),
                        id=app_ids.ResultsIDs.RIGHT_PANEL_COLUMN,
                        width=12,
                        lg=4,
                    ),
                ]
            )
        ],
        style={"display": "none"},  # Initially hidden, shown after backtest
    )
