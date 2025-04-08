import dash_bootstrap_components as dbc
from dash import dcc, html
import logging
from typing import Dict, Any, Optional, List

# Configure logging
logger = logging.getLogger(__name__)

def create_risk_management_section(available_tickers: List[str] = None) -> dbc.Card:
    """
    Creates the risk management configuration UI section.
    
    Args:
        available_tickers: List of available ticker symbols (optional)
        
    Returns:
        dbc.Card: A card component containing the risk management configuration UI
    """
    if not available_tickers:
        available_tickers = []
    
    return dbc.Card([
        dbc.CardHeader("Risk Management", className="bg-dark text-light"),
        dbc.CardBody([
            # Position Sizing
            html.H5("Position Sizing", className="mb-3 text-light"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Max Position Size (%)", html_for="max-position-size", className="text-light"),
                    dbc.Input(
                        id="max-position-size",
                        type="number",
                        min=0,
                        max=100,
                        value=5,
                        step=0.1,
                        className="bg-dark text-light border-secondary"
                    )
                ], width=6),
                dbc.Col([
                    dbc.Label("Max Portfolio Risk (%)", html_for="max-portfolio-risk", className="text-light"),
                    dbc.Input(
                        id="max-portfolio-risk",
                        type="number",
                        min=0,
                        max=100,
                        value=2,
                        step=0.1,
                        className="bg-dark text-light border-secondary"
                    )
                ], width=6)
            ], className="mb-3"),
            
            # Stop Loss
            html.H5("Stop Loss", className="mb-3 text-light"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Stop Loss Type", html_for="stop-loss-type", className="text-light"),
                    dbc.Select(
                        id="stop-loss-type",
                        options=[
                            {"label": "Fixed", "value": "fixed"},
                            {"label": "Trailing", "value": "trailing"},
                            {"label": "ATR", "value": "atr"}
                        ],
                        value="fixed",
                        className="bg-dark text-light border-secondary"
                    )
                ], width=6),
                dbc.Col([
                    dbc.Label("Stop Loss Value (%)", html_for="stop-loss-value", className="text-light"),
                    dbc.Input(
                        id="stop-loss-value",
                        type="number",
                        min=0,
                        max=100,
                        value=2,
                        step=0.1,
                        className="bg-dark text-light border-secondary"
                    )
                ], width=6)
            ], className="mb-3"),
            
            # Take Profit
            html.H5("Take Profit", className="mb-3 text-light"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Take Profit Type", html_for="take-profit-type", className="text-light"),
                    dbc.Select(
                        id="take-profit-type",
                        options=[
                            {"label": "Fixed", "value": "fixed"},
                            {"label": "Trailing", "value": "trailing"}
                        ],
                        value="fixed",
                        className="bg-dark text-light border-secondary"
                    )
                ], width=6),
                dbc.Col([
                    dbc.Label("Take Profit Value (%)", html_for="take-profit-value", className="text-light"),
                    dbc.Input(
                        id="take-profit-value",
                        type="number",
                        min=0,
                        max=100,
                        value=4,
                        step=0.1,
                        className="bg-dark text-light border-secondary"
                    )
                ], width=6)
            ], className="mb-3"),
            
            # Risk per Trade
            html.H5("Risk per Trade", className="mb-3 text-light"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Max Risk per Trade (%)", html_for="max-risk-per-trade", className="text-light"),
                    dbc.Input(
                        id="max-risk-per-trade",
                        type="number",
                        min=0,
                        max=100,
                        value=1,
                        step=0.1,
                        className="bg-dark text-light border-secondary"
                    )
                ], width=6),
                dbc.Col([
                    dbc.Label("Risk:Reward Ratio", html_for="risk-reward-ratio", className="text-light"),
                    dbc.Input(
                        id="risk-reward-ratio",
                        type="number",
                        min=0,
                        max=10,
                        value=2,
                        step=0.1,
                        className="bg-dark text-light border-secondary"
                    )
                ], width=6)
            ], className="mb-3")
        ], className="bg-dark")
    ], className="border-secondary")