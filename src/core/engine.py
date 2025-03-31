import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any, Optional
from dash import dcc  # Updated import to fix deprecation warning

from ..strategies.base import BaseStrategy  # Changed from Strategy to BaseStrategy
from .data import DataLoader
from .constants import CHART_THEME, BENCHMARK_TICKER

class BacktestEngine:
    def __init__(self, strategy=None, initial_capital=10000):
        self.initial_capital = initial_capital
        self.trades = []
        self.positions = {}
        self.strategy = strategy
    
    def set_strategy(self, strategy):
        self.strategy = strategy
        
    def run_backtest(self, ticker: str, data: pd.DataFrame) -> dict:
        """Run backtest for a single instrument"""
        try:
            logging.info(f"Running backtest for {ticker}")
            trading_data = data.copy()
            
            # Initialize with starting capital for this ticker
            available_cash = self.initial_capital / len(self.strategy.tickers) if self.strategy and hasattr(self.strategy, 'tickers') else self.initial_capital
            current_position = 0
            
            # Create list for portfolio values
            portfolio_values = []
            
            # Get trading period data only (avoid lookback period)
            trading_period = trading_data[trading_data.index >= pd.Timestamp('2020-01-01')]
            
            # Add first portfolio value (initial cash)
            portfolio_values.append(available_cash)
            
            # Process each day in trading period
            for i in range(len(trading_period)):
                current_day = trading_period.iloc[i]
                current_date = trading_period.index[i]
                
                # Get signal (previous day for entry decisions)
                prev_signal = trading_data['Signal'].iloc[trading_data.index.get_loc(current_date)-1] if i > 0 else 0
                
                # Process entries
                if current_position == 0 and prev_signal == 1:
                    shares = int(available_cash / current_day['Open'])
                    if shares > 0:
                        current_position = shares
                        cost = shares * current_day['Open']
                        available_cash -= cost
                        self.positions[ticker] = {
                            'shares': shares,
                            'cost_basis': current_day['Open'],
                            'entry_date': current_date
                        }
                
                # Process exits
                elif current_position > 0 and prev_signal in [-1, 0]:
                    exit_price = current_day['Open']
                    proceeds = current_position * exit_price
                    available_cash += proceeds
                    
                    # Record trade
                    self.trades.append({
                        'entry_date': self.positions[ticker]['entry_date'],
                        'exit_date': current_date,
                        'ticker': ticker,
                        'direction': 'LONG',
                        'shares': current_position,
                        'entry_price': self.positions[ticker]['cost_basis'],
                        'exit_price': exit_price,
                        'pnl': proceeds - (current_position * self.positions[ticker]['cost_basis'])
                    })
                    
                    current_position = 0
                    if ticker in self.positions:
                        del self.positions[ticker]
                
                # Calculate daily portfolio value
                position_value = current_position * current_day['Close']
                portfolio_value = position_value + available_cash
                portfolio_values.append(portfolio_value)
            
            # Create series aligned with trading period index
            # Ensure length matches trading period
            if len(portfolio_values) > len(trading_period):
                portfolio_values = portfolio_values[1:]  # Skip initial value
                
            portfolio_series = pd.Series(
                portfolio_values,
                index=trading_period.index
            )
            
            return {
                'Portfolio_Value': portfolio_series,
                'trades': self.trades
            }
            
        except Exception as e:
            logging.error(f"Backtest error in engine for {ticker}: {str(e)}", exc_info=True)
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Calculate trading statistics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'win_rate': 0.0,
                'avg_trade_return': 0.0
            }
        
        winning_trades = len([t for t in self.trades if t['pnl'] > 0])
        total_trades = len(self.trades)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0.0,
            'avg_trade_return': sum(t['pnl'] for t in self.trades) / total_trades if total_trades > 0 else 0.0
        }

def create_empty_chart(layout_title):
    """Create an empty chart with placeholder message"""
    return {
        'data': [],
        'layout': {
            'title': layout_title,
            'xaxis': {'visible': False},
            'yaxis': {'visible': False},
            'annotations': [{
                'text': 'No data available',
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 16, 'color': '#ffffff'},
                'x': 0.5,
                'y': 0.5
            }],
            'template': CHART_THEME,
            'paper_bgcolor': '#1e222d',
            'plot_bgcolor': '#1e222d',
            'margin': {'t': 50, 'l': 40, 'r': 40, 'b': 40}
        }
    }

def create_styled_chart(figure_data, layout_title):
    """Create a styled chart component with error handling"""
    try:
        if figure_data is None or not figure_data:
            return create_empty_chart(layout_title)
        
        traces = []
        for name, data in figure_data.items():
            if data is None or len(data) == 0:
                continue
                
            # Ensure data is series with DatetimeIndex
            if not isinstance(data, pd.Series):
                logging.warning(f"Expected Series but got {type(data)}")
                continue
                
            trace = {
                'x': data.index,
                'y': data.values,
                'name': 'Portfolio Value' if name == 'Portfolio' else f'Benchmark ({BENCHMARK_TICKER})',
                'type': 'scatter',
                'mode': 'lines',
                'line': {'color': '#17B897' if name == 'Portfolio' else '#FF6B6B'}
            }
            traces.append(trace)
        
        # If no valid traces, return empty chart
        if not traces:
            return create_empty_chart(layout_title)
            
        figure = {
            'data': traces,
            'layout': {
                'title': layout_title,
                'template': CHART_THEME,
                'paper_bgcolor': '#1e222d',
                'plot_bgcolor': '#1e222d',
                'font': {'color': '#ffffff'},
                'xaxis': {
                    'gridcolor': '#2a2e39',
                    'showgrid': True,
                    'zeroline': False,
                    'title': 'Date'
                },
                'yaxis': {
                    'gridcolor': '#2a2e39',
                    'showgrid': True,
                    'zeroline': True,
                    'zerolinecolor': '#2a2e39',
                    'title': 'Portfolio Value ($)'
                },
                'margin': {'t': 50, 'l': 60, 'r': 30, 'b': 50},
                'showlegend': True,
                'legend': {
                    'orientation': 'h',
                    'y': 1.1,
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'color': '#ffffff'},
                    'bgcolor': '#1e222d'
                },
                'height': 450,
                'autosize': True  # Fixed Python boolean
            }
        }
        
        return dcc.Graph(
            id=f"chart-{layout_title.lower().replace(' ', '-')}",
            figure=figure,
            config={
                'displayModeBar': True,
                'responsive': True,
                'scrollZoom': True,
                'modeBarButtonsToRemove': ['lasso2d', 'select2d']
            },
            style={'height': '100%', 'width': '100%'}
        )
    except Exception as e:
        logging.error(f"Error creating chart: {str(e)}", exc_info=True)
        return create_empty_chart(layout_title)
