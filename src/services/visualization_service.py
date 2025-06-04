"""
Visualization Service Module

This service provides visualization capabilities for the backtester application.
It centralizes all chart creation and visualization functionality.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import logging
from typing import Dict, List, Optional, Union, Tuple, Any, Callable
from datetime import datetime

# Local imports
from src.visualization.chart_utils import add_shapes_to_chart, format_currency

# Set up logging
logger = logging.getLogger(__name__)

class VisualizationService:
    """
    Service for creating and managing visualizations in the backtesting application.
    
    This class provides methods for generating charts and visual representations
    of backtesting data and results.
    """
    
    def __init__(self, theme: str = 'plotly', height: int = 600):
        """
        Initialize the VisualizationService.
        
        Args:
            theme: Visual theme for charts ('plotly', 'plotly_white', 'plotly_dark', etc.)
            height: Default height for charts in pixels
        """
        self.theme = theme
        self.height = height
        self.color_map = {
            'price': '#1f77b4',  # Blue
            'buy': 'green',
            'sell': 'red',
            'profit': '#2ca02c',  # Green
            'loss': '#d62728',    # Red
            'portfolio': '#ff7f0e',  # Orange
            'benchmark': '#1f77b4'  # Blue
        }
        logger.info(f"VisualizationService initialized with theme: {theme}")
        
    def create_ohlc_chart(self, 
                        data: pd.DataFrame, 
                        ticker: str,
                        show_volume: bool = True,
                        signals_df: Optional[pd.DataFrame] = None,
                        indicators: Optional[Dict[str, Dict[str, Any]]] = None,
                        ranges: Optional[List[Dict[str, Any]]] = None) -> go.Figure:
        """
        Create an OHLC candlestick chart with optional volume, signals, and indicators.
        
        Args:
            data: DataFrame with OHLCV data
            ticker: Ticker symbol for the chart title
            show_volume: Whether to include volume subplot
            signals_df: Optional DataFrame with trading signals
            indicators: Dictionary of indicators to add to the chart
                Format: {
                    'name': {
                        'values': series_or_array,
                        'line': {'color': 'red', 'width': 1, 'dash': 'solid'},
                        'subplot': 'main'  # or 'volume' or 'new'
                    }
                }
            ranges: List of date ranges to highlight
                Format: [
                    {
                        'start': datetime,
                        'end': datetime,
                        'color': 'rgba(255,0,0,0.1)',
                        'label': 'Recession'
                    }
                ]
                
        Returns:
            Plotly Figure object
        """
        # Create figure with secondary y-axis
        fig = make_subplots(
            rows=2 if show_volume else 1, 
            cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.02, 
            row_heights=[0.8, 0.2] if show_volume else [1]
        )
        
        # Add candlestick trace
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name=ticker,
                showlegend=False
            ),
            row=1, col=1
        )
        
        # Add volume trace
        if show_volume and 'Volume' in data.columns:
            colors = ['red' if data.loc[i, 'Close'] < data.loc[i, 'Open'] 
                     else 'green' for i in data.index]
            
            fig.add_trace(
                go.Bar(
                    x=data.index,
                    y=data['Volume'],
                    name='Volume',
                    marker_color=colors,
                    opacity=0.5,
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # Add signals if provided
        if signals_df is not None and not signals_df.empty:
            # Add buy signals
            buy_signals = signals_df[signals_df['Signal'] > 0]
            if not buy_signals.empty:
                fig.add_trace(
                    go.Scatter(
                        x=buy_signals.index,
                        y=buy_signals['Close'] * 0.98,  # Offset slightly for visibility
                        mode='markers',
                        marker=dict(
                            symbol='triangle-up',
                            size=10,
                            color=self.color_map['buy'],
                            line=dict(width=1, color='darkgreen')
                        ),
                        name='Buy Signal',
                        hoverinfo='text',
                        hovertext=[f"Buy: {index.strftime('%Y-%m-%d')}, Price: {price:.2f}" 
                                 for index, price in zip(buy_signals.index, buy_signals['Close'])],
                    ),
                    row=1, col=1
                )
            
            # Add sell signals
            sell_signals = signals_df[signals_df['Signal'] < 0]
            if not sell_signals.empty:
                fig.add_trace(
                    go.Scatter(
                        x=sell_signals.index,
                        y=sell_signals['Close'] * 1.02,  # Offset slightly for visibility
                        mode='markers',
                        marker=dict(
                            symbol='triangle-down',
                            size=10,
                            color=self.color_map['sell'],
                            line=dict(width=1, color='darkred')
                        ),
                        name='Sell Signal',
                        hoverinfo='text',
                        hovertext=[f"Sell: {index.strftime('%Y-%m-%d')}, Price: {price:.2f}" 
                                for index, price in zip(sell_signals.index, sell_signals['Close'])],
                    ),
                    row=1, col=1
                )
        
        # Add indicators if provided
        if indicators:
            for name, props in indicators.items():
                values = props.get('values', None)
                if values is None:
                    continue
                    
                line = props.get('line', {'color': 'blue'})
                subplot = props.get('subplot', 'main')
                
                row = 1 if subplot in ('main', 'new') else 2
                
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=values,
                        mode='lines',
                        name=name,
                        line=line
                    ),
                    row=row, col=1
                )
        
        # Add shapes for date ranges if provided
        if ranges:
            for range_dict in ranges:
                start = range_dict.get('start')
                end = range_dict.get('end')
                color = range_dict.get('color', 'rgba(255,0,0,0.1)')
                label = range_dict.get('label', '')
                
                if start and end:
                    fig.add_shape(
                        type="rect",
                        x0=start,
                        y0=0,
                        x1=end,
                        y1=1,
                        xref="x",
                        yref="paper",
                        fillcolor=color,
                        opacity=0.5,
                        layer="below",
                        line_width=0,
                    )
                    
                    # Add annotation for the range
                    if label:
                        fig.add_annotation(
                            x=start,
                            y=1,
                            xref="x",
                            yref="paper",
                            text=label,
                            showarrow=False,
                            xanchor="left",
                            yanchor="top",
                            bgcolor="rgba(255, 255, 255, 0.7)"
                        )
        
        # Update layout
        fig.update_layout(
            title=f"{ticker} Price Chart",
            xaxis_title="Date",
            yaxis_title="Price",
            height=self.height,
            xaxis_rangeslider_visible=False,
            template=self.theme,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=50, r=50, b=100, t=80, pad=4)
        )
        
        # Update y-axis labels
        fig.update_yaxes(title_text="Price", row=1, col=1)
        if show_volume:
            fig.update_yaxes(title_text="Volume", row=2, col=1)
        
        return fig
    
    def create_performance_chart(self, 
                               backtest_result: Dict[str, Any], 
                               benchmark_data: Optional[pd.DataFrame] = None) -> go.Figure:
        """
        Create a performance chart comparing strategy returns to a benchmark.
        """
        portfolio_values = backtest_result.get('portfolio_values')
        if portfolio_values is None:
            logger.error("No portfolio values available for performance chart (None found)")
            return go.Figure()
        if not isinstance(portfolio_values, pd.Series):
            portfolio_values = pd.Series(portfolio_values)
        if portfolio_values.empty:
            logger.error("No portfolio values available for performance chart (empty series)")
            return go.Figure()
            
        fig = go.Figure()
        
        portfolio_pct_change = portfolio_values.pct_change().fillna(0)
        if portfolio_pct_change.empty or portfolio_pct_change.isnull().all():
            portfolio_norm = pd.Series([100.0] * len(portfolio_values), index=portfolio_values.index)
        else:
            portfolio_norm = 100.0 * (1 + portfolio_pct_change.cumsum())
        
        if not portfolio_norm.empty and pd.isna(portfolio_norm.iloc[0]):
            portfolio_norm.iloc[0] = 100.0

        fig.add_trace(
            go.Scatter(
                x=portfolio_values.index,
                y=portfolio_norm,
                mode='lines',
                name='Portfolio', # Changed name
                line=dict(color=self.color_map.get('portfolio', '#ff7f0e'), width=2)
            )
        )
        
        if benchmark_data is not None and not benchmark_data.empty and 'Close' in benchmark_data.columns:
            benchmark = benchmark_data.reindex(portfolio_values.index, method='ffill')
            benchmark_returns = benchmark['Close'].pct_change().fillna(0)
            if benchmark_returns.empty or benchmark_returns.isnull().all():
                benchmark_norm = pd.Series([100.0] * len(benchmark), index=benchmark.index)
            else:
                benchmark_norm = 100.0 * (1 + benchmark_returns.cumsum())

            if not benchmark_norm.empty and pd.isna(benchmark_norm.iloc[0]):
                 benchmark_norm.iloc[0] = 100.0
            
            fig.add_trace(
                go.Scatter(
                    x=benchmark_norm.index,
                    y=benchmark_norm.values,
                    mode='lines',
                    name='Benchmark',
                    line=dict(color=self.color_map.get('benchmark', '#1f77b4'), width=2, dash='dash')
                )
            )
        
        drawdown = backtest_result.get('drawdown')
        if drawdown is not None:
            if not isinstance(drawdown, pd.Series):
                drawdown = pd.Series(drawdown)
            if not drawdown.empty:
                fig.add_trace(
                    go.Scatter(
                        x=drawdown.index,
                        y=-drawdown * 100,
                        mode='lines',
                        name='Drawdown', 
                        line=dict(color='purple', width=1.5),
                        yaxis="y2",
                        visible='legendonly' # Hidden on chart, shown in legend
                    )
                )
        
        fig.update_layout(
            height=self.height,
            template=self.theme,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left", # Align legend to left
                x=0
            ),
            margin=dict(l=50, r=20, b=20, t=5, pad=4), # Minimal top margin
            yaxis=dict(
                title_text=None, # Remove y-axis title
                side="left",
                showgrid=True
            ),
            yaxis2=dict(
                title_text=None, # Remove y-axis title for drawdown
                side="right",
                overlaying="y",
                showgrid=False,
                visible=False # Hide secondary y-axis if drawdown trace is legendonly
            ),
            xaxis=dict(
                title_text=None, # Remove x-axis title
                showticklabels=True
            ) 
        )
        return fig
    
    def create_drawdown_only_chart(self, backtest_result: Dict[str, Any]) -> go.Figure:
        """
        Create a chart showing only the drawdown.
        Args:
            backtest_result: Dictionary containing backtest results
                Must include 'drawdown' Series with DatetimeIndex
        Returns:
            Plotly Figure object
        """
        drawdown = backtest_result.get('drawdown')
        if drawdown is None:
            logger.warning("No drawdown data available for drawdown chart (None found)")
            return go.Figure() 

        if not isinstance(drawdown, pd.Series):
            drawdown = pd.Series(drawdown)

        if drawdown.empty:
            logger.warning("No drawdown data available for drawdown chart (empty series)")
            return go.Figure()

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=drawdown.index,
                y=-drawdown * 100,  # Convert to negative percentage
                mode='lines',
                name='Drawdown', # Legend name
                fill='tozeroy', 
                line=dict(color=self.color_map.get('loss', '#d62728'), width=1.5), # Use loss color
            )
        )
        
        # Placeholder for benchmark drawdown if it becomes available
        # benchmark_drawdown = backtest_result.get('benchmark_drawdown')
        # if benchmark_drawdown is not None and not benchmark_drawdown.empty:
        #     if not isinstance(benchmark_drawdown, pd.Series):
        #         benchmark_drawdown = pd.Series(benchmark_drawdown)
        #     fig.add_trace(go.Scatter(... name='Benchmark Drawdown' ...))


        fig.update_layout(
            height=self.height, 
            template=self.theme,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left", # Align legend to left
                x=0
            ),
            margin=dict(l=50, r=20, b=20, t=5, pad=4), # Minimal top margin
            yaxis=dict(
                title_text=None, 
                ticksuffix="%",   # Add % suffix to tick labels
                showgrid=True,
                zeroline=True, 
                zerolinecolor='rgba(128,128,128,0.5)' # Gray zeroline
            ),
            xaxis=dict(
                title_text=None, 
                showticklabels=True
            )
        )
        return fig

    def create_returns_distribution_chart(self, 
                                       backtest_result: Dict[str, Any], 
                                       benchmark_returns: Optional[pd.Series] = None) -> go.Figure:
        """
        Create a distribution chart of daily returns.
        
        Args:
            backtest_result: Dictionary containing backtest results
                Must include 'returns' Series
            benchmark_returns: Optional Series with benchmark returns
            
        Returns:
            Plotly Figure object
        """
        returns = backtest_result.get('returns')
        
        if returns is None or returns.empty:
            logger.error("No returns data available for distribution chart")
            return go.Figure()
        
        # Create figure
        fig = go.Figure()
        
        # Add strategy returns histogram
        fig.add_trace(
            go.Histogram(
                x=returns * 100,  # Convert to percentage
                name='Strategy Returns',
                opacity=0.7,
                marker_color=self.color_map['portfolio'],
                histnorm='probability density',
                nbinsx=50
            )
        )
        
        # Add normal distribution curve
        x = np.linspace(min(returns) * 100, max(returns) * 100, 100)
        mu = (returns * 100).mean()
        sigma = (returns * 100).std()
        y = 1/(sigma * np.sqrt(2 * np.pi)) * np.exp(-(x - mu)**2 / (2 * sigma**2))
        
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode='lines',
                name='Normal Distribution',
                line=dict(color='black', width=2, dash='dash')
            )
        )
        
        # Add benchmark returns if provided
        if benchmark_returns is not None and not benchmark_returns.empty:
            fig.add_trace(
                go.Histogram(
                    x=benchmark_returns * 100,  # Convert to percentage
                    name='Benchmark Returns',
                    opacity=0.7,
                    marker_color=self.color_map['benchmark'],
                    histnorm='probability density',
                    nbinsx=50
                )
            )
            
            # Add benchmark normal distribution
            x_bench = np.linspace(min(benchmark_returns) * 100, max(benchmark_returns) * 100, 100)
            mu_bench = (benchmark_returns * 100).mean()
            sigma_bench = (benchmark_returns * 100).std()
            y_bench = 1/(sigma_bench * np.sqrt(2 * np.pi)) * np.exp(-(x_bench - mu_bench)**2 / (2 * sigma_bench**2))
            
            fig.add_trace(
                go.Scatter(
                    x=x_bench,
                    y=y_bench,
                    mode='lines',
                    name='Benchmark Normal',
                    line=dict(color='gray', width=2, dash='dash')
                )
            )
        
        # Update layout
        fig.update_layout(
            title="Daily Returns Distribution",
            xaxis_title="Daily Return (%)",
            yaxis_title="Probability Density",
            height=self.height,
            template=self.theme,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=50, r=50, b=50, t=80, pad=4),
            bargap=0.1
        )
        
        # Add vertical line at zero
        fig.add_shape(
            type="line",
            x0=0, y0=0,
            x1=0, y1=1,
            yref="paper",
            line=dict(color="black", width=1, dash="dash")
        )
        
        return fig
    
    def create_metrics_table(self, 
                          metrics: Dict[str, Any], 
                          benchmark_metrics: Optional[Dict[str, Any]] = None) -> go.Figure:
        """
        Create a table visualization of performance metrics.
        
        Args:
            metrics: Dictionary of strategy performance metrics
            benchmark_metrics: Optional dictionary of benchmark metrics for comparison
            
        Returns:
            Plotly Figure object with a table
        """
        # Define the metrics to include and their display names
        metric_mapping = {
            'total_return': 'Total Return (%)',
            'annualized_return': 'Annual Return (%)',
            'annualized_volatility': 'Annual Volatility (%)',
            'sharpe_ratio': 'Sharpe Ratio',
            'sortino_ratio': 'Sortino Ratio',
            'max_drawdown': 'Max Drawdown (%)',
            'win_rate': 'Win Rate (%)',
            'profit_factor': 'Profit Factor',
            'avg_profit_per_trade': 'Avg Profit/Trade (%)',
            'avg_trade_duration': 'Avg Trade Duration (days)'
        }
        
        # Prepare table data
        headers = ['Metric', 'Strategy']
        if benchmark_metrics:
            headers.append('Benchmark')
            headers.append('Difference')
        
        table_data = [headers]
        
        for metric_key, metric_name in metric_mapping.items():
            if metric_key not in metrics:
                continue
                
            row = [metric_name]
            
            # Format the value based on the metric
            value = metrics[metric_key]
            if 'return' in metric_key or 'drawdown' in metric_key or 'volatility' in metric_key or 'rate' in metric_key:
                formatted_value = f"{value * 100:.2f}%" if isinstance(value, (int, float)) else str(value)
            elif 'ratio' in metric_key or 'factor' in metric_key:
                formatted_value = f"{value:.2f}" if isinstance(value, (int, float)) else str(value)
            else:
                formatted_value = str(value)
                
            row.append(formatted_value)
            
            # Add benchmark and difference if provided
            if benchmark_metrics and metric_key in benchmark_metrics:
                benchmark_value = benchmark_metrics[metric_key]
                
                # Format benchmark value
                if 'return' in metric_key or 'drawdown' in metric_key or 'volatility' in metric_key or 'rate' in metric_key:
                    benchmark_formatted = f"{benchmark_value * 100:.2f}%" if isinstance(benchmark_value, (int, float)) else str(benchmark_value)
                elif 'ratio' in metric_key or 'factor' in metric_key:
                    benchmark_formatted = f"{benchmark_value:.2f}" if isinstance(benchmark_value, (int, float)) else str(benchmark_value)
                else:
                    benchmark_formatted = str(benchmark_value)
                    
                row.append(benchmark_formatted)
                
                # Calculate and format difference
                if isinstance(value, (int, float)) and isinstance(benchmark_value, (int, float)):
                    diff = value - benchmark_value
                    
                    if 'return' in metric_key or 'drawdown' in metric_key or 'volatility' in metric_key or 'rate' in metric_key:
                        diff_formatted = f"{diff * 100:+.2f}%" 
                    elif 'ratio' in metric_key or 'factor' in metric_key:
                        diff_formatted = f"{diff:+.2f}"
                    else:
                        diff_formatted = f"{diff:+}"
                        
                    row.append(diff_formatted)
                else:
                    row.append("N/A")
            
            table_data.append(row)
        
        # Create table figure
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=headers,
                fill_color='lightgrey',
                align='left',
                font=dict(size=14)
            ),
            cells=dict(
                values=[list(x) for x in zip(*table_data[1:])],  # Transpose the data
                fill_color=[['white', 'white'] + (['lightgreen' if '+' in x[3] else 'lightcoral' 
                                                for x in table_data[1:]]) if benchmark_metrics else ['white']],
                align='left',
                font=dict(size=12)
            )
        )])
        
        # Update layout
        fig.update_layout(
            title="Performance Metrics",
            height=min(400, 50 + 30 * len(table_data)),
            margin=dict(l=10, r=10, b=10, t=40, pad=5)
        )
        
        return fig
    
    def create_trades_chart(self, trades_df: pd.DataFrame, price_data: pd.DataFrame) -> go.Figure:
        """
        Create a visualization of individual trades.
        
        Args:
            trades_df: DataFrame with trade information
            price_data: DataFrame with price history
            
        Returns:
            Plotly Figure object
        """
        if trades_df is None or trades_df.empty:
            logger.error("No trades data available for trades chart")
            return go.Figure()
            
        # Create figure
        fig = go.Figure()
        
        # Add price line
        fig.add_trace(
            go.Scatter(
                x=price_data.index,
                y=price_data['Close'],
                mode='lines',
                name='Price',
                line=dict(color=self.color_map['price'], width=1),
                hoverinfo='none'
            )
        )
        
        # Add each trade as a shape
        for _, trade in trades_df.iterrows():
            # Skip trades without entry or exit points
            if pd.isna(trade.get('entry_date')) or pd.isna(trade.get('exit_date')):
                continue
                
            entry_date = pd.to_datetime(trade['entry_date'])
            exit_date = pd.to_datetime(trade['exit_date'])
            entry_price = trade['entry_price']
            exit_price = trade['exit_price']
            profit = trade.get('profit', exit_price - entry_price)
            
            color = self.color_map['profit'] if profit > 0 else self.color_map['loss']
            
            # Add trade shape
            fig.add_shape(
                type="rect",
                x0=entry_date,
                y0=min(entry_price, exit_price) * 0.998,
                x1=exit_date,
                y1=max(entry_price, exit_price) * 1.002,
                line=dict(color=color, width=1),
                fillcolor=color,
                opacity=0.2,
                layer="below"
            )
            
            # Add entry point
            fig.add_trace(
                go.Scatter(
                    x=[entry_date],
                    y=[entry_price],
                    mode='markers',
                    marker=dict(
                        symbol='circle',
                        size=8,
                        color=color,
                        line=dict(width=1, color=color)
                    ),
                    name=f'Entry: {entry_date.strftime("%Y-%m-%d")}',
                    hoverinfo='text',
                    hovertext=f"Entry: {entry_date.strftime('%Y-%m-%d')}<br>Price: {entry_price:.2f}",
                    showlegend=False
                )
            )
            
            # Add exit point
            fig.add_trace(
                go.Scatter(
                    x=[exit_date],
                    y=[exit_price],
                    mode='markers',
                    marker=dict(
                        symbol='circle',
                        size=8,
                        color=color,
                        line=dict(width=1, color=color)
                    ),
                    name=f'Exit: {exit_date.strftime("%Y-%m-%d")}',
                    hoverinfo='text',
                    hovertext=f"Exit: {exit_date.strftime('%Y-%m-%d')}<br>Price: {exit_price:.2f}<br>Profit: {profit:.2f} ({100*profit/entry_price:.2f}%)",
                    showlegend=False
                )
            )
        
        # Update layout
        fig.update_layout(
            title="Trade History Visualization",
            xaxis_title="Date",
            yaxis_title="Price",
            height=self.height,
            template=self.theme,
            showlegend=False,
            margin=dict(l=50, r=50, b=50, t=80, pad=4)
        )
        
        return fig
    
    def create_correlation_heatmap(self, returns_data: pd.DataFrame) -> go.Figure:
        """
        Create a correlation heatmap of asset returns.
        
        Args:
            returns_data: DataFrame with returns for multiple assets
            
        Returns:
            Plotly Figure object
        """
        if returns_data is None or returns_data.empty:
            logger.error("No returns data available for correlation heatmap")
            return go.Figure()
            
        # Calculate correlation matrix
        corr_matrix = returns_data.corr()
        
        # Create heatmap
        fig = px.imshow(
            corr_matrix,
            text_auto='.2f',
            aspect="auto",
            color_continuous_scale='RdBu_r',
            zmin=-1,
            zmax=1
        )
        
        # Update layout
        fig.update_layout(
            title="Asset Correlation Heatmap",
            height=max(400, 300 + 20 * len(corr_matrix)),
            template=self.theme,
            margin=dict(l=50, r=50, b=50, t=80, pad=4)
        )
        
        return fig
        
    def set_theme(self, theme: str) -> None:
        """
        Change the visual theme for charts.
        
        Args:
            theme: Name of the plotly theme to use
        """
        self.theme = theme
        logger.info(f"Changed visualization theme to {theme}")
        
    def set_color_map(self, color_map: Dict[str, str]) -> None:
        """
        Update the color mapping for chart elements.
        
        Args:
            color_map: Dictionary mapping element names to color values
        """
        self.color_map.update(color_map)
        logger.info(f"Updated color map with {len(color_map)} elements")
        
    def create_monthly_returns_heatmap(self, portfolio_series):
        """
        Create a heatmap of monthly returns from a portfolio value series.
        """
        import calendar
        # Calculate end-of-month portfolio values and monthly returns
        try:
            monthly_vals = portfolio_series.resample('ME').last()
        except ValueError:
            logger.warning("'ME' offset unsupported - falling back to 'M'")
            monthly_vals = portfolio_series.resample('M').last()
        monthly_ret = monthly_vals.pct_change().dropna()
        # Prepare pivot table
        df = monthly_ret.to_frame(name='Return')
        df['Year'] = df.index.year
        df['Month'] = df.index.month
        pivot = df.pivot(index='Year', columns='Month', values='Return').fillna(0)
        # Map month numbers to names
        month_names = [calendar.month_abbr[m] for m in pivot.columns]
        # Plot heatmap
        fig = px.imshow(
            pivot.values,
            x=month_names,
            y=pivot.index,
            color_continuous_scale='RdYlGn', # Red-Yellow-Green scale
            labels={'x':'Month','y':'Year','color':'Return'},
            aspect='auto',
            title='Monthly Returns Heatmap',
            text_auto='.2%' # Format text as percentage
        )
        # Update layout for dark theme and better appearance
        fig.update_layout(
            height=self.height, 
            template=self.theme, # Use the service's theme (e.g., 'plotly_dark')
            plot_bgcolor='rgba(0,0,0,0)', # Transparent plot background
            paper_bgcolor='rgba(0,0,0,0)', # Transparent paper background
            margin=dict(l=50, r=50, b=50, t=80),
            xaxis_nticks=12, # Ensure all months are shown
            yaxis_nticks=len(pivot.index) # Ensure all years are shown
        )
        # Ensure text color contrasts with the heatmap colors
        # Use white text for better contrast on dark theme
        fig.update_layout(
            font=dict(color='white') # Set default font color for the whole chart
        )
        fig.update_traces(textfont_color='black') # Keep cell text black for RdYlGn contrast
        return fig

    def prepare_trades_for_table(self, trades):
        """
        Format trade records for display in a table.
        """
        formatted = []
        for t in trades:
            # Format dates
            entry = t.get('entry_date')
            exit = t.get('exit_date')
            entry_str = entry.strftime('%Y-%m-%d') if hasattr(entry, 'strftime') else str(entry)
            exit_str = exit.strftime('%Y-%m-%d') if hasattr(exit, 'strftime') else str(exit)
            # Format PnL
            pnl = t.get('pnl', 0)
            pnl_str = f"${pnl:.2f}"
            pnl_pct = t.get('pnl_pct', 0)
            pct_str = f"{pnl_pct:.2f}%"
            formatted.append({
                'Ticker': t.get('ticker'),
                'Entry': entry_str,
                'Exit': exit_str,
                'PnL': pnl_str,
                'PnL_pct': pct_str,
                'Reason': t.get('exit_reason', '')
            })
        return formatted

# end of class