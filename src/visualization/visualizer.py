import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import dcc, html
import dash_bootstrap_components as dbc

from ..core.constants import CHART_THEME
from .chart_utils import create_empty_chart, create_styled_chart

class BacktestVisualizer:
    """Class for creating backtest visualization"""
    
    def __init__(self):
        """Initialize visualizer with chart theme"""
        self.chart_theme = CHART_THEME

    def create_equity_curve(self, portfolio_values: pd.Series, 
                          benchmark_values: Optional[pd.Series] = None) -> dict:
        """Create equity curve chart
        
        Args:
            portfolio_values: Portfolio value series
            benchmark_values: Benchmark value series
            
        Returns:
            Chart figure dict
        """
        if portfolio_values.empty:
            return create_empty_chart("Portfolio Performance")
            
        data = {'Portfolio': portfolio_values}
        if benchmark_values is not None and not benchmark_values.empty:
            data['Benchmark'] = benchmark_values
            
        return create_styled_chart(data, "Portfolio Performance")

    def create_drawdown_chart(self, portfolio_values: pd.Series) -> dict:
        """Create drawdown chart
        
        Args:
            portfolio_values: Portfolio value series
            
        Returns:
            Chart figure dict
        """
        if portfolio_values.empty:
            return create_empty_chart("Portfolio Drawdown")
            
        # Calculate drawdown
        rolling_max = portfolio_values.cummax()
        drawdown = (portfolio_values - rolling_max) / rolling_max * 100
        
        return create_styled_chart(
            {'Drawdown': drawdown}, 
            "Portfolio Drawdown", 
            chart_type="area"
        )

    def create_monthly_returns_heatmap(self, portfolio_values: pd.Series) -> dict:
        """Create monthly returns heatmap
        
        Args:
            portfolio_values: Portfolio value series
            
        Returns:
            Chart figure dict
        """
        if portfolio_values.empty or len(portfolio_values) < 30:
            return create_empty_chart("Monthly Returns")
            
        # Calculate monthly returns
        returns = portfolio_values.pct_change()
        returns = returns[~returns.isna()]
        
        monthly_returns = returns.groupby([
            returns.index.year.rename('Year'), 
            returns.index.month.rename('Month')
        ]).apply(lambda x: (1 + x).prod() - 1)
        
        # Create heatmap data
        years = monthly_returns.index.get_level_values('Year').unique().sort_values()
        months = list(range(1, 13))
        
        z_data = np.full((len(years), 12), np.nan)
        
        for i, year in enumerate(years):
            for j, month in enumerate(months):
                try:
                    z_data[i, j] = monthly_returns.loc[(year, month)]
                except KeyError:
                    pass
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=z_data * 100,  # Convert to percentage
            x=[f"{m}" for m in months],
            y=[str(y) for y in years],
            colorscale=[
                [0, 'rgb(165,0,38)'],
                [0.5, 'rgb(49,54,149)'],
                [1, 'rgb(0,104,55)']
            ],
            colorbar=dict(
                title=dict(text="Return %", side="top"),
                tickformat=".1f",
                exponentformat="none"
            ),
            text=np.round(z_data * 100, 1),
            hovertemplate="Year: %{y}<br>Month: %{x}<br>Return: %{z:.2f}%<extra></extra>",
        ))
        
        fig.update_layout(
            title="Monthly Returns (%)",
            template=CHART_THEME,
            paper_bgcolor='#1e222d',
            plot_bgcolor='#1e222d',
            font={'color': '#ffffff'},
            margin={'t': 50, 'l': 50, 'r': 20, 'b': 50},
            xaxis={'title': 'Month', 'gridcolor': '#2a2e39'},
            yaxis={'title': 'Year', 'gridcolor': '#2a2e39'},
        )
        
        return fig

    def create_trade_distribution(self, trades: List[Dict]) -> Union[dcc.Graph, html.Div]:
        """Create trade distribution chart
        
        Args:
            trades: List of trade dictionaries
            
        Returns:
            Dash component with trade distribution
        """
        if not trades:
            return html.Div("No trades available", className="text-center text-muted my-5")
            
        # Extract returns from trades
        returns = [t.get('return_pct', 0) for t in trades]
        
        # Create histogram
        fig = go.Figure(data=go.Histogram(
            x=returns,
            marker_color=['#FF6B6B' if r < 0 else '#17B897' for r in returns],
            opacity=0.7,
            autobinx=False,
            xbins=dict(
                start=min(-50, min(returns)),
                end=max(50, max(returns)),
                size=5
            )
        ))
        
        fig.update_layout(
            title="Trade Return Distribution",
            template=CHART_THEME,
            paper_bgcolor='#1e222d',
            plot_bgcolor='#1e222d',
            font={'color': '#ffffff'},
            margin={'t': 50, 'l': 50, 'r': 20, 'b': 50},
            xaxis={'title': 'Return (%)', 'gridcolor': '#2a2e39'},
            yaxis={'title': 'Number of Trades', 'gridcolor': '#2a2e39'},
        )
        
        return dcc.Graph(
            figure=fig,
            config={
                'displayModeBar': True,
                'responsive': True,
                'modeBarButtonsToRemove': ['lasso2d', 'select2d']
            }
        )

    def create_backtest_charts(self, portfolio_values: pd.Series, 
                             benchmark_values: Optional[pd.Series] = None,
                             trades: Optional[List[Dict]] = None) -> List[Any]:
        """Create all backtest visualization charts
        
        Args:
            portfolio_values: Portfolio value series
            benchmark_values: Benchmark value series
            trades: List of trade dictionaries
            
        Returns:
            List of chart components
        """
        charts = []
        
        # Create equity curve
        equity_curve = self.create_equity_curve(portfolio_values, benchmark_values)
        charts.append(equity_curve)
        
        # Create drawdown chart if enough data
        if len(portfolio_values) > 20:
            drawdown_chart = self.create_drawdown_chart(portfolio_values)
            charts.append(drawdown_chart)
        
        # Create monthly returns heatmap if enough data
        if len(portfolio_values) > 60:
            monthly_chart = self.create_monthly_returns_heatmap(portfolio_values)
            charts.append(monthly_chart)
            
        # Create trade distribution if trades available
        if trades and len(trades) > 0:
            trade_chart = self.create_trade_distribution(trades)
            charts.append(trade_chart)
            
        return charts
