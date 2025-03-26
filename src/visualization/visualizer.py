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
        charts = []
        
        # Portfolio value chart
        if not portfolio_values.empty:
            equity_trace = {
                'x': portfolio_values.index,
                'y': portfolio_values.values,
                'name': 'Portfolio Value',
                'type': 'scatter',
                'mode': 'lines',
                'line': {'color': '#17B897'}
            }
            charts.append(equity_trace)
        
        # Add trade markers if available
        if trades:
            for trade in trades:
                marker = {
                    'x': [trade.entry_date],
                    'y': [trade.entry_price],
                    'name': f'{trade.ticker} {trade.direction}',
                    'mode': 'markers',
                    'marker': {
                        'symbol': 'triangle-up' if trade.direction == 'LONG' else 'triangle-down',
                        'size': 10,
                        'color': '#17B897' if trade.direction == 'LONG' else '#FF6B6B'
                    }
                }
                charts.append(marker)
        
        return charts
