import dash  # Added import
from dash.exceptions import PreventUpdate
import time
import logging
import traceback
from datetime import datetime
import pandas as pd

# Import ALL for pattern-matching callbacks
from dash import (
    Dash,
    dcc,
    html,
    Input,
    Output,
    State,
    callback,
    no_update,
    ctx,
    ClientsideFunction,
    ALL,
)
import plotly.graph_objects as go
import plotly.io as pio
import dash_bootstrap_components as dbc  # Import dbc
from dash import dash_table
from dash.dash_table.Format import Format, Scheme

# Import services and components
from src.services.backtest_service import BacktestService
from src.ui.components import create_metrics_table

# Import layout functions needed for the new callback
from src.visualization.chart_utils import create_empty_chart

# Corrected import: Use BacktestVisualizer instead of Visualizer
from src.visualization.visualizer import BacktestVisualizer
from src.core.exceptions import BacktestError, DataError
from src.core.constants import CHART_THEME

# Import centralized IDs
from src.ui.ids.ids import (
    ResultsIDs,
    WizardIDs,
    StrategyConfigIDs,
    SharedComponentIDs,
)  # MODIFIED

# Configure logging
logger = logging.getLogger(__name__)

# Initialize services (assuming a singleton or shared instance mechanism if needed)
# In a real Dash app, this might be handled differently (e.g., global variable, app context)
backtest_service = BacktestService()


def register_backtest_callbacks(app: Dash):
    """Register callbacks related to running backtests and displaying results."""

    logger.info("Registering backtest callbacks...")

    # --- Run Backtest Callback ---
    # This callback now outputs to the store instead of directly to result components
    @app.callback(
        Output(ResultsIDs.BACKTEST_RESULTS_STORE, "data"),
        Output(SharedComponentIDs.LOADING_OVERLAY, "style"),
        Output(ResultsIDs.BACKTEST_PROGRESS_BAR, "value"),
        Output(ResultsIDs.BACKTEST_PROGRESS_LABEL_TEXT, "children"),
        Output(ResultsIDs.BACKTEST_ANIMATED_TEXT, "children"),
        Output(ResultsIDs.BACKTEST_ANIMATION_INTERVAL, "disabled"),
        Output(WizardIDs.PROGRESS_BAR, "style", allow_duplicate=True),
        Output(ResultsIDs.CENTER_PANEL_COLUMN, "style"),
        Output(ResultsIDs.RIGHT_PANEL_COLUMN, "style"),
        Output(ResultsIDs.RESULTS_AREA_WRAPPER, "style"),
        Output(ResultsIDs.BACKTEST_PROGRESS_BAR_CONTAINER, "is_open"),
        Input(SharedComponentIDs.RUN_BACKTEST_TRIGGER_STORE, "data"),
        State(StrategyConfigIDs.STRATEGY_CONFIG_STORE_MAIN, "data"),
        background=True,
        running=[
            (
                Output(StrategyConfigIDs.RUN_BACKTEST_BUTTON_MAIN, "disabled"),
                True,
                False,
            ),
            (Output(WizardIDs.RUN_BACKTEST_BUTTON_WIZARD, "disabled"), True, False),
            (
                Output(SharedComponentIDs.LOADING_OVERLAY, "style"),
                # When running, show overlay with fixed position covering whole viewport
                {
                    "display": "flex",
                    "position": "fixed",
                    "top": "0",
                    "left": "0",
                    "right": "0",
                    "bottom": "0",
                    "backgroundColor": "rgba(18, 18, 18, 0.98)",
                    "zIndex": "1050",
                    "flexDirection": "column",
                    "alignItems": "center",
                    "justifyContent": "center",
                },
                # When not running, hide overlay
                {"display": "none"},
            ),
            (Output(ResultsIDs.BACKTEST_STATUS_MESSAGE, "children"), "", ""),
            (
                Output(ResultsIDs.BACKTEST_ANIMATED_TEXT, "children"),
                "Running backtest... (0%)",
                "",
            ),
            (
                Output(ResultsIDs.BACKTEST_PROGRESS_LABEL_TEXT, "children"),
                "Initializing...",
                " ",
            ),
            (Output(ResultsIDs.BACKTEST_ANIMATION_INTERVAL, "disabled"), False, True),
            (
                Output(ResultsIDs.BACKTEST_PROGRESS_BAR_CONTAINER, "is_open"),
                True,
                False,
            ),
            (Output(WizardIDs.PROGRESS_BAR, "style"), {"display": "none"}, no_update),
            # Both panels should be hidden during backtest and initially
            (
                Output(ResultsIDs.CENTER_PANEL_COLUMN, "style"),
                {"display": "none"},  # Style when RUNNING
                {"display": "none"},
            ),  # Style when NOT RUNNING (initial)
            (
                Output(ResultsIDs.RIGHT_PANEL_COLUMN, "style"),
                {"display": "none"},  # Style when RUNNING
                {"display": "none"},
            ),  # Style when NOT RUNNING (initial)
            (
                Output(ResultsIDs.RESULTS_AREA_WRAPPER, "style"),
                {"display": "none"},  # Style when RUNNING
                {"display": "none"},
            ),  # Style when NOT RUNNING (initial)
        ],
        progress=[
            Output(ResultsIDs.BACKTEST_PROGRESS_BAR, "value"),
            Output(ResultsIDs.BACKTEST_PROGRESS_LABEL_TEXT, "children"),
        ],
        prevent_initial_call=True,
    )
    def run_backtest(set_progress, trigger_data, config_data):
        def wrapped_set_progress(
            progress_tuple,
        ):  # progress_tuple is (value, detail_message)
            value, detail_message = progress_tuple
            set_progress(
                (value, detail_message)
            )  # Update bar value and inner detail message

            # Standard delays, adjust if necessary
            if value <= 4:
                time.sleep(0.01)
            elif value < 26:
                time.sleep(0.05)
            else:
                time.sleep(0.05)

        logger.info("--- run_backtest callback: Entered.")
        if not trigger_data:
            logger.warning("run_backtest triggered without trigger_data.")
            raise PreventUpdate

        initial_animated_text = "Running backtest... (0%)"  # Set by 'running' state, but good to have a default

        if not config_data:
            logger.warning("run_backtest triggered without config_data.")
            # value, inner_message, outer_message, interval_disabled
            return (
                {
                    "timestamp": time.time(),
                    "success": False,
                    "error": "Configuration data is missing.",
                },
                {"display": "none"},
                100,
                "Config Error",
                "Config Error (100%)",
                True,
                {"display": "none"},
                {"display": "none"},
                {"display": "none"},
                {"display": "none"},
                False,
            )

        logger.info(f"run_backtest: Received config_data: {config_data}")
        # ... (extract parameters as before) ...
        strategy_type = config_data.get("strategy_type")
        tickers = config_data.get("tickers")
        start_date_str = config_data.get("start_date")
        end_date_str = config_data.get("end_date")
        initial_capital = config_data.get("initial_capital")
        strategy_params_dict = config_data.get("strategy_params", {})
        risk_params_dict = config_data.get("risk_management", {})
        trading_costs_config = config_data.get("trading_costs", {})
        rebalancing_params_config = config_data.get("rebalancing", {})

        cost_params_dict = {
            "commission_per_trade": trading_costs_config.get("commission_bps"),
            "slippage_per_trade": trading_costs_config.get("slippage_bps"),
        }
        rebalancing_params_dict = {
            "frequency": rebalancing_params_config.get("frequency"),
            "threshold": rebalancing_params_config.get("threshold_pct"),
        }

        if isinstance(tickers, list) and tickers:
            tickers_list = [str(t).strip() for t in tickers if t]
        elif isinstance(tickers, str) and tickers.strip():
            tickers_list = [t.strip() for t in tickers.split(",") if t.strip()]
        else:
            tickers_list = []

        if not all(
            [
                strategy_type,
                tickers_list,
                start_date_str,
                end_date_str,
                initial_capital is not None,
            ]
        ):
            error_msg = "Missing required inputs."
            logger.error(f"run_backtest: Input validation failed: {error_msg}")
            return (
                {"timestamp": time.time(), "success": False, "error": error_msg},
                {"display": "none"},
                100,
                "Input Error",
                "Input Error (100%)",
                True,
                {"display": "none"},
                {"display": "none"},
                {"display": "none"},
                {"display": "none"},
                False,
            )
        try:
            start_date_dt = (
                datetime.strptime(start_date_str, "%Y-%m-%d").date()
                if start_date_str
                else None
            )
            end_date_dt = (
                datetime.strptime(end_date_str, "%Y-%m-%d").date()
                if end_date_str
                else None
            )
        except ValueError as e:
            error_msg = f"Invalid date format: {e}."
            logger.error(f"run_backtest: {error_msg}")
            return (
                {"timestamp": time.time(), "success": False, "error": error_msg},
                {"display": "none"},
                100,
                "Date Error",
                "Date Error (100%)",
                True,
                {"display": "none"},
                {"display": "none"},
                {"display": "none"},
                {"display": "none"},
                False,
            )

        if (
            "features" in risk_params_dict
            and "enabled_features" not in risk_params_dict
        ):
            risk_params_dict["enabled_features"] = risk_params_dict.pop("features")

        try:
            logger.info(
                "run_backtest: Setting initial progress (1% for inner message)."
            )
            wrapped_set_progress(
                (1, "Initializing Backtest...")
            )  # value, inner_message

            logger.info("run_backtest: Calling backtest_service.run_backtest.")
            start_time = time.time()

            results_package = backtest_service.run_backtest(
                strategy_type=strategy_type,
                tickers=tickers_list,
                start_date=start_date_dt,
                end_date=end_date_dt,
                initial_capital=initial_capital,
                strategy_params=strategy_params_dict,
                risk_params=risk_params_dict,
                cost_params=cost_params_dict,
                rebalancing_params=rebalancing_params_dict,
                progress_callback=wrapped_set_progress,
            )
            end_time = time.time()
            logger.info(
                f"run_backtest: backtest_service.run_backtest finished in {end_time - start_time:.2f} seconds."
            )
            results_package["timestamp"] = time.time()

            if results_package.get("success"):
                logger.info(f"run_backtest: Preparing SUCCESSFUL results.")
                wrapped_set_progress((100, "Complete"))
                time.sleep(0.05)
                logger.info("run_backtest: Exiting successfully.")
                return (
                    results_package,
                    {"display": "none"},
                    100,
                    "Complete",
                    "Complete (100%)",
                    True,
                    no_update,
                    {"display": "none"},
                    {"display": "none"},
                    {"display": "none"},
                    False,
                )  # Keep panels hidden until update_results_display shows them
            else:
                error_msg = results_package.get("error", "Unknown backtest failure")
                logger.error(f"run_backtest: Returning FAILED results: {error_msg}")
                display_error_msg = (
                    (error_msg[:30] + "...") if len(error_msg) > 33 else error_msg
                )
                outer_display_error_msg = (
                    (error_msg[:40] + "...") if len(error_msg) > 43 else error_msg
                )
                wrapped_set_progress((100, f"Failed: {display_error_msg}"))
                time.sleep(0.05)
                return (
                    results_package,
                    {"display": "none"},
                    100,
                    f"Failed: {display_error_msg}",
                    f"Failed: {outer_display_error_msg} (100%)",
                    True,
                    no_update,
                    {"display": "none"},
                    {"display": "none"},
                    {"display": "none"},
                    False,
                )  # Ensure panels stay hidden on failure

        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(
                f"run_backtest: An unexpected error occurred: {e}\nTraceback:\n{tb_str}"
            )
            error_msg = f"Unexpected error: {str(e)}"
            display_error_msg = (
                (error_msg[:30] + "...") if len(error_msg) > 33 else error_msg
            )
            outer_display_error_msg = (
                (error_msg[:40] + "...") if len(error_msg) > 43 else error_msg
            )
            wrapped_set_progress((100, f"Error: {display_error_msg}"))
            time.sleep(0.05)
            return (
                {"timestamp": time.time(), "success": False, "error": error_msg},
                {"display": "none"},
                100,
                f"Error: {display_error_msg}",
                f"Error: {outer_display_error_msg} (100%)",
                True,
                no_update,
                {"display": "none"},
                {"display": "none"},
                {"display": "none"},
                False,
            )  # Ensure panels stay hidden on error

    # --- NEW Animation Callback ---
    @app.callback(
        Output(ResultsIDs.BACKTEST_ANIMATED_TEXT, "children", allow_duplicate=True),
        Input(ResultsIDs.BACKTEST_ANIMATION_INTERVAL, "n_intervals"),
        State(ResultsIDs.BACKTEST_PROGRESS_BAR, "value"),
        State(ResultsIDs.BACKTEST_ANIMATION_INTERVAL, "disabled"),
        prevent_initial_call=True,
    )
    def update_animated_progress_text(
        n_intervals, current_progress_value, interval_disabled
    ):
        if (
            interval_disabled or n_intervals == 0
        ):  # Also check n_intervals to avoid update on first enable if not needed
            # When the interval is disabled (backtest not running or finished),
            # the run_backtest callback is responsible for setting the final static text.
            raise PreventUpdate

        # Ensure dots have consistent width using non-breaking spaces
        dots = [
            ".\u00a0\u00a0",
            "..\u00a0",
            "...",
        ]  # Replaced spaces with non-breaking spaces
        dot_str = dots[n_intervals % len(dots)]
        # Ensure current_progress_value is an int for formatting
        progress_percent = (
            int(current_progress_value) if current_progress_value is not None else 0
        )
        # Return the text and a span with the percentage to utilize the CSS spacing
        return [
            "Running backtest" + dot_str,
            html.Span(f"({progress_percent}%)", className="progress-bar-percentage"),
        ]

    # --- Result Update Callbacks (Triggered by Store) ---
    @app.callback(
        Output(ResultsIDs.PERFORMANCE_METRICS_CONTAINER, "children"),
        Output(ResultsIDs.TRADE_METRICS_CONTAINER, "children"),
        Output(ResultsIDs.TRADES_TABLE_CONTAINER, "children"),
        Output(ResultsIDs.PORTFOLIO_CHART, "figure"),
        Output(ResultsIDs.DRAWDOWN_CHART, "figure"),
        Output(ResultsIDs.MONTHLY_RETURNS_HEATMAP, "figure"),
        Output(ResultsIDs.SIGNALS_TICKER_SELECTOR, "options"),
        Output(ResultsIDs.SIGNALS_TICKER_SELECTOR, "value"),
        Output(ResultsIDs.RESULTS_AREA_WRAPPER, "style", allow_duplicate=True),
        Output(ResultsIDs.CENTER_PANEL_COLUMN, "style", allow_duplicate=True),
        Output(ResultsIDs.RIGHT_PANEL_COLUMN, "style", allow_duplicate=True),
        Output(ResultsIDs.PERFORMANCE_OVERVIEW_CARD, "style"),
        Output(ResultsIDs.TRADE_STATISTICS_CARD, "style"),
        Input(ResultsIDs.BACKTEST_RESULTS_STORE, "data"),
        prevent_initial_call=True,
    )
    def update_results_display(results_data):
        logger.info("--- update_results_display callback triggered ---")

        if not results_data or not results_data.get("success"):
            logger.warning(
                "--- update_results_display: results_data indicates failure or is invalid. Returning empty/default components and hiding panels."
            )
            empty_fig = create_empty_chart("No data available")
            # Always ensure panels are hidden when there's no valid data
            return (
                [],
                [],
                html.Div("Backtest failed or no data."),
                empty_fig,
                empty_fig,
                empty_fig,
                [],
                None,
                {"display": "none"},
                {"display": "none"},
                {"display": "none"},
                {"display": "none"},
                {"display": "none"},
            )

        metrics = results_data.get("metrics", {})
        trades_list = results_data.get("trades_data", [])

        # Make sure metrics is a dictionary, not None or empty list
        if not metrics or not isinstance(metrics, dict):
            logger.warning(
                "--- update_results_display: No metrics available or invalid metrics format"
            )
            metrics = {}

        # Make sure trades_list is a list, not None
        if not trades_list or not isinstance(trades_list, list):
            logger.warning(
                "--- update_results_display: No trades data available or invalid trades format"
            )
            trades_list = []

        trade_keys = {
            "trades-count",
            "winning-trades",
            "losing-trades",
            "win-rate",
            "profit-factor",
            "avg-trade",
            "avg-win",
            "avg-loss",
            "largest-win",
            "largest-loss",
        }

        perf_metrics = {k: v for k, v in metrics.items() if k not in trade_keys}
        trade_stats = {k: v for k, v in metrics.items() if k in trade_keys}

        # More robust check for meaningful data - ensure we have actual values to display
        has_performance_metrics = bool(perf_metrics) and any(
            v is not None and (not isinstance(v, (int, float)) or v != 0)
            for v in perf_metrics.values()
        )
        has_trade_stats = bool(trade_stats) and any(
            v is not None and (not isinstance(v, (int, float)) or v != 0)
            for v in trade_stats.values()
        )
        has_trades = (
            bool(trades_list)
            and len(trades_list) > 0
            and isinstance(trades_list[0], dict)
            and bool(trades_list[0])
        )

        has_meaningful_data = has_performance_metrics or has_trade_stats or has_trades

        if not has_meaningful_data:
            logger.warning(
                "--- update_results_display: Backtest successful but no meaningful data to display. Hiding panels."
            )
            empty_fig = create_empty_chart(
                "Backtest completed but no results to display"
            )
            return (
                [],
                [],
                html.Div("Backtest completed but no results to display."),
                empty_fig,
                empty_fig,
                empty_fig,
                [],
                None,
                {"display": "none"},
                {"display": "none"},
                {"display": "none"},
                {"display": "none"},
                {"display": "none"},
            )

        # Only create children components if we have meaningful data
        performance_metrics_children = []
        if has_performance_metrics:
            perf_rows = [
                ("Starting Balance", perf_metrics.get("starting-balance"), None),
                ("Ending Balance", perf_metrics.get("ending-balance"), None),
                ("Total Return %", perf_metrics.get("total-return"), perf_metrics.get("benchmark-return")),
                ("Excess Return %", perf_metrics.get("excess-return"), None),
                ("CAGR %", perf_metrics.get("cagr"), perf_metrics.get("benchmark-cagr")),
                ("Sharpe Ratio", perf_metrics.get("sharpe"), None),
                ("Sortino Ratio", perf_metrics.get("sortino"), None),
                ("Annual Volatility %", perf_metrics.get("annualized-volatility"), None),
                ("Max Drawdown %", perf_metrics.get("max-drawdown"), None),
                ("Calmar Ratio", perf_metrics.get("calmar-ratio"), None),
                ("Recovery Factor", perf_metrics.get("recovery-factor"), None),
                ("Alpha", perf_metrics.get("alpha"), None),
                ("Beta", perf_metrics.get("beta"), None),
                ("Information Ratio", perf_metrics.get("information-ratio"), None),
            ]

            performance_metrics_children = [
                dbc.Col(create_metrics_table(perf_rows), width=12)
            ]

        trade_metrics_children = []
        if has_trade_stats:
            trade_rows = [
                ("Trades Count", trade_stats.get("trades-count"), None),
                ("Winning Trades", trade_stats.get("winning-trades"), None),
                ("Losing Trades", trade_stats.get("losing-trades"), None),
                ("Win Rate %", trade_stats.get("win-rate"), None),
                ("Profit Factor", trade_stats.get("profit-factor"), None),
                ("Avg Trade %", trade_stats.get("avg-trade"), None),
                ("Avg Win PnL", trade_stats.get("avg-win"), None),
                ("Avg Loss PnL", trade_stats.get("avg-loss"), None),
                ("Largest Win PnL", trade_stats.get("largest-win"), None),
                ("Largest Loss PnL", trade_stats.get("largest-loss"), None),
            ]

            trade_metrics_children = [
                dbc.Col(create_metrics_table(trade_rows), width=12)
            ]

        # Create trades table only if we have valid trades data
        if has_trades:
            if trades_list and isinstance(trades_list[0], dict) and trades_list[0]:
                columns = [
                    {"name": "Entry Date", "id": "entry_date"},
                    {"name": "Exit Date", "id": "exit_date"},
                    {"name": "Ticker", "id": "ticker"},
                    {"name": "Direction", "id": "direction"},
                    {"name": "Entry Price", "id": "entry_price", "type": "numeric", "format": Format(precision=2, scheme=Scheme.fixed)},
                    {"name": "Exit Price", "id": "exit_price", "type": "numeric", "format": Format(precision=2, scheme=Scheme.fixed)},
                    {"name": "Size", "id": "size", "type": "numeric"},
                    {"name": "PnL", "id": "pnl", "type": "numeric", "format": Format(precision=2, scheme=Scheme.fixed)},
                    {"name": "Return %", "id": "return_pct", "type": "numeric", "format": Format(precision=2, scheme=Scheme.percentage)},
                    {"name": "Duration", "id": "duration"},
                    {"name": "Exit Reason", "id": "exit_reason"},
                ]
                trades_table_component = dash_table.DataTable(
                    data=trades_list,
                    columns=columns,
                    style_as_list_view=True,
                    style_header={
                        "backgroundColor": "rgb(30, 30, 30)",
                        "color": "white",
                        "fontWeight": "bold",
                    },
                    style_cell={
                        "backgroundColor": "rgb(50, 50, 50)",
                        "color": "white",
                        "textAlign": "left",
                        "padding": "5px",
                        "fontFamily": "inherit",
                        "fontSize": "14px",
                    },
                    style_data_conditional=[
                        {"if": {"filter_query": "{pnl} > 0", "column_id": "pnl"}, "color": "#28a745"},
                        {"if": {"filter_query": "{pnl} < 0", "column_id": "pnl"}, "color": "#dc3545"},
                    ],
                    page_size=10,
                )
            else:
                trades_table_component = html.Div(
                    "No trades executed or invalid trade data format."
                )
        else:
            trades_table_component = html.Div("No trades executed during the backtest.")

        # Process chart figures if available, otherwise create empty placeholders
        portfolio_chart_fig = None
        try:
            portfolio_chart_fig = (
                pio.from_json(results_data.get("portfolio_value_chart_json"))
                if results_data.get("portfolio_value_chart_json")
                else None
            )
        except Exception as e:
            logger.error(f"Error parsing portfolio chart: {e}")
        if not portfolio_chart_fig:
            portfolio_chart_fig = create_empty_chart(
                "Portfolio Value data not available"
            )

        drawdown_chart_fig = None
        try:
            drawdown_chart_fig = (
                pio.from_json(results_data.get("drawdown_chart_json"))
                if results_data.get("drawdown_chart_json")
                else None
            )
        except Exception as e:
            logger.error(f"Error parsing drawdown chart: {e}")
        if not drawdown_chart_fig:
            drawdown_chart_fig = create_empty_chart("Drawdown data not available")

        monthly_returns_heatmap_fig = None
        try:
            monthly_returns_heatmap_fig = (
                pio.from_json(results_data.get("monthly_returns_heatmap_json"))
                if results_data.get("monthly_returns_heatmap_json")
                else None
            )
        except Exception as e:
            logger.error(f"Error parsing monthly returns heatmap: {e}")
        if not monthly_returns_heatmap_fig:
            monthly_returns_heatmap_fig = create_empty_chart(
                "Monthly Returns data not available"
            )

        # Process ticker options
        tickers = results_data.get("selected_tickers", [])
        ticker_options = [{"label": t, "value": t} for t in tickers] if tickers else []
        ticker_value = tickers[0] if tickers else None

        logger.info(
            "--- update_results_display callback successfully processed data and is returning updates. ---"
        )

        # Only show panels if we have meaningful data to display
        if has_meaningful_data:
            logger.info("Showing result panels - meaningful data is available")
            return (
                performance_metrics_children,
                trade_metrics_children,
                trades_table_component,
                portfolio_chart_fig,
                drawdown_chart_fig,
                monthly_returns_heatmap_fig,
                ticker_options,
                ticker_value,
                {"display": "block"},  # RESULTS_AREA_WRAPPER
                {
                    "display": "block",
                    "paddingLeft": "3.75px",
                    "paddingRight": "3.75px",
                },  # CENTER_PANEL_COLUMN
                {"display": "block", "paddingLeft": "3.75px"},  # RIGHT_PANEL_COLUMN
                {"display": "block"},  # PERFORMANCE_OVERVIEW_CARD
                {"display": "block"},
            )  # TRADE_STATISTICS_CARD
        else:
            logger.warning(
                "Keeping result panels hidden - no meaningful data available"
            )
            return (
                [],
                [],
                html.Div("No meaningful backtest data to display."),
                create_empty_chart("No portfolio data"),
                create_empty_chart("No drawdown data"),
                create_empty_chart("No monthly returns data"),
                [],
                None,
                {"display": "none"},
                {"display": "none"},
                {"display": "none"},
                {"display": "none"},
                {"display": "none"},
            )

    logger.info("Backtest callbacks registered.")

    # --- New Interactive Chart Callbacks ---

    @app.callback(
        Output(ResultsIDs.PORTFOLIO_SETTINGS_POPOVER, "is_open"),
        Input(ResultsIDs.PORTFOLIO_SETTINGS_BUTTON, "n_clicks"),
        State(ResultsIDs.PORTFOLIO_SETTINGS_POPOVER, "is_open"),
        prevent_initial_call=True,
    )
    def toggle_portfolio_popover(n, is_open):
        if n:
            return not is_open
        return is_open

    @app.callback(
        Output(ResultsIDs.DRAWDOWN_SETTINGS_POPOVER, "is_open"),
        Input(ResultsIDs.DRAWDOWN_SETTINGS_BUTTON, "n_clicks"),
        State(ResultsIDs.DRAWDOWN_SETTINGS_POPOVER, "is_open"),
        prevent_initial_call=True,
    )
    def toggle_drawdown_popover(n, is_open):
        if n:
            return not is_open
        return is_open

    @app.callback(
        Output(ResultsIDs.PORTFOLIO_CHART, "figure", allow_duplicate=True),
        Output(ResultsIDs.PORTFOLIO_SETTINGS_STORE, "data"),
        Output(ResultsIDs.PORTFOLIO_VALUE_CURRENCY_USD, "outline"),
        Output(ResultsIDs.PORTFOLIO_VALUE_CURRENCY_PERCENT, "outline"),
        Output(ResultsIDs.PORTFOLIO_SCALE_LINEAR_BTN, "outline"),
        Output(ResultsIDs.PORTFOLIO_SCALE_LOG_BTN, "outline"),
        Input(ResultsIDs.PORTFOLIO_VALUE_CURRENCY_USD, "n_clicks"),
        Input(ResultsIDs.PORTFOLIO_VALUE_CURRENCY_PERCENT, "n_clicks"),
        Input(ResultsIDs.PORTFOLIO_SCALE_LINEAR_BTN, "n_clicks"),
        Input(ResultsIDs.PORTFOLIO_SCALE_LOG_BTN, "n_clicks"),
        State(ResultsIDs.PORTFOLIO_SETTINGS_STORE, "data"),
        State(ResultsIDs.BACKTEST_RESULTS_STORE, "data"),
        prevent_initial_call=True,
    )
    def update_portfolio_chart(
        usd_click, pct_click, lin_click, log_click, settings, results_data
    ):
        if not results_data:
            raise PreventUpdate
        settings = settings or {"y_axis": "usd", "scale": "linear"}
        triggered = ctx.triggered_id
        if triggered == ResultsIDs.PORTFOLIO_VALUE_CURRENCY_USD:
            settings["y_axis"] = "usd"
        elif triggered == ResultsIDs.PORTFOLIO_VALUE_CURRENCY_PERCENT:
            settings["y_axis"] = "percent"
        elif triggered == ResultsIDs.PORTFOLIO_SCALE_LINEAR_BTN:
            settings["scale"] = "linear"
        elif triggered == ResultsIDs.PORTFOLIO_SCALE_LOG_BTN:
            settings["scale"] = "log"

        fig_json = (
            results_data.get("portfolio_value_chart_json")
            if settings["y_axis"] == "usd"
            else results_data.get("portfolio_returns_chart_json")
        )
        if not fig_json:
            return dash.no_update, settings, False, True, False, True

        try:
            fig = pio.from_json(fig_json)
        except Exception as e:
            logger.error(f"Error decoding portfolio chart json: {e}")
            raise PreventUpdate

        fig.update_yaxes(type="log" if settings["scale"] == "log" else "linear")
        if settings["y_axis"] == "percent":
            fig.update_yaxes(ticksuffix="%", tickprefix=None)
        else:
            fig.update_yaxes(tickprefix="$", tickformat=",.0f")

        return (
            fig,
            settings,
            settings["y_axis"] != "usd",
            settings["y_axis"] != "percent",
            settings["scale"] != "linear",
            settings["scale"] != "log",
        )

    @app.callback(
        Output(ResultsIDs.DRAWDOWN_CHART, "figure", allow_duplicate=True),
        Output(ResultsIDs.DRAWDOWN_SETTINGS_STORE, "data"),
        Output(ResultsIDs.DRAWDOWN_YAXIS_USD_BTN, "outline"),
        Output(ResultsIDs.DRAWDOWN_YAXIS_PERCENT_BTN, "outline"),
        Output(ResultsIDs.DRAWDOWN_SCALE_LINEAR_BTN, "outline"),
        Output(ResultsIDs.DRAWDOWN_SCALE_LOG_BTN, "outline"),
        Input(ResultsIDs.DRAWDOWN_YAXIS_USD_BTN, "n_clicks"),
        Input(ResultsIDs.DRAWDOWN_YAXIS_PERCENT_BTN, "n_clicks"),
        Input(ResultsIDs.DRAWDOWN_SCALE_LINEAR_BTN, "n_clicks"),
        Input(ResultsIDs.DRAWDOWN_SCALE_LOG_BTN, "n_clicks"),
        State(ResultsIDs.DRAWDOWN_SETTINGS_STORE, "data"),
        State(ResultsIDs.BACKTEST_RESULTS_STORE, "data"),
        prevent_initial_call=True,
    )
    def update_drawdown_chart(
        usd_click, pct_click, lin_click, log_click, settings, results_data
    ):
        if not results_data:
            raise PreventUpdate
        settings = settings or {"y_axis": "percent", "scale": "linear"}
        triggered = ctx.triggered_id
        if triggered == ResultsIDs.DRAWDOWN_YAXIS_USD_BTN:
            settings["y_axis"] = "usd"
        elif triggered == ResultsIDs.DRAWDOWN_YAXIS_PERCENT_BTN:
            settings["y_axis"] = "percent"
        elif triggered == ResultsIDs.DRAWDOWN_SCALE_LINEAR_BTN:
            settings["scale"] = "linear"
        elif triggered == ResultsIDs.DRAWDOWN_SCALE_LOG_BTN:
            settings["scale"] = "log"

        fig_json = results_data.get("drawdown_chart_json")
        if not fig_json:
            return dash.no_update, settings, False, True, False, True

        try:
            fig = pio.from_json(fig_json)
        except Exception as e:
            logger.error(f"Error decoding drawdown chart json: {e}")
            raise PreventUpdate

        if settings["y_axis"] == "usd" and results_data.get(
            "portfolio_value_chart_json"
        ):
            pv_fig = pio.from_json(results_data["portfolio_value_chart_json"])
            for i, trace in enumerate(fig.data):
                if i < len(pv_fig.data):
                    pv = pd.Series(pv_fig.data[i].y)
                    rolling_max = pv.cummax()
                    dd = pv - rolling_max
                    trace.y = dd
            fig.update_yaxes(tickprefix="$", tickformat=",.0f")
        else:
            fig.update_yaxes(ticksuffix="%")

        fig.update_yaxes(type="log" if settings["scale"] == "log" else "linear")

        return (
            fig,
            settings,
            settings["y_axis"] != "usd",
            settings["y_axis"] != "percent",
            settings["scale"] != "linear",
            settings["scale"] != "log",
        )

    @app.callback(
        Output(ResultsIDs.SIGNALS_CHART, "figure"),
        Input(ResultsIDs.SIGNALS_TICKER_SELECTOR, "value"),
        State(ResultsIDs.BACKTEST_RESULTS_STORE, "data"),
        prevent_initial_call=True,
    )
    def update_signals_chart(ticker, results_data):
        """Update signals chart for selected ticker using strategy defaults."""
        if not ticker or not results_data:
            raise PreventUpdate

        strategy = (results_data.get("strategy_type") or "").upper()
        indicators = []
        if strategy == "MAC":
            indicators = ["sma50", "sma200"]
        elif strategy == "BB":
            indicators = ["bollinger"]
        elif strategy == "RSI":
            indicators = ["rsi"]

        fig = backtest_service.get_signals_chart(ticker, indicators)
        if fig is None:
            return create_empty_chart("No signal data")
        return fig
