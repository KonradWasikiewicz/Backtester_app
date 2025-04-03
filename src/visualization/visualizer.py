import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any
import plotly.graph_objects as go
from dash import dcc, html
import logging

logger = logging.getLogger(__name__)

# Importuj funkcje pomocnicze do tworzenia wykresów
try:
    from .chart_utils import (
        create_empty_chart,
        create_styled_chart,
        create_trade_histogram_figure,
        create_allocation_chart # Importuj funkcję alokacji
        # Importuj inne potrzebne funkcje, jeśli je dodasz/przywrócisz
        # create_drawdown_chart,
        # create_monthly_returns_heatmap
    )
except ImportError as e:
    logger.error(f"Failed to import chart utilities in Visualizer: {e}")
    # Definiuj puste funkcje jako fallback, aby uniknąć błędów atrybutów
    def create_empty_chart(*args, **kwargs): return html.Div("Chart Utils Error")
    def create_styled_chart(*args, **kwargs): return html.Div("Chart Utils Error")
    def create_trade_histogram_figure(*args, **kwargs): return html.Div("Chart Utils Error")
    def create_allocation_chart(*args, **kwargs): return html.Div("Chart Utils Error")


class BacktestVisualizer:
    """
    Class responsible for generating Dash components (graphs and tables)
    for visualizing backtest results. Uses utility functions from chart_utils.
    """

    def __init__(self):
        """Initializes the visualizer."""
        # Inicjalizacja może zawierać np. ustawienia domyślne, jeśli są potrzebne
        logger.info("BacktestVisualizer initialized.")


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


    # Możesz dodać tu inne metody, np.:
    # def create_drawdown_component(self, portfolio_values: Optional[pd.Series], ...) -> dcc.Graph:
    #     # Użyj create_styled_chart z odpowiednimi danymi drawdown
    #     pass

    # def create_monthly_heatmap_component(self, portfolio_values: Optional[pd.Series], ...) -> dcc.Graph:
    #     # Wywołaj odpowiednią funkcję z chart_utils
    #     pass