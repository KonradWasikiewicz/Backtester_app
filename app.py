import dash
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from dash import dcc, html, dash_table, callback, Output, Input, State, ALL, MATCH, ctx
import sys
import traceback
from pathlib import Path
import logging
import plotly.graph_objects as go
import inspect # Do inspekcji parametrów strategii

# --- Konfiguracja Logowania ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backtest.log", mode='w'), # Tryb 'w' nadpisuje log przy każdym uruchomieniu
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
# Zmniejszenie gadatliwości niektórych modułów
logging.getLogger('src.portfolio.portfolio_manager').setLevel(logging.INFO)
logging.getLogger('src.portfolio.risk_manager').setLevel(logging.INFO)
logging.getLogger('src.core.backtest_manager').setLevel(logging.INFO)
logging.getLogger('src.core.data').setLevel(logging.INFO)
logging.getLogger('src.core.engine').setLevel(logging.INFO)


# --- Dodawanie Ścieżki i Importy Lokalne ---
project_root = Path(__file__).parent.absolute()
sys.path.append(str(project_root))
try:
    from src.core.config import config
    from src.core.constants import AVAILABLE_STRATEGIES, CHART_THEME
    from src.core.data import DataLoader
    from src.core.backtest_manager import BacktestManager
    from src.portfolio.risk_manager import RiskManager
    # Importuj Visualizer, aby móc go używać
    from src.visualization.visualizer import BacktestVisualizer
    from src.visualization.chart_utils import create_styled_chart, create_empty_chart, create_allocation_chart # Usunięto create_trade_histogram_figure, bo używamy visualizera
    from src.ui.components import create_metric_card, create_metric_card_with_tooltip
    from src.analysis.metrics import (
        calculate_trade_statistics, calculate_alpha, calculate_beta,
        calculate_information_ratio, calculate_recovery_factor
    )
except ImportError as e:
    logger.error(f"CRITICAL: Failed to import local modules: {e}. Ensure script is run from project root or PYTHONPATH is set correctly.")
    logger.error(traceback.format_exc())
    sys.exit(1)


# --- Inicjalizacja Aplikacji Dash ---
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY, 'https://use.fontawesome.com/releases/v5.15.4/css/all.css'],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    assets_folder='assets',
    suppress_callback_exceptions=True
)
app.title = "Trading Strategy Backtester"
server = app.server

# --- Inicjalizacja Managerów i Wizualizatora ---
try:
    backtest_manager = BacktestManager(initial_capital=config.INITIAL_CAPITAL)
    visualizer = BacktestVisualizer() # Inicjalizacja Visualizera
    data_loader = DataLoader(data_path=config.DATA_PATH)
    logger.info("Managers and DataLoader initialized successfully.")
except Exception as e:
    logger.error(f"CRITICAL: Failed to initialize managers: {e}")
    logger.error(traceback.format_exc())
    sys.exit(1)

# --- Funkcje Pomocnicze (w tym definicja create_trade_table) ---

def get_available_tickers():
    """Dynamically load available tickers from the DataLoader."""
    try:
        tickers = data_loader.get_available_tickers()
        if not tickers:
             logger.warning("DataLoader returned no available tickers.")
             return []
        benchmark_ticker = config.BENCHMARK_TICKER
        available = sorted([t for t in tickers if t != benchmark_ticker])
        logger.info(f"Available tickers for selection: {available}")
        return available
    except Exception as e:
        logger.error(f"Error getting available tickers via DataLoader: {e}")
        traceback.print_exc()
        return []

def create_metric_cards(stats: dict):
    """Create metric cards layout."""
    # Definicja tej funkcji pozostaje bez zmian (jak w poprzedniej odpowiedzi)
    if not stats: # Jeśli słownik stats jest pusty
        return html.Div([
             dbc.Row([
                 dbc.Col(create_metric_card_with_tooltip("Status", "Run backtest to see metrics.", tooltip_text="Perform a backtest calculation to view performance details."), width=12)
             ])
        ], className="mb-1")

    tooltip_texts = {
        'Initial Capital': "Starting capital at the beginning of the backtest period.",
        'Final Capital': "Ending portfolio value at the end of the backtest period.",
        'CAGR': "Compound Annual Growth Rate (%). Measures the mean annual growth rate over the backtest period.",
        'Total Return': "The overall return (%) of the portfolio from start to finish.",
        'Max Drawdown': "Largest peak-to-trough decline (%) in portfolio value.",
        'Annualized Volatility': "Annualized standard deviation (%) of portfolio returns.",
        'Sharpe Ratio': f"Risk-adjusted return metric using {config.RISK_FREE_RATE*100:.1f}% risk-free rate.",
        'Sortino Ratio': f"Similar to Sharpe, but only penalizes downside volatility, using {config.RISK_FREE_RATE*100:.1f}% risk-free rate.",
        'Alpha': "Excess return (%) vs benchmark, adjusted for beta. Requires benchmark.",
        'Beta': "Portfolio volatility relative to the benchmark. Requires benchmark.",
        'Information Ratio': "Risk-adjusted return vs benchmark (active return / tracking error). Requires benchmark.",
        'Recovery Factor': "Absolute total return divided by maximum drawdown.",
        'Win Rate': "Percentage of trades that resulted in a profit.",
        'Profit Factor': "Gross profits divided by gross losses. Inf means no losses.",
        'Avg Win Pnl': "Average profit ($) per winning trade.",
        'Avg Loss Pnl': "Average loss ($) per losing trade.",
        'Total Trades': "Total number of closed trades executed.",
    }

    def format_value(key, value):
        # Definicja tej wewnętrznej funkcji pozostaje bez zmian
        if value is None or (isinstance(value, float) and (np.isnan(value) or np.isinf(value))): return "N/A"
        if isinstance(value, (int, float)):
            if key in ['Initial Capital', 'Final Capital', 'avg_win_pnl', 'avg_loss_pnl']: return f"${value:,.2f}"
            elif key in ['Total Return', 'CAGR', 'Max Drawdown', 'Annualized Volatility', 'Alpha', 'win_rate']: return f"{value:.2f}%"
            elif key in ['Sharpe Ratio', 'Sortino Ratio', 'Beta', 'Information Ratio', 'Recovery Factor', 'profit_factor']: return f"{value:.2f}"
            elif key in ['total_trades', 'winning_trades', 'losing_trades']: return f"{int(value):,d}"
        return str(value)

    metrics_to_display = [
        ('Initial Capital', 'Initial Capital'), ('Final Capital', 'Final Capital'),
        ('Total Return', 'Total Return'), ('CAGR', 'CAGR'),
        ('Max Drawdown', 'Max Drawdown'), ('Annualized Volatility', 'Annualized Volatility'),
        ('Sharpe Ratio', 'Sharpe Ratio'), ('Sortino Ratio', 'Sortino Ratio'),
        ('Recovery Factor', 'Recovery Factor'), ('Win Rate', 'win_rate'),
        ('Profit Factor', 'profit_factor'), ('Total Trades', 'total_trades'),
        ('Alpha', 'Alpha'), ('Beta', 'Beta'),
        ('Information Ratio', 'Information Ratio'), ('Avg Win Pnl', 'avg_win_pnl'),
        ('Avg Loss Pnl', 'avg_loss_pnl')
    ]

    cards_col1 = []
    cards_col2 = []
    col_target = cards_col1

    for label, key in metrics_to_display:
        if key in ['Alpha', 'Beta', 'Information Ratio'] and stats.get(key) is None: continue
        if key == 'avg_win_pnl' and stats.get('winning_trades', 0) == 0: continue
        if key == 'avg_loss_pnl' and stats.get('losing_trades', 0) == 0: continue
        value = stats.get(key)
        formatted = format_value(key, value)
        tooltip = tooltip_texts.get(label, "")
        card = create_metric_card_with_tooltip(label, formatted, tooltip)
        col_target.append(card)
        col_target = cards_col2 if col_target is cards_col1 else cards_col1

    while len(cards_col1) < len(cards_col2): cards_col1.append(html.Div(style={'minHeight': '80px'})) # Placeholder
    while len(cards_col2) < len(cards_col1): cards_col2.append(html.Div(style={'minHeight': '80px'})) # Placeholder

    return html.Div([
        dbc.Row([
            dbc.Col(cards_col1, width=6, className="pe-1"),
            dbc.Col(cards_col2, width=6, className="ps-1")
        ], className="g-2")
    ], className="mb-1")


def create_risk_input_row(checkbox_id_base, label_text, input_id_base, min_val, max_val, step_val, default_val, is_integer=False):
    """Helper to create a row with checkbox, label, and input for risk options."""
    # Definicja tej funkcji pozostaje bez zmian (jak w poprzedniej odpowiedzi)
    input_type = "number"
    checkbox_id = {'type': 'risk-checkbox', 'index': checkbox_id_base}
    input_id = {'type': 'risk-input', 'index': input_id_base}

    if "%" in label_text or "ratio" in label_text.lower() or "pct" in input_id_base:
         default_display_val = round(default_val * 100, 2) if isinstance(default_val, float) and default_val <= 1.0 else default_val
    else:
         default_display_val = default_val

    return dbc.Row([
        dbc.Col(dbc.Checkbox(id=checkbox_id, value=False, className="me-2"), width="auto"),
        dbc.Col(html.Label(label_text, className="form-check-label", style={'fontSize': '0.9em'}), width=True),
        dbc.Col(dcc.Input(
            id=input_id, type=input_type, min=min_val, max=max_val, step=step_val,
            value=default_display_val, disabled=True, className="form-control form-control-sm", debounce=True
        ), width=4)
    ], className="mb-2 align-items-center")


def create_risk_management_section():
    """Create the risk management configuration UI section."""
    # Definicja tej funkcji pozostaje bez zmian (jak w poprzedniej odpowiedzi)
    try:
        available_tickers = get_available_tickers()
        ticker_options = [{"label": ticker, "value": ticker} for ticker in available_tickers]
        default_tickers = available_tickers[:min(len(available_tickers), 5)]
    except Exception as e:
        logger.error(f"Error getting tickers for risk section: {e}")
        ticker_options, default_tickers = [], []

    try:
        default_risk = RiskManager()
        stop_loss_default = default_risk.stop_loss_pct * 100
        profit_target_default = default_risk.profit_target_ratio
        trailing_activation_default = default_risk.trailing_stop_activation * 100
        trailing_distance_default = default_risk.trailing_stop_distance * 100
        max_pos_size_default = default_risk.max_position_size * 100
        min_pos_size_default = default_risk.min_position_size * 100
        max_open_pos_default = default_risk.max_open_positions
        max_drawdown_default = default_risk.max_drawdown * 100
        max_daily_loss_default = default_risk.max_daily_loss * 100
        market_lookback_default = default_risk.market_trend_lookback
    except Exception as e:
        logger.error(f"Error getting default risk parameters: {e}. Using hardcoded defaults.")
        stop_loss_default, profit_target_default, trailing_activation_default, trailing_distance_default = 2.0, 2.0, 2.0, 1.5
        max_pos_size_default, min_pos_size_default, max_open_pos_default = 20.0, 1.0, 5
        max_drawdown_default, max_daily_loss_default, market_lookback_default = 20.0, 5.0, 100

    return html.Div([
        html.H6("Select Tickers for Backtest", className="mt-1 mb-2"),
        dcc.Dropdown(
            id="ticker-selector", options=ticker_options, value=default_tickers,
            multi=True, className="mb-3", placeholder="Select tickers..."
        ),
        dbc.RadioItems(
            id="risk-management-toggle",
            options=[
                {"label": "Disable Risk Management", "value": "disabled"},
                {"label": "Enable Risk Management", "value": "enabled"}
            ], value="disabled", className="mb-3"
        ),
        dbc.Collapse([
            dbc.Card(dbc.CardBody([
                html.H6("Position Limits", className="mt-2 mb-2"),
                create_risk_input_row("use-max-position-size", "Max Pos Size (%):", "max_position_size", 1, 100, 1, max_pos_size_default),
                create_risk_input_row("use-min-position-size", "Min Pos Size (%):", "min_position_size", 0.1, 10, 0.1, min_pos_size_default),
                create_risk_input_row("use-max-positions", "Max Open Pos:", "max_open_positions", 1, 50, 1, max_open_pos_default, is_integer=True),
                html.H6("Stop Management", className="mt-3 mb-2"),
                create_risk_input_row("use-stop-loss", "Stop Loss (%):", "stop_loss_pct", 0.1, 50, 0.1, stop_loss_default),
                create_risk_input_row("use-profit-target", "Profit Target (R:R):", "profit_target_ratio", 0.1, 10, 0.1, profit_target_default),
                dbc.Row([
                    dbc.Col(dbc.Checkbox(id={'type': 'risk-checkbox', 'index': "use-trailing-stop"}, value=False, className="me-2"), width="auto"),
                    dbc.Col(html.Label("Trailing Stop:", className="form-check-label", style={'fontSize': '0.9em'}), width=True),
                    dbc.Col(dcc.Input(id={'type': 'risk-input', 'index': "trailing_stop_activation"}, type="number", min=0.1, max=50, step=0.1, value=trailing_activation_default, placeholder="Act (%)", disabled=True, className="form-control form-control-sm mb-1")),
                    dbc.Col(dcc.Input(id={'type': 'risk-input', 'index': "trailing_stop_distance"}, type="number", min=0.1, max=50, step=0.1, value=trailing_distance_default, placeholder="Dist (%)", disabled=True, className="form-control form-control-sm")),
                ], className="mb-2 align-items-center"),
                html.H6("Portfolio Limits", className="mt-3 mb-2"),
                create_risk_input_row("use-max-drawdown", "Max Portfolio DD (%):", "max_drawdown", 1, 99, 1, max_drawdown_default),
                create_risk_input_row("use-max-daily-loss", "Max Daily Loss (%):", "max_daily_loss", 0.1, 50, 0.1, max_daily_loss_default),
                html.H6("Market Conditions", className="mt-3 mb-2"),
                 dbc.Row([
                     dbc.Col(dbc.Checkbox(id={'type': 'risk-checkbox', 'index': "use-market-filter"}, value=False, className="me-2"), width="auto"),
                     dbc.Col(html.Label("Enable Market Filter", className="form-check-label", style={'fontSize': '0.9em'}), width=True),
                 ], className="mb-2 align-items-center"),
                 dbc.Collapse(
                    dcc.Input(id={'type': 'risk-input', 'index': "market_trend_lookback"}, type="number", min=10, max=300, step=10, value=market_lookback_default, placeholder="Lookback (days)", disabled=True, className="form-control form-control-sm"),
                    id='market-filter-options-collapse', is_open=False
                 )
            ]), className="bg-secondary border-secondary")
        ], id="risk-management-options-collapse", is_open=False),
        dbc.Button("Run Backtest", id="run-backtest-button", color="primary", className="mt-3 w-100")
    ], className="p-3 border rounded")

# ==============================================================
# ===== DEFINICJA create_trade_table TUTAJ =====================
# ==============================================================
def create_trade_table(trades):
    """Create a Dash DataTable component for trade history."""
    if not trades or len(trades) == 0:
        return html.Div("No trades to display.", className="text-muted text-center p-3")

    trade_data = []
    for i, trade in enumerate(trades):
        try:
            # Formatowanie dat
            entry_date_str = pd.to_datetime(trade.get('entry_date')).strftime('%Y-%m-%d %H:%M') if pd.notnull(trade.get('entry_date')) else 'N/A'
            exit_date_str = pd.to_datetime(trade.get('exit_date')).strftime('%Y-%m-%d %H:%M') if pd.notnull(trade.get('exit_date')) else 'N/A'

            # Obliczanie czasu trwania
            holding_days = 'N/A'
            if pd.notnull(trade.get('entry_date')) and pd.notnull(trade.get('exit_date')):
                holding_period = pd.to_datetime(trade.get('exit_date')) - pd.to_datetime(trade.get('entry_date'))
                # Dodajemy obsługę krótszych okresów
                if holding_period.total_seconds() < 86400: # Mniej niż dzień
                     holding_days = f"{holding_period.total_seconds() / 3600:.1f} h" # Godziny
                else:
                     holding_days = f"{holding_period.days + holding_period.seconds / 86400:.1f}" # Dni z częścią dziesiętną

            # Pobieranie wartości numerycznych
            pnl = float(trade.get('pnl', 0))
            pnl_pct = float(trade.get('pnl_pct', 0))
            direction_val = int(trade.get('direction', 1))
            direction_str = 'Long' if direction_val > 0 else ('Short' if direction_val < 0 else 'N/A')

            trade_data.append({
                'ID': i + 1,
                'Ticker': trade.get('ticker', 'N/A'),
                'Entry Date': entry_date_str,
                'Exit Date': exit_date_str,
                'Duration': holding_days, # Zmieniona nazwa kolumny
                'Direction': direction_str,
                'Entry Price': f"${float(trade.get('entry_price', 0)):,.2f}", # Dodano formatowanie tysięcy
                'Exit Price': f"${float(trade.get('exit_price', 0)):,.2f}",
                'Shares': int(trade.get('shares', 0)),
                'P&L ($)': pnl, # Numeryczne dla sortowania/formatowania
                'P&L (%)': pnl_pct, # Numeryczne dla sortowania/formatowania
                'Exit Reason': trade.get('exit_reason', 'N/A').replace('_', ' ').title() # Formatowanie powodu
            })
        except Exception as e:
            logger.warning(f"Error processing trade for table: {trade}. Error: {e}")
            continue

    if not trade_data:
        return html.Div("Error processing trades for table.", className="text-warning text-center p-3")

    return dash_table.DataTable(
        id='trade-table',
        columns=[
            {'name': 'ID', 'id': 'ID', 'type': 'numeric'},
            {'name': 'Ticker', 'id': 'Ticker', 'type': 'text'},
            {'name': 'Entry Date', 'id': 'Entry Date', 'type': 'datetime'},
            {'name': 'Exit Date', 'id': 'Exit Date', 'type': 'datetime'},
            {'name': 'Duration', 'id': 'Duration', 'type': 'text'}, # Zmieniono typ na text
            {'name': 'Direction', 'id': 'Direction', 'type': 'text'},
            {'name': 'Entry', 'id': 'Entry Price', 'type': 'text'},
            {'name': 'Exit', 'id': 'Exit Price', 'type': 'text'},
            {'name': 'Shares', 'id': 'Shares', 'type': 'numeric', 'format': dash_table.Format.Format(group=',')}, # Formatowanie tysięcy
            {'name': 'P&L ($)', 'id': 'P&L ($)', 'type': 'numeric', 'format': dash_table.Format.Format(scheme=dash_table.Format.Scheme.fixed, precision=2, group=',', sign=dash_table.Format.Sign.positive)},
            {'name': 'P&L (%)', 'id': 'P&L (%)', 'type': 'numeric', 'format': dash_table.Format.Format(scheme=dash_table.Format.Scheme.percentage, precision=2, sign=dash_table.Format.Sign.positive)},
            {'name': 'Exit Reason', 'id': 'Exit Reason', 'type': 'text'},
        ],
        data=trade_data,
        style_table={'overflowX': 'auto', 'minWidth': '100%'},
        style_cell={
            'backgroundColor': '#1e222d',
            'color': 'white',
            'textAlign': 'center',
            'fontSize': '12px',
            'fontFamily': 'Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif',
            'padding': '5px', # Dodano padding
            'whiteSpace': 'normal', # Lepsze zawijanie tekstu
            'height': 'auto',
        },
        style_header={
            'backgroundColor': '#131722',
            'fontWeight': 'bold',
            'color': 'white',
            'textAlign': 'center',
            'padding': '8px 5px'
        },
        style_data_conditional=[ # Warunkowe kolorowanie P&L
            {
                'if': {'column_id': 'P&L ($)', 'filter_query': '{P&L ($)} < 0'},
                'color': VIZ_CFG['colors']['loss']
            },
            {
                'if': {'column_id': 'P&L ($)', 'filter_query': '{P&L ($)} > 0'},
                'color': VIZ_CFG['colors']['profit']
            },
             {
                'if': {'column_id': 'P&L (%)', 'filter_query': '{P&L (%)} < 0'},
                'color': VIZ_CFG['colors']['loss']
            },
            {
                'if': {'column_id': 'P&L (%)', 'filter_query': '{P&L (%)} > 0'},
                'color': VIZ_CFG['colors']['profit']
            }
        ],
        page_size=10, # Paginacja
        sort_action='native', # Sortowanie po stronie klienta
        sort_mode='multi', # Sortowanie po wielu kolumnach
        filter_action='native', # Filtrowanie po stronie klienta
        row_deletable=False,
        editable=False,
    )

# ==============================================================
# ===== KONIEC DEFINICJI create_trade_table ====================
# ==============================================================

# --- Główny Układ Aplikacji ---
app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("Trading Strategy Backtester", className="text-center my-4 text-primary"))),
    dbc.Row([
        # Left column (Konfiguracja)
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Configuration"),
                dbc.CardBody([
                    html.H6("Select Strategy", className="mb-2"),
                    dcc.Dropdown(
                        id="strategy-selector",
                        options=[{"label": name, "value": name} for name in AVAILABLE_STRATEGIES.keys()],
                        value=list(AVAILABLE_STRATEGIES.keys())[0] if AVAILABLE_STRATEGIES else None, # Bezpieczne pobranie domyślnej
                        className="mb-3", clearable=False
                    ),
                    html.H6("Strategy Parameters", className="mt-3 mb-2"),
                    html.Div(id="strategy-parameters-container", className="mb-3 border rounded p-2 bg-secondary", style={'minHeight': '80px'}),
                    html.H6("Tickers & Risk Management", className="mt-3 mb-2"),
                    create_risk_management_section()
                ])
            ], className="mb-4")
        ], width=3),

        # Center column (Wykresy Główne)
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Backtest Results"),
                dbc.CardBody([
                    dcc.Loading(
                        id="loading-indicator", type="default", fullscreen=False,
                        children=[
                            html.Div(id="calculation-status", className="mb-2"),
                            dbc.Row([
                                dbc.Col(html.Span("Backtest Period: ", className="fw-bold"), width="auto"),
                                dbc.Col(html.Span(id="backtest-period"), width=True)
                            ], className="mb-1 align-items-center"),
                            dbc.Row([
                                dbc.Col(html.Span("Instruments Tested: ", className="fw-bold"), width="auto"),
                                dbc.Col(html.Span(id="portfolio-instruments"), width=True)
                            ], className="mb-3 align-items-center"),
                            html.Div(id="equity-curve-container", className="mb-4", style={'minHeight': '400px'}),
                            html.H5("Portfolio Allocation Over Time", className="mt-3 mb-2"),
                            html.Div(id="portfolio-composition-container", style={'minHeight': '300px'})
                        ]
                    )
                ])
            ])
        ], width=6),

        # Right column (Metrics)
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Performance Metrics"),
                # Używamy Div jako kontenera dla metryk, stylizacja dla scrollowania jeśli potrzeba
                html.Div(id="metrics-container", style={'maxHeight': '80vh', 'overflowY': 'auto'})
            ], className="mb-4")
        ], width=3)
    ], className="mb-4"),

    # Bottom section (Trade Analysis)
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Trade Analysis"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H5("Trade P&L Distribution", className="mb-2 text-center"),
                            html.Div(id="trade-distribution-container", style={'minHeight': '250px'})
                        ], width=6, className="border-end"),
                        dbc.Col([
                            html.H5("Trade Duration Distribution", className="mb-2 text-center"),
                            html.Div(id="trade-duration-container", style={'minHeight': '250px'})
                        ], width=6)
                    ]),
                    html.Hr(),
                    dbc.Row([
                        dbc.Col([
                            html.H5("Trade History", className="mt-3 mb-2"),
                            html.Div(id="trade-table-container")
                        ], width=12)
                    ])
                ])
            ])
        ], width=12)
    ])
], fluid=True, style={"backgroundColor": VIZ_CFG['colors']['background'], "padding": "15px"})


# --- Callbacki ---

# Callback do dynamicznego generowania pól parametrów strategii
@app.callback(
    Output("strategy-parameters-container", "children"),
    Input("strategy-selector", "value")
)
def update_strategy_parameters(strategy_name):
    # Definicja tego callbacku pozostaje bez zmian (jak w poprzedniej odpowiedzi)
    if not strategy_name: return html.P("Select a strategy.", className="text-muted")
    try:
        strategy_class = AVAILABLE_STRATEGIES.get(strategy_name)
        if not strategy_class:
            logger.error(f"Strategy class for '{strategy_name}' not found.")
            return html.P(f"Error: Strategy class '{strategy_name}' not found.", className="text-danger")

        sig = inspect.signature(strategy_class.__init__)
        params_inputs = []
        for name, param in sig.parameters.items():
            if name in ['self', 'tickers', 'args', 'kwargs']: continue
            default_value = param.default if param.default is not inspect.Parameter.empty else None
            input_type, step, placeholder, required = 'text', 'any', str(default_value) if default_value is not None else "Required", default_value is None
            annotation = param.annotation
            target_type = type(default_value) if default_value is not None else (annotation if annotation != inspect.Parameter.empty else str)

            if target_type == bool:
                params_inputs.append(dbc.Row([
                    dbc.Label(name.replace('_', ' ').title(), width=6, className="small"),
                    dbc.Col(dbc.Checkbox(id={'type': 'strategy-param', 'index': name}, value=bool(default_value)), width=6)
                ], className="mb-2 align-items-center"))
                continue
            elif target_type == int: input_type, step = 'number', 1
            elif target_type == float:
                 input_type = 'number'
                 step = 0.1 if abs(default_value or 0.0) < 10 else (1 if abs(default_value or 0.0) < 100 else 10)

            params_inputs.append(dbc.Row([
                dbc.Label(name.replace('_', ' ').title(), width=6, className="small", html_for=str({'type': 'strategy-param', 'index': name})),
                dbc.Col(dcc.Input(id={'type': 'strategy-param', 'index': name}, type=input_type, value=default_value, step=step if input_type == 'number' else None,
                                  placeholder=placeholder, required=required, className="form-control form-control-sm", debounce=True), width=6)
            ], className="mb-2 align-items-center"))
        if not params_inputs: return html.P("This strategy has no configurable parameters.", className="text-muted")
        return html.Div(params_inputs)
    except Exception as e:
        logger.error(f"Error inspecting strategy parameters for {strategy_name}: {e}", exc_info=True)
        return html.P(f"Error loading parameters for {strategy_name}.", className="text-danger")

# Callbacki do obsługi interaktywności sekcji ryzyka
@app.callback(Output("risk-management-options-collapse", "is_open"), Input("risk-management-toggle", "value"))
def toggle_risk_options_visibility(toggle_value):
    return toggle_value == "enabled"

@app.callback(Output({'type': 'risk-input', 'index': MATCH}, 'disabled'), Input({'type': 'risk-checkbox', 'index': MATCH}, 'value'), State("risk-management-toggle", "value"), prevent_initial_call=True)
def toggle_risk_input_disabled_state(checkbox_value, risk_mode):
    return (risk_mode == "disabled") or (not checkbox_value)

@app.callback([Output({'type': 'risk-input', 'index': "trailing_stop_activation"}, 'disabled'), Output({'type': 'risk-input', 'index': "trailing_stop_distance"}, 'disabled')], Input({'type': 'risk-checkbox', 'index': "use-trailing-stop"}, 'value'), State("risk-management-toggle", "value"), prevent_initial_call=True)
def toggle_trailing_stop_inputs_disabled_state(checked, risk_mode):
    is_disabled = (risk_mode == "disabled") or (not checked)
    return is_disabled, is_disabled

@app.callback(Output('market-filter-options-collapse', 'is_open'), Output({'type': 'risk-input', 'index': "market_trend_lookback"}, 'disabled'), Input({'type': 'risk-checkbox', 'index': "use-market-filter"}, 'value'), State("risk-management-toggle", "value"), prevent_initial_call=True)
def toggle_market_filter_input_visibility_and_disabled(checked, risk_mode):
    is_open = (risk_mode == "enabled") and checked
    is_disabled = (risk_mode == "disabled") or (not checked)
    return is_open, is_disabled

# Funkcja pomocnicza do parsowania parametrów ryzyka
def parse_risk_param_value(input_id, input_value):
    # Definicja tej funkcji pozostaje bez zmian (jak w poprzedniej odpowiedzi)
    if input_value is None or input_value == '': return None
    if isinstance(input_id, str) and ("pct" in input_id or "size" in input_id or "drawdown" in input_id or "loss" in input_id or "activation" in input_id or "distance" in input_id):
        try: return float(input_value) / 100.0
        except (ValueError, TypeError): return None
    elif isinstance(input_id, str) and "ratio" in input_id:
        try: return float(input_value)
        except (ValueError, TypeError): return None
    elif isinstance(input_id, str) and ("positions" in input_id or "lookback" in input_id):
        try: return int(input_value)
        except (ValueError, TypeError): return None
    return input_value


# Główny callback do uruchamiania backtestu
@app.callback(
    # Definicja Outputs pozostaje bez zmian
    Output("calculation-status", "children", allow_duplicate=True),
    Output("equity-curve-container", "children", allow_duplicate=True),
    Output("metrics-container", "children", allow_duplicate=True),
    Output("trade-distribution-container", "children", allow_duplicate=True),
    Output("trade-table-container", "children", allow_duplicate=True),
    Output("backtest-period", "children", allow_duplicate=True),
    Output("portfolio-instruments", "children", allow_duplicate=True),
    Output("portfolio-composition-container", "children", allow_duplicate=True),
    Output("trade-duration-container", "children", allow_duplicate=True),
    Input("run-backtest-button", "n_clicks"),
    # Definicja States pozostaje bez zmian
    State("strategy-selector", "value"),
    State("ticker-selector", "value"),
    State("risk-management-toggle", "value"),
    State({'type': 'strategy-param', 'index': ALL}, 'value'),
    State({'type': 'strategy-param', 'index': ALL}, 'id'),
    State({'type': 'risk-checkbox', 'index': ALL}, 'value'), # Używamy 'value' dla checkboxów
    State({'type': 'risk-checkbox', 'index': ALL}, 'id'),
    State({'type': 'risk-input', 'index': ALL}, 'value'),
    State({'type': 'risk-input', 'index': ALL}, 'id'),
    prevent_initial_call=True
)
def run_full_backtest(n_clicks, strategy_name, selected_tickers, risk_toggle_value,
                      strategy_param_values, strategy_param_ids,
                      risk_checkbox_values, risk_checkbox_ids,
                      risk_input_values, risk_input_ids):

    start_time = pd.Timestamp.now()
    triggered_input = ctx.triggered_id
    logger.info("="*50)
    logger.info(f"Backtest triggered by: {triggered_input}. Click: {n_clicks}")
    logger.info(f"Strategy: {strategy_name}, Tickers: {selected_tickers}, Risk Mode: {risk_toggle_value}")

    # Inicjalizacja pustych wyników (używamy pustych komponentów)
    empty_metrics = create_metric_cards({})
    empty_chart = create_empty_chart("Equity Curve")
    empty_alloc_chart = create_empty_chart("Allocation")
    empty_trade_hist = create_empty_chart("P/L Distribution")
    empty_duration_hist = create_empty_chart("Duration Distribution")
    empty_trade_table = html.Div("Run backtest to see trades.", className="text-muted text-center p-3")
    initial_status = html.Div("Configuration ready. Click 'Run Backtest'.", className="text-info")

    def return_empty_state(status_msg=initial_status):
        return (status_msg, empty_chart, empty_metrics, empty_trade_hist,
                empty_trade_table, "", "", empty_alloc_chart, empty_duration_hist)

    if not strategy_name: return return_empty_state(html.Div("Please select a strategy.", className="text-warning"))
    if not selected_tickers: return return_empty_state(html.Div("Please select at least one ticker.", className="text-warning"))

    loading_status = html.Div([dbc.Spinner(size="sm", color="primary"), " Running backtest..."], className="text-info")
    # Zwracamy stan ładowania na początku
    # Używamy initial_outputs_with_loading zdefiniowanego wcześniej może być problematyczne, lepiej zdefiniować tu
    initial_outputs = list(return_empty_state(loading_status))
    # Zwróć stan ładowania tylko dla statusu, reszta komponentów pozostaje pusta
    # To wymagałoby multiple Output definitions for the same component ID, which Dash doesn't like without allow_duplicate=True
    # With allow_duplicate=True, we can update just the status here, but let's return everything for now.
    # return (loading_status, dash.no_update, ...) # This might be better with more complex state management

    try:
        # --- Zbieranie parametrów (jak poprzednio) ---
        strategy_params = {}
        strategy_class = AVAILABLE_STRATEGIES.get(strategy_name)
        if not strategy_class: raise ValueError(f"Strategy class {strategy_name} not found.")
        sig = inspect.signature(strategy_class.__init__)
        param_map = {pid['index']: val for pid, val in zip(strategy_param_ids, strategy_param_values)}

        for name, param in sig.parameters.items():
            if name in ['self', 'tickers', 'args', 'kwargs']: continue
            param_value = param_map.get(name)
            expected_type = str
            if param.annotation != inspect.Parameter.empty: expected_type = param.annotation
            elif param.default is not inspect.Parameter.empty: expected_type = type(param.default)
            try:
                if expected_type == bool: converted_value = bool(param_value)
                elif expected_type == int: converted_value = int(param_value)
                elif expected_type == float: converted_value = float(param_value)
                else: converted_value = param_value # string or other
                strategy_params[name] = converted_value
            except (ValueError, TypeError) as e:
                logger.warning(f"Param Conversion Warning: Param '{name}', Value '{param_value}', Expected {expected_type}. Error: {e}. Using raw value.")
                strategy_params[name] = param_value
        logger.info(f"Collected strategy parameters: {strategy_params}")

        risk_params = {}
        risk_enabled = (risk_toggle_value == "enabled")
        if risk_enabled:
            # Mapowanie checkboxów i inputów (jak poprzednio)
            checkbox_states = {cb_id['index']: checked for cb_id, checked in zip(risk_checkbox_ids, risk_checkbox_values)}
            input_values = {inp_id['index']: value for inp_id, value in zip(risk_input_ids, risk_input_values)}
            risk_mapping = {
                "use-max-position-size": "max_position_size", "use-min-position-size": "min_position_size",
                "use-max-positions": "max_open_positions", "use-stop-loss": "stop_loss_pct",
                "use-profit-target": "profit_target_ratio", "use-trailing-stop": ["use_trailing_stop", "trailing_stop_activation", "trailing_stop_distance"], # Dodaj flagę 'use_trailing_stop'
                "use-max-drawdown": "max_drawdown", "use-max-daily-loss": "max_daily_loss",
                "use-market-filter": ["use_market_filter", "market_trend_lookback"] # Dodaj flagę 'use_market_filter'
            }
            for checkbox_base_id, manager_param_keys in risk_mapping.items():
                if checkbox_states.get(checkbox_base_id, False):
                     if isinstance(manager_param_keys, list):
                         # Pierwszy element listy to flaga lub główny parametr
                         main_param_key = manager_param_keys[0]
                         risk_params[main_param_key] = True # Ustaw flagę 'use_...'
                         # Przetwarzaj pozostałe powiązane parametry
                         for param_key in manager_param_keys[1:]:
                              parsed_value = parse_risk_param_value(param_key, input_values.get(param_key))
                              if parsed_value is not None: risk_params[param_key] = parsed_value
                     else: # Pojedynczy parametr powiązany z checkboxem
                          param_key = manager_param_keys
                          parsed_value = parse_risk_param_value(param_key, input_values.get(param_key))
                          if parsed_value is not None: risk_params[param_key] = parsed_value
            logger.info(f"Risk Management ENABLED. Params: {risk_params}")
        else:
            logger.info("Risk Management DISABLED.")
            risk_params = None # Przekaż None, aby użyć domyślnego RiskManagera

        # --- Uruchomienie Backtestu ---
        logger.info("Calling backtest_manager.run_backtest...")
        # Przekaż use_risk_management jako flagę, jeśli manager tego wymaga, lub polegaj na risk_params is None
        signals, results, stats = backtest_manager.run_backtest(
            strategy_type=strategy_name, tickers=selected_tickers,
            strategy_params=strategy_params, risk_params=risk_params
        )
        logger.info("Backtest manager finished.")

        # --- Przetwarzanie Wyników ---
        if results is None or stats is None:
            logger.error("Backtest manager returned None for results or stats.")
            return return_empty_state(html.Div("Error during backtest execution. Check logs.", className="text-danger"))

        portfolio_values = results.get('Portfolio_Value', pd.Series())
        benchmark_values = results.get('Benchmark') # Może być None
        trades = results.get('trades', [])

        if portfolio_values.empty:
            logger.warning("Backtest completed, but no portfolio data generated.")
            metrics_cards = create_metric_cards(stats) # Spróbuj wyświetlić statystyki (np. liczbę transakcji)
            trade_table = create_trade_table(trades)
            return (
                 html.Div("Backtest completed, but no portfolio equity generated.", className="text-warning"),
                 empty_chart, metrics_cards, empty_trade_hist, trade_table,
                 "", ", ".join(selected_tickers), empty_alloc_chart, empty_duration_hist
            )

        logger.info("Generating result components...")
        # Użyj visualizera do tworzenia komponentów
        equity_chart_component = visualizer.create_equity_curve_component(portfolio_values, benchmark_values)
        metrics_cards_component = create_metric_cards(stats) # Ta funkcja już zwraca komponent
        trade_histogram_component = visualizer.create_trade_distribution_component(trades)
        trade_table_component = create_trade_table(trades) # Ta funkcja zwraca komponent
        duration_histogram_component = create_duration_histogram(trades) # Ta funkcja zwraca komponent
        allocation_chart_component = visualizer.create_allocation_component(results)

        # Informacje o okresie i instrumentach
        start_date_str, end_date_str = "N/A", "N/A"
        if not portfolio_values.empty:
             start_date_str = portfolio_values.index.min().strftime('%Y-%m-%d')
             end_date_str = portfolio_values.index.max().strftime('%Y-%m-%d')
        backtest_period = f"{start_date_str} to {end_date_str}"
        instruments_str = ", ".join(sorted(selected_tickers))

        end_time = pd.Timestamp.now()
        duration = round((end_time - start_time).total_seconds(), 2)
        status_msg = html.Div(f"Backtest completed successfully in {duration}s.", className="text-success")
        logger.info(f"Backtest completed successfully in {duration}s.")

        return (
            status_msg, equity_chart_component, metrics_cards_component, trade_histogram_component, trade_table_component,
            backtest_period, instruments_str, allocation_chart_component, duration_histogram_component
        )

    except Exception as e:
        logger.error(f"CRITICAL Unhandled error in backtest callback: {str(e)}", exc_info=True) # Dodano exc_info=True
        return return_empty_state(html.Div(f"An critical error occurred: {str(e)}. Check logs.", className="text-danger"))


# Dodaj funkcję do tworzenia histogramu czasu trwania transakcji (jak poprzednio)
def create_duration_histogram(trades):
    """Create a histogram of trade durations."""
    # Definicja tej funkcji pozostaje bez zmian (jak w poprzedniej odpowiedzi)
    if not trades: return create_empty_chart("Trade Duration")
    durations = []
    for trade in trades:
        try:
            entry, exit_d = pd.to_datetime(trade.get('entry_date')), pd.to_datetime(trade.get('exit_date'))
            if pd.notna(entry) and pd.notna(exit_d):
                days = (exit_d - entry).days
                if days >= 0: durations.append(days)
        except Exception as e: logger.warning(f"Duration calc error: {e}")
    if not durations: return create_empty_chart("Trade Duration")
    fig = go.Figure(data=[go.Histogram(x=durations, nbinsx=20, marker_color='#36A2EB', name='Duration')])
    fig.update_layout(title=None, template=CHART_TEMPLATE, paper_bgcolor='#1e222d', plot_bgcolor='#1e222d',
                      font={'color': '#ffffff'}, xaxis={'title': 'Duration (Days)', 'gridcolor': GRID_COLOR},
                      yaxis={'title': 'Number of Trades', 'gridcolor': GRID_COLOR}, bargap=0.1, height=250,
                      margin=dict(t=20, l=40, r=20, b=40))
    return dcc.Graph(figure=fig, config={'displayModeBar': False})

# --- Uruchomienie Aplikacji ---
if __name__ == '__main__':
    logger.info("Starting Dash application...")
    try:
        startup_tickers = get_available_tickers()
        if not startup_tickers: logger.warning("No tickers found during startup check.")
        else: logger.info(f"Found {len(startup_tickers)} tickers during startup.")
    except Exception as e: logger.error(f"Error during startup ticker check: {e}")
    # Użyj wartości z config lub domyślnych dla host/port
    app_host = os.environ.get("HOST", "0.0.0.0")
    app_port = int(os.environ.get("PORT", 8050))
    app_debug = os.environ.get("DEBUG", "True").lower() == "true"
    logger.info(f"Running app on {app_host}:{app_port} with debug={app_debug}")
    app.run(debug=app_debug, host=app_host, port=app_port)
    logger.info("Dash application stopped.")