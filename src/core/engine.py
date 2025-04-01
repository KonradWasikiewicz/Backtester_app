import pandas as pd
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
from src.core.config import config  # Add this import
from dash import dcc  # Updated import to fix deprecation warning
from dash import html
import plotly.graph_objects as go

from ..strategies.base import BaseStrategy  # Changed from Strategy to BaseStrategy
from .data import DataLoader
from .constants import CHART_THEME, BENCHMARK_TICKER

class BacktestEngine:
    """Engine for running backtests on a single ticker"""
    
    def __init__(self, initial_capital=100000.0, strategy=None):
        """Initialize backtest engine with capital and strategy"""
        self.initial_capital = initial_capital
        self.strategy = strategy
        self.logger = logging.getLogger(__name__)
        
    def run_backtest(self, ticker, data):
        """Run a backtest for a single ticker"""
        try:
            # Check for required data
            if data is None or data.empty or 'Signal' not in data.columns:
                return None
                
            # Filter data by configured dates
            start_date = pd.to_datetime(config.START_DATE)
            end_date = pd.to_datetime(config.END_DATE)
            data = data.loc[(data.index >= start_date) & (data.index <= end_date)]
            
            if len(data) == 0:
                return None
                
            # Initialize portfolio metrics
            initial_capital = self.initial_capital
            positions = 0
            cash = initial_capital
            portfolio_values = []
            trades = []
            
            # Process signals for each day
            for date, row in data.iterrows():
                position_value = positions * row['Close']
                total_value = cash + position_value
                
                # Store portfolio value for this date
                portfolio_values.append({
                    'date': date,
                    'value': total_value
                })
                
                # Process position changes
                if 'Position' in row and not pd.isna(row['Position']):
                    # Buy signal (1)
                    if row['Position'] > 0:
                        # Calculate how many shares we can buy with our cash
                        shares_to_buy = int(cash / row['Close'])
                        if shares_to_buy > 0:
                            # Update positions and cash
                            positions += shares_to_buy
                            cost = shares_to_buy * row['Close']
                            cash -= cost
                            
                            # Log the trade
                            trades.append({
                                'ticker': ticker,
                                'entry_date': date,
                                'exit_date': None,
                                'entry_price': row['Close'],
                                'exit_price': None,
                                'shares': shares_to_buy,
                                'direction': 'Long',
                                'pnl': None,
                                'status': 'Open'
                            })
                    
                    # Sell signal (-1)
                    elif row['Position'] < 0 and positions > 0:
                        # Sell all current positions
                        proceeds = positions * row['Close']
                        
                        # Find the open trade and close it
                        for trade in trades:
                            if trade['status'] == 'Open' and trade['ticker'] == ticker:
                                trade['exit_date'] = date
                                trade['exit_price'] = row['Close']
                                trade['pnl'] = (row['Close'] - trade['entry_price']) * trade['shares']
                                trade['status'] = 'Closed'
                        
                        # Update positions and cash
                        positions = 0
                        cash += proceeds
            
            # Close any remaining open trades at the last price
            if positions > 0:
                last_date = data.index[-1]
                last_price = data.iloc[-1]['Close']
                
                # Find and close any open trades
                for trade in trades:
                    if trade['status'] == 'Open':
                        trade['exit_date'] = last_date
                        trade['exit_price'] = last_price
                        trade['pnl'] = (last_price - trade['entry_price']) * trade['shares']
                        trade['status'] = 'Closed'
                
                # Update final portfolio value
                cash += positions * last_price
                positions = 0
                
                # Update the last portfolio value
                if portfolio_values:
                    portfolio_values[-1]['value'] = cash
            
            # Create portfolio series
            portfolio_series = pd.Series(
                [pv['value'] for pv in portfolio_values],
                index=[pv['date'] for pv in portfolio_values]
            )
            
            # Remove trades with status field
            clean_trades = []
            for trade in trades:
                if trade['status'] == 'Closed':
                    trade_copy = trade.copy()
                    trade_copy.pop('status', None)
                    clean_trades.append(trade_copy)
            
            return {
                'Portfolio_Value': portfolio_series,
                'trades': clean_trades
            }
            
        except Exception as e:
            self.logger.error(f"Backtest error in engine for {ticker}: {str(e)}")
            import traceback
            traceback.print_exc()
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

def create_allocation_chart(results):
    """Create portfolio allocation chart showing position values and cash over time"""
    if not results or 'allocations' not in results:
        return html.Div("No allocation data available")
        
    # Extract allocation data
    allocations = results.get('allocations', [])
    if not allocations:
        return html.Div("No allocation data available")
        
    # Convert allocations to DataFrame
    alloc_records = []
    for ticker_allocs in allocations.values():
        for alloc in ticker_allocs:
            alloc_records.append(alloc)
            
    if not alloc_records:
        return html.Div("No allocation data available")
        
    # Create DataFrame from records
    df_alloc = pd.DataFrame(alloc_records)
    
    # Group by date and aggregate
    df_pivot = df_alloc.pivot_table(
        index='date', 
        columns='ticker', 
        values='value',
        aggfunc='sum'
    ).fillna(0)
    
    # Add cash column
    cash_by_date = df_alloc.groupby('date')['cash'].first()
    df_pivot['Cash'] = cash_by_date
    
    # Calculate percentages
    total_by_date = df_alloc.groupby('date')['total'].first()
    for col in df_pivot.columns:
        df_pivot[f'{col}_pct'] = (df_pivot[col] / total_by_date) * 100
    
    # Create figure for values
    fig_values = go.Figure()
    
    # Add area traces for each ticker (stacked)
    for ticker in df_pivot.columns:
        if ticker != 'Cash' and not ticker.endswith('_pct'):
            fig_values.add_trace(
                go.Scatter(
                    x=df_pivot.index,
                    y=df_pivot[ticker],
                    name=ticker,
                    stackgroup='one',
                    mode='lines',
                    line=dict(width=0.5),
                    hovertemplate='%{y:$,.2f}<extra>%{x|%Y-%m-%d}: ' + ticker + '</extra>'
                )
            )
    
    # Add cash as the bottom area
    fig_values.add_trace(
        go.Scatter(
            x=df_pivot.index,
            y=df_pivot['Cash'],
            name='Cash',
            stackgroup='one',
            mode='lines',
            line=dict(width=0.5),
            fillcolor='rgba(200, 200, 200, 0.5)',
            hovertemplate='%{y:$,.2f}<extra>%{x|%Y-%m-%d}: Cash</extra>'
        )
    )
    
    # Create figure for percentages
    fig_pct = go.Figure()
    
    # Add area traces for percentages (stacked)
    for ticker in [col for col in df_pivot.columns if not col.endswith('_pct') and col != 'Cash']:
        fig_pct.add_trace(
            go.Scatter(
                x=df_pivot.index,
                y=df_pivot[f'{ticker}_pct'],
                name=ticker,
                stackgroup='one',
                mode='lines',
                line=dict(width=0.5),
                hovertemplate='%{y:.1f}%<extra>%{x|%Y-%m-%d}: ' + ticker + '</extra>'
            )
        )
    
    # Add cash percentage
    fig_pct.add_trace(
        go.Scatter(
            x=df_pivot.index,
            y=df_pivot['Cash_pct'],
            name='Cash',
            stackgroup='one',
            mode='lines',
            line=dict(width=0.5),
            fillcolor='rgba(200, 200, 200, 0.5)',
            hovertemplate='%{y:.1f}%<extra>%{x|%Y-%m-%d}: Cash</extra>'
        )
    )
    
    # Layout for values chart
    fig_values.update_layout(
        title='Portfolio Allocation (Values)',
        template=CHART_THEME,
        paper_bgcolor='#1e222d',
        plot_bgcolor='#1e222d',
        font={'color': '#ffffff'},
        xaxis={
            'gridcolor': '#2a2e39',
            'showgrid': True,
            'zeroline': False,
            'title': 'Date'
        },
        yaxis={
            'gridcolor': '#2a2e39',
            'showgrid': True,
            'zeroline': True,
            'zerolinecolor': '#2a2e39',
            'title': 'Allocation Value ($)'
        },
        margin={'t': 50, 'l': 60, 'r': 30, 'b': 50},
        showlegend=True,
        legend={
            'orientation': 'h',
            'y': 1.1,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'color': '#ffffff'},
            'bgcolor': '#1e222d'
        },
        height=300,
        autosize=True
    )
    
    # Layout for percentage chart
    fig_pct.update_layout(
        title='Portfolio Allocation (Percentages)',
        template=CHART_THEME,
        paper_bgcolor='#1e222d',
        plot_bgcolor='#1e222d',
        font={'color': '#ffffff'},
        xaxis={
            'gridcolor': '#2a2e39',
            'showgrid': True,
            'zeroline': False,
            'title': 'Date'
        },
        yaxis={
            'gridcolor': '#2a2e39',
            'showgrid': True,
            'zeroline': True,
            'zerolinecolor': '#2a2e39',
            'title': 'Allocation (%)'
        },
        margin={'t': 50, 'l': 60, 'r': 30, 'b': 50},
        showlegend=True,
        legend={
            'orientation': 'h',
            'y': 1.1,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'color': '#ffffff'},
            'bgcolor': '#1e222d'
        },
        height=300,
        autosize=True
    )
    
    # Return both charts
    return html.Div([
        dcc.Graph(figure=fig_values, config={'displayModeBar': True}),
        dcc.Graph(figure=fig_pct, config={'displayModeBar': True})
    ])
