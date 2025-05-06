import dash
from dash import html, dcc, Input, Output, State, ALL, MATCH, ctx, no_update
from dash.exceptions import PreventUpdate # Added import
import logging
# Make sure logging is configured appropriately elsewhere (e.g., in app_factory or main app.py)
# from ...config.logging_config import setup_logging
from src.core.constants import STRATEGY_DESCRIPTIONS # Poprawna ścieżka do stałych
from src.core.constants import DEFAULT_STRATEGY_PARAMS  # added import for default params
from src.core.constants import AVAILABLE_STRATEGIES # Ensure this is imported
from src.ui.ids import WizardIDs, StrategyConfigIDs  # Import the centralized IDs and StrategyConfigIDs

logger = logging.getLogger(__name__)

def register_wizard_callbacks(app):
    """
    Register callbacks for the wizard interface, including step transitions and validation.
    """
    logger.info("Registering wizard callbacks...")

    # Removed duplicate strategy description callback (registered in strategy_callbacks)

    # --- Consolidated Step Transition Callback ---
    @app.callback(
        [
            # Step Content Visibility
            Output(WizardIDs.step_content("strategy-selection"), "style"),
            Output(WizardIDs.step_content("date-range-selection"), "style"),
            Output(WizardIDs.step_content("tickers-selection"), "style"),
            Output(WizardIDs.step_content("risk-management"), "style"),
            Output(WizardIDs.step_content("trading-costs"), "style"),
            Output(WizardIDs.step_content("rebalancing-rules"), "style"),
            Output(WizardIDs.step_content("wizard-summary"), "style"),
            # Header class toggles for each step
            Output(WizardIDs.step_header("strategy-selection"), "className"),
            Output(WizardIDs.step_header("date-range-selection"), "className"),
            Output(WizardIDs.step_header("tickers-selection"), "className"),
            Output(WizardIDs.step_header("risk-management"), "className"),
            Output(WizardIDs.step_header("trading-costs"), "className"),
            Output(WizardIDs.step_header("rebalancing-rules"), "className"),
            Output(WizardIDs.step_header("wizard-summary"), "className"),
            # --- UPDATED Progress Bar Output ID ---
            Output(WizardIDs.PROGRESS_BAR, "value"),
            # --- ADDED Progress Bar Style Output ---
            Output(WizardIDs.PROGRESS_BAR, "style")
        ],
        [
            # Confirm Buttons (Inputs) - Using centralized IDs for all wizard confirm buttons
            Input(WizardIDs.CONFIRM_STRATEGY_BUTTON, "n_clicks"),
            Input(WizardIDs.CONFIRM_DATES_BUTTON, "n_clicks"),
            Input(WizardIDs.CONFIRM_TICKERS_BUTTON, "n_clicks"),
            Input(WizardIDs.CONFIRM_RISK_BUTTON, "n_clicks"),
            Input(WizardIDs.CONFIRM_COSTS_BUTTON, "n_clicks"),
            Input(WizardIDs.CONFIRM_REBALANCING_BUTTON, "n_clicks"),
            # Step Headers (Inputs) - Using WizardID helper methods
            Input(WizardIDs.step_header("strategy-selection"), "n_clicks"),
            Input(WizardIDs.step_header("date-range-selection"), "n_clicks"),
            Input(WizardIDs.step_header("tickers-selection"), "n_clicks"),
            Input(WizardIDs.step_header("risk-management"), "n_clicks"),
            Input(WizardIDs.step_header("trading-costs"), "n_clicks"),
            Input(WizardIDs.step_header("rebalancing-rules"), "n_clicks"),
            Input(WizardIDs.step_header("wizard-summary"), "n_clicks")
        ],
        prevent_initial_call=True
    )
    def handle_step_transition(*args):
        """Handles navigation between wizard steps based on button or header clicks."""
        if not ctx.triggered:
            logger.warning("Step transition callback triggered without context.")
            return no_update

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        logger.info(f"Step transition triggered by: {trigger_id}")

        # Define step indices
        steps = [
            "strategy-selection", "date-range-selection", "tickers-selection",
            "risk-management", "trading-costs", "rebalancing-rules", "wizard-summary"
        ]
        num_steps = len(steps)
        target_step_index = 0 # Default to the first step

        # --- Determine if trigger is a header click ---
        is_header_click = "-header" in trigger_id

        try:
            # Check if trigger is one of the centralized confirm buttons
            if trigger_id == WizardIDs.CONFIRM_STRATEGY_BUTTON:
                target_step_index = 1  # Move to date selection
                logger.info(f"Confirm strategy button clicked. Target step index: {target_step_index}")
            elif trigger_id == WizardIDs.CONFIRM_DATES_BUTTON:
                target_step_index = 2  # Move to ticker selection
                logger.info(f"Confirm dates button clicked. Target step index: {target_step_index}")
            elif trigger_id == WizardIDs.CONFIRM_TICKERS_BUTTON:
                target_step_index = 3  # Move to risk management
                logger.info(f"Confirm tickers button clicked. Target step index: {target_step_index}")
            elif trigger_id == WizardIDs.CONFIRM_RISK_BUTTON:
                target_step_index = 4  # Move to trading costs
                logger.info(f"Confirm risk button clicked. Target step index: {target_step_index}")
            elif trigger_id == WizardIDs.CONFIRM_COSTS_BUTTON:
                target_step_index = 5  # Move to rebalancing
                logger.info(f"Confirm costs button clicked. Target step index: {target_step_index}")
            elif trigger_id == WizardIDs.CONFIRM_REBALANCING_BUTTON:
                target_step_index = 6  # Move to summary
                logger.info(f"Confirm rebalancing button clicked. Target step index: {target_step_index}")
            elif "-header" in trigger_id:
                header_map = {
                    WizardIDs.step_header("strategy-selection"): 0, 
                    WizardIDs.step_header("date-range-selection"): 1,
                    WizardIDs.step_header("tickers-selection"): 2, 
                    WizardIDs.step_header("risk-management"): 3,
                    WizardIDs.step_header("trading-costs"): 4, 
                    WizardIDs.step_header("rebalancing-rules"): 5, 
                    WizardIDs.step_header("wizard-summary"): 6
                }
                target_step_index = header_map.get(trigger_id)
                if target_step_index is None:
                    logger.error(f"Unknown header ID: {trigger_id}")
                    return no_update
                logger.info(f"Header '{trigger_id}' clicked. Target step index: {target_step_index}")
            else:
                logger.error(f"Unhandled trigger ID in step transition: {trigger_id}")
                return no_update

            # --- Generate Outputs ---
            visible_style = {"display": "block", "marginLeft": "30px", "paddingTop": "10px"}
            hidden_style = {"display": "none", "marginLeft": "30px", "paddingTop": "10px"}
            step_styles = [hidden_style] * num_steps
            status_classes = ["step-status"] * num_steps # Base class

            if 0 <= target_step_index < num_steps:
                step_styles[target_step_index] = visible_style
                for i in range(num_steps):
                    if i < target_step_index: status_classes[i] += " completed"
                    elif i == target_step_index: status_classes[i] += " current"
                    else: status_classes[i] += " pending"
            else:
                logger.error(f"Invalid target_step_index calculated: {target_step_index}. Defaulting to step 0.")
                step_styles[0] = visible_style # Fallback to first step
                status_classes[0] += " current"
                for i in range(1, num_steps): status_classes[i] += " pending"

            progress = ((target_step_index + 1) / num_steps) * 100

            # --- Determine strategy progress bar style ---
            # Show if a header was clicked, otherwise no_update (run_backtest callback will hide it)
            progress_bar_style = {'display': 'block'} if is_header_click else no_update

            logger.debug(f"Returning statuses: {status_classes}")
            logger.debug(f"Returning progress: {progress}")
            logger.debug(f"Returning progress bar style: {progress_bar_style}")

            # Return styles, classes, progress value, and progress bar style
            return step_styles + status_classes + [progress, progress_bar_style]

        except Exception as e:
            logger.error(f"Error in handle_step_transition callback: {e}", exc_info=True)
            # Ensure the number of no_update matches the number of outputs
            return [no_update] * (num_steps * 2 + 2) # 7 styles + 7 classes + value + style

    # --- Validation Callbacks (Crucial for enabling Confirm buttons) ---
    # These should be updated with centralized IDs in Phase 3 when those sections are also refactored

    @app.callback(
        Output(WizardIDs.CONFIRM_DATES_BUTTON, "disabled"),
        [Input(WizardIDs.DATE_RANGE_START_PICKER, "date"),
         Input(WizardIDs.DATE_RANGE_END_PICKER, "date")]
    )
    def validate_date_range(start_date, end_date):
        is_disabled = not (start_date and end_date)
        logger.debug(f"Dates selected: Start={start_date}, End={end_date}. Confirm Dates button disabled: {is_disabled}")
        return is_disabled

    @app.callback(
        Output(WizardIDs.CONFIRM_TICKERS_BUTTON, "disabled"),
        Input(WizardIDs.TICKER_DROPDOWN, "value") 
    )
    def validate_ticker_selection(tickers):
        # Add more robust validation if needed (e.g., check format)
        is_disabled = not bool(tickers)
        logger.debug(f"Tickers selected: {tickers}. Confirm Tickers button disabled: {is_disabled}")
        return is_disabled

    @app.callback(
        Output(WizardIDs.CONFIRM_COSTS_BUTTON, "disabled"),
        [Input(WizardIDs.COMMISSION_INPUT, "value"), Input(WizardIDs.SLIPPAGE_INPUT, "value")]
    )
    def validate_costs(commission, slippage):
        ok = commission is not None and slippage is not None
        logger.debug(f"Costs inputs: commission={commission}, slippage={slippage}, valid: {ok}")
        return not ok

    @app.callback(
        [Output(WizardIDs.CONFIRM_RISK_BUTTON, "disabled"), Output(WizardIDs.CONFIRM_RISK_BUTTON, "children")],
        [Input(WizardIDs.RISK_FEATURES_CHECKLIST, 'value'),
         Input(WizardIDs.MAX_POSITION_SIZE_INPUT, 'value'),
         Input(WizardIDs.STOP_LOSS_TYPE_SELECT, 'value'),
         Input(WizardIDs.STOP_LOSS_INPUT, 'value'),
         Input(WizardIDs.TAKE_PROFIT_TYPE_SELECT, 'value'),
         Input(WizardIDs.TAKE_PROFIT_INPUT, 'value'),
         Input(WizardIDs.MAX_RISK_PER_TRADE_INPUT, 'value'),
         Input(WizardIDs.MARKET_TREND_LOOKBACK_INPUT, 'value'),
         Input(WizardIDs.MAX_DRAWDOWN_INPUT, 'value'),
         Input(WizardIDs.MAX_DAILY_LOSS_INPUT, 'value')
        ]
    )
    def validate_risk_tab(selected_features, max_pos, sl_type, sl_val, tp_type, tp_val, rpt, mtl, md, mdl):
        """Enable confirm-risk when no features selected (always enabled) or all selected feature params are filled."""
        # Base label
        if not selected_features:
            # No features: always enabled, custom label
            return False, "Continue without additional risk measures"
        # If features selected, validate required inputs
        feature_checks = {
            'position_sizing': max_pos is not None,
            'stop_loss': (sl_type is not None and sl_val is not None),
            'take_profit': (tp_type is not None and tp_val is not None),
            'risk_per_trade': rpt is not None,
            'market_filter': mtl is not None,
            'drawdown_protection': (md is not None and mdl is not None)
        }
        # If any selected feature fails check, disable
        for feat in selected_features:
            if not feature_checks.get(feat, True):
                return True, "Confirm"
        # All good
        return False, "Confirm"

    # --- Select/Deselect All Tickers Callbacks ---
    @app.callback(
        Output(WizardIDs.TICKER_DROPDOWN, 'value'),
        [Input(WizardIDs.SELECT_ALL_TICKERS_BUTTON, 'n_clicks'), Input(WizardIDs.DESELECT_ALL_TICKERS_BUTTON, 'n_clicks')],
        [State(WizardIDs.TICKER_DROPDOWN, 'options')],
        prevent_initial_call=True
    )
    def update_ticker_selection(n_select_all, n_deselect_all, options):
        """Select or deselect all tickers based on which button was clicked."""
        ctx_trigger = ctx.triggered[0]['prop_id'].split('.')[0]
        if ctx_trigger == WizardIDs.SELECT_ALL_TICKERS_BUTTON:
            # options is a list of dicts with 'value' key
            return [opt['value'] for opt in options]
        elif ctx_trigger == WizardIDs.DESELECT_ALL_TICKERS_BUTTON:
            return []
        return no_update

    # --- Summary Generation and Run Button Activation ---
    @app.callback(
        [Output(WizardIDs.SUMMARY_OUTPUT_CONTAINER, 'children'), 
         Output(WizardIDs.RUN_BACKTEST_BUTTON_WIZARD, 'disabled', allow_duplicate=True)], 
        Input(WizardIDs.step_content("wizard-summary"), 'style'),
        [
            State(WizardIDs.STRATEGY_DROPDOWN, 'value'),
            # ADDED: State for initial capital
            State(WizardIDs.INITIAL_CAPITAL_INPUT, 'value'),
            State({'type': 'strategy-param', 'strategy': ALL, 'param': ALL}, 'value'),
            State({'type': 'strategy-param', 'strategy': ALL, 'param': ALL}, 'id'),
            State(WizardIDs.DATE_RANGE_START_PICKER, 'date'),
            State(WizardIDs.DATE_RANGE_END_PICKER, 'date'),
            State(WizardIDs.TICKER_DROPDOWN, 'value'),
            State(WizardIDs.RISK_FEATURES_CHECKLIST, 'value'),
            State(WizardIDs.MAX_POSITION_SIZE_INPUT, 'value'),
            State(WizardIDs.STOP_LOSS_TYPE_SELECT, 'value'),
            State(WizardIDs.STOP_LOSS_INPUT, 'value'),
            State(WizardIDs.TAKE_PROFIT_TYPE_SELECT, 'value'),
            State(WizardIDs.TAKE_PROFIT_INPUT, 'value'),
            State(WizardIDs.MAX_RISK_PER_TRADE_INPUT, 'value'),
            State(WizardIDs.MARKET_TREND_LOOKBACK_INPUT, 'value'),
            State(WizardIDs.MAX_DRAWDOWN_INPUT, 'value'),
            State(WizardIDs.MAX_DAILY_LOSS_INPUT, 'value'),
            State(WizardIDs.COMMISSION_INPUT, 'value'),
            State(WizardIDs.SLIPPAGE_INPUT, 'value'),
            State(WizardIDs.REBALANCING_FREQUENCY_DROPDOWN, 'value'),
            State(WizardIDs.REBALANCING_THRESHOLD_INPUT, 'value')
        ],
        prevent_initial_call=True
    )
    def update_summary_and_run(summary_style, strat_value, initial_capital, # Added initial_capital
                               param_values, param_ids,
                               start_date, end_date, tickers,
                               risk_feats, max_ps, sl_type, sl_val,
                               tp_type, tp_val, rpt, mtl,
                               mdd, mdl, comm, slip, reb_freq, reb_thresh):
        if not summary_style or summary_style.get('display') != 'block':
            # Don't update if the summary step is not visible
            return no_update, no_update # Return no_update for both outputs

        summary_elements = []

        # --- Strategy ---
        strategy_label = strat_value # Default to value if not found
        for strategy_info in AVAILABLE_STRATEGIES:
            if strategy_info.get('value') == strat_value:
                strategy_label = strategy_info.get('label', strat_value)
                break
        summary_elements.append(html.Div([
            html.Strong("Strategy: "),
            html.Span(strategy_label)
        ], className="mb-1")) # Use mb-1 for closer spacing like screenshot

        # --- Initial Capital ---
        summary_elements.append(html.Div([
            html.Strong("Initial Capital: "),
            # Assuming initial_capital is already formatted string like "100 000"
            html.Span(f"${initial_capital}" if initial_capital else "Not Set")
        ], className="mb-1"))

        # --- Parameters ---
        if param_ids and param_values:
            params_list = []
            for i, pid in enumerate(param_ids):
                # Ensure pid is a dictionary and has 'param' key
                if isinstance(pid, dict) and 'param' in pid:
                    name = pid.get('param')
                    val = param_values[i] if i < len(param_values) else 'N/A'
                    # Format parameter name nicely
                    formatted_name = name.replace('_', ' ').title()
                    params_list.append(html.Li(f"{formatted_name}: {val}"))
                else:
                     logger.warning(f"Invalid param_id structure found: {pid}")

            if params_list: # Only add if there are valid parameters
                 summary_elements.append(html.Div([
                     html.Strong("Parameters:"),
                     html.Ul(params_list, style={'paddingLeft': '20px', 'marginTop': '0px', 'marginBottom': '4px'}) # Indent list
                 ], className="mb-1"))


        # --- Date Range ---
        summary_elements.append(html.Div([
            html.Strong("Date Range: "),
            html.Span(f"{start_date} to {end_date}")
        ], className="mb-1"))

        # --- Tickers ---
        summary_elements.append(html.Div([
            html.Strong("Tickers: "),
            html.Span(", ".join(tickers or ["None"]))
        ], className="mb-1"))

        # --- Risk Measures ---
        risk_measures_list = []
        if risk_feats:
            if 'position_sizing' in risk_feats: risk_measures_list.append(html.Li(f"Position Sizing: {max_ps}%"))
            if 'stop_loss' in risk_feats: risk_measures_list.append(html.Li(f"Stop Loss ({sl_type}): {sl_val}%"))
            if 'take_profit' in risk_feats: risk_measures_list.append(html.Li(f"Take Profit ({tp_type}): {tp_val}%"))
            if 'risk_per_trade' in risk_feats: risk_measures_list.append(html.Li(f"Risk per Trade: {rpt}%"))
            if 'market_filter' in risk_feats: risk_measures_list.append(html.Li(f"Market Filter lookback: {mtl} days"))
            if 'drawdown_protection' in risk_feats: risk_measures_list.append(html.Li(f"Max Drawdown: {mdd}%, Max Daily Loss: {mdl}%"))

        if risk_measures_list:
             summary_elements.append(html.Div([
                 html.Strong("Risk Measures:"),
                 html.Ul(risk_measures_list, style={'paddingLeft': '20px', 'marginTop': '0px', 'marginBottom': '4px'}) # Indent list
             ], className="mb-1"))
        else:
             summary_elements.append(html.Div([
                 html.Strong("Risk Measures: "),
                 html.Span("None")
             ], className="mb-1"))


        # --- Costs ---
        summary_elements.append(html.Div([
            html.Strong("Commission: "),
            html.Span(f"{comm}%"),
            html.Strong(", Slippage: ", style={'marginLeft': '5px'}),
            html.Span(f"{slip}%")
        ], className="mb-1"))

        # --- Rebalancing ---
        rebal_freq_label = reb_freq # Default
        freq_map = {'D': 'Daily', 'W': 'Weekly', 'M': 'Monthly', 'Q': 'Quarterly', 'A': 'Annually', 'N': 'None'}
        rebal_freq_label = freq_map.get(reb_freq, reb_freq)

        summary_elements.append(html.Div([
            html.Strong("Rebalancing: "),
            html.Span(f"{rebal_freq_label}"),
            html.Strong(", Threshold: ", style={'marginLeft': '5px'}),
            html.Span(f"{reb_thresh}%")
        ], className="mb-1"))

        # Enable Run Backtest button
        return summary_elements, False

    # --- Connect Wizard Run Backtest Button to Backtest Execution ---
    @app.callback(
        [
            Output(StrategyConfigIDs.RUN_BACKTEST_BUTTON_MAIN, 'n_clicks', allow_duplicate=True),
            Output(StrategyConfigIDs.STRATEGY_SELECTOR, 'value', allow_duplicate=True),
            Output(StrategyConfigIDs.TICKER_INPUT_MAIN, 'value', allow_duplicate=True),
            Output(StrategyConfigIDs.START_DATE_PICKER_MAIN, 'date', allow_duplicate=True),
            Output(StrategyConfigIDs.END_DATE_PICKER_MAIN, 'date', allow_duplicate=True),
            Output(StrategyConfigIDs.INITIAL_CAPITAL_INPUT_MAIN, 'value', allow_duplicate=True)
        ],
        Input(WizardIDs.RUN_BACKTEST_BUTTON_WIZARD, 'n_clicks'),
        [
            State(WizardIDs.STRATEGY_DROPDOWN, 'value'),
            State(WizardIDs.INITIAL_CAPITAL_INPUT, 'value'),
            State(WizardIDs.DATE_RANGE_START_PICKER, 'date'),
            State(WizardIDs.DATE_RANGE_END_PICKER, 'date'),
            State(WizardIDs.TICKER_DROPDOWN, 'value'),
            State({'type': 'strategy-param', 'strategy': ALL, 'param': ALL}, 'value'),
            State({'type': 'strategy-param', 'strategy': ALL, 'param': ALL}, 'id'),
            State(WizardIDs.RISK_FEATURES_CHECKLIST, 'value'),
            State(WizardIDs.MAX_POSITION_SIZE_INPUT, 'value'),
            State(WizardIDs.STOP_LOSS_TYPE_SELECT, 'value'),
            State(WizardIDs.STOP_LOSS_INPUT, 'value'),
            State(WizardIDs.TAKE_PROFIT_TYPE_SELECT, 'value'),
            State(WizardIDs.TAKE_PROFIT_INPUT, 'value'),
            State(WizardIDs.MAX_RISK_PER_TRADE_INPUT, 'value'),
            State(WizardIDs.MARKET_TREND_LOOKBACK_INPUT, 'value'),
            State(WizardIDs.MAX_DRAWDOWN_INPUT, 'value'),
            State(WizardIDs.MAX_DAILY_LOSS_INPUT, 'value'),
            State(WizardIDs.COMMISSION_INPUT, 'value'),
            State(WizardIDs.SLIPPAGE_INPUT, 'value'),
            State(WizardIDs.REBALANCING_FREQUENCY_DROPDOWN, 'value'),
            State(WizardIDs.REBALANCING_THRESHOLD_INPUT, 'value')
        ],
        prevent_initial_call=True
    )
    def trigger_backtest_from_wizard(n_clicks, strategy_type, initial_capital, 
                                     start_date, end_date, tickers,
                                     strategy_param_values, strategy_param_ids,
                                     risk_feats, max_ps, sl_type, sl_val,
                                     tp_type, tp_val, rpt, mtl, mdd, mdl,
                                     comm, slip, reb_freq, reb_thresh):
        """
        When the wizard's Run Backtest button is clicked, this callback transfers wizard 
        configuration data to the main backtest form components and triggers the main backtest execution.
        """
        if not n_clicks or n_clicks <= 0:
            raise PreventUpdate
            
        logger.info(f"Wizard Run Backtest button clicked. Transferring wizard config to main form and triggering backtest with strategy: {strategy_type}")
        
        # Match the expected form of ticker input for the main backtest component
        # The main backtest expects a string for ticker-input
        tickers_str = ', '.join(tickers) if isinstance(tickers, list) else str(tickers)
        
        # Return values to update the main backtest form components and trigger the backtest
        return (
            1,  # Increment n_clicks for main run button
            strategy_type, 
            tickers_str, 
            start_date, 
            end_date, 
            initial_capital
        )

    # --- Callback to trigger main backtest button from wizard --- 
    @app.callback(
        Output(StrategyConfigIDs.RUN_BACKTEST_BUTTON_MAIN, 'n_clicks', allow_duplicate=True), # Use StrategyConfigID for the main button
        Input(WizardIDs.RUN_BACKTEST_BUTTON_WIZARD, 'n_clicks'),
        State(StrategyConfigIDs.RUN_BACKTEST_BUTTON_MAIN, 'n_clicks'), # Read current n_clicks of the main button
        prevent_initial_call=True
    )
    def run_backtest_from_wizard_button(wizard_n_clicks, main_n_clicks):
        """
        When the wizard's run button is clicked, this callback increments the n_clicks
        of the main application's run backtest button, effectively triggering it.
        """
        if wizard_n_clicks and wizard_n_clicks > 0:
            logger.info(f"Wizard's run button clicked. Triggering main run backtest button.")
            # Increment n_clicks of the main button
            current_main_n_clicks = main_n_clicks or 0
            return current_main_n_clicks + 1
        raise PreventUpdate

    logger.info("Wizard callbacks registered successfully.")