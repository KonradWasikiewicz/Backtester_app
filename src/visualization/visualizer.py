import plotly.graph_objs as go
from .chart_utils import create_empty_chart, create_equity_curve, get_base_layout
import dash_core_components as dcc

class BacktestVisualizer:
    def __init__(self):
        self.chart_theme = {
            'paper_bgcolor': '#1e222d',
            'plot_bgcolor': '#1e222d',
            'font': {'color': '#e1e1e1'}
        }

    def create_backtest_charts(self, results):
        if results is None:
            return [create_empty_chart("No Data Available")]
        
        charts = []
        # Equity curve
        equity_chart = create_equity_curve(results)
        charts.append(dcc.Graph(
            id='equity-curve-chart',
            figure=equity_chart,
            config={'displayModeBar': True}
        ))
        
        # Add drawdown chart
        drawdown_data = (results["Portfolio_Value"] - results["Portfolio_Value"].cummax()) / results["Portfolio_Value"].cummax()
        drawdown_chart = {
            "data": [
                go.Scatter(
                    x=results.index,
                    y=drawdown_data,
                    mode="lines",
                    fill="tozeroy",
                    line=dict(color="#FF6B6B"),
                    name="Drawdown"
                )
            ],
            "layout": get_base_layout("Drawdown")
        }
        charts.append(dcc.Graph(
            id='drawdown-chart',
            figure=drawdown_chart,
            config={'displayModeBar': True}
        ))
        
        return charts
