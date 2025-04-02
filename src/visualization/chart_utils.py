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

def create_empty_chart(layout_title: str = "No Data") -> dcc.Graph:
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
    """Create trade return distribution histogram"""
    if not trades:
        return create_empty_chart()
    
    # Calculate % returns for each trade
    trade_returns = []
    for trade in trades:
        if 'entry_price' in trade and 'exit_price' in trade and 'shares' in trade:
            entry_price = float(trade['entry_price'])
            exit_price = float(trade['exit_price'])
            shares = float(trade['shares'])
            
            if entry_price > 0 and shares > 0:
                profit = (exit_price - entry_price) * shares
                percent_return = (profit / (entry_price * shares)) * 100
                trade_returns.append(percent_return)
    
    if not trade_returns:
        return create_empty_chart()
    
    # Create histogram figure
    fig = go.Figure()
    
    # Add histogram
    fig.add_trace(go.Histogram(
        x=trade_returns,
        nbinsx=20,
        marker_color=['#FF6B6B' if x < 0 else '#17B897' for x in trade_returns],
        name='Trade Returns'
    ))
    
    # Add vertical line at 0%
    fig.add_vline(
        x=0, line_width=2, line_dash="dash", line_color="#ffffff", 
        annotation_text="Breakeven", annotation_position="top right"
    )
    
    # Add mean return line
    mean_return = np.mean(trade_returns)
    fig.add_vline(
        x=mean_return, line_width=2, line_dash="dot", line_color="#36A2EB", 
        annotation_text=f"Avg: {mean_return:.1f}%", annotation_position="top right"
    )
    
    # Update layout
    fig.update_layout(
        title='Trade Return Distribution',
        template=CHART_THEME,
        paper_bgcolor='#1e222d',
        plot_bgcolor='#1e222d',
        font={'color': '#ffffff'},
        xaxis={
            'title': 'Return (%)',
            'gridcolor': '#2a2e39',
            'zerolinecolor': '#2a2e39'
        },
        yaxis={
            'title': 'Number of Trades',
            'gridcolor': '#2a2e39'
        },
        bargap=0.05,
        margin={'t': 30, 'l': 40, 'r': 30, 'b': 40},
        showlegend=False,
        height=250
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})
