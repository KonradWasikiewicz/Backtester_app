from dash import Input, Output, State, callback_context, dash, exceptions
import dash_bootstrap_components as dbc
import logging
from typing import Dict, List, Any
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)

# Import local modules
from src.core.constants import AVAILABLE_STRATEGIES
from src.core.data import DataLoader
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
            # Get available tickers from the DataLoader
            data_loader = DataLoader()
            available_tickers = data_loader.get_available_tickers()
            logger.info(f"Found {len(available_tickers)} tickers for UI: {available_tickers[:5]}...")
            return create_risk_management_section(available_tickers)
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
    
    # Date range selection callbacks
    @app.callback(
        [Output("date-slider-container", "style"),
         Output("manual-date-container", "style")],
        [Input("manual-date-toggle", "value")]
    )
    def toggle_date_input_method(use_manual):
        """
        Toggle between date range slider and manual date picker.
        
        Args:
            use_manual: Whether to use manual date picker
            
        Returns:
            Styles for the date slider and manual date picker containers
        """
        if use_manual:
            return {"display": "none"}, {"display": "block"}
        else:
            return {"display": "block"}, {"display": "none"}
    
    @app.callback(
        [Output("selected-start-date", "children"),
         Output("selected-end-date", "children"),
         Output("backtest-daterange", "start_date"),
         Output("backtest-daterange", "end_date")],
        [Input("backtest-date-slider", "value")]
    )
    def update_selected_dates(date_range_timestamps):
        """
        Update the display of selected dates from the slider and synchronize with date picker.
        
        Args:
            date_range_timestamps: List of [start_timestamp, end_timestamp] from the slider
            
        Returns:
            Formatted start and end dates for display and date picker
        """
        if not date_range_timestamps or len(date_range_timestamps) != 2:
            return "N/A", "N/A", None, None
        
        try:
            # Convert timestamps (ms) back to datetime
            start_ts, end_ts = date_range_timestamps
            start_date = pd.to_datetime(start_ts, unit='ms')
            end_date = pd.to_datetime(end_ts, unit='ms')
            
            # Format for display
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            return start_date_str, end_date_str, start_date_str, end_date_str
        except Exception as e:
            logger.error(f"Error converting date range timestamps: {e}")
            return "Error", "Error", None, None
    
    @app.callback(
        Output("backtest-date-slider", "value"),
        [Input("backtest-daterange", "start_date"),
         Input("backtest-daterange", "end_date")]
    )
    def update_date_slider_from_picker(start_date_str, end_date_str):
        """
        Update the date slider when manual date picker changes.
        
        Args:
            start_date_str: Start date string from date picker
            end_date_str: End date string from date picker
            
        Returns:
            List of [start_timestamp, end_timestamp] for the slider
        """
        ctx = callback_context
        if not ctx.triggered or (not start_date_str or not end_date_str):
            # Don't update if this is the initial load or dates are not set
            raise dash.exceptions.PreventUpdate
        
        try:
            # Convert date strings to timestamps
            start_date = pd.to_datetime(start_date_str)
            end_date = pd.to_datetime(end_date_str)
            
            start_ts = int(start_date.timestamp() * 1000)
            end_ts = int(end_date.timestamp() * 1000)
            
            return [start_ts, end_ts]
        except Exception as e:
            logger.error(f"Error updating slider from date picker: {e}")
            raise dash.exceptions.PreventUpdate