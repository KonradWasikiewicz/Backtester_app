from dash import html, dcc, callback, Output, Input, State, ALL, MATCH, no_update, callback_context
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import logging
from typing import List, Dict, Any
import pandas as pd
import base64
import io

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
    
    # Combined callback for all date-related updates to avoid conflicts
    @app.callback(
        [Output("backtest-date-slider", "value", allow_duplicate=True),
         Output("slider-start-date-picker", "date"),
         Output("slider-end-date-picker", "date"),
         Output("backtest-daterange", "start_date"),
         Output("backtest-daterange", "end_date")],
        [Input("backtest-date-slider", "value"),
         Input("backtest-date-slider", "drag_value"),
         Input("slider-start-date-picker", "date"),
         Input("slider-end-date-picker", "date")],
        [State("backtest-date-slider", "min"),
         State("backtest-date-slider", "max")],
        prevent_initial_call=True
    )
    def update_all_date_components(date_range_timestamps, drag_value, start_date_picker, end_date_picker, min_allowed, max_allowed):
        """
        Update all date-related components based on which one changed.
        Handles slider movements, slider dragging, and date picker changes.
        
        Returns:
            Updated values for all date-related components
        """
        ctx = callback_context
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
        
        try:
            # If triggered by date picker (direct selection)
            if triggered_id in ["slider-start-date-picker", "slider-end-date-picker"]:
                # Get the dates from the date pickers
                if not start_date_picker or not end_date_picker:
                    raise PreventUpdate
                
                start_date = pd.to_datetime(start_date_picker)
                end_date = pd.to_datetime(end_date_picker)
                
                # Make sure end date is not before start date
                if end_date < start_date:
                    if triggered_id == "slider-start-date-picker":
                        end_date = start_date
                    else:
                        start_date = end_date
                
                # Convert to timestamps for slider
                start_ts = int(start_date.timestamp() * 1000)
                end_ts = int(end_date.timestamp() * 1000)
                
                # Ensure dates are within allowed range
                start_ts = max(min_allowed, min(max_allowed, start_ts))
                end_ts = max(min_allowed, min(max_allowed, end_ts))
                
                # Format the dates for other components
                start_date_str = start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')
                
                return [start_ts, end_ts], start_date_str, end_date_str, start_date_str, end_date_str
            
            # If triggered by slider
            else:
                # Use drag value during dragging, otherwise use the final value
                values_to_use = drag_value if drag_value is not None and triggered_id == "backtest-date-slider" else date_range_timestamps
                
                if not values_to_use or len(values_to_use) != 2:
                    raise PreventUpdate
                
                # Convert timestamps (ms) back to datetime
                start_ts, end_ts = values_to_use
                start_date = pd.to_datetime(start_ts, unit='ms')
                end_date = pd.to_datetime(end_ts, unit='ms')
                
                # Format for display
                start_date_str = start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')
                
                return [start_ts, end_ts], start_date_str, end_date_str, start_date_str, end_date_str
                
        except Exception as e:
            logger.error(f"Error updating date components: {e}")
            raise PreventUpdate
    
    # Add a callback specifically for updating the display dates during slider movement
    @app.callback(
        [Output("selected-start-date", "children", allow_duplicate=True),
         Output("selected-end-date", "children", allow_duplicate=True)],
        [Input("backtest-date-slider", "value"),
         Input("backtest-date-slider", "drag_value")],
        prevent_initial_call=True
    )
    def update_date_display(date_range_timestamps, drag_value):
        """
        Update the display of selected dates when the slider is moved.
        This provides immediate visual feedback during dragging.
        """
        # Use drag_value during dragging if available
        values_to_use = drag_value if drag_value is not None else date_range_timestamps
        
        if not values_to_use or len(values_to_use) != 2:
            return "N/A", "N/A"
        
        try:
            # Convert timestamps (ms) back to datetime
            start_ts, end_ts = values_to_use
            start_date = pd.to_datetime(start_ts, unit='ms')
            end_date = pd.to_datetime(end_ts, unit='ms')
            
            # Format for display
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            return start_date_str, end_date_str
        except Exception as e:
            logger.error(f"Error updating date display: {e}")
            return "Error", "Error"

    # Zastępuję problematyczne callbacky wykorzystujące nieistniejącą właściwość is_open
    # Usunięcie callbacków otwierających kalendarz po kliknięciu na przycisk daty
    @app.callback(
        [Output("slider-start-date-picker", "date", allow_duplicate=True),
         Output("selected-start-date", "children")],
        Input("selected-start-date", "n_clicks"),
        State("slider-start-date-picker", "date"),
        prevent_initial_call=True
    )
    def handle_start_date_click(n_clicks, current_date):
        """Aktualizuje tekst wyświetlania daty po zmianie w datepicker"""
        # Ten callback nie otwiera kalendarza (bo nie ma takiej właściwości), 
        # ale wyświetla aktualną datę po kliknięciu
        if n_clicks:
            if current_date:
                formatted_date = pd.to_datetime(current_date).strftime('%Y-%m-%d')
                return current_date, formatted_date
        raise PreventUpdate

    @app.callback(
        [Output("slider-end-date-picker", "date", allow_duplicate=True),
         Output("selected-end-date", "children", allow_duplicate=True)],
        Input("selected-end-date", "n_clicks"),
        State("slider-end-date-picker", "date"),
        prevent_initial_call=True
    )
    def handle_end_date_click(n_clicks, current_date):
        """Aktualizuje tekst wyświetlania daty po zmianie w datepicker"""
        if n_clicks:
            if current_date:
                formatted_date = pd.to_datetime(current_date).strftime('%Y-%m-%d')
                return current_date, formatted_date
        raise PreventUpdate

    # Callback do synchronizacji dat po zmianie w kalendarzu
    @app.callback(
        Output("backtest-date-slider", "value", allow_duplicate=True),
        [Input("slider-start-date-picker", "date"),
         Input("slider-end-date-picker", "date")],
        [State("backtest-date-slider", "min"),
         State("backtest-date-slider", "max"),
         State("backtest-date-slider", "value")],
        prevent_initial_call=True
    )
    def update_slider_from_pickers(start_date_str, end_date_str, min_allowed, max_allowed, current_value):
        """
        Aktualizuje suwak po zmianie daty w kalendarzu.
        """
        ctx = callback_context
        if not ctx.triggered:
            return current_value
        
        # Określamy, który picker został użyty
        input_id = ctx.triggered[0]['prop_id'].split('.')[0]
        try:
            if input_id == "slider-start-date-picker" and start_date_str:
                start_date = pd.to_datetime(start_date_str)
                start_ts = int(start_date.timestamp() * 1000)
                # Zachowaj obecną datę końcową
                end_ts = current_value[1] if current_value and len(current_value) > 1 else max_allowed
                
                # Upewniamy się, że data początkowa nie jest później niż końcowa
                if start_ts > end_ts:
                    start_ts = end_ts
                
                return [max(min_allowed, min(max_allowed, start_ts)), end_ts]
            
            elif input_id == "slider-end-date-picker" and end_date_str:
                end_date = pd.to_datetime(end_date_str)
                end_ts = int(end_date.timestamp() * 1000)
                # Zachowaj obecną datę początkową
                start_ts = current_value[0] if current_value and len(current_value) > 0 else min_allowed
                
                # Upewniamy się, że data końcowa nie jest wcześniej niż początkowa
                if end_ts < start_ts:
                    end_ts = start_ts
                
                return [start_ts, min(max_allowed, max(min_allowed, end_ts))]
            
            return current_value
        
        except Exception as e:
            logger.error(f"Error updating slider from date pickers: {e}")
            return current_value

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
        Input({"type": "ticker-checkbox", "index": ALL}, "value"),
        State({"type": "ticker-checkbox", "index": ALL}, "id")
    )
    def update_backtest_button_state(checkbox_values, checkbox_ids):
        """
        Aktualizuje stan przycisku "Run Backtest" i listę wybranych tickerów.
        """
        if not checkbox_values or not checkbox_ids:
            return True, []
        
        # Sprawdź czy którykolwiek ticker jest zaznaczony
        any_selected = any(checkbox_values)
        
        # Zbierz zaznaczone tickery dla komponentu ticker-selector
        selected_tickers = []
        for i, is_checked in enumerate(checkbox_values):
            if is_checked and i < len(checkbox_ids):
                selected_tickers.append(checkbox_ids[i]["index"])
        
        # Ustaw disabled=True jeśli nie ma zaznaczonych tickerów
        button_disabled = not any_selected
        
        logger.info(f"Stan przycisku Run Backtest zaktualizowany: disabled={button_disabled}, wybrano {len(selected_tickers)} tickerów")
        return button_disabled, selected_tickers
    
    # Usuń możliwe konflikty - wyraźnie usuń duplikujące się callbacki

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

    @app.callback(
        Output("backtest-date-slider", "value", allow_duplicate=True),
        [Input("date-range-1m", "n_clicks"),
         Input("date-range-3m", "n_clicks"),
         Input("date-range-6m", "n_clicks"),
         Input("date-range-1y", "n_clicks"),
         Input("date-range-2y", "n_clicks"),
         Input("date-range-all", "n_clicks")],
        [State("backtest-date-slider", "min"),
         State("backtest-date-slider", "max")],
        prevent_initial_call=True
    )
    def handle_quick_date_ranges(n_clicks_1m, n_clicks_3m, n_clicks_6m, n_clicks_1y, n_clicks_2y, n_clicks_all, min_date_ts, max_date_ts):
        """
        Obsługuje przyciski szybkiego wyboru zakresów dat.
        Ustawia zakres dat na podstawie klikniętego przycisku.
        """
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
            
        # Identyfikujemy, który przycisk został kliknięty
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        now = pd.Timestamp.now()
        
        if button_id == "date-range-1m":
            start_date = now - pd.DateOffset(months=1)
        elif button_id == "date-range-3m":
            start_date = now - pd.DateOffset(months=3)
        elif button_id == "date-range-6m":
            start_date = now - pd.DateOffset(months=6)
        elif button_id == "date-range-1y":
            start_date = now - pd.DateOffset(years=1)
        elif button_id == "date-range-2y":
            start_date = now - pd.DateOffset(years=2)
        elif button_id == "date-range-all":
            # Używamy pełnego dostępnego zakresu
            return [min_date_ts, max_date_ts]
        else:
            raise PreventUpdate
            
        # Konwersja dat do timestampów dla slidera
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(now.timestamp() * 1000)
        
        # Upewniamy się, że daty są w dopuszczalnym zakresie
        start_ts = max(min_date_ts, min(max_date_ts, start_ts))
        end_ts = max(min_date_ts, min(max_date_ts, end_ts))
        
        # Aktualizujemy slider i pola dat
        return [start_ts, end_ts]