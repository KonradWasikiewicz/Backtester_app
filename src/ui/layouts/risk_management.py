import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, ClientsideFunction, State
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
    
    # Create individual risk management feature options with their associated panels
    def create_feature_with_panel(label, value, panel_content):
        return html.Div([
            dbc.Checklist(
                options=[{"label": label, "value": value}],
                value=[],  # Default is unchecked
                id=f"{value}-checkbox",
                inline=False,
                className="text-light mb-2"
            ),
            html.Div(
                panel_content,
                id=f"{value}-container",
                style={"display": "none", "marginLeft": "20px", "marginBottom": "15px"}
            )
        ])
    
    # Position Sizing panel content
    position_sizing_panel = [
        html.Div([
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
        ])
    ]
    
    # Stop Loss panel content
    stop_loss_panel = [
        html.Div([
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
        ])
    ]
    
    # Take Profit panel content
    take_profit_panel = [
        html.Div([
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
        ])
    ]
    
    # Risk per Trade panel content
    risk_per_trade_panel = [
        html.Div([
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
        ])
    ]
    
    # Market Filter panel content
    market_filter_panel = [
        html.Div([
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
        ])
    ]
    
    # Drawdown Protection panel content
    drawdown_protection_panel = [
        html.Div([
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
        ])
    ]
    
    # Assemble the card with the new structure
    card = dbc.Card([
        dbc.CardHeader("Risk Management", className="bg-dark text-light"),
        dbc.CardBody([
            # Title for the risk management section
            html.H5("Risk Management Features", className="mb-3 text-light"),
            
            # Position Sizing feature
            create_feature_with_panel("Enable Position Sizing Controls", "position_sizing", position_sizing_panel),
            
            # Stop Loss feature
            create_feature_with_panel("Enable Stop Loss", "stop_loss", stop_loss_panel),
            
            # Take Profit feature
            create_feature_with_panel("Enable Take Profit", "take_profit", take_profit_panel),
            
            # Risk per Trade feature
            create_feature_with_panel("Enable Risk per Trade Limits", "risk_per_trade", risk_per_trade_panel),
            
            # Market Filter feature
            create_feature_with_panel("Enable Market Filtering", "market_filter", market_filter_panel),
            
            # Drawdown Protection feature
            create_feature_with_panel("Enable Drawdown Protection", "drawdown_protection", drawdown_protection_panel),
            
            # Continue to iterate option
            dbc.Checklist(
                options=[
                    {"label": "Continue to iterate when risk limits are breached", "value": "continue_iterate"},
                ],
                value=[],
                id="continue-iterate-checkbox",
                inline=False,
                className="text-light mt-3"
            ),
            
            # Hidden div for storing client-side state
            html.Div(id='risk-management-client-side-store', style={'display': 'none'}),
            
            # Hidden combined checklist to maintain compatibility with existing code
            dbc.Checklist(
                id="risk-features-checklist",
                options=[
                    {"label": "", "value": "position_sizing"},
                    {"label": "", "value": "stop_loss"},
                    {"label": "", "value": "take_profit"},
                    {"label": "", "value": "risk_per_trade"},
                    {"label": "", "value": "market_filter"},
                    {"label": "", "value": "drawdown_protection"},
                    {"label": "", "value": "continue_iterate"},
                ],
                value=[],
                className="d-none"  # Hidden checklist
            ),
        ], className="bg-dark")
    ], className="border-secondary")
    
    return card

def add_risk_management_callbacks(app):
    """
    Register clientside callbacks for risk management section.
    This is separate from the layout to avoid circular imports.
    
    Args:
        app: The Dash application instance
    """
    # Create callbacks for toggling the visibility of each container
    features = [
        "position_sizing",
        "stop_loss",
        "take_profit",
        "risk_per_trade",
        "market_filter",
        "drawdown_protection"
    ]
    
    for feature in features:
        # Register clientside callback for each feature checkbox
        app.clientside_callback(
            f"""
            function(isChecked) {{
                const containerId = "{feature}-container";
                return isChecked.length > 0 ? {{"display": "block"}} : {{"display": "none"}};
            }}
            """,
            Output(f"{feature}-container", "style"),
            Input(f"{feature}-checkbox", "value")
        )
        
        # Also update the hidden combined checklist to maintain compatibility
        app.clientside_callback(
            f"""
            function(isChecked, currentValues) {{
                let newValues = [...currentValues];
                if(isChecked.length > 0) {{
                    if(!newValues.includes("{feature}")) {{
                        newValues.push("{feature}");
                    }}
                }} else {{
                    newValues = newValues.filter(value => value !== "{feature}");
                }}
                return newValues;
            }}
            """,
            Output("risk-features-checklist", "value"),
            Input(f"{feature}-checkbox", "value"),
            State("risk-features-checklist", "value"),
            prevent_initial_call=True
        )
    
    # Special handling for continue_iterate checkbox
    app.clientside_callback(
        """
        function(isChecked, currentValues) {
            let newValues = [...currentValues];
            if(isChecked.length > 0) {
                if(!newValues.includes("continue_iterate")) {
                    newValues.push("continue_iterate");
                }
            } else {
                newValues = newValues.filter(value => value !== "continue_iterate");
            }
            return newValues;
        }
        """,
        Output("risk-features-checklist", "value", allow_duplicate=True),
        Input("continue-iterate-checkbox", "value"),
        State("risk-features-checklist", "value"),
        prevent_initial_call=True
    )