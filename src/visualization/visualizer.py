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

    def create_backtest_charts(self, 
                             signals: Dict[str, pd.DataFrame], 
                             trades: List[Dict],
                             portfolio_values: pd.Series) -> go.Figure:
        """Create interactive backtest visualization charts"""
        
        fig = make_subplots(rows=2, cols=1,
                           shared_xaxes=True,
                           vertical_spacing=0.05,
                           row_heights=[0.7, 0.3])

        # Price and signals chart
        for ticker, df in signals.items():
            fig.add_trace(
                go.Scatter(x=df.index, y=df['Close'],
                          name=f"{ticker} Price",
                          line=dict(color='#2962ff')),
                row=1, col=1
            )

            # Add buy/sell points
            buys = df[df['Signal'] == 1]
            sells = df[df['Signal'] == -1]
            
            fig.add_trace(
                go.Scatter(x=buys.index, y=buys['Close'],
                          mode='markers',
                          name='Buy Signal',
                          marker=dict(color='#00c853', size=8)),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(x=sells.index, y=sells['Close'],
                          mode='markers', 
                          name='Sell Signal',
                          marker=dict(color='#ff1744', size=8)),
                row=1, col=1
            )

        # Portfolio value chart
        fig.add_trace(
            go.Scatter(x=portfolio_values.index,
                      y=portfolio_values.values,
                      name='Portfolio Value',
                      line=dict(color='#00c853')),
            row=2, col=1
        )

        fig.update_layout(
            title='Backtest Results',
            height=800,
            **self.chart_theme
        )

        return fig
