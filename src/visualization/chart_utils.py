from dash import dcc
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, Optional, Union, List
import numpy as np
import plotly.express as px
from src.core.constants import CHART_THEME
from src.analysis.metrics import get_trade_bins_dynamic

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

def create_trade_histogram_figure(trades: List[Dict], stats: Dict) -> dcc.Graph:
    """Create trade distribution histogram with comprehensive error handling"""
    if not trades:
        return create_empty_chart("Trade Distribution")
    
    # Calculate trade returns with error handling
    returns = []
    for trade in trades:
        try:
            entry_price = float(trade['entry_price'])
            exit_price = float(trade['exit_price'])
            
            # Skip trades with invalid prices
            if entry_price <= 0 or pd.isna(entry_price) or pd.isna(exit_price):
                continue
                
            returns.append((exit_price - entry_price) / entry_price * 100)
        except (KeyError, ValueError, TypeError, ZeroDivisionError) as e:
            print(f"Error processing trade return: {e}")
            continue
    
    if not returns:
        return create_empty_chart("Trade Distribution")
    
    # Get dynamic bins
    bins, outliers_low, outliers_high = get_trade_bins_dynamic(returns)
    
    # Create histogram figure
    figure = {
        'data': [
            # Main histogram
            {
                'x': returns,
                'type': 'histogram',
                'autobinx': False,
                'xbins': {
                    'start': bins[0],
                    'end': bins[-1],
                    'size': 5
                },
                'marker': {
                    'color': ['#FF6B6B' if x < 0 else '#17B897' for x in bins[:-1]],
                },
                'opacity': 0.75,
                'name': 'Trades'
            }
        ],
        'layout': {
            'title': 'Trade Return Distribution',
            'template': CHART_THEME,
            'paper_bgcolor': '#1e222d',
            'plot_bgcolor': '#1e222d',
            'font': {'color': '#ffffff', 'family': 'system-ui'},
            'xaxis': {
                'title': 'Return (%)',
                'gridcolor': '#2a2e39',
                'range': [bins[0], bins[-1]],
                'zeroline': True,
                'zerolinecolor': '#4d5666',
                'zerolinewidth': 1.5
            },
            'yaxis': {
                'title': 'Number of Trades',
                'gridcolor': '#2a2e39'
            },
            'bargap': 0.1,
            'margin': {'t': 50, 'l': 50, 'r': 20, 'b': 50},
            'showlegend': False,
            'height': 350,
            'annotations': [
                # Add statistics for outliers if they exist
                *([{
                    'x': bins[0],
                    'y': max([h['y'] for h in figure['data'][0]['histfunc']]) * 0.9 if 'histfunc' in figure['data'][0] else 5,
                    'text': f"{len(outliers_low)} trades < {bins[0]}%",
                    'showarrow': True,
                    'arrowhead': 2,
                    'arrowcolor': '#FF6B6B',
                    'font': {'color': '#FF6B6B'}
                }] if outliers_low else []),
                *([{
                    'x': bins[-1],
                    'y': max([h['y'] for h in figure['data'][0]['histfunc']]) * 0.9 if 'histfunc' in figure['data'][0] else 5,
                    'text': f"{len(outliers_high)} trades > {bins[-1]}%",
                    'showarrow': True,
                    'arrowhead': 2,
                    'arrowcolor': '#17B897',
                    'font': {'color': '#17B897'}
                }] if outliers_high else [])
            ]
        }
    }
    
    return dcc.Graph(
        id='trade-distribution',
        figure=figure,
        config={
            'displayModeBar': True,
            'responsive': True,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'Trade_Distribution',
                'height': 500,
                'width': 700,
                'scale': 2
            }
        },
        style={'width': '100%', 'height': '100%'}
    )
