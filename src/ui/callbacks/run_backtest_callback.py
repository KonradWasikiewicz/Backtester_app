import dash
from dash import Dash, Input, Output, State, ctx
import logging
import time
from src.ui.ids.ids import WizardIDs, SharedComponentIDs, StrategyConfigIDs
from src.core.constants import DEFAULT_STRATEGY_PARAMS

# Configure logging
logger = logging.getLogger(__name__)

def register_run_backtest_callback(app: Dash):
    """
    Register the callback that connects the Run Backtest button in the wizard
    to the backtest trigger store.
    """
    logger.info("Registering Run Backtest button callback...")
    
    @app.callback(
        [
            Output(StrategyConfigIDs.STRATEGY_CONFIG_STORE_MAIN, 'data', allow_duplicate=True),
            Output(SharedComponentIDs.RUN_BACKTEST_TRIGGER_STORE, 'data')
        ],
        Input(WizardIDs.RUN_BACKTEST_BUTTON_WIZARD, 'n_clicks'),
        [
            State(StrategyConfigIDs.STRATEGY_CONFIG_STORE_MAIN, 'data'),
            State(WizardIDs.STRATEGY_DROPDOWN, "value"),
            State(WizardIDs.INITIAL_CAPITAL_INPUT, "value"),
            State(WizardIDs.DATE_RANGE_START_PICKER, "date"),
            State(WizardIDs.DATE_RANGE_END_PICKER, "date"),
            State(WizardIDs.TICKER_DROPDOWN, "value"),
            State(WizardIDs.MAX_POSITION_SIZE_INPUT, "value"),
            State(WizardIDs.STOP_LOSS_INPUT, "value"),
            State(WizardIDs.TAKE_PROFIT_INPUT, "value"),
            State(WizardIDs.COMMISSION_INPUT, "value"),
            State(WizardIDs.SLIPPAGE_INPUT, "value"),
            State(WizardIDs.REBALANCING_FREQUENCY_DROPDOWN, "value"),
            State(WizardIDs.REBALANCING_THRESHOLD_INPUT, "value")        ],
        prevent_initial_call=True
    )
    def on_run_backtest_button_clicked(n_clicks, current_config, strategy_type, initial_capital, 
                                      start_date, end_date, ticker, max_position_size, 
                                      stop_loss, take_profit, commission, slippage, 
                                      rebalancing_frequency, rebalancing_threshold):
        """
        When the Run Backtest button is clicked:
        1. Update the main config store with the latest wizard values
        2. Trigger the backtest by updating the RUN_BACKTEST_TRIGGER_STORE with the current timestamp
        """
        if not n_clicks:
            return dash.no_update, dash.no_update
        
        # Create or update the configuration
        config_data = current_config or {}
        
        # Get strategy parameters from defaults
        strategy_params = {}
        if strategy_type and strategy_type in DEFAULT_STRATEGY_PARAMS:
            strategy_params = DEFAULT_STRATEGY_PARAMS[strategy_type]
          # Safe conversion of numeric inputs with error handling
        try:
            # Remove spaces from initial_capital and other numeric fields if needed
            def sanitize_num(val):
                if isinstance(val, str):
                    return float(val.replace(' ', ''))
                return float(val) if val is not None else None
            initial_capital_value = sanitize_num(initial_capital) if initial_capital else None
            max_position_size_value = sanitize_num(max_position_size) if max_position_size else None
            stop_loss_value = sanitize_num(stop_loss) if stop_loss else None
            take_profit_value = sanitize_num(take_profit) if take_profit else None
            commission_value = sanitize_num(commission) if commission else None
            slippage_value = sanitize_num(slippage) if slippage else None
            threshold_value = sanitize_num(rebalancing_threshold) if rebalancing_threshold else None
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to convert numeric values: {e}. Using None for invalid values.")
            initial_capital_value = None if not isinstance(initial_capital, (int, float)) else initial_capital
            max_position_size_value = None if not isinstance(max_position_size, (int, float)) else max_position_size
            stop_loss_value = None if not isinstance(stop_loss, (int, float)) else stop_loss
            take_profit_value = None if not isinstance(take_profit, (int, float)) else take_profit
            commission_value = None if not isinstance(commission, (int, float)) else commission
            slippage_value = None if not isinstance(slippage, (int, float)) else slippage
            threshold_value = None if not isinstance(rebalancing_threshold, (int, float)) else rebalancing_threshold
        
        # Update with the wizard values
        config_data.update({            "strategy_type": strategy_type,
            "initial_capital": initial_capital_value,
            "start_date": start_date,
            "end_date": end_date,
            "tickers": [ticker] if ticker else [],
            "strategy_params": strategy_params,            "risk_management": {
                "max_position_size": max_position_size_value,
                "stop_loss": stop_loss_value,
                "take_profit": take_profit_value
            },            "trading_costs": {
                "commission_bps": commission_value,
                "slippage_bps": slippage_value
            },            "rebalancing": {
                "frequency": rebalancing_frequency,
                "threshold_pct": threshold_value
            }
        })
        
        # Log what we're doing
        logger.info(f"Run Backtest button clicked. Updated config and triggering backtest.")
        
        # Validate configuration has required fields
        required_fields = ["strategy_type", "tickers", "start_date", "end_date", "initial_capital"]
        missing_fields = [field for field in required_fields if field not in config_data or not config_data[field]]
        
        if missing_fields:
            logger.warning(f"Run Backtest button clicked but config_data is missing required fields: {missing_fields}")
        else:
            logger.info(f"Config validated successfully.")
            
        # Return both the updated config and the trigger value
        return config_data, {"timestamp": time.time(), "source": "wizard"}
