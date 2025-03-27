import pandas as pd
from typing import Dict, List
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .chart_utils import create_empty_chart, create_equity_curve, get_base_layout
from dash import dcc

class BacktestVisualizer:
    def __init__(self):
        self.chart_theme = {
            'paper_bgcolor': '#1e222d',
            'plot_bgcolor': '#1e222d',
            'font_color': '#e1e1e1',
            'grid_color': '#2a2e39'
        }

    def create_backtest_charts(self, trades, portfolio_values, signals):
        """Create all backtest visualization charts"""
        if portfolio_values.empty:
            return []
            
        charts = []
        
        # Portfolio value chart
        portfolio_trace = {
            'data': [{
                'x': portfolio_values.index,
                'y': portfolio_values.values,
                'name': 'Portfolio Value',
                'type': 'scatter',
                'mode': 'lines',
                'line': {'color': '#17B897'}
            }],
            'layout': {
                'title': 'Portfolio Value',
                'xaxis': {'title': 'Date'},
                'yaxis': {'title': 'Value ($)'}
            }
        }
        charts.append(portfolio_trace)
        
        return charts
