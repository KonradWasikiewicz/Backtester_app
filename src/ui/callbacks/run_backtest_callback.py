import dash
from dash import Dash, Input, Output, State, ctx
import logging
import time
from src.ui.ids.ids import WizardIDs, SharedComponentIDs, StrategyConfigIDs

# Configure logging
logger = logging.getLogger(__name__)

def register_run_backtest_callback(app: Dash):
    """
    Register the callback that connects the Run Backtest button in the wizard
    to the backtest trigger store.
    """
    logger.info("Registering Run Backtest button callback...")
    
    @app.callback(
        Output(SharedComponentIDs.RUN_BACKTEST_TRIGGER_STORE, 'data'),
        Input(WizardIDs.RUN_BACKTEST_BUTTON_WIZARD, 'n_clicks'),
        State(StrategyConfigIDs.STRATEGY_CONFIG_STORE_MAIN, 'data'),
        prevent_initial_call=True
    )
    def on_run_backtest_button_clicked(n_clicks, config_data):
        """
        When the Run Backtest button is clicked, trigger the backtest by updating
        the RUN_BACKTEST_TRIGGER_STORE with the current timestamp.
        """
        if not n_clicks:
            return dash.no_update
            
        logger.info(f"Run Backtest button clicked. Triggering backtest with config: {config_data}")
        
        # Return a trigger value (timestamp) that the backtest callback listens for
        return {"timestamp": time.time(), "source": "wizard"}
