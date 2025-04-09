import dash
from dash import Input, Output, State, clientside_callback
from dash.dependencies import ClientsideFunction
import json
import logging

# Configure logger
logger = logging.getLogger(__name__)

def register_risk_management_callbacks(app: dash.Dash) -> None:
    """
    Register all risk management related callbacks.
    
    Args:
        app: The Dash application instance
    """
    logger.info("Registering risk management callbacks")
    
    # Create callbacks for toggling the visibility of each container
    features = [
        "position_sizing",
        "stop_loss",
        "take_profit",
        "risk_per_trade",
        "market_filter",
        "drawdown_protection"
    ]
    
    for i, feature in enumerate(features):
        # Register clientside callback for each feature checkbox
        clientside_callback(
            f"""
            function(isChecked) {{
                return isChecked.length > 0 ? {{"display": "block", "marginLeft": "20px", "marginBottom": "15px"}} : {{"display": "none"}};
            }}
            """,
            Output(f"{feature}-container", "style"),
            Input(f"{feature}-checkbox", "value"),
            prevent_initial_call=False
        )
        
        # Also update the hidden combined checklist to maintain compatibility with existing code
        clientside_callback(
            f"""
            function(isChecked, currentValues) {{
                let newValues = currentValues || [];
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
            Output("risk-features-checklist", "value", allow_duplicate=True),
            Input(f"{feature}-checkbox", "value"),
            State("risk-features-checklist", "value"),
            prevent_initial_call=True
        )
    
    # Special handling for continue_iterate checkbox
    clientside_callback(
        """
        function(isChecked, currentValues) {
            let newValues = currentValues || [];
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
    
    # Sync from hidden checklist back to individual checkboxes (for initializing from saved state)
    for feature in features:
        clientside_callback(
            f"""
            function(combinedValues) {{
                return combinedValues.includes("{feature}") ? ["{feature}"] : [];
            }}
            """,
            Output(f"{feature}-checkbox", "value"),
            Input("risk-features-checklist", "value"),
            prevent_initial_call=False
        )
    
    # Sync the continue_iterate checkbox
    clientside_callback(
        """
        function(combinedValues) {
            return combinedValues.includes("continue_iterate") ? ["continue_iterate"] : [];
        }
        """,
        Output("continue-iterate-checkbox", "value"),
        Input("risk-features-checklist", "value"),
        prevent_initial_call=False
    )

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