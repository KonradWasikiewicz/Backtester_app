# (Keep imports and other callbacks as they were in the previous correct version)
import dash
from dash import Input, Output, State, ALL, MATCH, callback_context, ClientsideFunction, no_update
import dash_bootstrap_components as dbc
from typing import Dict, Any, List
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
    logger.info("Registering risk management callbacks...") # Add log

    # Panel visibility callback (Should be correct)
    @app.callback(
        [
            Output("position_sizing-panel", "style"),
            Output("stop_loss-panel", "style"),
            Output("take_profit-panel", "style"),
            Output("risk_per_trade-panel", "style"),
            Output("market_filter-panel", "style"),
            Output("drawdown_protection-panel", "style")
        ],
        Input("risk-features-checklist", "value"),
         prevent_initial_call=True
    )
    def update_panel_visibility(enabled_features: List[str]):
        """Aktualizuje widoczność paneli na podstawie listy włączonych funkcji"""
        logger.debug(f"Updating panel visibility based on features: {enabled_features}")
        features = [
            "position_sizing", "stop_loss", "take_profit",
            "risk_per_trade", "market_filter", "drawdown_protection"
        ]
        hidden_style = {"display": "none"}
        visible_style = {"display": "block", "marginLeft": "20px", "marginBottom": "15px"}
        if enabled_features is None: enabled_features = []
        styles = [visible_style if feature in enabled_features else hidden_style for feature in features]
        return styles

    # Register clientside callback to sync checkboxes TO the checklist value
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
            Output("continue-iterate-checkbox", "value") # Assuming this exists
        ],
        [Input("risk-features-checklist", "value")],
        # --- ADDED prevent_initial_call=True ---
        # Prevent client sync on initial load to avoid conflict with server
        prevent_initial_call=True
    )
    logger.debug("Registered clientside callback syncCheckboxesToList with prevent_initial_call=True")

    # Server-side callback to update the checklist FROM the checkboxes (Should be correct)
    @app.callback(
        Output("risk-features-checklist", "value"),
        [
            Input("position_sizing-checkbox", "value"),
            Input("stop_loss-checkbox", "value"),
            Input("take_profit-checkbox", "value"),
            Input("risk_per_trade-checkbox", "value"),
            Input("market_filter-checkbox", "value"),
            Input("drawdown_protection-checkbox", "value"),
            Input("continue-iterate-checkbox", "value") # Assuming this exists
        ],
        State("risk-features-checklist", "value"),
        prevent_initial_call=True
    )
    def update_features_list_from_checkboxes(*args):
        """Aktualizuje listę włączonych funkcji na podstawie *zmienionego* checkboxa"""
        current_checklist_value = args[-1] if args[-1] is not None else []
        checkbox_values = args[:-1]
        features_order = [
            "position_sizing", "stop_loss", "take_profit",
            "risk_per_trade", "market_filter", "drawdown_protection",
            "continue_iterate" # Assuming this exists
        ]
        ctx = callback_context
        if not ctx.triggered: return no_update
        trigger_prop_id = ctx.triggered[0]['prop_id']
        logger.debug(f"update_features_list_from_checkboxes triggered by: {trigger_prop_id}")
        selected_features = [features_order[i] for i, val in enumerate(checkbox_values) if i < len(features_order) and val]
        if set(selected_features) != set(current_checklist_value):
            logger.debug(f"Updating risk-features-checklist from checkboxes: {selected_features}")
            return selected_features
        else:
            logger.debug("Checkbox change resulted in same feature list, no update needed.")
            return no_update

    # Store the risk management configuration data (Should be correct)
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
        ],
         prevent_initial_call=True
    )
    def update_risk_management_store(
        enabled_features, max_position_size, max_portfolio_risk,
        stop_loss_type, stop_loss_value, take_profit_type, take_profit_value,
        max_risk_per_trade, risk_reward_ratio, market_trend_lookback,
        max_drawdown, max_daily_loss
    ):
        """Store all risk management configuration in the risk-management-store"""
        logger.debug("Updating risk-management-store")
        risk_config = {
            "enabled_features": enabled_features or [],
            "position_sizing": {"max_position_size": max_position_size, "max_portfolio_risk": max_portfolio_risk},
            "stop_loss": {"type": stop_loss_type, "value": stop_loss_value},
            "take_profit": {"type": take_profit_type, "value": take_profit_value},
            "risk_per_trade": {"max_risk_per_trade": max_risk_per_trade, "risk_reward_ratio": risk_reward_ratio},
            "market_filter": {"trend_lookback": market_trend_lookback},
            "drawdown_protection": {"max_drawdown": max_drawdown, "max_daily_loss": max_daily_loss}
        }
        return risk_config

    logger.info("Risk management callbacks registered.") # Add log