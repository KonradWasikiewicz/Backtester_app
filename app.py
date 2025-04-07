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
import os  # Missing import for os module
from flask_caching import Cache
import gc

# Konfiguracja wydajności pandas
pd.set_option('compute.use_bottleneck', True)
pd.set_option('compute.use_numexpr', True)

# Visualization config constants
VIZ_CFG = {
    'colors': {
        'background': '#131722',      # Dark background
        'card_background': '#1e222d', # Slightly lighter card background
        'profit': '#17B897',          # Green for profits
        'loss': '#FF6B6B',            # Red for losses
        'text_color': '#dee2e6',      # Light text color
        'grid_color': '#2a2e39',      # Grid line color
    }
}

# Chart constants
CHART_TEMPLATE = "plotly_dark"  # Use plotly's dark theme
GRID_COLOR = "#2a2e39"          # Grid color for charts

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
    suppress_callback_exceptions=True,
    title="Trading Strategy Backtester"
)
server = app.server

# --- Cache Configuration ---
cache = Cache(app.server, config={
    'CACHE_TYPE': 'simple',  # Używamy prostego cachingu w pamięci
    'CACHE_DEFAULT_TIMEOUT': 300  # 5 minut
})

# --- Error Handling ---
def handle_error(e):
    """Uniform error handler for critical errors"""
    logger.error(f"CRITICAL: {str(e)}", exc_info=True)
    return html.Div(f"An error occurred: {str(e)}. Check logs.", className="text-danger text-center")

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

@cache.memoize(timeout=300)
def process_metrics_stats(stats):
    """Przetwórz statystyki dla kart metryk z wykorzystaniem cachingu"""
    if not stats:
        return {}
        
    # Wykonaj kosztowne obliczenia tutaj
    processed_stats = stats.copy()
    return processed_stats

# Dodaj poniższy kod po definicji process_metrics_stats a przed create_metric_cards:

@cache.memoize(timeout=300)
def process_trades_for_table(trades):
    """Przetwórz dane transakcji do tabeli z wykorzystaniem cachingu"""
    if not trades or len(trades) == 0:
        return None
        
    trade_data = []
    try:
        # Użyj pandas dla szybszego przetwarzania
        if isinstance(trades, list) and len(trades) > 0:
            # Konwersja listy słowników na DataFrame dla wydajnego przetwarzania
            df = pd.DataFrame(trades)
            
            # Konwersja dat jednocześnie dla wszystkich wierszy
            if 'entry_date' in df.columns:
                df['entry_date'] = pd.to_datetime(df['entry_date'], errors='coerce')
            if 'exit_date' in df.columns:
                df['exit_date'] = pd.to_datetime(df['exit_date'], errors='coerce')
                
            # Obliczanie czasu trwania dla wszystkich transakcji jednocześnie
            if 'entry_date' in df.columns and 'exit_date' in df.columns:
                df['duration_seconds'] = (df['exit_date'] - df['entry_date']).dt.total_seconds()
                df['duration_days'] = df['duration_seconds'] / 86400
                df['duration_text'] = np.where(
                    df['duration_seconds'] < 86400,
                    df['duration_seconds'].apply(lambda x: f"{x / 3600:.1f} h"),
                    df['duration_days'].apply(lambda x: f"{x:.1f}")
                )
            
            # Formatowanie pozostałych danych
            for i, row in df.iterrows():
                pnl = float(row.get('pnl', 0))
                pnl_pct = float(row.get('pnl_pct', 0))
                direction_val = int(row.get('direction', 1))
                direction_str = 'Long' if direction_val > 0 else ('Short' if direction_val < 0 else 'N/A')
                
                entry_date_str = row['entry_date'].strftime('%Y-%m-%d %H:%M') if pd.notnull(row.get('entry_date')) else 'N/A'
                exit_date_str = row['exit_date'].strftime('%Y-%m-%d %H:%M') if pd.notnull(row.get('exit_date')) else 'N/A'
                
                trade_data.append({
                    'ID': i + 1,
                    'Ticker': row.get('ticker', 'N/A'),
                    'Entry Date': entry_date_str,
                    'Exit Date': exit_date_str,
                    'Duration': row.get('duration_text', 'N/A'),
                    'Direction': direction_str,
                    'Entry Price': f"${float(row.get('entry_price', 0)):,.2f}",
                    'Exit Price': f"${float(row.get('exit_price', 0)):,.2f}",
                    'Shares': int(row.get('shares', 0)),
                    'P&L ($)': pnl,
                    'P&L (%)': pnl_pct,
                    'Exit Reason': row.get('exit_reason', 'N/A').replace('_', ' ').title()
                })
                
    except Exception as e:
        logger.warning(f"Error processing trades for table: {e}")
        return None
        
    return trade_data

@cache.memoize(timeout=300)
def generate_equity_curve(portfolio_values, benchmark_values):
    """Zoptymalizowana funkcja generująca wykres krzywej kapitału"""
    if portfolio_values is None or portfolio_values.empty:
        return None
    
    # Używamy maksymalnie 500 punktów danych dla wykresu
    if len(portfolio_values) > 500:
        # Wybierz równomiernie rozłożone punkty
        idx = np.linspace(0, len(portfolio_values) - 1, 500).astype(int)
        portfolio_values = portfolio_values.iloc[idx]
        if benchmark_values is not None and len(benchmark_values) > 500:
            benchmark_values = benchmark_values.iloc[idx]
    
    return visualizer.create_equity_curve_figure(portfolio_values, benchmark_values)

@cache.memoize(timeout=300)
def generate_trade_distribution(trades):
    """Cached function for generating trade distribution figures"""
    if not trades or len(trades) == 0:
        return None
    
    # Implementacja własnej funkcji zamiast polegania na metodzie visualizera
    wins = []
    losses = []
    
    for trade in trades:
        pnl = trade.get('pnl', 0)
        if pnl > 0:
            wins.append(pnl)
        elif pnl < 0:
            losses.append(pnl)
    
    fig = go.Figure()
    if wins:
        fig.add_trace(go.Histogram(
            x=wins,
            name="Zyski",
            marker_color=VIZ_CFG['colors']['profit'],
            opacity=0.7,
            autobinx=True
        ))
    
    if losses:
        fig.add_trace(go.Histogram(
            x=losses,
            name="Straty",
            marker_color=VIZ_CFG['colors']['loss'],
            opacity=0.7,
            autobinx=True
        ))
    
    fig.update_layout(
        title="Rozkład zysków i strat",
        xaxis_title="P&L ($)",
        yaxis_title="Liczba transakcji",
        template=CHART_TEMPLATE,
        barmode='overlay',
        bargap=0.1,
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        paper_bgcolor=VIZ_CFG['colors']['background'],
        plot_bgcolor=VIZ_CFG['colors']['background'],
        font=dict(color=VIZ_CFG['colors']['text_color'])
    )
    
    # Dodaj linie siatki
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=GRID_COLOR)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=GRID_COLOR)
    
    return fig

@cache.memoize(timeout=300)
def generate_duration_histogram_figure(trades):
    """Cached function for generating duration histogram figure"""
    if not trades or len(trades) == 0:
        return None
        
    durations = []
    colors = []
    
    # Szybsze przetwarzanie trades
    for trade in trades:
        try:
            if pd.notnull(trade.get('entry_date')) and pd.notnull(trade.get('exit_date')):
                entry_date = pd.to_datetime(trade.get('entry_date'))
                exit_date = pd.to_datetime(trade.get('exit_date'))
                duration_days = (exit_date - entry_date).total_seconds() / 86400
                durations.append(duration_days)
                colors.append(VIZ_CFG['colors']['profit'] if trade.get('pnl', 0) > 0 else VIZ_CFG['colors']['loss'])
        except Exception as e:
            logger.warning(f"Error calculating trade duration: {e}")
            continue
    
    if not durations:
        return None
    
    # Uproszczone obliczanie przedziałów
    max_duration = max(durations)
    if max_duration < 1:
        bin_size, bin_text = 1/24, "Hours"  # 1 godzina
    elif max_duration < 7:
        bin_size, bin_text = 1.0, "Days"
    elif max_duration < 30:
        bin_size, bin_text = 7.0, "Weeks"
    else:
        bin_size, bin_text = 30.0, "Months"
    
    # Tworzenie wykresu z zoptymalizowanymi ustawieniami
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=durations,
        marker_color=colors,
        opacity=0.75,
        xbins=dict(size=bin_size),
        name="Duration Distribution"
    ))
    
    # Uproszczone aktualizacje układu
    fig.update_layout(
        title=f"Trade Duration Distribution",
        xaxis_title=f"Duration ({bin_text})",
        yaxis_title="Number of Trades",
        template=CHART_TEMPLATE,
        margin=dict(l=40, r=40, t=40, b=40),
        paper_bgcolor=VIZ_CFG['colors']['background'],
        plot_bgcolor=VIZ_CFG['colors']['background'],
        font=dict(color=VIZ_CFG['colors']['text_color'])
    )
    
    # Dodaj linie siatki
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=GRID_COLOR)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=GRID_COLOR)
    
    return fig

def create_metric_cards(stats: dict):
    """Create metric cards layout."""
    # Jeśli słownik stats jest pusty
    if not stats:
        return html.Div([
             dbc.Row([
                 dbc.Col(create_metric_card_with_tooltip("Status", "Run backtest to see metrics.", tooltip_text="Perform a backtest calculation to view performance details."), width=12)
             ])
        ], className="mb-1")

    # Użyj zbuforowanej funkcji do przetwarzania statystyk
    processed_stats = process_metrics_stats(stats)
    
    # Kontynuuj jak wcześniej...
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

    # Dodaj definicję card_style, która wcześniej była pominięta
    card_style = {
        'marginBottom': '8px',
        'height': 'auto'
    }

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
        
        # Używaj kompaktowego stylu dla kart
        card = dbc.Card(
            dbc.CardBody([
                html.P(label, className="small text-muted mb-0"),
                html.H6(formatted, className="mb-0")
            ], className="p-2"),  # Mniejszy padding
            style=card_style,
            className="mb-2"
        )
        
        col_target.append(card)
        col_target = cards_col2 if col_target is cards_col1 else cards_col1

    return html.Div([
        dbc.Row([
            dbc.Col(html.Div(cards_col1), width=6, className="pe-1"),
            dbc.Col(html.Div(cards_col2), width=6, className="ps-1")
        ], className="g-2")
    ], className="p-2", style={'maxHeight': '70vh', 'overflowY': 'auto'})
 
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

    # Wykorzystaj buforowaną funkcję do przetworzenia danych
    trade_data = process_trades_for_table(trades)
    if not trade_data:
        return html.Div("No valid trades to display.", className="text-muted text-center p-3")

    # Zdefiniuj kolumny tylko raz
    columns = [
        {'name': 'ID', 'id': 'ID', 'type': 'numeric'},
        {'name': 'Ticker', 'id': 'Ticker', 'type': 'text'},
        {'name': 'Entry Date', 'id': 'Entry Date', 'type': 'text'},
        {'name': 'Exit Date', 'id': 'Exit Date', 'type': 'text'},
        {'name': 'Duration', 'id': 'Duration', 'type': 'text'},
        {'name': 'Direction', 'id': 'Direction', 'type': 'text'},
        {'name': 'Entry', 'id': 'Entry Price', 'type': 'text'},
        {'name': 'Exit', 'id': 'Exit Price', 'type': 'text'},
        {'name': 'Shares', 'id': 'Shares', 'type': 'numeric', 'format': dash_table.Format.Format(group=',')},
        {'name': 'P&L ($)', 'id': 'P&L ($)', 'type': 'numeric', 'format': dash_table.Format.Format(
            scheme=dash_table.Format.Scheme.fixed, precision=2, group=',', sign=dash_table.Format.Sign.positive)},
        {'name': 'P&L (%)', 'id': 'P&L (%)', 'type': 'numeric', 'format': dash_table.Format.Format(
            scheme=dash_table.Format.Scheme.percentage, precision=2, sign=dash_table.Format.Sign.positive)},
        {'name': 'Exit Reason', 'id': 'Exit Reason', 'type': 'text'},
    ]

    # Zoptymalizowane wyświetlanie
    return dash_table.DataTable(
        id='trade-table',
        columns=columns,
        data=trade_data,
        style_table={'overflowX': 'auto', 'minWidth': '100%'},
        style_cell={
            'backgroundColor': '#1e222d',
            'color': 'white',
            'textAlign': 'center',
            'fontSize': '12px',
            'fontFamily': 'Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif',
            'padding': '5px',
            'whiteSpace': 'normal',
            'height': 'auto',
        },
        style_header={
            'backgroundColor': '#131722',
            'fontWeight': 'bold',
            'color': 'white',
            'textAlign': 'center',
            'padding': '8px 5px'
        },
        style_data_conditional=[
            {'if': {'column_id': 'P&L ($)', 'filter_query': '{P&L ($)} < 0'}, 'color': VIZ_CFG['colors']['loss']},
            {'if': {'column_id': 'P&L ($)', 'filter_query': '{P&L ($)} > 0'}, 'color': VIZ_CFG['colors']['profit']},
            {'if': {'column_id': 'P&L (%)', 'filter_query': '{P&L (%)} < 0'}, 'color': VIZ_CFG['colors']['loss']},
            {'if': {'column_id': 'P&L (%)', 'filter_query': '{P&L (%) > 0}'}, 'color': VIZ_CFG['colors']['profit']}
        ],
        page_size=10,
        sort_action='native',
        sort_mode='multi',
        filter_action='native',
        page_action='native',  # Paginacja po stronie przeglądarki
        virtualization=True,   # Włącz wirtualizację dla lepszej wydajności
    )

# ==============================================================
# ===== KONIEC DEFINICJI create_trade_table ====================
# ==============================================================

# ==============================================================
# ===== DEFINICJA create_duration_histogram TUTAJ ==============
# ==============================================================
def create_duration_histogram(trades):
    """Create a histogram of trade durations."""
    if not trades or len(trades) == 0:
        return create_empty_chart("Trade Duration (days)")
        
    # Wykorzystaj zbuforowaną funkcję
    fig = generate_duration_histogram_figure(trades)
    if fig is None:
        return create_empty_chart("Trade Duration (days)")
        
    return dcc.Graph(figure=fig, config={'displayModeBar': False})
# ==============================================================
# ===== KONIEC DEFINICJI create_duration_histogram =============
# ==============================================================

# Zaimplementuj własną funkcję pomocniczą do tworzenia wykresu alokacji

def create_my_allocation_chart(results):
    """Tworzy wykres alokacji portfela bez używania funkcji create_allocation_chart"""
    try:
        if not results or 'positions' not in results:
            return create_empty_chart("No allocation data")
        
        # Dane pozycji dziennych
        positions_data = results['positions']
        if positions_data.empty:
            return create_empty_chart("No position data")
        
        # Konwersja wartości pieniężnych na procenty
        total_value = positions_data['Total']
        pct_data = positions_data.div(total_value, axis=0).multiply(100)
        
        # Inicjalizacja wykresu
        fig = go.Figure()
        
        # Dodaj gotówkę jako obszar
        fig.add_trace(go.Scatter(
            x=pct_data.index,
            y=pct_data['Cash'],
            name='Cash Allocation',
            mode='lines',
            stackgroup='one',
            line=dict(width=0.5, color='#6c757d'),
            fillcolor='rgba(108, 117, 125, 0.5)'
        ))
        
        # Dodaj inwestycje jako obszar
        # Sumuj wszystkie kolumny poza Cash i Total
        investments = pct_data.drop(['Cash', 'Total'], axis=1).sum(axis=1)
        fig.add_trace(go.Scatter(
            x=pct_data.index,
            y=investments,
            name='Positions Allocation',
            mode='lines',
            stackgroup='one',
            line=dict(width=0.5, color='#0d6efd'),
            fillcolor='rgba(13, 110, 253, 0.5)'
        ))
        
        # Układ
        fig.update_layout(
            height=300,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(0,0,0,0)',
                bordercolor='rgba(0,0,0,0)'
            ),
            margin=dict(l=50, r=10, t=10, b=40),
            paper_bgcolor=VIZ_CFG['colors']['background'],
            plot_bgcolor=VIZ_CFG['colors']['card_background'],
            font=dict(
                family="Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif",
                color=VIZ_CFG['colors']['text_color']
            ),
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="#1e222d",
                bordercolor="#2a2e39",
                font=dict(color="#dee2e6"),
            ),
            xaxis=dict(
                title="Date",
                linecolor=GRID_COLOR,
                gridcolor=GRID_COLOR,
                zeroline=False,
                automargin=True
            ),
            yaxis=dict(
                title="Allocation (%)",
                gridcolor=GRID_COLOR,
                ticksuffix="%",
                range=[0, 100]
            )
        )
        
        return fig
    except Exception as e:
        logger.error(f"Error in create_my_allocation_chart: {e}")
        return create_empty_chart("Error creating chart")

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
                        id="results-loading", 
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
                        ],
                        type="default"
                    ),
                    
                    # Osobny loading dla equity curve
                    dcc.Loading(
                        id="equity-loading",
                        children=[html.Div(id="equity-curve-container", className="mb-4", style={'minHeight': '400px'})],
                        type="circle"
                    ),
                    
                    html.H5("Portfolio Allocation Over Time", className="mt-3 mb-2"),
                    
                    # Osobny loading dla alokacji
                    dcc.Loading(
                        id="allocation-loading",
                        children=[html.Div(id="portfolio-composition-container", style={'minHeight': '300px'})],
                        type="circle"
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
@app.callback(
    # Special outputs first (ones with unique IDs)
    Output('market-filter-options-collapse', 'is_open'),
    # Individual outputs for specific components with explicit IDs to avoid pattern conflicts
    Output({'type': 'risk-input', 'index': "trailing_stop_activation"}, 'disabled'),
    Output({'type': 'risk-input', 'index': "trailing_stop_distance"}, 'disabled'),
    Output({'type': 'risk-input', 'index': "market_trend_lookback"}, 'disabled'),
    Output({'type': 'risk-input', 'index': "max_position_size"}, 'disabled'),
    Output({'type': 'risk-input', 'index': "min_position_size"}, 'disabled'),
    Output({'type': 'risk-input', 'index': "max_open_positions"}, 'disabled'),
    Output({'type': 'risk-input', 'index': "stop_loss_pct"}, 'disabled'),
    Output({'type': 'risk-input', 'index': "profit_target_ratio"}, 'disabled'),
    Output({'type': 'risk-input', 'index': "max_drawdown"}, 'disabled'),
    Output({'type': 'risk-input', 'index': "max_daily_loss"}, 'disabled'),
    # Inputs
    Input({'type': 'risk-checkbox', 'index': ALL}, 'value'),
    Input({'type': 'risk-checkbox', 'index': ALL}, 'id'),
    Input("risk-management-toggle", "value"),
    prevent_initial_call=True
)
def update_all_risk_inputs(checkbox_values, checkbox_ids, risk_mode):
    # Create mapping of checkbox IDs to values
    checkbox_states = {cb_id['index']: val for cb_id, val in zip(checkbox_ids, checkbox_values)}
    risk_enabled = (risk_mode == "enabled")
    
    # Market filter collapse state
    market_filter_open = risk_enabled and checkbox_states.get("use-market-filter", False)
    
    # Each input's disabled state depends on risk_enabled and its associated checkbox
    trailing_stop_activation_disabled = (not risk_enabled) or (not checkbox_states.get("use-trailing-stop", False))
    trailing_stop_distance_disabled = (not risk_enabled) or (not checkbox_states.get("use-trailing-stop", False))
    market_trend_lookback_disabled = (not risk_enabled) or (not checkbox_states.get("use-market-filter", False))
    max_position_size_disabled = (not risk_enabled) or (not checkbox_states.get("use-max-position-size", False))
    min_position_size_disabled = (not risk_enabled) or (not checkbox_states.get("use-min-position-size", False))
    max_open_positions_disabled = (not risk_enabled) or (not checkbox_states.get("use-max-positions", False))
    stop_loss_pct_disabled = (not risk_enabled) or (not checkbox_states.get("use-stop-loss", False))
    profit_target_ratio_disabled = (not risk_enabled) or (not checkbox_states.get("use-profit-target", False))
    max_drawdown_disabled = (not risk_enabled) or (not checkbox_states.get("use-max-drawdown", False))
    max_daily_loss_disabled = (not risk_enabled) or (not checkbox_states.get("use-max-daily-loss", False))
    
    # Return all states
    return (
        market_filter_open,
        trailing_stop_activation_disabled,
        trailing_stop_distance_disabled,
        market_trend_lookback_disabled,
        max_position_size_disabled,
        min_position_size_disabled,
        max_open_positions_disabled,
        stop_loss_pct_disabled,
        profit_target_ratio_disabled,
        max_drawdown_disabled,
        max_daily_loss_disabled
    )

# Funkcja pomocnicza do parsowania parametrów ryzyka
def parse_risk_param_value(input_id, input_value):
    """Parse risk parameter values with better type handling."""
    if input_value is None or input_value == '':
        return None
        
    # Convert to appropriate types based on parameter name pattern
    try:
        if isinstance(input_id, str):
            # Percentage values that need to be divided by 100
            if any(x in input_id for x in ["pct", "size", "drawdown", "loss", "activation", "distance"]):
                return float(input_value) / 100.0
            # Standard float values
            elif "ratio" in input_id:
                return float(input_value)
            # Integer values
            elif any(x in input_id for x in ["positions", "lookback"]):
                return int(input_value)
        # Default case
        return input_value
    except (ValueError, TypeError):
        logger.warning(f"Could not parse risk parameter {input_id}: {input_value}")
        return None


# Główny callback do uruchamiania backtestu
@app.callback(
    Output("calculation-status", "children"),
    Output("equity-curve-container", "children"),
    Output("metrics-container", "children"),
    Output("trade-distribution-container", "children"),
    Output("trade-table-container", "children"),
    Output("backtest-period", "children"),
    Output("portfolio-instruments", "children"),
    Output("portfolio-composition-container", "children"),
    Output("trade-duration-container", "children"),
    Input("run-backtest-button", "n_clicks"),
    State("strategy-selector", "value"),
    State("ticker-selector", "value"),
    State("risk-management-toggle", "value"),
    State({'type': 'strategy-param', 'index': ALL}, 'value'),
    State({'type': 'strategy-param', 'index': ALL}, 'id'),
    State({'type': 'risk-checkbox', 'index': ALL}, 'value'),
    State({'type': 'risk-checkbox', 'index': ALL}, 'id'),
    State({'type': 'risk-input', 'index': ALL}, 'value'),
    State({'type': 'risk-input', 'index': ALL}, 'id'),
    prevent_initial_call=True
)
def run_full_backtest(n_clicks, strategy_name, selected_tickers, risk_toggle_value, 
                      strategy_param_values, strategy_param_ids, risk_checkbox_values, 
                      risk_checkbox_ids, risk_input_values, risk_input_ids):
    """Run backtest with selected configuration and display results."""
    # Początek timingu i inicjalizacji
    start_time = pd.Timestamp.now()
    logger.info("="*50)
    logger.info(f"Backtest triggered: Strategy={strategy_name}, Tickers={selected_tickers}, Risk={risk_toggle_value}")
    
    # Inicjalizacja pustych komponentów
    empty_components = {
        'metrics': create_metric_cards({}),
        'chart': create_empty_chart("Equity Curve"),
        'alloc': create_empty_chart("Allocation"),
        'trade_hist': create_empty_chart("P/L Distribution"),
        'duration_hist': create_empty_chart("Duration Distribution"),
        'table': html.Div("Run backtest to see trades.", className="text-muted text-center p-3")
    }
    initial_status = html.Div("Config ready. Click 'Run Backtest'.", className="text-info text-center")
    
    def return_empty_state(status_msg=initial_status):
        """Zwróć pusty stan z opcjonalnym komunikatem statusu."""
        return (status_msg, empty_components['chart'], empty_components['metrics'], 
                empty_components['trade_hist'], empty_components['table'], "", "", 
                empty_components['alloc'], empty_components['duration_hist'])
    
    # Walidacja danych wejściowych
    if not strategy_name:
        return return_empty_state(html.Div("Please select a strategy.", className="text-warning text-center"))
    if not selected_tickers:
        return return_empty_state(html.Div("Please select at least one ticker.", className="text-warning text-center"))
    
    try:
        # Przetwórz parametry strategii
        strategy_params = process_strategy_params(strategy_name, strategy_param_ids, strategy_param_values)
        
        # Przetwórz parametry ryzyka
        risk_params = None
        if risk_toggle_value == "enabled":
            risk_params = process_risk_params(risk_checkbox_ids, risk_checkbox_values, 
                                             risk_input_ids, risk_input_values)
            logger.info(f"Risk enabled with params: {risk_params}")
        
        # Uruchom backtest
        logger.info("Starting backtest...")
        signals, results, stats = backtest_manager.run_backtest(
            strategy_type=strategy_name, 
            tickers=selected_tickers,
            strategy_params=strategy_params,
            risk_params=risk_params
        )
        logger.info("Backtest completed.")
        
        # Obsłuż puste wyniki
        if results is None or stats is None:
            logger.error("Backtest manager returned None.")
            return return_empty_state(html.Div("Error during backtest execution. Check logs.", 
                                              className="text-danger text-center"))
        
        # Wyodrębnij kluczowe dane
        portfolio_values = results.get('Portfolio_Value', pd.Series())
        benchmark_values = results.get('Benchmark')
        trades = results.get('trades', [])
        
        # Obsłuż pusty portfel
        if portfolio_values.empty:
            logger.warning("Backtest completed, but no portfolio data generated.")
            return (
                html.Div("Backtest completed, no portfolio equity generated.", 
                        className="text-warning text-center"),
                empty_components['chart'],
                create_metric_cards(stats),
                empty_components['trade_hist'],
                create_trade_table(trades),
                "",
                ", ".join(selected_tickers),
                empty_components['alloc'],
                empty_components['duration_hist']
            )
        
        # Przygotuj komponenty wynikowe z leniwym ładowaniem
        logger.info("Generating result components...")
        
        # Sformatuj zakres dat
        date_range = "N/A"
        if not portfolio_values.empty:
            start_date = portfolio_values.index.min().strftime('%Y-%m-%d')
            end_date = portfolio_values.index.max().strftime('%Y-%m-%d')
            date_range = f"{start_date} to {end_date}"
        
        # Format instruments and finish timing
        instruments = ", ".join(sorted(selected_tickers))
        duration = round((pd.Timestamp.now() - start_time).total_seconds(), 2)
        status = html.Div([html.Span(f"Backtest completed successfully in {duration}s. ", className="text-success"), html.Span("Generating visualizations...", id="viz-status", className="text-info")])
        
        # Tworzenie komponentów z wykorzystaniem zbuforowanych funkcji
        logger.info("Generating result components...")
        
        # Sformatuj zakres dat
        date_range = "N/A"
        if not portfolio_values.empty:
            start_date = portfolio_values.index.min().strftime('%Y-%m-%d')
            end_date = portfolio_values.index.max().strftime('%Y-%m-%d')
            date_range = f"{start_date} to {end_date}"
        
        # Format instruments and finish timing
        instruments = ", ".join(sorted(selected_tickers))
        duration = round((pd.Timestamp.now() - start_time).total_seconds(), 2)
        status = html.Div([html.Span(f"Backtest completed successfully in {duration}s. ", className="text-success"), html.Span("Generating visualizations...", id="viz-status", className="text-info")])
        
        # Zoptymalizuj generowanie wyników - przetwarzaj wykresy jeden po drugim
        # Spróbuj użyć zbuforowanych wersji, a jeśli się nie uda, to użyj bezpośrednio visualizera
        try:
            equity_fig = generate_equity_curve(portfolio_values, benchmark_values)
        except Exception as e:
            logger.warning(f"Error using generate_equity_curve: {e}, falling back to direct method")
            equity_fig = visualizer.create_equity_curve_figure(portfolio_values, benchmark_values)
            
        equity_curve = dcc.Loading(
            id="loading-equity",
            children=html.Div(
                dcc.Graph(
                    figure=equity_fig,
                    config={'displayModeBar': False}
                )
            ), 
            type="circle"
        )
        
        metrics = create_metric_cards(stats)
        
        # Generuj kolejny wykres
        try:
            trade_dist_fig = generate_trade_distribution(trades)
        except Exception as e:
            logger.warning(f"Error generating trade distribution: {e}")
            trade_dist_fig = create_empty_chart("P/L Distribution")
            
        trade_hist = dcc.Loading(
            id="loading-trade-hist",
            children=html.Div(
                dcc.Graph(
                    figure=trade_dist_fig,
                    config={'displayModeBar': False}
                )
            ), 
            type="circle"
        )
        
        # Generuj tabelę transakcji
        trade_table = dcc.Loading(
            id="loading-trade-table", 
            children=create_trade_table(trades),
            type="circle"
        )
        
        # Generuj wykres alokacji
        try:
            # Użyj naszej własnej implementacji
            allocation_fig = create_my_allocation_chart(results)
            
            # Teraz allocation_fig na pewno jest obiektem Figure
            allocation = dcc.Loading(
                id="loading-allocation",
                children=html.Div(
                    dcc.Graph(
                        id="allocation-graph",
                        figure=allocation_fig,
                        config={'displayModeBar': False}
                    )
                ),
                type="circle"
            )
        except Exception as e:
            logger.warning(f"Error creating allocation chart: {e}")
            allocation = dcc.Loading(
                id="loading-allocation",
                children=html.Div("Error generating allocation chart", className="text-danger text-center p-3"),
                type="circle"
            )
        
        # Generuj histogram czasu trwania
        duration_hist = dcc.Loading(
            id="loading-duration",
            children=create_duration_histogram(trades),
            type="circle"
        )
        
        # Uruchom garbage collector po zakończeniu obliczeń
        gc.collect()
        
        logger.info(f"Backtest successful in {duration}s.")
        
        # Return results
        return (
            status,
            equity_curve,
            metrics,
            trade_hist,
            trade_table,
            date_range,
            instruments,
            allocation,
            duration_hist
        )
        
    except Exception as e:
        # Zapisz szczegóły błędu
        error_details = traceback.format_exc()
        logger.error(f"CRITICAL: Unhandled error in backtest callback: {str(e)}")
        logger.error(error_details)
        
        # Wyświetl bardziej szczegółowy komunikat dla użytkownika
        error_msg = html.Div([
            html.H5("An error occurred during backtest", className="text-danger"),
            html.P(f"Error type: {type(e).__name__}", className="mb-1"),
            html.P(f"Error message: {str(e)}", className="mb-3"),
            html.P("Check application logs for more details.", className="small text-muted")
        ], className="text-center p-3")
        
        return return_empty_state(error_msg)


def process_strategy_params(strategy_name, strategy_param_ids, strategy_param_values):
    """Process and validate strategy parameters."""
    strategy_params = {}
    strategy_class = AVAILABLE_STRATEGIES.get(strategy_name)
    
    if not strategy_class:
        raise ValueError(f"Strategy class {strategy_name} not found.")
    
    # Map parameter IDs to values
    param_map = {pid['index']: val for pid, val in zip(strategy_param_ids, strategy_param_values)}
    
    # Process each parameter from signature
    sig = inspect.signature(strategy_class.__init__)
    for name, param in sig.parameters.items():
        if name in ['self', 'tickers', 'args', 'kwargs']:
            continue
            
        param_value = param_map.get(name)
        
        # Determine expected type
        expected_type = str
        if param.annotation != inspect.Parameter.empty:
            expected_type = param.annotation
        elif param.default is not inspect.Parameter.empty:
            expected_type = type(param.default)
        
        # Convert to expected type
        try:
            if expected_type == bool:
                converted_value = bool(param_value)
            elif expected_type == int and param_value is not None:
                converted_value = int(param_value)
            elif expected_type == float and param_value is not None:
                converted_value = float(param_value)
            else:
                converted_value = param_value
                
            if converted_value is not None:
                strategy_params[name] = converted_value
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Parameter conversion warning: {name}={param_value} ({expected_type}). Error: {e}")
            strategy_params[name] = param_value
            
    logger.info(f"Strategy parameters: {strategy_params}")
    return strategy_params

def process_risk_params(risk_checkbox_ids, risk_checkbox_values, risk_input_ids, risk_input_values):
    """Process and validate risk management parameters."""
    risk_params = {}
    
    # Create mappings
    checkbox_states = {cb_id['index']: checked for cb_id, checked in zip(risk_checkbox_ids, risk_checkbox_values)}
    input_values = {inp_id['index']: value for inp_id, value in zip(risk_input_ids, risk_input_values)}
    
    # Define parameter mappings
    risk_mapping = {
        "use-max-position-size": "max_position_size",
        "use-min-position-size": "min_position_size",
        "use-max-positions": "max_open_positions",
        "use-stop-loss": "stop_loss_pct",
        "use-profit-target": "profit_target_ratio",
        "use-trailing-stop": ["use_trailing_stop", "trailing_stop_activation", "trailing_stop_distance"],
        "use-max-drawdown": "max_drawdown",
        "use-max-daily-loss": "max_daily_loss",
        "use-market-filter": ["use_market_filter", "market_trend_lookback"]
    }
    
    # Process each parameter based on checkbox state
    for checkbox_id, param_keys in risk_mapping.items():
        if checkbox_states.get(checkbox_id, False):
            if isinstance(param_keys, list):
                # Handle multi-parameter cases (e.g. trailing stop)
                main_param = param_keys[0]
                risk_params[main_param] = True
                
                for param_key in param_keys[1:]:
                    parsed_value = parse_risk_param_value(param_key, input_values.get(param_key))
                    if parsed_value is not None:
                        risk_params[param_key] = parsed_value
            else:
                # Handle single parameter cases
                param_key = param_keys
                parsed_value = parse_risk_param_value(param_key, input_values.get(param_key))
                if parsed_value is not None:
                    risk_params[param_key] = parsed_value
                    
    return risk_params

# =============================================================================
# ===== URUCHOMIENIE APLIKACJI ================================================
# =============================================================================
if __name__ == '__main__':
    logger.info("Starting Dash application...")
    
    # Check data availability before starting
    try:
        startup_tickers = get_available_tickers()
        if not startup_tickers:
            logger.warning("No tickers found during startup check. Application may not function properly.")
        else:
            logger.info(f"Found {len(startup_tickers)} tickers during startup.")
    except Exception as e:
        logger.error(f"Error during startup ticker check: {e}", exc_info=True)
    
    # Configure server
    app_host = os.environ.get("HOST", "127.0.0.1")
    app_port = int(os.environ.get("PORT", 8050))
    app_debug = os.environ.get("DASH_DEBUG_MODE", "True").lower() in ['true', '1', 't']
    
    # Run application
    logger.info(f"Running app on http://{app_host}:{app_port}/ with debug={app_debug}")
    try:
        app.run(debug=app_debug, host=app_host, port=app_port)
        logger.info("Dash application stopped.")
    except Exception as e:
        logger.critical(f"Application crashed: {e}", exc_info=True)
        sys.exit(1)
