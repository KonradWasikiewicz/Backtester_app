import dash_bootstrap_components as dbc
from dash import html, dcc
import logging
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

def create_ticker_input() -> html.Div:
    """
    Creates ticker input field with explanatory text.
    
    Returns:
        html.Div: Container with ticker input
    """
    return html.Div([
        dbc.Label("Tickers (comma-separated)", className="mb-1"),
        dbc.Input(
            id="ticker-input", 
            type="text", 
            placeholder="e.g. AAPL, MSFT, GOOG", 
            className="mb-2"
        ),
        html.Small(
            "Enter ticker symbols separated by commas for backtest", 
            className="text-muted d-block mb-3"
        )
    ])

def create_date_range_selector() -> html.Div:
    """
    Creates date range selector with preset periods.
    
    Returns:
        html.Div: Container with date range selector
    """
    return html.Div([
        dbc.Label("Backtest Period", className="mb-1"),
        dbc.Row([
            dbc.Col(
                dcc.DatePickerRange(
                    id='date-range-picker',
                    min_date_allowed='2010-01-01',
                    max_date_allowed='2025-01-01',  # Adjust as needed
                    initial_visible_month='2020-01-01',
                    start_date='2020-01-01',
                    end_date='2021-12-31',
                    className="date-picker-custom"
                ), 
                width=12
            ),
        ], className="mb-3")
    ])

def create_risk_parameters() -> html.Div:
    """
    Creates form fields for risk management parameters.
    
    Returns:
        html.Div: Container with risk parameters
    """
    return html.Div([
        html.H6("Risk Management", className="mt-3 mb-2"),
        dbc.Row([
            dbc.Col([
                dbc.Label("Position Sizing", className="small"),
                dbc.Select(
                    id="position-sizing-selector",
                    options=[
                        {"label": "Equal Weight", "value": "equal"},
                        {"label": "Fixed Dollar", "value": "fixed_dollar"},
                        {"label": "Percent of Capital", "value": "percent"},
                        {"label": "Volatility Adjusted", "value": "volatility"}
                    ],
                    value="percent",
                    className="mb-2"
                )
            ], width=6),
            dbc.Col([
                dbc.Label("Risk Per Trade (%)", className="small"),
                dbc.Input(
                    id="risk-per-trade",
                    type="number",
                    value=2.0,
                    min=0.1,
                    max=10,
                    step=0.1,
                    className="mb-2"
                )
            ], width=6)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Label("Stop Loss Type", className="small"),
                dbc.Select(
                    id="stop-loss-selector",
                    options=[
                        {"label": "No Stop Loss", "value": "none"},
                        {"label": "Fixed Percent", "value": "percent"},
                        {"label": "ATR Multiple", "value": "atr"}
                    ],
                    value="percent",
                    className="mb-2"
                )
            ], width=6),
            dbc.Col([
                dbc.Label("Stop Loss Value", className="small"),
                dbc.Input(
                    id="stop-loss-value",
                    type="number",
                    value=5.0,
                    min=0.1,
                    max=20,
                    step=0.1,
                    className="mb-2"
                )
            ], width=6)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Label("Max Open Positions", className="small"),
                dbc.Input(
                    id="max-positions",
                    type="number",
                    value=5,
                    min=1,
                    max=50,
                    step=1,
                    className="mb-2"
                )
            ], width=6),
            dbc.Col([
                dbc.Checkbox(
                    id="use-market-filter",
                    label="Use Market Trend Filter",
                    value=True,
                    className="mt-4"
                )
            ], width=6)
        ])
    ])

def create_risk_management_section() -> html.Div:
    """
    Creates the complete risk management UI section including tickers and dates.
    
    Returns:
        html.Div: Container with the full risk management section
    """
    return html.Div([
        # Ticker input
        create_ticker_input(),
        
        # Date range selector
        create_date_range_selector(),
        
        # Risk parameters
        create_risk_parameters(),
        
        # Run backtest button
        html.Div([
            dbc.Button(
                "Run Backtest", 
                id="run-backtest-button", 
                color="primary", 
                size="lg", 
                className="w-100 mt-3"
            ),
            html.Div(id="backtest-status", className="text-center mt-2")
        ])
    ])