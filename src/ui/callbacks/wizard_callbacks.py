import dash
from dash import html, dcc, Input, Output, State, ALL, MATCH, ctx, no_update
import logging
# Make sure logging is configured appropriately elsewhere (e.g., in app_factory or main app.py)
# from ...config.logging_config import setup_logging
from src.core.constants import STRATEGY_DESCRIPTIONS # Poprawna ścieżka do stałych
from src.core.constants import DEFAULT_STRATEGY_PARAMS  # added import for default params
from src.core.constants import AVAILABLE_STRATEGIES # Ensure this is imported

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
            Output("strategy-selection-content", "style"),
            Output("date-range-selection-content", "style"),
            Output("tickers-selection-content", "style"),
            Output("risk-management-content", "style"),
            Output("trading-costs-content", "style"),
            Output("rebalancing-rules-content", "style"),
            Output("wizard-summary-content", "style"),
            # Header class toggles for each step
            Output("strategy-selection-header", "className"),
            Output("date-range-selection-header", "className"),
            Output("tickers-selection-header", "className"),
            Output("risk-management-header", "className"),
            Output("trading-costs-header", "className"),
            Output("rebalancing-rules-header", "className"),
            Output("wizard-summary-header", "className"),
            # Progress Bar
            Output("wizard-progress", "value")
        ],
        [
            # Confirm Buttons (Inputs) - Verify these IDs
            Input("confirm-strategy", "n_clicks"),
            Input("confirm-dates", "n_clicks"),
            Input("confirm-tickers", "n_clicks"),
            Input("confirm-risk", "n_clicks"),
            Input("confirm-costs", "n_clicks"),
            Input("confirm-rebalancing", "n_clicks"),
            # Step Headers (Inputs) - Verify these IDs
            Input("strategy-selection-header", "n_clicks"),
            Input("date-range-selection-header", "n_clicks"),
            Input("tickers-selection-header", "n_clicks"),
            Input("risk-management-header", "n_clicks"),
            Input("trading-costs-header", "n_clicks"),
            Input("rebalancing-rules-header", "n_clicks"),
            Input("wizard-summary-header", "n_clicks")
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

        try:
            if "confirm-" in trigger_id:
                confirm_map = {
                    "confirm-strategy": 1, "confirm-dates": 2, "confirm-tickers": 3,
                    "confirm-risk": 4, "confirm-costs": 5, "confirm-rebalancing": 6
                }
                target_step_index = confirm_map.get(trigger_id)
                if target_step_index is None:
                    logger.error(f"Unknown confirm button ID: {trigger_id}")
                    return no_update
                logger.info(f"Confirm button '{trigger_id}' clicked. Target step index: {target_step_index}")

            elif "-header" in trigger_id:
                header_map = {
                    "strategy-selection-header": 0, "date-range-selection-header": 1,
                    "tickers-selection-header": 2, "risk-management-header": 3,
                    "trading-costs-header": 4, "rebalancing-rules-header": 5, "wizard-summary-header": 6
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

            # logger.debug(f"Returning styles: {step_styles}") # Removed this log
            logger.debug(f"Returning statuses: {status_classes}")
            logger.debug(f"Returning progress: {progress}")

            return step_styles + status_classes + [progress]

        except Exception as e:
            logger.error(f"Error in handle_step_transition callback: {e}", exc_info=True)
            return no_update # Prevent app crash

    # --- Validation Callbacks (Crucial for enabling Confirm buttons) ---

    @app.callback(
        Output("confirm-dates", "disabled"),
        [Input("backtest-start-date", "date"), # Verify these IDs
         Input("backtest-end-date", "date")]
    )
    def validate_date_range(start_date, end_date):
        is_disabled = not (start_date and end_date)
        logger.debug(f"Dates selected: Start={start_date}, End={end_date}. Confirm Dates button disabled: {is_disabled}")
        return is_disabled

    @app.callback(
        Output("confirm-tickers", "disabled"),
        Input("ticker-input", "value") # Verify this ID (or the correct component for ticker selection)
    )
    def validate_ticker_selection(tickers):
        # Add more robust validation if needed (e.g., check format)
        is_disabled = not bool(tickers)
        logger.debug(f"Tickers selected: {tickers}. Confirm Tickers button disabled: {is_disabled}")
        return is_disabled

    @app.callback(
        Output("confirm-costs", "disabled"),
        [Input("commission-input", "value"), Input("slippage-input", "value")]
    )
    def validate_costs(commission, slippage):
        ok = commission is not None and slippage is not None
        logger.debug(f"Costs inputs: commission={commission}, slippage={slippage}, valid: {ok}")
        return not ok

    @app.callback(
        Output("confirm-rebalancing", "disabled"),
        [Input("rebalancing-frequency", "value"), Input("rebalancing-threshold", "value")]
    )
    def validate_rebalancing(frequency, threshold):
        ok = bool(frequency) and threshold is not None
        logger.debug(f"Rebalancing inputs: freq={frequency}, thresh={threshold}, valid: {ok}")
        return not ok

    @app.callback(
        [Output("confirm-risk", "disabled"), Output("confirm-risk", "children")],
        [Input('risk-features-checklist', 'value'),
         Input('max-position-size', 'value'),
         Input('stop-loss-type', 'value'),
         Input('stop-loss-value', 'value'),
         Input('take-profit-type', 'value'),
         Input('take-profit-value', 'value'),
         Input('max-risk-per-trade', 'value'),
         Input('market-trend-lookback', 'value'),
         Input('max-drawdown', 'value'),
         Input('max-daily-loss', 'value')
        ]
    )
    def validate_risk_tab(selected_features, max_pos, sl_type, sl_val, tp_type, tp_val, rmt, mtl, md, mdl):
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
            'risk_per_trade': rmt is not None,
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
        Output('ticker-input', 'value'),
        [Input('select-all-tickers', 'n_clicks'), Input('deselect-all-tickers', 'n_clicks')],
        [State('ticker-input', 'options')],
        prevent_initial_call=True
    )
    def update_ticker_selection(n_select_all, n_deselect_all, options):
        """Select or deselect all tickers based on which button was clicked."""
        ctx_trigger = ctx.triggered[0]['prop_id'].split('.')[0]
        if ctx_trigger == 'select-all-tickers':
            # options is a list of dicts with 'value' key
            return [opt['value'] for opt in options]
        elif ctx_trigger == 'deselect-all-tickers':
            return []
        return no_update

    # --- Summary Generation and Run Button Activation ---
    @app.callback(
        [Output('wizard-summary-output', 'children'), 
         Output('run-backtest-button', 'disabled', allow_duplicate=True)], # ADDED allow_duplicate=True
        Input('wizard-summary-content', 'style'),
        [
            State('strategy-dropdown', 'value'),
            # ADDED: State for initial capital
            State('initial-capital-input', 'value'),
            State({'type': 'strategy-param', 'strategy': ALL, 'param': ALL}, 'value'),
            State({'type': 'strategy-param', 'strategy': ALL, 'param': ALL}, 'id'),
            State('backtest-start-date', 'date'),
            State('backtest-end-date', 'date'),
            State('ticker-input', 'value'),
            State('risk-features-checklist', 'value'),
            State('max-position-size', 'value'),
            State('stop-loss-type', 'value'),
            State('stop-loss-value', 'value'),
            State('take-profit-type', 'value'),
            State('take-profit-value', 'value'),
            State('max-risk-per-trade', 'value'),
            State('market-trend-lookback', 'value'),
            State('max-drawdown', 'value'),
            State('max-daily-loss', 'value'),
            State('commission-input', 'value'),
            State('slippage-input', 'value'),
            State('rebalancing-frequency', 'value'),
            State('rebalancing-threshold', 'value')
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

    logger.info("Wizard callbacks registered successfully.")

# Remember to ensure this function is called during app setup, e.g., in create_app()