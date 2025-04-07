from dash import Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import logging
from typing import Dict, List, Any

# Configure logging
logger = logging.getLogger(__name__)

# Import local modules
from src.core.constants import AVAILABLE_STRATEGIES
from src.ui.layouts.strategy_config import generate_strategy_parameters
from src.ui.layouts.risk_management import create_risk_management_section

def register_strategy_callbacks(app):
    """
    Register all strategy-related callbacks with the Dash app.
    
    Args:
        app: The Dash application instance
    """
    
    @app.callback(
        Output("strategy-parameters-container", "children"),
        Input("strategy-selector", "value")
    )
    def update_strategy_parameters(strategy_type):
        """
        Update the strategy parameters UI when a strategy is selected.
        
        Args:
            strategy_type: Selected strategy type
            
        Returns:
            HTML component with strategy parameters
        """
        if not strategy_type or strategy_type not in AVAILABLE_STRATEGIES:
            return "Please select a valid strategy."
        
        try:
            strategy_class = AVAILABLE_STRATEGIES[strategy_type]
            return generate_strategy_parameters(strategy_class)
        except Exception as e:
            logger.error(f"Error updating strategy parameters: {e}", exc_info=True)
            return f"Error loading parameters: {str(e)}"
    
    @app.callback(
        Output("risk-management-container", "children"),
        Input("strategy-selector", "value")
    )
    def update_risk_management(strategy_type):
        """
        Update the risk management UI when a strategy is selected.
        
        Args:
            strategy_type: Selected strategy type
            
        Returns:
            HTML component with risk management form
        """
        if not strategy_type:
            return "Please select a strategy first."
        
        try:
            return create_risk_management_section()
        except Exception as e:
            logger.error(f"Error updating risk management UI: {e}", exc_info=True)
            return f"Error loading risk management: {str(e)}"
    
    @app.callback(
        [Output("stop-loss-value", "disabled"), 
         Output("stop-loss-value", "value")],
        Input("stop-loss-selector", "value")
    )
    def toggle_stop_loss(stop_loss_type):
        """
        Enable/disable stop loss value input based on selected type.
        
        Args:
            stop_loss_type: Selected stop loss type
            
        Returns:
            Tuple with disabled status and value
        """
        if stop_loss_type == "none":
            return True, 0.0
        elif stop_loss_type == "percent":
            return False, 5.0
        elif stop_loss_type == "atr":
            return False, 2.0
        return False, 5.0
    
    @app.callback(
        [Output("risk-per-trade", "disabled"),
         Output("risk-per-trade", "value")],
        Input("position-sizing-selector", "value")
    )
    def toggle_position_sizing(position_sizing):
        """
        Adjust risk per trade input based on position sizing method.
        
        Args:
            position_sizing: Selected position sizing method
            
        Returns:
            Tuple with disabled status and value
        """
        if position_sizing == "equal":
            return True, 0.0
        elif position_sizing == "fixed_dollar":
            return False, 1000.0  # Default to $1000 per position
        elif position_sizing == "percent":
            return False, 2.0  # Default to 2% risk per trade
        elif position_sizing == "volatility":
            return False, 1.0  # Default to 1x ATR risk
        return False, 2.0