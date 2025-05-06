import dash
from dash import Input, Output, State, ALL, MATCH, callback_context, ClientsideFunction, no_update
import dash_bootstrap_components as dbc
from typing import Dict, Any, List
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

from src.ui.ids.ids import WizardIDs # ADDED IMPORT

def register_risk_management_callbacks(app: dash.Dash) -> None:
    """
    Register all risk management callbacks with the application

    Args:
        app: The Dash application
    """
    logger.info("Registering risk management callbacks...") # Add log

    # Panel visibility callback (Depends only on the checklist - should be fine)
    @app.callback(
        [
            Output(WizardIDs.RISK_PANEL_POSITION_SIZING, "style"),
            Output(WizardIDs.RISK_PANEL_STOP_LOSS, "style"),
            Output(WizardIDs.RISK_PANEL_TAKE_PROFIT, "style"),
            Output(WizardIDs.RISK_PANEL_RISK_PER_TRADE, "style"),
            Output(WizardIDs.RISK_PANEL_MARKET_FILTER, "style"),
            Output(WizardIDs.RISK_PANEL_DRAWDOWN_PROTECTION, "style")
        ],
        Input(WizardIDs.RISK_FEATURES_CHECKLIST, "value"),
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

    # --- REMOVED/COMMENTED OUT CLIENTSIDE CALLBACK ---
    # app.clientside_callback(
    #     ClientsideFunction(
    #         namespace='clientside',
    #         function_name='syncCheckboxesToList'
    #     ),
    #     [
    #         Output("position_sizing-checkbox", "value"),
    #         Output("stop_loss-checkbox", "value"),
    #         Output("take_profit-checkbox", "value"),
    #         Output("risk_per_trade-checkbox", "value"),
    #         Output("market_filter-checkbox", "value"),
    #         Output("drawdown_protection-checkbox", "value"),
    #         Output("continue-iterate-checkbox", "value") # Assuming this exists
    #     ],
    #     [Input("risk-features-checklist", "value")],
    #     prevent_initial_call=True # This was added before, but removing the callback is cleaner
    # )
    # logger.debug("REMOVED clientside callback syncCheckboxesToList")
    # --- END OF REMOVED/COMMENTED OUT SECTION ---


    # Server-side callback to update the checklist FROM the checkboxes (Keep this)
    @app.callback(
        Output(WizardIDs.RISK_FEATURES_CHECKLIST, "value"),
        [
            # These inputs might be from a previous design. 
            # The current wizard layout (strategy_config.py) uses a single checklist (RISK_FEATURES_CHECKLIST)
            # and then specific input fields for each selected feature. 
            # These individual checkboxes (e.g., "position_sizing-checkbox") are not defined with WizardIDs.
            # This callback might need to be re-evaluated or removed if these checkboxes no longer exist.
            # For now, I will leave them as string literals as they don't have WizardID counterparts.
            Input("position_sizing-checkbox", "value"),
            Input("stop_loss-checkbox", "value"),
            Input("take_profit-checkbox", "value"),
            Input("risk_per_trade-checkbox", "value"),
            Input("market_filter-checkbox", "value"),
            Input("drawdown_protection-checkbox", "value"),
            Input("continue-iterate-checkbox", "value") # Assuming this exists
        ],
        State(WizardIDs.RISK_FEATURES_CHECKLIST, "value"),
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

        # Rebuild the list based ONLY on the checkbox states
        selected_features = []
        for i, feature in enumerate(features_order):
             # Checkbox value is truthy (e.g., [feature_name] or True) if checked
            if i < len(checkbox_values) and checkbox_values[i]:
                selected_features.append(feature)

        # Only update if the calculated list is different from the current state
        if set(selected_features) != set(current_checklist_value):
            logger.debug(f"Updating risk-features-checklist from checkboxes: {selected_features}")
            return selected_features
        else:
            logger.debug("Checkbox change resulted in same feature list, no update needed.")
            return no_update


    # Store the risk management configuration data (Keep this)
    @app.callback(
        Output(WizardIDs.RISK_MANAGEMENT_STORE_WIZARD, 'data'), # UPDATED to Wizard Store ID
        [
            Input(WizardIDs.RISK_FEATURES_CHECKLIST, 'value'),
            Input(WizardIDs.MAX_POSITION_SIZE_INPUT, 'value'),
            # 'max-portfolio-risk' is not in WizardIDs or strategy_config.py layout for the wizard
            # Input('max-portfolio-risk', 'value'), # Placeholder, needs to be added to WizardIDs and layout if used
            Input(WizardIDs.STOP_LOSS_TYPE_SELECT, 'value'),
            Input(WizardIDs.STOP_LOSS_INPUT, 'value'),
            Input(WizardIDs.TAKE_PROFIT_TYPE_SELECT, 'value'),
            Input(WizardIDs.TAKE_PROFIT_INPUT, 'value'),
            Input(WizardIDs.MAX_RISK_PER_TRADE_INPUT, 'value'),
            # 'risk-reward-ratio' is not in WizardIDs or strategy_config.py layout for the wizard
            # Input('risk-reward-ratio', 'value'), # Placeholder, needs to be added to WizardIDs and layout if used
            Input(WizardIDs.MARKET_TREND_LOOKBACK_INPUT, 'value'),
            Input(WizardIDs.MAX_DRAWDOWN_INPUT, 'value'),
            Input(WizardIDs.MAX_DAILY_LOSS_INPUT, 'value')
        ],
         prevent_initial_call=True
    )
    def update_risk_management_store(
        enabled_features, max_position_size, # max_portfolio_risk, # Commented out as per above
        stop_loss_type, stop_loss_value, take_profit_type, take_profit_value,
        max_risk_per_trade, # risk_reward_ratio, # Commented out as per above
        market_trend_lookback, max_drawdown, max_daily_loss
    ):
        """Store all risk management configuration in the risk-management-store"""
        logger.debug("Updating risk-management-store")
        risk_config = {
            "enabled_features": enabled_features or [],
            "position_sizing": {"max_position_size": max_position_size, "max_portfolio_risk": None}, # Set max_portfolio_risk to None
            "stop_loss": {"type": stop_loss_type, "value": stop_loss_value},
            "take_profit": {"type": take_profit_type, "value": take_profit_value},
            "risk_per_trade": {"max_risk_per_trade": max_risk_per_trade, "risk_reward_ratio": None}, # Set risk_reward_ratio to None
            "market_filter": {"trend_lookback": market_trend_lookback},
            "drawdown_protection": {"max_drawdown": max_drawdown, "max_daily_loss": max_daily_loss}
        }
        return risk_config

    logger.info("Risk management callbacks registered.") # Add log
