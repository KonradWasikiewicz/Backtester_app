import dash_bootstrap_components as dbc
from dash import dcc, html
import logging
from typing import Dict, Any, Optional, List

# Configure logging
logger = logging.getLogger(__name__)

def create_risk_management_section():
    """
    Create the risk management configuration section of the UI.
    
    Returns:
        Dash layout object for risk management settings
    """
    
    return dbc.Card([
        dbc.CardHeader([
            html.H5("Risk Management", className="mb-0")
        ], className="bg-primary text-white"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Position Sizing Method", className="form-label"),
                    dcc.Dropdown(
                        id="position-sizing-selector",
                        options=[
                            {"label": "Fixed Risk Per Trade", "value": "risk"},
                            {"label": "Equal Position Sizing", "value": "equal"}
                        ],
                        value="risk",
                        clearable=False
                    )
                ], width=6),
                dbc.Col([
                    html.Label("Risk Per Trade (%)", className="form-label"),
                    dbc.Input(
                        id="risk-per-trade",
                        type="number",
                        value=2,
                        min=0.1,
                        max=10,
                        step=0.1
                    )
                ], width=6),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    html.Label("Stop Loss Type", className="form-label"),
                    dcc.Dropdown(
                        id="stop-loss-selector",
                        options=[
                            {"label": "Fixed Percentage", "value": "fixed"},
                            {"label": "Trailing Stop", "value": "trailing"},
                            {"label": "No Stop Loss", "value": "none"}
                        ],
                        value="fixed",
                        clearable=False
                    )
                ], width=6),
                dbc.Col([
                    html.Label("Stop Loss Value (%)", className="form-label"),
                    dbc.Input(
                        id="stop-loss-value",
                        type="number",
                        value=2,
                        min=0.1,
                        max=20,
                        step=0.1
                    )
                ], width=6),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    html.Label("Maximum Open Positions", className="form-label"),
                    dbc.Input(
                        id="max-positions",
                        type="number",
                        value=5,
                        min=1,
                        max=50,
                        step=1
                    )
                ], width=6),
                dbc.Col([
                    dbc.Checkbox(
                        id="use-market-filter",
                        label="Use Market Filter",
                        value=True
                    ),
                    dbc.Tooltip(
                        "Only enter positions when market trend is favorable",
                        target="use-market-filter"
                    )
                ], width=6, className="d-flex align-items-center"),
            ], className="mb-3")
        ])
    ], className="mb-4")