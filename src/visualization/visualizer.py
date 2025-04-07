import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any, Tuple
import plotly.graph_objects as go
import plotly.express as px
from dash import dcc, html
import logging

logger = logging.getLogger(__name__)

# Importuj funkcje pomocnicze do tworzenia wykresów
try:
    from .chart_utils import (
        create_empty_chart,
        create_styled_chart,
        create_trade_histogram_figure,
        create_allocation_chart,
        _create_base_layout # Importuj funkcję do tworzenia podstawowego layoutu
    )
except ImportError as e:
    logger.error(f"Failed to import chart utilities in Visualizer: {e}")
    # Definiuj puste funkcje jako fallback, aby uniknąć błędów atrybutów
    def create_empty_chart(*args, **kwargs): return html.Div("Chart Utils Error")
    def create_styled_chart(*args, **kwargs): return html.Div("Chart Utils Error")
    def create_trade_histogram_figure(*args, **kwargs): return html.Div("Chart Utils Error")
    def create_allocation_chart(*args, **kwargs): return html.Div("Chart Utils Error")
    def _create_base_layout(*args, **kwargs): return {}


class BacktestVisualizer:
    """
    Class responsible for generating Dash components (graphs and tables)
    for visualizing backtest results. Uses utility functions from chart_utils.
    """

    def __init__(self):
        """Initializes the visualizer."""
        # Inicjalizacja może zawierać np. ustawienia domyślne, jeśli są potrzebne
        logger.info("BacktestVisualizer initialized.")
        
        # Import visualization config for consistent colors/styles
        try:
            from src.core.config import VISUALIZATION_CONFIG as VIZ_CFG
            self.viz_cfg = VIZ_CFG
        except ImportError:
            logger.warning("Could not import VISUALIZATION_CONFIG. Using fallback colors.")
            # Basic fallback settings for colors
            self.viz_cfg = {
                "colors": {
                    "portfolio": "#17B897", "benchmark": "#FF6B6B", "profit": "#28a745",
                    "loss": "#dc3545", "primary": "#0d6efd", "secondary": "#6c757d",
                    "background": "#131722", "card_background": "#1e222d",
                    "grid_color": "#2a2e39", "text_color": "#dee2e6", "text_muted": "#6c757d"
                }
            }


    def create_equity_curve_component(self,
                                      portfolio_values: Optional[pd.Series],
                                      benchmark_values: Optional[pd.Series] = None,
                                      title: str = "Portfolio Performance",
                                      height: int = 400) -> dcc.Graph:
        """
        Creates a Dash Graph component for the equity curve.

        Args:
            portfolio_values (Optional[pd.Series]): Time series of portfolio values.
            benchmark_values (Optional[pd.Series]): Time series of benchmark values (aligned).
            title (str): Chart title.
            height (int): Chart height.

        Returns:
            dcc.Graph: Dash component containing the equity curve chart or an empty chart.
        """
        figure_data = {}
        if portfolio_values is not None and not portfolio_values.empty:
            figure_data['Portfolio'] = portfolio_values
        if benchmark_values is not None and not benchmark_values.empty:
            # Upewnij się, że benchmark ma nazwę dla legendy
            benchmark_values.name = benchmark_values.name or "Benchmark"
            figure_data[benchmark_values.name] = benchmark_values

        # Użyj funkcji z chart_utils do stworzenia wykresu
        # Ta funkcja zwraca dcc.Graph
        return create_styled_chart(
            figure_data=figure_data,
            layout_title=title,
            yaxis_title="Portfolio Value",
            yaxis_format="$", # Formatowanie osi Y jako waluta
            height=height
        )


    def create_trade_distribution_component(self,
                                            trades: Optional[List[Dict]],
                                            height: int = 250) -> Union[dcc.Graph, html.Div]:
        """
        Creates a Dash component for the trade P&L distribution histogram.

        Args:
            trades (Optional[List[Dict]]): List of completed trade dictionaries.
            height (int): Chart height.

        Returns:
            Union[dcc.Graph, html.Div]: Dash component with the histogram or a message.
        """
        if not trades:
            return create_empty_chart("Trade P/L Distribution - No Trades", height=height)

        # Użyj funkcji z chart_utils, która zwraca go.Figure lub html.Div
        fig_or_div = create_trade_histogram_figure(trades, {}) # Drugi argument (stats) nie jest używany w tej wersji

        if isinstance(fig_or_div, go.Figure):
            # Ustaw wysokość figury przed opakowaniem w dcc.Graph
            fig_or_div.update_layout(height=height)
            return dcc.Graph(figure=fig_or_div, config={'displayModeBar': False})
        elif isinstance(fig_or_div, html.Div):
            # Zwróć komunikat błędu/ostrzeżenia z chart_utils
            return fig_or_div
        else:
            logger.error("create_trade_histogram_figure returned unexpected type.")
            return create_empty_chart("Error Generating Histogram", height=height)


    def create_allocation_component(self,
                                    results: Optional[Dict],
                                    height: int = 300) -> Union[dcc.Graph, html.Div]:
        """
        Creates a Dash component for the portfolio allocation chart.

        Args:
            results (Optional[Dict]): Dictionary containing backtest results,
                                      expected to have 'Portfolio_Value' and 'trades'.
            height (int): Chart height.

        Returns:
            Union[dcc.Graph, html.Div]: Dash component with the allocation chart or a message.
        """
        if not results:
            return create_empty_chart("Portfolio Allocation - No Results", height=height)

        # Użyj funkcji z chart_utils, która zwraca dcc.Graph lub html.Div
        # Ta funkcja już opakowuje w dcc.Graph, jeśli się uda
        allocation_component = create_allocation_chart(results)

        # Możemy dostosować wysokość, jeśli komponent to dcc.Graph
        if isinstance(allocation_component, dcc.Graph):
             allocation_component.figure.update_layout(height=height)
             return allocation_component
        elif isinstance(allocation_component, html.Div):
             # Zwróć komunikat
             return allocation_component
        else:
             logger.error("create_allocation_chart returned unexpected type.")
             return create_empty_chart("Error Generating Allocation Chart", height=height)


    def create_equity_curve_figure(self, 
                                  portfolio_values: pd.Series, 
                                  benchmark_values: Optional[pd.Series] = None,
                                  chart_type: str = "value",
                                  initial_capital: float = 100000) -> go.Figure:
        """
        Create a portfolio performance chart figure.
        
        Args:
            portfolio_values: Time series of portfolio values
            benchmark_values: Optional benchmark series
            chart_type: Type of chart to create ('value', 'returns', or 'drawdown')
            initial_capital: Initial portfolio capital
            
        Returns:
            go.Figure: Plotly figure object
        """
        # Check if we have data
        if portfolio_values is None or portfolio_values.empty:
            fig = go.Figure()
            fig.update_layout(
                title="No Portfolio Data Available",
                annotations=[{
                    "text": "No portfolio data available",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 18, "color": self.viz_cfg["colors"]["text_muted"]}
                }]
            )
            return fig

        if chart_type == "value":
            # Standard equity curve
            figure_data = {}
            figure_data['Portfolio'] = portfolio_values
            
            if benchmark_values is not None and not benchmark_values.empty:
                benchmark_values.name = benchmark_values.name or "Benchmark"
                figure_data[benchmark_values.name] = benchmark_values
                
            # Create chart using existing utility function
            chart = create_styled_chart(
                figure_data=figure_data,
                layout_title="Portfolio Performance",
                yaxis_title="Portfolio Value",
                yaxis_format="$",
                height=400
            )
            return chart.figure
            
        elif chart_type == "returns":
            # Calculate returns series
            returns = portfolio_values.pct_change().fillna(0) * 100
            cumulative_returns = (1 + returns / 100).cumprod() * 100 - 100
            
            benchmark_cum_returns = None
            if benchmark_values is not None and not benchmark_values.empty:
                bench_returns = benchmark_values.pct_change().fillna(0) * 100
                benchmark_cum_returns = (1 + bench_returns / 100).cumprod() * 100 - 100
            
            # Create figure
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=cumulative_returns.index, 
                y=cumulative_returns.values,
                mode='lines',
                name='Portfolio',
                line=dict(color=self.viz_cfg["colors"]["portfolio"], width=2)
            ))
            
            if benchmark_cum_returns is not None:
                fig.add_trace(go.Scatter(
                    x=benchmark_cum_returns.index, 
                    y=benchmark_cum_returns.values,
                    mode='lines',
                    name='Benchmark',
                    line=dict(color=self.viz_cfg["colors"]["benchmark"], width=2)
                ))
            
            layout = _create_base_layout(
                title="Cumulative Returns",
                height=400,
                xaxis_title="Date",
                yaxis=dict(
                    title="Return (%)", 
                    ticksuffix="%"
                )
            )
            fig.update_layout(layout)
            return fig
            
        elif chart_type == "drawdown":
            # Calculate drawdowns
            rolling_max = portfolio_values.cummax()
            drawdowns = -((portfolio_values - rolling_max) / rolling_max) * 100
            
            benchmark_drawdowns = None
            if benchmark_values is not None and not benchmark_values.empty:
                bench_rolling_max = benchmark_values.cummax()
                benchmark_drawdowns = -((benchmark_values - bench_rolling_max) / bench_rolling_max) * 100
            
            # Create figure
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=drawdowns.index, 
                y=drawdowns.values,
                mode='lines',
                name='Portfolio',
                line=dict(color=self.viz_cfg["colors"]["loss"], width=2),
                fill='tozeroy',
                fillcolor=f'rgba({int(self.viz_cfg["colors"]["loss"][1:3], 16)}, '
                          f'{int(self.viz_cfg["colors"]["loss"][3:5], 16)}, '
                          f'{int(self.viz_cfg["colors"]["loss"][5:7], 16)}, 0.3)'
            ))
            
            if benchmark_drawdowns is not None:
                fig.add_trace(go.Scatter(
                    x=benchmark_drawdowns.index, 
                    y=benchmark_drawdowns.values,
                    mode='lines',
                    name='Benchmark',
                    line=dict(color=self.viz_cfg["colors"]["benchmark"], width=2)
                ))
            
            layout = _create_base_layout(
                title="Drawdown Analysis",
                height=400,
                xaxis_title="Date",
                yaxis=dict(
                    title="Drawdown (%)", 
                    ticksuffix="%",
                    autorange="reversed"  # Invert y-axis for better visualization
                )
            )
            fig.update_layout(layout)
            return fig
            
        else:
            # Default to value chart
            logger.warning(f"Unknown chart type: {chart_type}. Using value chart.")
            return self.create_equity_curve_figure(portfolio_values, benchmark_values)

    
    def create_monthly_returns_heatmap(self, portfolio_values: pd.Series) -> go.Figure:
        """
        Create a monthly returns heatmap.
        
        Args:
            portfolio_values: Time series of portfolio values
            
        Returns:
            go.Figure: Plotly figure object
        """
        if portfolio_values is None or portfolio_values.empty:
            fig = go.Figure()
            fig.update_layout(
                title="No Data Available for Monthly Returns",
                annotations=[{
                    "text": "No portfolio data available",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 18, "color": self.viz_cfg["colors"]["text_muted"]}
                }]
            )
            return fig
            
        # Calculate monthly returns
        try:
            # Make sure we have DatetimeIndex
            if not isinstance(portfolio_values.index, pd.DatetimeIndex):
                portfolio_values = portfolio_values.copy()
                portfolio_values.index = pd.to_datetime(portfolio_values.index)
                
            # Calculate daily returns
            daily_returns = portfolio_values.pct_change().fillna(0)
            
            # Resample to month end and calculate monthly returns
            # Use 'ME' instead of deprecated 'M'
            monthly_returns = (1 + daily_returns).resample('ME').prod() - 1
            
            # Create dataframe with year and month
            returns_df = pd.DataFrame({
                'Year': monthly_returns.index.year,
                'Month': monthly_returns.index.month,
                'Return': monthly_returns.values * 100  # Convert to percentage
            })
            
            # Pivot for heatmap format
            pivot_df = returns_df.pivot(index="Year", columns="Month", values="Return")
            
            # Map month numbers to names for better display
            month_names = {
                1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
            }
            pivot_df = pivot_df.reindex(columns=range(1, 13))
            pivot_df.columns = [month_names[m] for m in pivot_df.columns]
            
            # Create heatmap
            colorscale = [
                [0.0, self.viz_cfg["colors"]["loss"]],
                [0.5, "#333333"],  # Middle (0% return)
                [1.0, self.viz_cfg["colors"]["profit"]]
            ]
            
            # Find max absolute value for symmetric color scale
            max_abs = max(abs(pivot_df.min().min()), abs(pivot_df.max().max()))
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=pivot_df.values,
                x=pivot_df.columns,
                y=pivot_df.index,
                colorscale=colorscale,
                zmin=-max_abs,
                zmax=max_abs,
                hoverongaps=False,
                colorbar=dict(
                    title="Return (%)",
                    ticksuffix="%"
                ),
                hovertemplate="Year: %{y}<br>Month: %{x}<br>Return: %{z:.2f}%<extra></extra>"
            ))
            
            # Update layout
            layout = _create_base_layout(
                title="Monthly Returns",
                height=400,
                margin=dict(t=50, l=40, r=80, b=40)
            )
            fig.update_layout(layout)
            return fig
            
        except Exception as e:
            logger.error(f"Error creating monthly returns heatmap: {e}", exc_info=True)
            fig = go.Figure()
            fig.update_layout(
                title="Error Creating Monthly Returns Heatmap",
                annotations=[{
                    "text": f"Error: {str(e)}",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 14, "color": self.viz_cfg["colors"]["loss"]}
                }]
            )
            return fig
    
    def create_signals_chart(self, ticker: str, signals_df: pd.DataFrame, trades: List[Dict]) -> go.Figure:
        """
        Create a chart showing price data with signals and trades for a specific ticker.
        
        Args:
            ticker: Ticker symbol
            signals_df: DataFrame with OHLCV data and signals
            trades: List of trades for this ticker
            
        Returns:
            go.Figure: Plotly figure object
        """
        if signals_df is None or signals_df.empty:
            fig = go.Figure()
            fig.update_layout(
                title=f"No Signal Data Available for {ticker}",
                annotations=[{
                    "text": f"No signal data for {ticker}",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 18, "color": self.viz_cfg["colors"]["text_muted"]}
                }]
            )
            return fig
            
        try:
            # Create figure
            fig = go.Figure()
            
            # Add price data
            if 'close' in signals_df.columns:
                # Używamy małych liter dla nazw kolumn
                fig.add_trace(go.Scatter(
                    x=signals_df.index,
                    y=signals_df['close'],
                    mode='lines',
                    name='Price',
                    line=dict(color='#888888', width=1.5),
                    hovertemplate="Date: %{x}<br>Price: $%{y:.2f}<extra></extra>"
                ))
            elif 'Close' in signals_df.columns:
                # Alternatywnie, używamy wielkich liter
                fig.add_trace(go.Scatter(
                    x=signals_df.index,
                    y=signals_df['Close'],
                    mode='lines',
                    name='Price',
                    line=dict(color='#888888', width=1.5),
                    hovertemplate="Date: %{x}<br>Price: $%{y:.2f}<extra></extra>"
                ))
            else:
                logger.warning(f"No 'Close' or 'close' column in signals DataFrame for {ticker}")
                return create_empty_chart(f"Missing Price Data for {ticker}", height=500)
            
            # Określamy kolumnę ceny na podstawie dostępnych danych
            price_col = 'close' if 'close' in signals_df.columns else 'Close'
            
            # Add buy signals
            if 'Signal' in signals_df.columns:
                buy_signals = signals_df[signals_df['Signal'] > 0]
                if not buy_signals.empty:
                    fig.add_trace(go.Scatter(
                        x=buy_signals.index,
                        y=buy_signals[price_col],
                        mode='markers',
                        name='Buy Signal',
                        marker=dict(
                            symbol='triangle-up',
                            size=10,
                            color=self.viz_cfg["colors"]["profit"],
                            line=dict(width=1, color='white')
                        ),
                        hovertemplate="Date: %{x}<br>Buy Signal at $%{y:.2f}<extra></extra>"
                    ))
                
                # Add sell signals
                sell_signals = signals_df[signals_df['Signal'] < 0]
                if not sell_signals.empty:
                    fig.add_trace(go.Scatter(
                        x=sell_signals.index,
                        y=sell_signals[price_col],
                        mode='markers',
                        name='Sell Signal',
                        marker=dict(
                            symbol='triangle-down',
                            size=10,
                            color=self.viz_cfg["colors"]["loss"],
                            line=dict(width=1, color='white')
                        ),
                        hovertemplate="Date: %{x}<br>Sell Signal at $%{y:.2f}<extra></extra>"
                    ))
            
            # Add actual trades
            if trades:
                # Buy trades
                entry_x = [pd.to_datetime(trade['entry_date']) for trade in trades]
                entry_y = [float(trade['entry_price']) for trade in trades]
                fig.add_trace(go.Scatter(
                    x=entry_x,
                    y=entry_y,
                    mode='markers',
                    name='Trade Entry',
                    marker=dict(
                        symbol='circle',
                        size=8,
                        color=self.viz_cfg["colors"]["primary"],
                        line=dict(width=1, color='white')
                    ),
                    hovertemplate="Entry: %{x}<br>Price: $%{y:.2f}<extra></extra>"
                ))
                
                # Sell trades
                exit_x = [pd.to_datetime(trade['exit_date']) for trade in trades]
                exit_y = [float(trade['exit_price']) for trade in trades]
                exit_colors = [self.viz_cfg["colors"]["profit"] if float(trade.get('pnl', 0)) >= 0 
                            else self.viz_cfg["colors"]["loss"] for trade in trades]
                fig.add_trace(go.Scatter(
                    x=exit_x,
                    y=exit_y,
                    mode='markers',
                    name='Trade Exit',
                    marker=dict(
                        symbol='circle',
                        size=8,
                        color=exit_colors,
                        line=dict(width=1, color='white')
                    ),
                    hovertemplate="Exit: %{x}<br>Price: $%{y:.2f}<extra></extra>"
                ))
                
                # Draw lines connecting entries and exits
                for i, trade in enumerate(trades):
                    entry_date = pd.to_datetime(trade['entry_date'])
                    exit_date = pd.to_datetime(trade['exit_date'])
                    entry_price = float(trade['entry_price'])
                    exit_price = float(trade['exit_price'])
                    trade_color = self.viz_cfg["colors"]["profit"] if float(trade.get('pnl', 0)) >= 0 else self.viz_cfg["colors"]["loss"]
                    
                    fig.add_shape(
                        type="line",
                        x0=entry_date,
                        y0=entry_price,
                        x1=exit_date,
                        y1=exit_price,
                        line=dict(
                            color=trade_color,
                            width=1.5,
                            dash="dot",
                        )
                    )
            
            # Update layout
            layout = _create_base_layout(
                title=f"{ticker} Price and Signals",
                height=500,
                xaxis_title="Date",
                yaxis_title="Price ($)",
                yaxis=dict(tickprefix="$")
            )
            fig.update_layout(layout)
            fig.update_layout(legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ))
            return fig
            
        except Exception as e:
            logger.error(f"Error creating signals chart for {ticker}: {e}", exc_info=True)
            fig = go.Figure()
            fig.update_layout(
                title=f"Error Creating Signals Chart for {ticker}",
                annotations=[{
                    "text": f"Error: {str(e)}",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 14, "color": self.viz_cfg["colors"]["loss"]}
                }]
            )
            return fig