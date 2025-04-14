from dash import html, dcc, callback, Output, Input, State, ALL, MATCH, no_update, callback_context
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import logging
from typing import List, Dict, Any
import pandas as pd
import base64
import io
import inspect

# Configure logging
logger = logging.getLogger(__name__)

# Import local modules
from src.core.constants import AVAILABLE_STRATEGIES
from src.core.data import DataLoader
from src.ui.layouts.strategy_config import generate_strategy_parameters
# Usuwam, gdy nie potrzebujemy tworzyć tej sekcji ponownie
# from src.ui.layouts.risk_management import create_risk_management_section

def register_strategy_callbacks(app):
    """
    Register all strategy-related callbacks with the Dash app.
    
    Args:
        app: The Dash application instance
    """
    
    # Define strategy descriptions for display
    strategy_descriptions = {
        'MA': {
            'name': 'Moving Average Crossover',
            'description': [
                'Uses crossing of two moving averages to generate signals',
                'Buy when fast MA crosses above slow MA',
                'Sell when fast MA crosses below slow MA',
                'Effective in trending markets'
            ]
        },
        'RSI': {
            'name': 'Relative Strength Index',
            'description': [
                'Uses overbought/oversold conditions to generate signals',
                'Buy when RSI crosses above oversold threshold',
                'Sell when RSI crosses below overbought threshold',
                'Effective in ranging markets'
            ]
        },
        'BB': {
            'name': 'Bollinger Bands',
            'description': [
                'Uses price movement relative to volatility bands',
                'Buy when price touches lower band and starts rising',
                'Sell when price touches upper band and starts falling',
                'Adapts to changing market volatility'
            ]
        }
    }
    
    @app.callback(
        Output("strategy-description", "children"),
        Input("strategy-selector", "value")
    )
    def update_strategy_description(strategy_type):
        """
        Update the strategy description when a strategy is selected.
        
        Args:
            strategy_type: The selected strategy type
            
        Returns:
            List of HTML components with the strategy description
        """
        if not strategy_type or strategy_type not in strategy_descriptions:
            return []
        
        description = strategy_descriptions[strategy_type]
        
        return [
            html.H6(description['name'], className="text-light mb-2"),
            html.Ul([
                html.Li(point, className="text-light small") 
                for point in description['description']
            ], className="ps-3")
        ]
    
    @app.callback(
        Output("strategy-parameters", "children"),
        Input("strategy-selector", "value")
    )
    def update_strategy_parameters(strategy_type):
        """
        Update the strategy parameters UI based on the selected strategy.
        
        Args:
            strategy_type: The selected strategy type
            
        Returns:
            HTML div with strategy-specific parameter controls
        """
        if not strategy_type or strategy_type not in AVAILABLE_STRATEGIES:
            return []
            
        strategy_class = AVAILABLE_STRATEGIES[strategy_type]
        
        # Extract default params from the strategy class
        strategy_init = inspect.signature(strategy_class.__init__)
        params = {}
        
        # Skip self parameter
        for param_name, param in list(strategy_init.parameters.items())[1:]:
            if param.default is not inspect.Parameter.empty:
                params[param_name] = param.default
                
        if not params:
            return html.Div(
                "This strategy has no configurable parameters.",
                className="text-light font-italic"
            )
            
        # Build parameter inputs
        parameter_inputs = []
        
        for i, (param_name, default_value) in enumerate(params.items()):
            # Create a more user-friendly name
            display_name = " ".join(word.capitalize() for word in param_name.split("_"))
            
            # Create parameter control based on type
            if isinstance(default_value, bool):
                # Boolean parameter gets a switch
                parameter_control = create_boolean_parameter(param_name, default_value, i)
            elif isinstance(default_value, int) or isinstance(default_value, float):
                # Numeric parameters get a slider or number input
                parameter_control = create_numeric_parameter(param_name, default_value, i)
            else:
                # Text parameters get a text input
                parameter_control = create_text_parameter(param_name, default_value, i)
            
            parameter_row = dbc.Row(
                dbc.Col([
                    dbc.Label(display_name, html_for=f"param-{param_name}", className="text-light mb-1"),
                    parameter_control,
                    html.Small(
                        f"Default: {default_value}",
                        className="text-muted d-block mt-1"
                    )
                ])
            )
            parameter_inputs.append(parameter_row)
        
        return html.Div([
            html.H6("Strategy Parameters", className="text-light mb-3"),
            *parameter_inputs
        ], style={"backgroundColor": "#2a2e39", "padding": "15px", "borderRadius": "5px"})
    
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
    
    # Updated date range callback
    @app.callback(
        [Output("date-range-preview", "children"),
         Output("backtest-start-date", "date"),
         Output("backtest-end-date", "date")],
        [Input("backtest-start-date", "date"),
         Input("backtest-end-date", "date"),
         Input("date-range-1m", "n_clicks"),
         Input("date-range-3m", "n_clicks"),
         Input("date-range-6m", "n_clicks"),
         Input("date-range-1y", "n_clicks"),
         Input("date-range-2y", "n_clicks"),
         Input("date-range-all", "n_clicks")],
        [State("backtest-start-date", "min_date_allowed"),
         State("backtest-end-date", "max_date_allowed")],
        prevent_initial_call=True
    )
    def update_date_range(start_date, end_date, n_clicks_1m, n_clicks_3m, n_clicks_6m, 
                         n_clicks_1y, n_clicks_2y, n_clicks_all, min_date_allowed, max_date_allowed):
        """
        Handle date selection through the date pickers or preset buttons
        """
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        try:
            data_loader = DataLoader()
            min_date, max_date = data_loader.get_date_range()
            now = pd.Timestamp.now()
            
            # For preset buttons
            if triggered_id.startswith("date-range-"):
                if triggered_id == "date-range-1m":
                    start_date_obj = now - pd.DateOffset(months=1)
                    end_date_obj = now
                elif triggered_id == "date-range-3m":
                    start_date_obj = now - pd.DateOffset(months=3)
                    end_date_obj = now
                elif triggered_id == "date-range-6m":
                    start_date_obj = now - pd.DateOffset(months=6)
                    end_date_obj = now
                elif triggered_id == "date-range-1y":
                    start_date_obj = now - pd.DateOffset(years=1)
                    end_date_obj = now
                elif triggered_id == "date-range-2y":
                    start_date_obj = now - pd.DateOffset(years=2)
                    end_date_obj = now
                elif triggered_id == "date-range-all":
                    start_date_obj = min_date if min_date else pd.Timestamp('2020-01-01')
                    end_date_obj = max_date if max_date else now
                
                # Format for date picker
                start_date = start_date_obj.strftime('%Y-%m-%d')
                end_date = end_date_obj.strftime('%Y-%m-%d')
            # Date picker changes
            else:
                if not start_date or not end_date:
                    raise PreventUpdate
                    
                # Parse dates
                start_date_obj = pd.to_datetime(start_date)
                end_date_obj = pd.to_datetime(end_date)
                
                # Ensure end date is not before start date
                if end_date_obj < start_date_obj:
                    if triggered_id == "backtest-start-date":
                        end_date_obj = start_date_obj
                        end_date = start_date
                    else:
                        start_date_obj = end_date_obj
                        start_date = end_date
            
            # Create preview text
            preview_text = f"Selected period: {start_date} to {end_date}"
            
            return preview_text, start_date, end_date
            
        except Exception as e:
            logger.error(f"Error in update_date_range: {e}")
            # Return existing values if there's an error
            return f"Selected period: {start_date} to {end_date}", start_date, end_date

    # Remove the problematic duplicate date range callbacks
    
    # --- CAŁKOWITA REORGANIZACJA CALLBACKÓW TICKERÓW ---
    # Usunięcie wszystkich poprzednich callbacków dotyczących tickerów
    # i zastąpienie ich nowymi, lepiej zorganizowanymi callbackami
    
    # 1. Callback do filtrowania widoczności tickerów (tylko UI, nie wpływa na stan)
    @app.callback(
        Output({"type": "ticker-checkbox-container", "index": ALL}, "style"),
        Input("ticker-search", "value"),
        State({"type": "ticker-checkbox", "index": ALL}, "id")
    )
    def filter_ticker_visibility(search_term, checkbox_ids):
        """
        Filtruje widoczność tickerów na podstawie wyszukiwania.
        """
        styles = []
        if not search_term:
            # Jeśli nie ma filtra, pokaż wszystkie
            return [{"display": "block"} for _ in checkbox_ids]
        
        # Filtruj według wyszukiwanego tekstu
        for ticker in checkbox_ids:
            ticker_name = ticker["index"]
            if search_term.lower() in ticker_name.lower():
                styles.append({"display": "block"})
            else:
                styles.append({"display": "none"})
        
        return styles
    
    # 2. Główny callback do obsługi akcji przycisków Select All i Clear All
    @app.callback(
        Output({"type": "ticker-checkbox", "index": ALL}, "value"),
        [Input("select-all-tickers", "n_clicks"),
         Input("clear-all-tickers", "n_clicks")],
        [State({"type": "ticker-checkbox", "index": ALL}, "id"),
         State({"type": "ticker-checkbox", "index": ALL}, "value"),
         State("ticker-search", "value")]
    )
    def handle_ticker_selection_buttons(select_clicks, clear_clicks, 
                                       checkbox_ids, current_values, search_filter):
        """
        Obsługuje przyciski "Select All" i "Clear All" dla tickerów.
        """
        if not checkbox_ids:
            raise PreventUpdate
        
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
        
        # Sprawdź który przycisk został kliknięty
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Użyj bieżących wartości lub utwórz nowe jeśli nie istnieją
        values = list(current_values) if current_values else [False] * len(checkbox_ids)
        
        # Określ widoczne tickery (według filtra)
        visible_tickers = []
        for i, ticker in enumerate(checkbox_ids):
            ticker_name = ticker["index"]
            if not search_filter or search_filter.lower() in ticker_name.lower():
                visible_tickers.append(i)
        
        # Wykonaj odpowiednią akcję
        if button_id == "select-all-tickers":
            # Zaznacz wszystkie widoczne
            for i in visible_tickers:
                values[i] = True
        elif button_id == "clear-all-tickers":
            # Odznacz wszystkie widoczne
            for i in visible_tickers:
                values[i] = False
        
        logger.info(f"Zaktualizowano wybór tickerów po akcji: {button_id}")
        return values
    
    # 3. Oddzielny callback do synchronizacji stanu przycisku "Run Backtest" i komponentu ticker-selector
    @app.callback(
        [Output("run-backtest-button", "disabled"),
         Output("ticker-selector", "value")],
        [Input({"type": "ticker-checkbox", "index": ALL}, "value"),
         Input("wizard-progress", "value"),
         Input("summary-strategy", "children"),
         Input("summary-tickers", "children")],
        State({"type": "ticker-checkbox", "index": ALL}, "id")
    )
    def update_run_backtest_button(checkbox_values, progress, strategy, tickers, checkbox_ids):
        """
        Update the state of the "Run Backtest" button and the selected tickers list.
        """
        if not checkbox_values or not checkbox_ids:
            return True, []

        # Check if any ticker is selected
        any_selected = any(checkbox_values)

        # Gather selected tickers for the ticker-selector component
        selected_tickers = []
        for i, is_checked in enumerate(checkbox_values):
            if is_checked and i < len(checkbox_ids):
                selected_tickers.append(checkbox_ids[i]["index"])

        # Set disabled=True if no tickers are selected
        button_disabled = not any_selected

        logger.info(f"Run Backtest button state updated: disabled={button_disabled}, {len(selected_tickers)} tickers selected")
        return button_disabled, selected_tickers

    @app.callback(
        Output("import-tickers-modal", "is_open"),
        [Input("import-tickers", "n_clicks"),
         Input("import-tickers-close", "n_clicks"),
         Input("import-tickers-submit", "n_clicks")],
        [State("import-tickers-modal", "is_open")]
    )
    def toggle_import_modal(open_clicks, close_clicks, submit_clicks, is_open):
        """
        Toggle the import tickers modal.
        """
        if open_clicks or close_clicks or submit_clicks:
            return not is_open
        return is_open

    # New unified callback to handle wizard steps properly
    @app.callback(
        [Output("wizard-progress", "value"),
         Output("step1-collapse", "is_open"),
         Output("step2-collapse", "is_open"),
         Output("step3-collapse", "is_open"),
         Output("step1-summary-collapse", "is_open"),
         Output("step2-summary-collapse", "is_open"),
         Output("step3-summary-collapse", "is_open"),
         Output("step1-status", "className"),
         Output("step2-status", "className"),
         Output("step3-status", "className"),
         Output("step1-header-card", "className"),
         Output("step2-header-card", "className"),
         Output("step3-header-card", "className")],
        [Input("confirm-step1-btn", "n_clicks"),
         Input("confirm-step2-btn", "n_clicks"),
         Input("step1-header-card", "n_clicks"),
         Input("step2-header-card", "n_clicks"),
         Input("step3-header-card", "n_clicks")],
        State("wizard-progress", "value"),
        prevent_initial_call=True
    )
    def handle_wizard_steps(confirm_step1, confirm_step2, 
                           click_step1, click_step2, click_step3, 
                           current_progress):
        """
        Handle wizard step transitions and UI state
        """
        ctx = callback_context
        if not ctx.triggered:
            # Initial state
            return (
                0,  # progress value
                True, False, False,  # step collapses
                False, False, False,  # summary collapses
                "", "", "",  # step status icons
                "mb-2", "mb-2", "mb-2"  # header card classes
            )
        
        # Get the ID of the element that triggered the callback
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Default values that will be updated based on trigger
        step1_open = False
        step2_open = False
        step3_open = False
        step1_summary = False
        step2_summary = False 
        step3_summary = False
        step1_status = ""
        step2_status = ""
        step3_status = ""
        step1_header = "mb-2"
        step2_header = "mb-2"
        step3_header = "mb-2"
        progress = current_progress or 0
        
        # Process wizard step transitions based on trigger
        if trigger_id == "confirm-step1-btn":
            # User completed Step 1, move to Step 2
            step1_open = False
            step2_open = True 
            step3_open = False
            step1_summary = True
            step1_status = "fas fa-check text-success"
            progress = 33
            step1_header = "mb-2 border-success"
        elif trigger_id == "confirm-step2-btn":
            # User completed Step 2, move to Step 3
            step1_open = False
            step2_open = False
            step3_open = True
            step1_summary = True
            step2_summary = True
            step1_status = "fas fa-check text-success"
            step2_status = "fas fa-check text-success"
            progress = 66
            step1_header = "mb-2 border-success"
            step2_header = "mb-2 border-success"
        elif trigger_id == "step1-header-card":
            # User clicked Step 1 header
            step1_open = True
            step2_open = False
            step3_open = False
            step1_summary = False if progress < 33 else True
            step2_summary = True if progress >= 66 else False
            step1_header = "mb-2 border-primary"
        elif trigger_id == "step2-header-card":
            # User clicked Step 2 header
            if progress >= 33:  # Only allow if Step 1 was completed
                step1_open = False
                step2_open = True
                step3_open = False
                step1_summary = True
                step2_summary = False if progress < 66 else True
                step2_header = "mb-2 border-primary"
        elif trigger_id == "step3-header-card":
            # User clicked Step 3 header
            if progress >= 66:  # Only allow if Step 2 was completed
                step1_open = False
                step2_open = False
                step3_open = True
                step1_summary = True
                step2_summary = True
                step3_header = "mb-2 border-primary"
        
        # Update status icons based on progress
        if progress >= 33:
            step1_status = "fas fa-check text-success"
        if progress >= 66:
            step2_status = "fas fa-check text-success"
        if progress >= 100:
            step3_status = "fas fa-check text-success"
            
        logger.info(f"Wizard step transition: trigger={trigger_id}, progress={progress}")
        
        return (
            progress,
            step1_open, step2_open, step3_open,
            step1_summary, step2_summary, step3_summary,
            step1_status, step2_status, step3_status,
            step1_header, step2_header, step3_header
        )

    # Create summaries of each step's content
    @app.callback(
        [Output("step1-content-summary", "children"),
         Output("step2-content-summary", "children"),
         Output("step3-content-summary", "children"),
         Output("step1-header-summary", "children"),
         Output("step2-header-summary", "children"),
         Output("step3-header-summary", "children")],
        [Input("strategy-selector", "value"),
         Input("slider-start-date-picker", "date"),
         Input("slider-end-date-picker", "date"),
         Input({"type": "ticker-checkbox", "index": ALL}, "value"),
         Input("risk-features-checklist", "value"),
         Input("stop-loss-type", "value"),
         Input("stop-loss-value", "value"),
         Input("wizard-progress", "value")],
        [State({"type": "ticker-checkbox", "index": ALL}, "id"),
         State("wizard-state", "data")]
    )
    def update_step_summaries(strategy, start_date, end_date, 
                             ticker_values, risk_features,
                             stop_loss_type, stop_loss_value, wizard_progress,
                             ticker_ids, wizard_state):
        """
        Update the summaries for each wizard step
        """
        if not wizard_progress:
            # No progress yet, don't update summaries
            return ["", "", "", "", "", ""]
            
        # Calculate selected tickers
        selected_tickers = []
        if ticker_ids and ticker_values:
            for i, is_selected in enumerate(ticker_values):
                if is_selected and i < len(ticker_ids):
                    selected_tickers.append(ticker_ids[i]["index"])
                    
        # Format dates for display
        date_range = f"{start_date} to {end_date}" if start_date and end_date else "Not set"
        
        # Create Step 1 Summary
        step1_summary = html.Div([
            html.H6("Strategy & Assets", className="mb-2"),
            dbc.Row([
                dbc.Col([
                    html.Strong("Strategy: "),
                    html.Span(strategy or "None selected")
                ], width=6),
                dbc.Col([
                    html.Strong("Date Range: "),
                    html.Span(date_range)
                ], width=6)
            ]),
            dbc.Row([
                dbc.Col([
                    html.Strong("Selected Tickers: "),
                    html.Span(
                        f"{len(selected_tickers)} tickers" if selected_tickers else "None"
                    )
                ], width=12)
            ])
        ])
        
        step1_header = f"{strategy or 'No strategy'}, {len(selected_tickers)} assets"
        
        # Create Step 2 Summary
        if wizard_progress >= 33:
            enabled_features = risk_features or []
            risk_summary = ", ".join([f.replace("_", " ").title() for f in enabled_features]) if enabled_features else "None"
            
            step2_summary = html.Div([
                html.H6("Risk Management", className="mb-2"),
                dbc.Row([
                    dbc.Col([
                        html.Strong("Enabled Features: "),
                        html.Span(risk_summary)
                    ], width=12)
                ]),
                dbc.Row([
                    dbc.Col([
                        html.Strong("Stop Loss: "),
                        html.Span(
                            f"{stop_loss_type} ({stop_loss_value})" if stop_loss_type != "none" else "None"
                        )
                    ], width=12)
                ])
            ])
            
            step2_header = f"{len(enabled_features)} risk features"
        else:
            step2_summary = ""
            step2_header = ""
            
        # Create Step 3 Summary
        if wizard_progress >= 66:
            step3_summary = html.Div([
                html.H6("Ready to Run", className="mb-2"),
                html.P("Configuration complete. Click Run Backtest to execute.")
            ])
            
            step3_header = "Ready to run"
        else:
            step3_summary = ""
            step3_header = ""
            
        return [step1_summary, step2_summary, step3_summary, step1_header, step2_header, step3_header]

def create_boolean_parameter(param_name, default_value, index):
    """Creates a boolean parameter input."""
    return dbc.Checkbox(
        id={"type": "strategy-param", "index": param_name},
        value=default_value,
        className="form-check-input"
    )
    
def create_numeric_parameter(param_name, default_value, index):
    """Creates a numeric parameter input."""
    # Determine if integer or float
    step = 1 if isinstance(default_value, int) else 0.1
    
    # Set reasonable min/max based on parameter name and default value
    if "period" in param_name.lower() or "window" in param_name.lower():
        # For periods or windows, range from 2 to 200
        min_val = 2
        max_val = 200
    elif "threshold" in param_name.lower() or "level" in param_name.lower():
        # For thresholds, range from 0 to 100
        min_val = 0
        max_val = 100
    else:
        # Default ranges
        min_val = 0 if default_value > 0 else default_value * 2
        max_val = default_value * 5 if default_value > 0 else abs(default_value) * 5
        max_val = max(max_val, min_val + 10*step)
    
    return dbc.InputGroup([
        dbc.Input(
            id={"type": "strategy-param", "index": param_name},
            type="number",
            value=default_value,
            step=step,
            min=min_val,
            max=max_val,
            className="bg-dark text-light border-secondary"
        )
    ])
    
def create_text_parameter(param_name, default_value, index):
    """Creates a text parameter input."""
    return dbc.Input(
        id={"type": "strategy-param", "index": param_name},
        type="text",
        value=str(default_value),
        className="bg-dark text-light border-secondary"
    )