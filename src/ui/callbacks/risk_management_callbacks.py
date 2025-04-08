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
    
    # Register the clientside callback for toggling visibility of risk management sections
    clientside_callback(
        """
        function(checkedValues) {
            // Default style (hidden)
            const hiddenStyle = {display: 'none'};
            const visibleStyle = {display: 'block'};
            
            // Initialize all containers as hidden
            let positionSizingStyle = {...hiddenStyle};
            let stopLossStyle = {...hiddenStyle};
            let takeProfitStyle = {...hiddenStyle};
            let riskPerTradeStyle = {...hiddenStyle};
            let marketFilterStyle = {...hiddenStyle};
            let drawdownProtectionStyle = {...hiddenStyle};
            
            // Show containers based on checklist values
            if(checkedValues.includes('position_sizing')) {
                positionSizingStyle = {...visibleStyle};
            }
            
            if(checkedValues.includes('stop_loss')) {
                stopLossStyle = {...visibleStyle};
            }
            
            if(checkedValues.includes('take_profit')) {
                takeProfitStyle = {...visibleStyle};
            }
            
            if(checkedValues.includes('risk_per_trade')) {
                riskPerTradeStyle = {...visibleStyle};
            }
            
            if(checkedValues.includes('market_filter')) {
                marketFilterStyle = {...visibleStyle};
            }
            
            if(checkedValues.includes('drawdown_protection')) {
                drawdownProtectionStyle = {...visibleStyle};
            }
            
            return [
                positionSizingStyle,
                stopLossStyle,
                takeProfitStyle,
                riskPerTradeStyle,
                marketFilterStyle,
                drawdownProtectionStyle
            ];
        }
        """,
        [Output('position-sizing-container', 'style'),
         Output('stop-loss-container', 'style'),
         Output('take-profit-container', 'style'),
         Output('risk-per-trade-container', 'style'),
         Output('market-filter-container', 'style'),
         Output('drawdown-protection-container', 'style')],
        [Input('risk-features-checklist', 'value')],
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