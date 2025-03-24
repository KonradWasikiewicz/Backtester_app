import plotly.graph_objs as go
from .chart_utils import create_empty_chart, create_equity_curve, get_base_layout
from dash import dcc

class BacktestVisualizer:
    def __init__(self):
        self.chart_theme = {
            'paper_bgcolor': '#1e222d',
            'plot_bgcolor': '#1e222d',
            'font': {'color': '#e1e1e1'}
        }

    def create_backtest_charts(self, results):
        if results is None:
            return []
        
        charts = []
        # Equity curve
        charts.append(dcc.Graph(
            id='equity-curve-chart',
            figure=create_equity_curve(results)
        ))
        
        # Add drawdown chart with updated layout
        drawdown_data = (results["Portfolio_Value"] - results["Portfolio_Value"].cummax()) / results["Portfolio_Value"].cummax()
        drawdown_fig = go.Figure(
            data=[go.Scatter(
                x=results.index,
                y=drawdown_data,
                mode="lines",
                fill="tozeroy",
                line=dict(color="#FF6B6B"),
                name="Drawdown"
            )],
            layout=get_base_layout("Drawdown Analysis")
        )
        
        charts.append(dcc.Graph(
            id='drawdown-chart',
            figure=drawdown_fig,
            style={'height': '300px'}  # Adjust height for grid layout
        ))
        
        return charts
