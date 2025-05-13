import dash
from dash import Input, Output, State, ALL, MATCH, callback_context, ClientsideFunction, no_update
import dash_bootstrap_components as dbc
from typing import Dict, Any, List
import json
import logging

# Import centralized IDs
from src.ui.ids.ids import StrategyConfigIDs

# Configure logging
logger = logging.getLogger(__name__)

def register_risk_management_callbacks(app: dash.Dash) -> None:
    """
    Register all risk management callbacks with the application

    Args:
        app: The Dash application
    """
    # Panel visibility callback (This one is correct, depends only on the checklist)
    @app.callback(
        [
            Output(StrategyConfigIDs.POSITION_SIZING_PANEL_ALT, "style"),
            Output(StrategyConfigIDs.STOP_LOSS_PANEL_ALT, "style"),
            Output(StrategyConfigIDs.TAKE_PROFIT_PANEL_ALT, "style"),
            Output(StrategyConfigIDs.RISK_PER_TRADE_PANEL_ALT, "style"),
            Output(StrategyConfigIDs.MARKET_FILTER_PANEL_ALT, "style"),
            Output(StrategyConfigIDs.DRAWDOWN_PROTECTION_PANEL_ALT, "style")
        ],
        Input(StrategyConfigIDs.RISK_FEATURES_CHECKLIST_ALT, "value"),
         prevent_initial_call=True # Good practice
    )
    def update_panel_visibility(enabled_features: List[str]):
        """Aktualizuje widoczność paneli na podstawie listy włączonych funkcji"""
        logger.debug(f"Updating panel visibility based on features: {enabled_features}")
        features = [
            "position_sizing", "stop_loss", "take_profit",
            "risk_per_trade", "market_filter", "drawdown_protection"
        ]

        # Default style - hidden
        hidden_style = {"display": "none"}
        # Style for visible panels
        visible_style = {"display": "block", "marginLeft": "20px", "marginBottom": "15px"}

        # Ensure enabled_features is a list
        if enabled_features is None:
            enabled_features = []

        # For each feature check if it's enabled
        styles = []
        for feature in features:
            if feature in enabled_features:
                styles.append(visible_style)
            else:
                styles.append(hidden_style)

        return styles

    # Register clientside callback to sync checkboxes TO the checklist value
    # This makes the UI checkboxes reflect the master list state immediately.
    app.clientside_callback(
        ClientsideFunction(
            namespace='clientside',
            function_name='syncCheckboxesToList'
        ),
        [
            # Outputs are the individual checkboxes
            Output(StrategyConfigIDs.POSITION_SIZING_CHECKBOX_ALT, "value"),
            Output(StrategyConfigIDs.STOP_LOSS_CHECKBOX_ALT, "value"),
            Output(StrategyConfigIDs.TAKE_PROFIT_CHECKBOX_ALT, "value"),
            Output(StrategyConfigIDs.RISK_PER_TRADE_CHECKBOX_ALT, "value"),
            Output(StrategyConfigIDs.MARKET_FILTER_CHECKBOX_ALT, "value"),
            Output(StrategyConfigIDs.DRAWDOWN_PROTECTION_CHECKBOX_ALT, "value"),
            Output(StrategyConfigIDs.CONTINUE_ITERATE_CHECKBOX_ALT, "value") # Assuming this exists
        ],
        # Input is the master checklist
        [Input(StrategyConfigIDs.RISK_FEATURES_CHECKLIST_ALT, "value")],
         # prevent_initial_call=False # Allow initial sync
    )
    logger.debug("Registered clientside callback syncCheckboxesToList")

    # Server-side callback to update the checklist FROM the checkboxes
    # This is the one causing the loop. It should ONLY update the checklist.
    @app.callback(
        Output(StrategyConfigIDs.RISK_FEATURES_CHECKLIST_ALT, "value"), # Output is ONLY the checklist
        [
            # Inputs are the individual checkboxes
            Input(StrategyConfigIDs.POSITION_SIZING_CHECKBOX_ALT, "value"),
            Input(StrategyConfigIDs.STOP_LOSS_CHECKBOX_ALT, "value"),
            Input(StrategyConfigIDs.TAKE_PROFIT_CHECKBOX_ALT, "value"),
            Input(StrategyConfigIDs.RISK_PER_TRADE_CHECKBOX_ALT, "value"),
            Input(StrategyConfigIDs.MARKET_FILTER_CHECKBOX_ALT, "value"),
            Input(StrategyConfigIDs.DRAWDOWN_PROTECTION_CHECKBOX_ALT, "value"),
            Input(StrategyConfigIDs.CONTINUE_ITERATE_CHECKBOX_ALT, "value") # Assuming this exists
        ],
        State(StrategyConfigIDs.RISK_FEATURES_CHECKLIST_ALT, "value"), # Get current checklist value as State
        prevent_initial_call=True # Prevent firing on load
    )
    def update_features_list_from_checkboxes(*args):
        """Aktualizuje listę włączonych funkcji na podstawie *zmienionego* checkboxa"""
        # The last argument is the current state of risk-features-checklist
        current_checklist_value = args[-1] if args[-1] is not None else []
        # The preceding arguments are the values of the input checkboxes
        checkbox_values = args[:-1]

        features_order = [
            "position_sizing", "stop_loss", "take_profit",
            "risk_per_trade", "market_filter", "drawdown_protection",
            "continue_iterate" # Assuming this exists
        ]

        ctx = callback_context
        if not ctx.triggered:
            logger.debug("update_features_list_from_checkboxes: No trigger, no update.")
            return no_update

        # Identify which checkbox triggered the callback
        trigger_prop_id = ctx.triggered[0]['prop_id']
        logger.debug(f"update_features_list_from_checkboxes triggered by: {trigger_prop_id}")

        # Rebuild the list based ONLY on the checkbox states
        selected_features = []
        for i, feature in enumerate(features_order):
             # Checkbox value is truthy (e.g., [feature_name] or True) if checked
            if i < len(checkbox_values) and checkbox_values[i]:
                selected_features.append(feature)

        # Only update if the calculated list is different from the current state
        # This helps prevent unnecessary updates and potential loops if state matches
        if set(selected_features) != set(current_checklist_value):
            logger.debug(f"Updating risk-features-checklist from checkboxes: {selected_features}")
            return selected_features
        else:
            logger.debug("Checkbox change resulted in same feature list, no update needed.")
            return no_update


    # Store the risk management configuration data (This seems fine)
    @app.callback(
        Output(StrategyConfigIDs.RISK_MANAGEMENT_STORE_ALT, 'data'),
        [
            Input(StrategyConfigIDs.RISK_FEATURES_CHECKLIST_ALT, 'value'),
            Input(StrategyConfigIDs.MAX_POSITION_SIZE_ALT, 'value'),
            Input(StrategyConfigIDs.MAX_PORTFOLIO_RISK_ALT, 'value'),
            Input(StrategyConfigIDs.STOP_LOSS_TYPE_ALT, 'value'),
            Input(StrategyConfigIDs.STOP_LOSS_VALUE_ALT, 'value'),
            Input(StrategyConfigIDs.TAKE_PROFIT_TYPE_ALT, 'value'),
            Input(StrategyConfigIDs.TAKE_PROFIT_VALUE_ALT, 'value'),
            Input(StrategyConfigIDs.MAX_RISK_PER_TRADE_ALT, 'value'),
            Input(StrategyConfigIDs.RISK_REWARD_RATIO_ALT, 'value'),
            Input(StrategyConfigIDs.MARKET_TREND_LOOKBACK_ALT, 'value'),
            Input(StrategyConfigIDs.MAX_DRAWDOWN_ALT, 'value'),
            Input(StrategyConfigIDs.MAX_DAILY_LOSS_ALT, 'value')
        ],
         prevent_initial_call=True # Good practice
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
        # Consider adding validation here before returning
        return risk_config
