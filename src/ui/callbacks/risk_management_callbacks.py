import dash
from dash import Input, Output, State, ALL, MATCH, callback_context, ClientsideFunction
import dash_bootstrap_components as dbc
from typing import Dict, Any
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

def register_risk_management_callbacks(app: dash.Dash) -> None:
    """
    Register all risk management callbacks with the application
    
    Args:
        app: The Dash application
    """
    # Panel visibility callback
    @app.callback(
        [
            Output("position_sizing-panel", "style"),
            Output("stop_loss-panel", "style"),
            Output("take_profit-panel", "style"),
            Output("risk_per_trade-panel", "style"),
            Output("market_filter-panel", "style"),
            Output("drawdown_protection-panel", "style")
        ],
        Input("risk-features-checklist", "value")
    )
    def update_panel_visibility(enabled_features):
        """Aktualizuje widoczność wszystkich paneli na podstawie listy włączonych funkcji"""
        features = [
            "position_sizing", "stop_loss", "take_profit", 
            "risk_per_trade", "market_filter", "drawdown_protection"
        ]
        
        # Domyślny styl - ukryty
        hidden_style = {"display": "none"}
        # Styl dla widocznych paneli
        visible_style = {"display": "block", "marginLeft": "20px", "marginBottom": "15px"}
        
        # Dla każdej funkcji sprawdzamy, czy jest włączona
        styles = []
        for feature in features:
            if enabled_features and feature in enabled_features:
                styles.append(visible_style)
            else:
                styles.append(hidden_style)
                
        return styles

    # BREAKING THE CIRCULAR DEPENDENCY:
    # Instead of having two callbacks updating each other, we'll use only one direction
    # and register a clientside callback for immediate UI feedback

    # Register clientside callback to sync checkboxes to the checklist for immediate UI feedback
    app.clientside_callback(
        ClientsideFunction(
            namespace='clientside',
            function_name='syncCheckboxesToList'
        ),
        [
            Output("position_sizing-checkbox", "value"),
            Output("stop_loss-checkbox", "value"),
            Output("take_profit-checkbox", "value"),
            Output("risk_per_trade-checkbox", "value"),
            Output("market_filter-checkbox", "value"),
            Output("drawdown_protection-checkbox", "value"),
            Output("continue-iterate-checkbox", "value")
        ],
        [Input("risk-features-checklist", "value")]
    )
    
    # Only keep one server-side callback that converts checkbox states to the list
    @app.callback(
        Output("risk-features-checklist", "value"),
        [
            Input("position_sizing-checkbox", "value"),
            Input("stop_loss-checkbox", "value"),
            Input("take_profit-checkbox", "value"),
            Input("risk_per_trade-checkbox", "value"),
            Input("market_filter-checkbox", "value"),
            Input("drawdown_protection-checkbox", "value"),
            Input("continue-iterate-checkbox", "value")
        ],
        # Prevent callback firing during initial load
        prevent_initial_call=True
    )
    def update_features_list(*checkbox_values):
        """Aktualizuje listę włączonych funkcji na podstawie stanów checkboxów"""
        features = [
            "position_sizing", "stop_loss", "take_profit", 
            "risk_per_trade", "market_filter", "drawdown_protection",
            "continue_iterate"
        ]
        
        # Get callback context to determine which checkbox triggered the callback
        ctx = callback_context
        if not ctx.triggered:
            return dash.no_update
            
        # Czysty zbiór wybranych funkcji
        selected_features = []
        
        # Dodajemy feature, jeśli odpowiadający checkbox jest zaznaczony
        for i, feature in enumerate(features):
            if i < len(checkbox_values) and checkbox_values[i]:
                selected_features.append(feature)
        
        return selected_features

    # Store the risk management configuration data
    @app.callback(
        Output('risk-management-store', 'data'),
        [
            Input('risk-features-checklist', 'value'),
            Input('max-position-size', 'value'),
            Input('max-portfolio-risk', 'value'),
            Input('stop-loss-type', 'value'),
            Input('stop-loss-value', 'value'),
            Input('take-profit-type', 'value'),
            Input('take-profit-value', 'value'),
            Input('max-risk-per-trade', 'value'),
            Input('risk-reward-ratio', 'value'),
            Input('market-trend-lookback', 'value'),
            Input('max-drawdown', 'value'),
            Input('max-daily-loss', 'value')
        ]
    )
    def update_risk_management_store(
        enabled_features, max_position_size, max_portfolio_risk,
        stop_loss_type, stop_loss_value, take_profit_type, take_profit_value,
        max_risk_per_trade, risk_reward_ratio, market_trend_lookback,
        max_drawdown, max_daily_loss
    ):
        """Store all risk management configuration in the risk-management-store"""
        risk_config = {
            "enabled_features": enabled_features or [],
            "position_sizing": {
                "max_position_size": max_position_size,
                "max_portfolio_risk": max_portfolio_risk
            },
            "stop_loss": {
                "type": stop_loss_type,
                "value": stop_loss_value
            },
            "take_profit": {
                "type": take_profit_type,
                "value": take_profit_value
            },
            "risk_per_trade": {
                "max_risk_per_trade": max_risk_per_trade,
                "risk_reward_ratio": risk_reward_ratio
            },
            "market_filter": {
                "trend_lookback": market_trend_lookback
            },
            "drawdown_protection": {
                "max_drawdown": max_drawdown,
                "max_daily_loss": max_daily_loss
            }
        }
        return risk_config