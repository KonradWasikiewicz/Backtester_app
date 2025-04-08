import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, ClientsideFunction
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
    
    card = dbc.Card([
        dbc.CardHeader("Risk Management", className="bg-dark text-light"),
        dbc.CardBody([
            # Enable/Disable Risk Management Features
            html.H5("Enable Risk Management Features", className="mb-3 text-light"),
            dbc.Row([
                dbc.Col([
                    dbc.Checklist(
                        options=[
                            {"label": "Enable Position Sizing Controls", "value": "position_sizing"},
                            {"label": "Enable Stop Loss", "value": "stop_loss"},
                            {"label": "Enable Take Profit", "value": "take_profit"},
                            {"label": "Enable Risk per Trade Limits", "value": "risk_per_trade"},
                            {"label": "Enable Market Filtering", "value": "market_filter"},
                            {"label": "Enable Drawdown Protection", "value": "drawdown_protection"},
                            {"label": "Continue to iterate when risk limits are breached", "value": "continue_iterate"},
                        ],
                        value=[],  # Default is empty - no advanced risk management
                        id="risk-features-checklist",
                        inline=False,
                        className="text-light"
                    ),
                ], width=12)
            ], className="mb-3"),
            
            # Position Sizing (will be shown/hidden based on checkbox)
            html.Div([
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
            ], id="position-sizing-container", style={"display": "none"}),
            
            # Stop Loss
            html.Div([
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
            ], id="stop-loss-container", style={"display": "none"}),
            
            # Take Profit
            html.Div([
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
            ], id="take-profit-container", style={"display": "none"}),
            
            # Risk per Trade
            html.Div([
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
                ], className="mb-3"),
            ], id="risk-per-trade-container", style={"display": "none"}),

            # Market Filter
            html.Div([
                html.H5("Market Filter", className="mb-3 text-light"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Market Trend Lookback (days)", html_for="market-trend-lookback", className="text-light"),
                        dbc.Input(
                            id="market-trend-lookback",
                            type="number",
                            min=10,
                            max=500,
                            value=100,
                            step=10,
                            className="bg-dark text-light border-secondary"
                        )
                    ], width=6),
                ], className="mb-3"),
            ], id="market-filter-container", style={"display": "none"}),

            # Drawdown Protection
            html.Div([
                html.H5("Drawdown Protection", className="mb-3 text-light"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Max Drawdown (%)", html_for="max-drawdown", className="text-light"),
                        dbc.Input(
                            id="max-drawdown",
                            type="number",
                            min=0,
                            max=100,
                            value=20,
                            step=1,
                            className="bg-dark text-light border-secondary"
                        )
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Max Daily Loss (%)", html_for="max-daily-loss", className="text-light"),
                        dbc.Input(
                            id="max-daily-loss",
                            type="number",
                            min=0,
                            max=100,
                            value=5,
                            step=0.5,
                            className="bg-dark text-light border-secondary"
                        )
                    ], width=6)
                ], className="mb-3"),
            ], id="drawdown-protection-container", style={"display": "none"}),
            
            # Hidden div for storing client-side state
            html.Div(id='risk-management-client-side-store', style={'display': 'none'})
        ], className="bg-dark")
    ], className="border-secondary")
    
    # Add JavaScript for toggle behavior
    clientside_callback_code = """
    function(values) {
        const displayStates = {};
        
        // Set display style based on checkbox values
        displayStates['position-sizing-container'] = values.includes('position_sizing') ? 'block' : 'none';
        displayStates['stop-loss-container'] = values.includes('stop_loss') ? 'block' : 'none';
        displayStates['take-profit-container'] = values.includes('take_profit') ? 'block' : 'none';
        displayStates['risk-per-trade-container'] = values.includes('risk_per_trade') ? 'block' : 'none';
        displayStates['market-filter-container'] = values.includes('market_filter') ? 'block' : 'none';
        displayStates['drawdown-protection-container'] = values.includes('drawdown_protection') ? 'block' : 'none';
        
        return displayStates;
    }
    """
    
    # Create the clientside callbacks to handle the visibility toggles
    add_risk_management_callbacks(clientside_callback_code)
    
    return card

def add_risk_management_callbacks(clientside_callback_code):
    """
    Register clientside callbacks for risk management section.
    This is separate from the layout to avoid circular imports.
    """
    clientside_callback = ClientsideFunction(
        namespace='clientside',
        function_name='updateRiskManagementVisibility'
    )
    
    # Output the style dictionaries for each container
    outputs = [
        Output('position-sizing-container', 'style'),
        Output('stop-loss-container', 'style'),
        Output('take-profit-container', 'style'),
        Output('risk-per-trade-container', 'style'),
        Output('market-filter-container', 'style'),
        Output('drawdown-protection-container', 'style')
    ]
    
    # Define the JavaScript function in the page
    risk_management_js_code = f"""
    window.dash_clientside = Object.assign({{}}, window.dash_clientside, {{
        clientside: {{
            updateRiskManagementVisibility: {clientside_callback_code}
        }}
    }});
    """
    
    # Add the script to the layout
    dcc.Store(id='risk-management-js', data=risk_management_js_code)