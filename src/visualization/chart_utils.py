import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from dash import dcc, html
from typing import Dict, Any, Optional, Union, List, Tuple
import logging

logger = logging.getLogger(__name__)

# Importuj konfigurację wizualizacji
try:
    from src.core.config import VISUALIZATION_CONFIG as VIZ_CFG
except ImportError:
    logger.warning("Could not import VISUALIZATION_CONFIG. Using default visualization settings.")
    # Podstawowe ustawienia fallback
    VIZ_CFG = {
        "chart_height": 400, "dark_theme": True, "template": "plotly_dark",
        "colors": {
            "portfolio": "#17B897", "benchmark": "#FF6B6B", "profit": "#28a745",
            "loss": "#dc3545", "primary": "#0d6efd", "secondary": "#6c757d",
            "background": "#131722", "card_background": "#1e222d",
            "grid_color": "#2a2e39", "text_color": "#dee2e6", "text_muted": "#6c757d"
        }
    }

CHART_TEMPLATE = VIZ_CFG.get("template", "plotly_dark")
PLOT_BGCOLOR = VIZ_CFG["colors"]["card_background"]
PAPER_BGCOLOR = VIZ_CFG["colors"]["background"]
GRID_COLOR = VIZ_CFG["colors"]["grid_color"]
TEXT_COLOR = VIZ_CFG["colors"]["text_color"]
DEFAULT_HEIGHT = VIZ_CFG.get("chart_height", 400)

# --- Funkcje pomocnicze ---

def _create_base_layout(title: str = "", height: int = DEFAULT_HEIGHT, **kwargs) -> go.Layout:
    """Creates a base Plotly layout object with common theme settings."""
    layout = go.Layout(
        title=dict(text=title, x=0.05, xanchor='left', font=dict(size=16, color=TEXT_COLOR)), # Tytuł po lewej
        height=height,
        template=CHART_TEMPLATE,
        paper_bgcolor=PAPER_BGCOLOR,
        plot_bgcolor=PLOT_BGCOLOR,
        font=dict(color=TEXT_COLOR, family="Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"), # Lepszy font stack
        xaxis=dict(gridcolor=GRID_COLOR, linecolor=GRID_COLOR, zeroline=False, automargin=True),
        yaxis=dict(gridcolor=GRID_COLOR, linecolor=GRID_COLOR, zeroline=False, automargin=True),
        margin=dict(t=50, l=50, r=20, b=40), # Dopasowane marginesy
        hovermode='x unified',
        hoverlabel=dict(bgcolor=VIZ_CFG['colors']['card_background'], bordercolor=GRID_COLOR, font=dict(color=TEXT_COLOR)),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.01, # Legenda na górze po lewej
            bgcolor='rgba(0,0,0,0)', # Przezroczyste tło legendy
            bordercolor='rgba(0,0,0,0)'
        )
    )
    layout.update(**kwargs) # Zastosuj dodatkowe argumenty layoutu
    return layout

# --- Funkcje tworzące komponenty Dash ---

def create_empty_chart(title: str = "No Data Available", height: int = DEFAULT_HEIGHT) -> dcc.Graph:
    """Creates a Dash Graph component displaying a 'No Data' message."""
    layout = _create_base_layout(title="", height=height) # Tytuł w adnotacji
    layout.xaxis.showticklabels = False
    layout.xaxis.showgrid = False
    layout.yaxis.showticklabels = False
    layout.yaxis.showgrid = False
    layout.annotations = [
        go.layout.Annotation(
            text=title,
            showarrow=False,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            font=dict(size=18, color=VIZ_CFG["colors"]["text_muted"])
        )
    ]
    figure = go.Figure(data=[], layout=layout)

    return dcc.Graph(
        figure=figure,
        config={'displayModeBar': False}, # Ukryj pasek narzędzi dla pustego wykresu
        style={'height': f'{height}px', 'width': '100%'}
    )


def create_styled_chart(figure_data: Dict[str, pd.Series],
                        layout_title: str,
                        yaxis_title: str = "Value",
                        yaxis_format: Optional[str] = None, # np. '.2%' dla procentów, '$' dla tickprefix
                        height: int = DEFAULT_HEIGHT) -> dcc.Graph:
    """
    Creates a styled line chart for comparing time series (e.g., Portfolio vs Benchmark).

    Args:
        figure_data (Dict[str, pd.Series]): Dict where keys are trace names and values are pd.Series.
        layout_title (str): Title for the chart layout.
        yaxis_title (str): Title for the Y-axis.
        yaxis_format (str): Plotly tick format string for Y-axis (e.g., '.2f', '.0%').
        height (int): Height of the chart in pixels.

    Returns:
        dcc.Graph: Dash Graph component.
    """
    if not figure_data or all(v is None or v.empty for v in figure_data.values()):
        return create_empty_chart(f"{layout_title} - No Data", height=height)

    traces = []
    colors = [VIZ_CFG['colors']['portfolio'], VIZ_CFG['colors']['benchmark'], VIZ_CFG['colors']['primary'], VIZ_CFG['colors']['secondary']]
    color_idx = 0

    for name, data in figure_data.items():
        if data is None or data.empty:
            logger.warning(f"Skipping empty series: {name} in create_styled_chart")
            continue

        cleaned_data = data.dropna() # Usuń NaN przed rysowaniem
        if cleaned_data.empty:
             logger.warning(f"Skipping series '{name}' as it is empty after dropping NaNs.")
             continue

        # Wybierz kolor
        trace_color = colors[color_idx % len(colors)]
        color_idx += 1

        traces.append(go.Scatter(
            x=cleaned_data.index,
            y=cleaned_data.values,
            name=name,
            mode='lines',
            line=dict(color=trace_color, width=2),
            hoverinfo='x+y+name'
        ))

    if not traces:
        return create_empty_chart(f"{layout_title} - No Valid Data", height=height)

    # Ustawienia osi Y
    yaxis_config = dict(title=yaxis_title, gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, automargin=True)
    if yaxis_format:
        if yaxis_format == '$':
            yaxis_config['tickprefix'] = '$'
            yaxis_config['tickformat'] = ',.2f' # Formatuj jako liczba z przecinkami i 2 miejscami
        else:
            yaxis_config['tickformat'] = yaxis_format


    layout = _create_base_layout(title=layout_title, height=height)
    layout.xaxis.title = "Date"
    layout.yaxis = yaxis_config
    layout.showlegend = len(traces) > 1 # Pokaż legendę tylko jeśli jest więcej niż jedna seria

    figure = go.Figure(data=traces, layout=layout)

    return dcc.Graph(
        figure=figure,
        config={'displayModeBar': True, 'responsive': True, 'scrollZoom': True, 'modeBarButtonsToRemove': ['lasso2d', 'select2d']},
        style={'height': f'{height}px', 'width': '100%'}
    )


def create_trade_histogram_figure(trades: List[Dict], stats: Dict) -> go.Figure | html.Div:
    """
    Creates a Plotly Figure object for the trade P&L distribution histogram.

    Args:
        trades (List[Dict]): List of trade dictionaries, requiring 'pnl_pct'.
        stats (Dict): Dictionary possibly containing avg_trade_pnl or other stats for annotations.

    Returns:
        go.Figure | html.Div: Plotly Figure object or a Div with error message.
    """
    if not trades:
        return html.Div("No trades available for histogram.", className="text-muted text-center p-3")

    pnl_pcts = []
    for t in trades:
        pnl_pct = t.get('pnl_pct')
        if pnl_pct is not None:
            try: pnl_pcts.append(float(pnl_pct))
            except (ValueError, TypeError): pass

    if not pnl_pcts:
        return html.Div("Could not extract P&L percentages from trades.", className="text-warning text-center p-3")

    # Determine bin range, handling outliers
    q1 = np.percentile(pnl_pcts, 5)
    q3 = np.percentile(pnl_pcts, 95)
    iqr = q3 - q1
    lower_bound = max(min(pnl_pcts), q1 - 1.5 * iqr)
    upper_bound = min(max(pnl_pcts), q3 + 1.5 * iqr)
    # Ensure range includes 0
    lower_bound = min(-1.0, lower_bound)
    upper_bound = max(1.0, upper_bound)

    # Create figure with two traces: one for wins, one for losses
    fig = go.Figure()
    wins = [p for p in pnl_pcts if p >= 0]
    losses = [p for p in pnl_pcts if p < 0]

    # Heurystyka dla liczby binów
    num_bins = max(10, min(50, int(len(pnl_pcts)**0.5 * 2))) # Zależna od liczby transakcji, min 10, max 50

    if wins:
        fig.add_trace(go.Histogram(
            x=wins,
            name='Wins',
            marker_color=VIZ_CFG['colors']['profit'],
            opacity=0.75,
            nbinsx=num_bins, # Użyj tej samej liczby binów dla obu
            xbins=dict(start=0, end=upper_bound) # Określ zakres dla dodatnich
        ))
    if losses:
        fig.add_trace(go.Histogram(
            x=losses,
            name='Losses',
            marker_color=VIZ_CFG['colors']['loss'],
            opacity=0.75,
            nbinsx=num_bins,
            xbins=dict(start=lower_bound, end=0) # Określ zakres dla ujemnych
        ))

    layout = _create_base_layout(title="", height=250) # Tytuł nad wykresem w app.py
    layout.xaxis = dict(title='Trade Return (%)', ticksuffix='%', gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, zeroline=True)
    layout.yaxis = dict(title='Number of Trades', gridcolor=GRID_COLOR)
    layout.barmode = 'overlay' # Nakładaj słupki
    layout.bargap = 0.1
    layout.showlegend = False # Legenda nie jest potrzebna przy dwóch kolorach
    layout.margin = dict(t=10, l=40, r=10, b=40) # Zmniejszone marginesy

    # Dodaj linię średniego zwrotu % jeśli jest dostępna
    avg_return_pct = np.mean(pnl_pcts)
    fig.add_vline(x=avg_return_pct, line_width=1, line_dash="dash", line_color=VIZ_CFG['colors']['primary'],
                  annotation_text=f"Avg: {avg_return_pct:.2f}%", annotation_position="top right", annotation_font_size=10)

    fig.update_layout(layout)
    return fig


def create_allocation_chart(results: Dict) -> go.Figure | html.Div:
    """
    Creates stacked area charts showing portfolio allocation over time (Percentage and Dollar Value).
    Requires 'portfolio_values' (Series) and 'trades' (List[Dict]) in the results dictionary.
    """
    if not results or 'Portfolio_Value' not in results or results['Portfolio_Value'].empty:
        return create_empty_chart("Portfolio Allocation - No Data", height=300)

    portfolio_values = results['Portfolio_Value']
    trades = results.get('trades', [])
    initial_capital = portfolio_values.iloc[0]
    dates = portfolio_values.index

    if not isinstance(dates, pd.DatetimeIndex):
        logger.error("Cannot create allocation chart: portfolio_values index is not DatetimeIndex.")
        return create_empty_chart("Allocation Chart Error", height=300)

    # --- Calculate Holdings Over Time ---
    # Create a DataFrame to hold the dollar value of each asset and cash over time
    holdings_df = pd.DataFrame(index=dates)
    holdings_df['Cash'] = initial_capital # Start with full cash

    # Track shares held for each ticker
    current_shares = {} # ticker -> shares

    # Iterate through dates and update holdings based on trades executed *before* or *on* that date
    all_trade_dates = sorted(list(set([pd.to_datetime(t['entry_date']) for t in trades] + [pd.to_datetime(t['exit_date']) for t in trades])))

    last_portfolio_value = initial_capital
    active_tickers = set()

    # Pre-calculate prices for efficiency (using portfolio_values for consistency is tricky)
    # It's better to have the full OHLCV data available here.
    # Fallback: Use portfolio value changes to approximate asset value (less accurate)

    # Simplified approach: Track cash changes from trades
    cash_changes = pd.Series(0.0, index=dates)
    positions_value = pd.DataFrame(0.0, index=dates, columns=[]) # Store value of each position

    logger.debug(f"Starting allocation calculation for {len(trades)} trades over {len(dates)} dates.")
    processed_trades = 0
    for trade in trades:
        try:
            ticker = trade['ticker']
            entry_date = pd.to_datetime(trade['entry_date'])
            exit_date = pd.to_datetime(trade['exit_date'])
            shares = int(trade['shares'])
            entry_price = float(trade['entry_price'])
            exit_price = float(trade['exit_price'])
            direction = int(trade.get('direction', 1)) # Assume long if missing

            # Subtract cost at entry date
            entry_cost = shares * entry_price
            if entry_date in cash_changes.index:
                 cash_changes.loc[entry_date:] -= entry_cost
            else: # If exact date not in index, apply from next available date
                 next_date_idx = cash_changes.index.searchsorted(entry_date)
                 if next_date_idx < len(cash_changes.index):
                      cash_changes.iloc[next_date_idx:] -= entry_cost


            # Add proceeds at exit date
            exit_proceeds = shares * exit_price
            if exit_date in cash_changes.index:
                 cash_changes.loc[exit_date:] += exit_proceeds
            else:
                 next_date_idx = cash_changes.index.searchsorted(exit_date)
                 if next_date_idx < len(cash_changes.index):
                      cash_changes.iloc[next_date_idx:] += exit_proceeds

            processed_trades += 1
        except Exception as e:
             logger.warning(f"Error processing trade for allocation calc: {trade}. Error: {e}")

    logger.debug(f"Processed {processed_trades} trades for cash changes.")

    # Calculate cash series over time
    holdings_df['Cash'] = initial_capital + cash_changes.cumsum()

    # Calculate total value of positions (Total Portfolio Value - Cash)
    # Ensure portfolio_values index aligns with holdings_df index
    aligned_portfolio_values = portfolio_values.reindex(holdings_df.index).ffill().bfill()
    holdings_df['PositionsTotal'] = aligned_portfolio_values - holdings_df['Cash']
    # Ensure non-negative position values (cash calculation might be slightly off)
    holdings_df['PositionsTotal'] = holdings_df['PositionsTotal'].clip(lower=0)


    # --- Create Percentage Chart ---
    # Calculate percentages based on the *aligned* portfolio values
    total_value_aligned = holdings_df['Cash'] + holdings_df['PositionsTotal']
    # Avoid division by zero if total value is zero
    safe_total_value = total_value_aligned.replace(0, 1e-9)

    alloc_pct_df = pd.DataFrame(index=dates)
    alloc_pct_df['Cash'] = (holdings_df['Cash'] / safe_total_value) * 100
    alloc_pct_df['Positions'] = (holdings_df['PositionsTotal'] / safe_total_value) * 100


    pct_fig = go.Figure()
    pct_fig.add_trace(go.Scatter(
        x=alloc_pct_df.index, y=alloc_pct_df['Cash'], name='Cash Allocation',
        mode='lines', stackgroup='one', line=dict(width=0.5, color=VIZ_CFG['colors']['secondary']),
        fillcolor='rgba(108, 117, 125, 0.5)' # Use secondary color with alpha
    ))
    pct_fig.add_trace(go.Scatter(
        x=alloc_pct_df.index, y=alloc_pct_df['Positions'], name='Positions Allocation',
        mode='lines', stackgroup='one', line=dict(width=0.5, color=VIZ_CFG['colors']['primary']),
        fillcolor='rgba(13, 110, 253, 0.5)' # Use primary color with alpha
    ))

    layout_pct = _create_base_layout(title="", height=300) # Tytuł nad wykresem
    layout_pct.yaxis = dict(title='Allocation (%)', ticksuffix='%', range=[0, 100], gridcolor=GRID_COLOR)
    layout_pct.xaxis.title = "Date"
    layout_pct.showlegend = True
    layout_pct.margin = dict(t=10, l=50, r=10, b=40) # Zmniejszone marginesy

    pct_fig.update_layout(layout_pct)


    # --- Create Dollar Value Chart ---
    # (Optional - percentage is often more informative)
    # value_fig = go.Figure()
    # value_fig.add_trace(go.Scatter(
    #     x=holdings_df.index, y=holdings_df['Cash'], name='Cash Value',
    #     mode='lines', stackgroup='one', line=dict(width=0.5, color=VIZ_CFG['colors']['secondary']),
    #     fillcolor='rgba(108, 117, 125, 0.5)'
    # ))
    # value_fig.add_trace(go.Scatter(
    #     x=holdings_df.index, y=holdings_df['PositionsTotal'], name='Positions Value',
    #     mode='lines', stackgroup='one', line=dict(width=0.5, color=VIZ_CFG['colors']['primary']),
    #     fillcolor='rgba(13, 110, 253, 0.5)'
    # ))
    # layout_value = _create_base_layout(title="", height=300)
    # layout_value.yaxis = dict(title='Value ($)', tickprefix='$', gridcolor=GRID_COLOR)
    # layout_value.xaxis.title = "Date"
    # layout_value.showlegend = True
    # layout_value.margin = dict(t=10, l=50, r=10, b=40)
    # value_fig.update_layout(layout_value)

    # Return only the percentage chart for now
    return dcc.Graph(figure=pct_fig, config={'displayModeBar': False})