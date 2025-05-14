# Update main configuration store when wizard summary is shown
import dash
from dash import Input, Output, State, ctx, no_update
import logging
from src.ui.ids.ids import WizardIDs, StrategyConfigIDs
from src.core.constants import DEFAULT_STRATEGY_PARAMS

logger = logging.getLogger(__name__)

def register_config_update_callback(app):
    """
    Register a callback to update the main configuration store when the wizard summary is shown.
    This ensures the main configuration is ready when the Run Backtest button is clicked.
    """
    logger.info("Registering wizard config update callback...")
    
    @app.callback(
        Output(StrategyConfigIDs.STRATEGY_CONFIG_STORE_MAIN, 'data', allow_duplicate=True),
        [Input(WizardIDs.step_content("wizard-summary"), "style")],
        [
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
            State(WizardIDs.REBALANCING_THRESHOLD_INPUT, "value"),
            # Include the current config data to preserve any additional fields not set by the wizard
            State(StrategyConfigIDs.STRATEGY_CONFIG_STORE_MAIN, "data"),
        ],
        prevent_initial_call=True
    )
    def update_main_config_store(summary_style, strategy_type, initial_capital, start_date, end_date, 
                                tickers, max_position_size, stop_loss, take_profit, commission, 
                                slippage, rebalancing_frequency, rebalancing_threshold, current_config):
        """
        Update the main configuration store when the wizard summary is shown.
        This ensures the main configuration is ready when the Run Backtest button is clicked.
        """
        # If the summary is not visible, don't update
        if summary_style is None or summary_style.get("display") == "none":
            logger.debug("update_main_config_store: Summary not visible, not updating main config store")
            return dash.no_update
        
        # Start with the current config if it exists (to preserve any fields)
        config_data = current_config or {}
        
        # Extract default strategy parameters
        strategy_params = {}
        if strategy_type and strategy_type in DEFAULT_STRATEGY_PARAMS:
            strategy_params = DEFAULT_STRATEGY_PARAMS[strategy_type]
        
        # Update with the wizard values
        config_data.update({
            "strategy_type": strategy_type,
            "initial_capital": initial_capital,
            "start_date": start_date,
            "end_date": end_date,
            "tickers": tickers,
            "strategy_params": strategy_params,
            "risk_management": {
                "max_position_size": max_position_size,
                "stop_loss": stop_loss,
                "take_profit": take_profit
            },
            "trading_costs": {
                "commission_bps": commission,
                "slippage_bps": slippage
            },
            "rebalancing": {
                "frequency": rebalancing_frequency,
                "threshold_pct": rebalancing_threshold
            }
        })
        
        logger.info(f"Updated main configuration store with wizard data: {config_data}")
        return config_data
