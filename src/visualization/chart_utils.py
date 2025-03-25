import plotly.graph_objects as go
import pandas as pd
from ..core.constants import CHART_THEME

def get_base_layout(title: str = "", x_title: str = "", y_title: str = "") -> dict:
    """Returns base chart layout with theme applied"""
    return {
        'title': title,
        'xaxis_title': x_title,
        'yaxis_title': y_title,
        'paper_bgcolor': CHART_THEME['paper_bgcolor'],
        'plot_bgcolor': CHART_THEME['plot_bgcolor'],
        'font': {'color': CHART_THEME['font_color']},
        'xgrid': {'color': CHART_THEME['grid_color']},
        'ygrid': {'color': CHART_THEME['grid_color']},
    }

def create_empty_chart() -> go.Figure:
    """Creates an empty figure with base theme"""
    fig = go.Figure()
    fig.update_layout(get_base_layout())
    return fig

def create_equity_curve(equity_data: pd.Series) -> go.Figure:
    """Creates equity curve chart"""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=equity_data.index,
            y=equity_data.values,
            mode='lines',
            name='Equity Curve'
        )
    )
    
    fig.update_layout(
        get_base_layout(
            title="Portfolio Equity Curve",
            x_title="Date",
            y_title="Portfolio Value"
        )
    )
    
    return fig
