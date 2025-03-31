from dash import dcc
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, Optional, Union, List
import numpy as np
import plotly.express as px
from src.core.constants import CHART_THEME
from src.analysis.metrics import get_trade_bins_dynamic
import math  # Dodano import dla funkcji math.floor/ceil

def get_base_layout(title: str = "", x_title: str = "", y_title: str = "") -> dict:
    """Returns base chart layout with theme applied"""
    return {
        'title': title,
        'xaxis_title': x_title,
        'yaxis_title': y_title,
        'paper_bgcolor': CHART_THEME['paper_bgcolor'],
        'plot_bgcolor': CHART_THEME['plot_bgcolor'],
        'font': {'color': CHART_THEME['font_color']},
        'xaxis': {'gridcolor': CHART_THEME['grid_color']},
        'yaxis': {'gridcolor': CHART_THEME['grid_color']},
    }

def create_empty_chart(layout_title: str) -> dcc.Graph:
    """Create an empty chart with informative message"""
    figure = {
        'data': [],
        'layout': {
            'title': layout_title,
            'template': CHART_THEME,
            'paper_bgcolor': '#1e222d',
            'plot_bgcolor': '#1e222d',
            'font': {'color': '#ffffff', 'family': 'system-ui'},
            'xaxis': {
                'showticklabels': False,
                'showgrid': False,
            },
            'yaxis': {
                'showticklabels': False,
                'showgrid': False,
            },
            'annotations': [{
                'text': 'No data available',
                'showarrow': False,
                'font': {'size': 20, 'color': '#6c757d'},
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
            }],
            'height': 450,
            'autosize': True
        }
    }
    
    return dcc.Graph(
        id=f"empty-chart-{layout_title.lower().replace(' ', '-')}",
        figure=figure,
        config={'displayModeBar': False},
        style={'height': '100%', 'width': '100%'}
    )

def create_styled_chart(figure_data: Dict[str, pd.Series], 
                        layout_title: str, 
                        benchmark_ticker: str = "SPY") -> dcc.Graph:
    """Create a professionally styled chart component with consistent styling"""
    if not figure_data or not any(len(series) > 0 for series in figure_data.values()):
        return create_empty_chart(layout_title)
    
    traces = []
    for name, data in figure_data.items():
        # Skip empty data series
        if data is None or len(data) == 0:
            continue
            
        # Filter data for trading period
        if isinstance(data, pd.Series):
            # Make copy to prevent pandas SettingWithCopyWarning
            data = data.copy()
            
        color = '#17B897' if name == 'Portfolio' else '#FF6B6B'
        trace_name = 'Portfolio Value' if name == 'Portfolio' else f'Benchmark ({benchmark_ticker})'
        
        trace = {
            'x': data.index,
            'y': data.values,
            'name': trace_name,
            'type': 'scatter',
            'mode': 'lines',
            'line': {'color': color, 'width': 2}
        }
        traces.append(trace)
    
    figure = {
        'data': traces,
        'layout': {
            'title': layout_title,
            'template': CHART_THEME,
            'paper_bgcolor': '#1e222d',
            'plot_bgcolor': '#1e222d',
            'font': {'color': '#ffffff', 'family': 'system-ui'},
            'xaxis': {
                'gridcolor': '#2a2e39',
                'showgrid': True,
                'zeroline': False,
                'title': 'Date',
                'rangeslider': {'visible': False}
            },
            'yaxis': {
                'gridcolor': '#2a2e39',
                'showgrid': True,
                'zeroline': True,
                'zerolinecolor': '#2a2e39',
                'title': 'Portfolio Value ($)',
                'tickprefix': '$'
            },
            'margin': {'t': 50, 'l': 50, 'r': 20, 'b': 50},
            'showlegend': True,
            'legend': {
                'orientation': 'h',
                'y': 1.1,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'color': '#ffffff'},
                'bgcolor': '#1e222d'
            },
            'hovermode': 'x unified',
            'hoverlabel': {'bgcolor': '#2a2e39', 'font': {'color': 'white'}},
            'height': 450,
            'autosize': True
        }
    }

    return dcc.Graph(
        id=f"chart-{layout_title.lower().replace(' ', '-')}",
        figure=figure,
        config={
            'displayModeBar': True,
            'responsive': True,
            'scrollZoom': True,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': f'{layout_title}',
                'height': 500,
                'width': 700,
                'scale': 2
            }
        },
        style={'height': '100%', 'width': '100%'}
    )

def create_trade_histogram_figure(trades, stats):
    """
    Create enhanced trade return distribution histogram with better bin distribution
    and special handling for outliers
    """
    if not trades:
        return dcc.Graph(figure={
            'data': [],
            'layout': {
                'title': 'Trade Return Distribution',
                'xaxis': {'visible': False},
                'yaxis': {'visible': False},
                'annotations': [{
                    'text': 'No trade data available',
                    'showarrow': False,
                    'font': {'size': 16, 'color': '#ffffff'},
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 0.5,
                    'y': 0.5
                }],
                'paper_bgcolor': '#1e222d',
                'plot_bgcolor': '#1e222d'
            }
        })
    
    # Calculate trade returns as percentages
    returns = []
    for trade in trades:
        try:
            entry_price = trade.get('entry_price', 0)
            exit_price = trade.get('exit_price', 0)
            shares = trade.get('shares', 0)
            
            if entry_price > 0 and shares > 0:
                trade_return = (exit_price - entry_price) / entry_price * 100
                returns.append(trade_return)
        except (KeyError, TypeError, ZeroDivisionError):
            continue
    
    if not returns:
        return dcc.Graph(figure={'data': [], 'layout': {'title': 'No valid returns data'}})
    
    # Calculate the min and max returns for bin sizing
    min_return = min(returns)
    max_return = max(returns)
    
    # Determine if we need outlier handling (ranges > +-20%)
    needs_outlier_handling = min_return < -20 or max_return > 20
    
    # Define thresholds
    if needs_outlier_handling:
        upper_threshold = 20  # Zwroty powyżej 20% jako górne outliery
        lower_threshold = -20  # Zwroty poniżej -20% jako dolne outliery
    else:
        # Dla wąskich rozkładów użyj faktycznych min/max z buforem
        range_size = max_return - min_return
        
        if range_size <= 10:  # Bardzo wąski zakres
            # Zaokrąglenie do najbliższego 1% z małym buforem
            lower_threshold = math.floor(min_return - 1)
            upper_threshold = math.ceil(max_return + 1)
        else:
            # Zaokrąglenie do najbliższego 5% z buforem
            lower_threshold = math.floor(min_return / 5) * 5 - 5
            upper_threshold = math.ceil(max_return / 5) * 5 + 5
    
    # Filtruj zwroty na normalne i outliery
    normal_returns = [r for r in returns if lower_threshold <= r <= upper_threshold]
    upper_outliers = [r for r in returns if r > upper_threshold]
    lower_outliers = [r for r in returns if r < lower_threshold]
    
    # Oblicz odpowiedni rozmiar przedziału dla normalnego zakresu
    # Dla wąskich zakresów (np. -4% do 4%), użyj mniejszych przedziałów
    range_width = upper_threshold - lower_threshold
    
    if range_width <= 10:
        # Użyj bardzo małych przedziałów dla wąskich rozkładów (1%)
        bin_size = 1.0
    elif range_width <= 20:
        # Użyj małych przedziałów dla umiarkowanych rozkładów (2%)
        bin_size = 2.0
    else:
        # Użyj adaptacyjnego rozmiaru przedziału w oparciu o ilość danych
        min_bins = max(10, int(np.sqrt(len(normal_returns))))
        bin_size = range_width / min_bins
        # Zaokrąglij do najbliższego 0.5 dla czytelniejszych przedziałów
        bin_size = math.ceil(bin_size * 2) / 2
    
    # Upewnij się, że 0 jest dokładnie na granicy przedziału
    # Znajdź liczbę przedziałów poniżej zera
    num_negative_bins = math.ceil(abs(lower_threshold) / bin_size)
    # Dostosuj dolny próg, aby 0 było dokładnie na granicy przedziału
    lower_threshold = -num_negative_bins * bin_size
    
    # Utwórz krawędzie przedziałów dla normalnego zakresu
    bin_edges = np.arange(lower_threshold, upper_threshold + bin_size, bin_size)
    
    # Przygotuj histogram
    fig = go.Figure()
    
    # Dodaj oddzielny histogram dla każdego przedziału, aby mieć pełną kontrolę nad kolorami
    for i in range(len(bin_edges) - 1):
        left_edge = bin_edges[i]
        right_edge = bin_edges[i+1]
        
        # Filtruj zwroty w tym przedziale
        bin_returns = [r for r in normal_returns if left_edge <= r < right_edge]
        
        # Ustal kolor na podstawie wartości przedziału
        if right_edge <= 0:
            color = '#FF6B6B'  # Czerwony dla przedziałów całkowicie ujemnych
        else:
            color = '#17B897'  # Zielony dla przedziałów z wartościami >= 0
        
        # Dodaj histogram dla tego przedziału
        fig.add_trace(go.Histogram(
            x=bin_returns,
            xbins=dict(
                start=left_edge,
                end=right_edge,
                size=bin_size
            ),
            marker_color=color,
            opacity=0.8,
            showlegend=False,
            name=f"{left_edge:.1f}% to {right_edge:.1f}%"
        ))
    
    # Dodaj outliery jeśli istnieją
    if upper_outliers:
        fig.add_trace(go.Histogram(
            x=upper_outliers,
            xbins=dict(
                start=upper_threshold,
                end=max(upper_outliers) + 5,
                size=5
            ),
            marker_color='#00E676',  # Jasny zielony dla wyjątkowych zwrotów
            opacity=0.8,
            name=f'Zwroty > {upper_threshold}%'
        ))
    
    if lower_outliers:
        fig.add_trace(go.Histogram(
            x=lower_outliers,
            xbins=dict(
                start=min(lower_outliers) - 5,
                end=lower_threshold,
                size=5
            ),
            marker_color='#FF1744',  # Jasny czerwony dla dużych strat
            opacity=0.8,
            name=f'Zwroty < {lower_threshold}%'
        ))
    
    # Utwórz układ histogramu
    fig.update_layout(
        title='Rozkład zwrotów z tradów',
        barmode='overlay',
        paper_bgcolor='#1e222d',
        plot_bgcolor='#1e222d',
        font={'color': '#ffffff'},
        xaxis={
            'title': 'Zwrot (%)',
            'gridcolor': '#2a2e39',
            'zeroline': True,
            'zerolinecolor': '#ff6b6b',
            'zerolinewidth': 1
        },
        yaxis={
            'title': 'Liczba tradów',
            'gridcolor': '#2a2e39'
        },
        bargap=0.05,
        bargroupgap=0.1,
        margin={'t': 50, 'b': 50, 'l': 50, 'r': 20},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color='#ffffff')
        )
    )
    
    # Dodaj pionowe linie dla kluczowych statystyk
    fig.add_shape(
        type="line",
        x0=0, y0=0,
        x1=0, y1=1,
        yref="paper",
        line=dict(color="#ffffff", width=1, dash="dot"),
    )
    
    fig.add_shape(
        type="line",
        x0=np.mean(returns), y0=0,
        x1=np.mean(returns), y1=1,
        yref="paper",
        line=dict(color="#17B897", width=1, dash="dot"),
    )
    
    # Dodaj adnotację ze średnim zwrotem
    fig.add_annotation(
        x=np.mean(returns),
        y=0.85,
        text=f'Średni zwrot: {np.mean(returns):.2f}%',
        showarrow=True,
        arrowhead=2,
        arrowcolor='#ffffff',
        arrowsize=1,
        arrowwidth=1,
        yref="paper",
        ax=0,
        ay=-40
    )
    
    # Zwróć wykres w komponencie Dash Graph
    return dcc.Graph(
        id='trade-histogram',
        figure=fig,
        config={'displayModeBar': True}
    )
