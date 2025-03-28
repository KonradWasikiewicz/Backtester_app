import dash
import dash_bootstrap_components as dbc
import pandas as pd  # Add pandas import
from dash import dcc, html, callback_context, dash_table
from dash.dependencies import Input, Output, State

from src.core.config import config, VISUALIZATION_CONFIG, BACKTEST_CONFIG
from src.core.constants import AVAILABLE_STRATEGIES, CHART_THEME, DROPDOWN_STYLE  
from src.core.data import DataLoader
from src.core.exceptions import DataError 

# Add BENCHMARK constant
BENCHMARK = "^GSPC"  # S&P 500 as default benchmark

from src.strategies import MovingAverageCrossover, RSIStrategy, BollingerBandsStrategy
from src.visualization.visualizer import BacktestVisualizer
from src.analysis.metrics import (
    calculate_cagr, calculate_sharpe_ratio, calculate_sortino_ratio,
    calculate_max_drawdown, calculate_calmar_ratio, calculate_pure_profit_score
)
from src.portfolio.models import Trade
from src.portfolio.portfolio_manager import PortfolioManager
from src.portfolio.risk_manager import RiskManager
from src.core.engine import BacktestEngine
from src.strategies.moving_average import MovingAverageCrossover
from src.strategies.rsi import RSIStrategy
from src.strategies.bollinger import BollingerBandsStrategy

# Initialize Dash app with dark theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "Trading Strategy Backtester"
  
def create_metric_card(title, value, prefix="", suffix=""):
    """Create a styled metric card component with dark theme"""
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-subtitle text-muted"),
            html.H4(f"{prefix}{value}{suffix}", className="card-title text-info")
        ]),
        className="mb-3 bg-dark"
    )

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

def create_chart(figure_data, layout_title):
    """Create a styled chart component"""
    if (figure_data is None):
        return create_empty_chart(layout_title)
    
    traces = []
    for name, data in figure_data.items():
        # Filter data for trading period
        if isinstance(data, pd.Series):
            data = data[data.index >= pd.Timestamp('2020-01-01', tz='UTC')]
        
        trace = {
            'x': data.index,
            'y': data.values,
            'name': 'Portfolio Value' if name == 'Portfolio' else f'Benchmark ({config.BENCHMARK_TICKER})',
            'type': 'scatter',
            'mode': 'lines',
            'line': {'color': '#17B897' if name == 'Portfolio' else '#FF6B6B'}
        }
        traces.append(trace)
    
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
            'margin': {'t': 50, 'l': 50, 'r': 20, 'b': 50},  # Reduced right margin
            'showlegend': True,
            'legend': {
                'orientation': 'h',  # Horizontal legend
                'y': 1.1,  # Position above chart
                'x': 0.5,  # Center legend
                'xanchor': 'center',
                'font': {'color': '#ffffff'},
                'bgcolor': '#1e222d'
            },
            'width': 600  # Reduced width by 25%
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
        }
    )

def create_trade_histogram(trades):
    """Create trade return distribution histogram"""
    if not trades:
        return create_empty_chart("Trade Distribution")
    
    # Calculate returns for each trade
    returns = [(trade['exit_price'] - trade['entry_price']) / trade['entry_price'] * 100 
              for trade in trades]
    
    # Create bins from -50% to 50% in 5% increments
    bins = list(range(-50, 55, 5))
    
    # Split returns into gains and losses
    gains = [r for r in returns if r >= 0]
    losses = [r for r in returns if r < 0]
    
    figure = {
        'data': [
            # Losses histogram
            {
                'x': losses,
                'type': 'histogram',
                'name': 'Losses',
                'autobinx': False,
                'xbins': {'start': -50, 'end': 0, 'size': 5},
                'marker': {'color': '#FF6B6B'},
                'opacity': 0.75
            },
            # Gains histogram
            {
                'x': gains,
                'type': 'histogram',
                'name': 'Gains',
                'autobinx': False,
                'xbins': {'start': 0, 'end': 50, 'size': 5},
                'marker': {'color': '#17B897'},
                'opacity': 0.75
            }
        ],
        'layout': {
            'title': 'Trade Return Distribution',
            'template': CHART_THEME,
            'paper_bgcolor': '#1e222d',
            'plot_bgcolor': '#1e222d',
            'font': {'color': '#ffffff'},
            'xaxis': {
                'title': 'Return (%)',
                'gridcolor': '#2a2e39',
                'range': [-50, 50]
            },
            'yaxis': {
                'title': 'Number of Trades',
                'gridcolor': '#2a2e39'
            },
            'bargap': 0.1,
            'margin': {'t': 50, 'l': 50, 'r': 20, 'b': 50},
            'showlegend': True,
            'legend': {
                'orientation': 'h',
                'y': 1.1,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'color': '#ffffff'},
                'bgcolor': '#1e222d'
            },
            'width': 450,  # Dostosowana szerokość
            'height': 350,  # Dodana stała wysokość
        }
    }
    
    return dcc.Graph(
        id='trade-distribution',
        figure=figure,
        config={
            'displayModeBar': True,
            'responsive': True,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        },
        style={'height': '100%', 'width': '100%'}
    )

def run_backtest(strategy_type, strategy_params=None):
    """Run backtest with specified parameters"""
    try:
        # Get data with lookback period
        data = DataLoader.extend_historical_data()
        
        # Get available tickers first
        available_tickers = DataLoader.get_available_tickers()
        
        # Print initial summary
        data_rows = len(data)
        print("\nInitializing backtest with:")
        print(f"Trading instruments: {', '.join(available_tickers)}")
        print(f"Benchmark: {config.BENCHMARK_TICKER}")
        print(f"Data rows per instrument: {data_rows // (len(available_tickers) + 1)}\n")
        
        # Load data for trading instruments
        data_dict = {}
        loaded_tickers = []
        
        for ticker in available_tickers:
            try:
                df = DataLoader.load_data(ticker)
                if df is not None and not df.empty:
                    data_dict[ticker] = df
                    loaded_tickers.append(ticker)
            except Exception as e:
                print(f"Failed to load {ticker}: {str(e)}")
                continue

        if loaded_tickers:
            print(f"✓ {', '.join(loaded_tickers)}")
        
        if not data_dict:
            raise ValueError("No valid data loaded")

        # Load benchmark data
        try:
            benchmark_data = DataLoader.load_data(config.BENCHMARK_TICKER)
            if benchmark_data is not None:
                benchmark_data = benchmark_data.ffill().bfill()
                print(f"✓ Benchmark ({config.BENCHMARK_TICKER})")
        except Exception:
            benchmark_data = None
            print("✗ Benchmark not available")

        strategy_params = strategy_params or {}
        
        # Strategy initialization with error handling
        if strategy_type == "BB" or not strategy_type:
            strategy = BollingerBandsStrategy(window=20, num_std=2)
        elif strategy_type == "MA":
            strategy = MovingAverageCrossover(
                short_window=strategy_params.get('short_window', 50),
                long_window=strategy_params.get('long_window', 200)
            )
        elif strategy_type == "RSI":
            strategy = RSIStrategy(period=strategy_params.get('period', 14))
        else:
            raise ValueError("Invalid strategy type")
            
        # Generate signals for all instruments
        signals = strategy.generate_signals(data_dict)
        
        # Initialize portfolio manager and risk manager with correct initial capital
        risk_manager = RiskManager()
        portfolio_manager = PortfolioManager(initial_capital=10000, risk_manager=risk_manager)
        
        # Initialize engine with strategy
        engine = BacktestEngine(strategy=strategy, initial_capital=10000)
        all_results = {}
        
        # Get trading dates once
        trading_dates = None
        for ticker in signals.keys():
            ticker_data = data_dict[ticker].copy()
            if trading_dates is None:
                trading_dates = ticker_data[ticker_data.index >= pd.Timestamp('2020-01-01', tz='UTC')].index
        
        # Initialize portfolio value series with initial cash
        initial_portfolio = pd.Series(10000, index=trading_dates)
        
        # Run backtest for each ticker
        for ticker in signals.keys():
            ticker_data = data_dict[ticker].copy()
            ticker_data['Signal'] = signals[ticker]['Signal']
            results = engine.run_backtest(ticker, ticker_data)
            all_results[ticker] = results
        
        # Create portfolio value series starting from initial capital
        portfolio_values = pd.DataFrame(
            {ticker: result['Portfolio_Value'].reindex(trading_dates).fillna(0)
             for ticker, result in all_results.items()},
            index=trading_dates
        )
        
        # Calculate final portfolio value (start with initial capital, then subtract it)
        combined_results = {
            'Portfolio_Value': initial_portfolio + portfolio_values.sum(axis=1) - 10000,
            'trades': engine.trades,
            'signals': signals
        }
        
        # Add benchmark if available
        if benchmark_data is not None:
            benchmark_data['Close'] = benchmark_data['Close'].ffill()
            benchmark_start_date = pd.Timestamp('2020-01-01', tz='UTC')
            benchmark_data = benchmark_data[benchmark_data.index >= benchmark_start_date]
            benchmark_start_price = benchmark_data['Close'].iloc[0]
            
            # Calculate benchmark shares to start exactly at 10000
            benchmark_shares = 10000 / benchmark_start_price
            benchmark_values = pd.Series(
                benchmark_data['Close'] * benchmark_shares,
                index=benchmark_data.index,
                name='Benchmark'
            )
            
            combined_results['Benchmark'] = benchmark_values
        
        # Calculate portfolio statistics
        stats = {
            'initial_capital': 10000,  # Changed from 100000
            'final_capital': float(combined_results['Portfolio_Value'].iloc[-1]),
            'total_return': ((float(combined_results['Portfolio_Value'].iloc[-1]) / 10000) - 1) * 100,
            'total_trades': sum(len(result.get('trades', [])) for result in all_results.values()),
            'win_rate': 0.0,  # Will be calculated if trades exist
            'sharpe_ratio': 0.0  # Will be calculated if enough data points exist
        }
        
        # Additional metrics for valid data
        if len(combined_results) >= 2:
            # Use ffill() instead of fillna(method='ffill')
            combined_results['Portfolio_Value'] = combined_results['Portfolio_Value'].ffill()
            portfolio_returns = combined_results['Portfolio_Value'].pct_change(fill_method=None).dropna()
            if len(portfolio_returns) >= 2:
                metrics = {
                    'cagr': calculate_cagr(combined_results['Portfolio_Value']) * 100,
                    'sharpe_ratio': calculate_sharpe_ratio(portfolio_returns),
                    'sortino_ratio': calculate_sortino_ratio(portfolio_returns),
                    'max_drawdown': calculate_max_drawdown(combined_results['Portfolio_Value'], method='percent') * 100,
                    'calmar_ratio': calculate_calmar_ratio(portfolio_returns),
                    'pure_profit_score': calculate_pure_profit_score(portfolio_returns)
                }
                stats.update(metrics)
        
        # Add engine statistics
        engine_stats = engine.get_statistics()
        if engine_stats:
            stats.update(engine_stats)
            
        return signals, combined_results, stats
            
    except Exception as e:
        print(f"Backtest error: {str(e)}")
        return None, None, None

def create_metric_cards(stats):
    """Create metric cards layout with advanced metrics"""
    return dbc.Row([
        dbc.Col([
            create_metric_card("CAGR", f"{stats['cagr']:.2f}%"),
            create_metric_card("Total Return", f"{stats['total_return']:.2f}%"),
            create_metric_card("Win Rate", f"{stats['win_rate']:.2f}%"),
        ]),
        dbc.Col([
            create_metric_card("Max Drawdown", f"{stats['max_drawdown']:.2f}%"),
            create_metric_card("Sharpe Ratio", f"{stats['sharpe_ratio']:.2f}"),
            create_metric_card("Sortino Ratio", f"{stats['sortino_ratio']:.2f}"),
        ]),
        dbc.Col([
            create_metric_card("Calmar Ratio", f"{stats['calmar_ratio']:.2f}"),
            create_metric_card("Pure Profit Score", f"{stats['pure_profit_score']:.2f}"),
            create_metric_card("Total Trades", f"{stats['total_trades']}")
        ])
    ])

# Initialize visualizer
visualizer = BacktestVisualizer()

def create_charts(results):
    """Create charts layout"""
    if results is None:
        return []
    
    charts = []
    
    # Create equity curve
    equity_trace = {
        'x': results['Portfolio_Value'].index,
        'y': results['Portfolio_Value'].values,
        'name': 'Portfolio Value',
        'type': 'scatter',
        'mode': 'lines',
        'line': {'color': '#17B897'}
    }
    
    if 'Benchmark' in results:
        benchmark_trace = {
            'x': results['Benchmark'].index,
            'y': results['Benchmark'].values,
            'name': 'Benchmark',
            'type': 'scatter',
            'mode': 'lines',
            'line': {'color': '#FF6B6B'}
        }
        charts.extend([equity_trace, benchmark_trace])
    else:
        charts.append(equity_trace)
    
    return charts

def create_empty_cards():
    """Create empty metric cards"""
    return dbc.Row([
        dbc.Col(create_metric_card("Initial Capital", "N/A")),
        dbc.Col(create_metric_card("Final Capital", "N/A")),
        dbc.Col(create_metric_card("Total Return", "N/A")),
        dbc.Col(create_metric_card("Total Trades", "N/A"))  # Changed from Sharpe Ratio to Total Trades
    ])

def create_trade_table(trades):
    """Create unified trade history table"""
    if not trades:
        return html.Div("No trades available")
    
    trade_records = []
    for trade in trades:
        record = {
            'Date In': pd.to_datetime(trade['entry_date']).strftime('%Y-%m-%d'),
            'Date Out': pd.to_datetime(trade['exit_date']).strftime('%Y-%m-%d'),
            'Ticker': trade['ticker'],
            'Type': trade['direction'],
            'Shares': f"{trade['shares']:,}",
            'Entry': f"${trade['entry_price']:.2f}",
            'Exit': f"${trade['exit_price']:.2f}",
            'P&L': f"${trade['pnl']:.2f}",
            'Return': f"{(trade['pnl'] / (trade['entry_price'] * trade['shares']) * 100):.1f}%"
        }
        trade_records.append(record)
    
    df = pd.DataFrame(trade_records)
    
    return dash_table.DataTable(
        id='trade-table',
        columns=[
            {"name": i, "id": i} for i in df.columns
        ],
        data=df.to_dict('records'),
        sort_action="native",
        style_table={
            'height': '640px',
            'overflowY': 'auto',
            'minWidth': '100%',
            'maxWidth': '100%'
        },
        fixed_rows={'headers': True},
        style_cell={
            'backgroundColor': '#1e222d',
            'color': '#e1e1e1',
            'fontFamily': 'system-ui',
            'fontSize': '13px',
            'height': 'auto',
            'minWidth': '70px',
            'maxWidth': '90px',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'textAlign': 'left',
            'padding': '8px 12px'
        },
        style_data={
            'whiteSpace': 'normal',
            'height': 'auto',
            'lineHeight': '15px'
        },
        style_header={
            'backgroundColor': '#2a2e39',
            'fontWeight': 'bold',
            'border': '1px solid #2a2e39',
            'whiteSpace': 'normal',
            'height': 'auto'
        },
        style_data_conditional=[
            {
                'if': {'filter_query': '{P&L} contains "+"'},
                'color': '#17B897'
            },
            {
                'if': {'filter_query': '{P&L} contains "-"'},
                'color': '#FF6B6B'
            }
        ],
        css=[{
            'selector': '.dash-table-container',
            'rule': 'max-height: 640px; font-family: system-ui;'
        }, {
            'selector': '::-webkit-scrollbar',
            'rule': 'width: 8px; height: 8px;'
        }, {
            'selector': '::-webkit-scrollbar-track',
            'rule': 'background: #1e222d;'
        }, {
            'selector': '::-webkit-scrollbar-thumb',
            'rule': 'background: #2a2e39; border-radius: 4px;'
        }, {
            'selector': '::-webkit-scrollbar-thumb:hover',
            'rule': 'background: #363b47;'
        }]
    )

# Update layout to include containers for metric cards and charts
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Portfolio Backtester", className="text-center my-4")
        ])
    ]),

    dbc.Row([
        # Left column (Strategy Settings) - zmniejszony z width=3 do width=2
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Strategy Settings"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Select Strategy", className="text-light mb-2"),
                            dcc.Dropdown(
                                id="strategy-selector",
                                options=[
                                    {"label": "Bollinger Bands", "value": "BB"},
                                    {"label": "Moving Average Crossover", "value": "MA"},
                                    {"label": "RSI", "value": "RSI"}
                                ],
                                value="MA",
                                className="mb-3",
                                style={
                                    'backgroundColor': '#1e222d',
                                    'color': '#ffffff',
                                },
                                optionHeight=35,
                                clearable=False,
                            )
                        ], width=12)
                    ]),
                    html.Div([
                        html.Label("Backtest Period"),
                        html.P(id="backtest-period", className="text-info"),
                        html.Label("Portfolio Instruments"),
                        html.Div(id="portfolio-instruments", className="text-info")
                    ], className="mt-3"),
                    dbc.Spinner(html.Div(id="calculation-status"))
                ])
            ], className="mb-4")
        ], width=2),  # Zmniejszona szerokość
        
        # Center column (Equity Curve) - bez zmian width=6
        dbc.Col([
            dbc.Row([
                dbc.Col(html.Div(id="equity-curve-container"), className="mb-4")
            ]),
            dbc.Row([
                dbc.Col(html.Div(id="metrics-container"), className="mb-4")
            ]),
            dbc.Row([
                dbc.Col(html.Div(id="additional-charts"))
            ])
        ], width=6),
        
        # Right column (Trade Distribution & History) - zwiększony z width=3 do width=4
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Trade Distribution"),
                dbc.CardBody([
                    html.Div(id="trade-distribution-container")
                ])
            ], className="mb-4"),
            dbc.Card([
                dbc.CardHeader("Trade History"),
                dbc.CardBody([
                    html.Div(id="trade-table-container")
                ])
            ])
        ], width=4)  # Zwiększona szerokość
    ])
], fluid=True, style={"backgroundColor": "#131722"})

@app.callback(
    [Output("calculation-status", "children"),
     Output("equity-curve-container", "children"),
     Output("metrics-container", "children"),
     Output("additional-charts", "children"),
     Output("trade-distribution-container", "children"),  # Added output
     Output("trade-table-container", "children"),
     Output("backtest-period", "children"),
     Output("portfolio-instruments", "children")],
    [Input("strategy-selector", "value")]
)
def update_backtest(strategy):
    if not strategy:
        return "Please select a strategy", [], create_empty_cards(), [], "No trades available", "", ""
    
    try:
        signals, results, stats = run_backtest(strategy)
        
        if any(x is None for x in [signals, results, stats]):
            return (
                html.Div("Error running backtest", className="text-danger"),
                [],
                create_empty_cards(),
                [],
                "No trades available",
                "",
                ""
            )
            
        # Print debug information
        print(f"\nStrategy: {strategy}")
        print_portfolio_summary(results)
        
        # Rest of the callback...
        
        # Add signals to results
        results['signals'] = signals  # Ensure signals are included in results
        
        # Create components with proper data structure
        equity_curve = create_chart({
            'Portfolio': results['Portfolio_Value'],
            'Benchmark': results.get('Benchmark', pd.Series())
        }, "Equity Curve")
        
        metric_cards = create_metric_cards(stats)
        additional_charts = create_charts(results)  # Now includes signals
        trade_distribution = create_trade_histogram(results.get('trades', []))
        trade_table = create_trade_table(results.get('trades', []))
        
        # Get actual backtest period (2020 onwards only)
        portfolio_values = results['Portfolio_Value']
        trading_period = portfolio_values[portfolio_values.index >= pd.Timestamp('2020-01-01', tz='UTC')]
        start_date = trading_period.index[0].strftime('%Y-%m-%d')
        end_date = trading_period.index[-1].strftime('%Y-%m-%d')
        backtest_period = f"{start_date} to {end_date}"
        
        return (
            html.Div("Calculation complete", className="text-success"),
            equity_curve,
            metric_cards,
            additional_charts,
            trade_distribution,  # Added return value
            trade_table,
            backtest_period,
            ", ".join(signals.keys())
        )
        
    except Exception as e:
        return (
            html.Div(f"Error: {str(e)}", className="text-danger"),
            [], [], [], [], "No trades available", "", ""  # Updated number of return values
        )

# Add this to main() for debugging
def main():
    try:
        print("Checking CSV file content...")
        df = pd.read_csv(config.DATA_FILE)
        print("\nCSV columns:", df.columns.tolist())
        print("\nUnique tickers:", df['Ticker'].unique())
        print("\nDate range:", df['Date'].min(), "to", df['Date'].max())
        print("\nSample data:\n", df.head())
        
        # Get all available tickers from CSV
        available_tickers = DataLoader.get_available_tickers()
        
        # Create strategy instance
        strategy = MovingAverageCrossover()
        
        # Initialize backtesting engine with strategy
        engine = BacktestEngine(strategy=strategy, initial_capital=100000)
        
        # Run backtest for all tickers
        results = run_backtest("MA")  # Use the existing run_backtest function
        
        if results is not None:
            signals, combined_results, stats = results
            
            # Print basic results
            print("\nBacktest Results:")
            print(f"Total Return: {stats['total_return']:.2f}%")
            print(f"Total Trades: {stats['total_trades']}")
            print(f"Win Rate: {stats['win_rate']:.2f}%")
            print(f"Sharpe Ratio: {stats['sharpe_ratio']:.2f}")
            
    except Exception as e:
        print(f"Error running backtest: {str(e)}")

def print_portfolio_summary(results, days=15):
    """Print daily portfolio values and trades for first n days"""
    if results is None or 'Portfolio_Value' not in results:
        print("No results available")
        return
        
    # Get trading days starting from 2020
    start_date = pd.Timestamp('2020-01-01', tz='UTC')
    portfolio_values = results['Portfolio_Value'][results['Portfolio_Value'].index >= start_date]
    benchmark_values = results.get('Benchmark', pd.Series())[results.get('Benchmark', pd.Series()).index >= start_date]
    
    # Get trades
    trades = results.get('trades', [])
    
    # Create date range for first n days
    dates = portfolio_values.index[:days]
    
    # Print header
    print("\nDaily Portfolio Summary (First 3 Weeks)")
    print("=" * 100)
    print(f"{'Date':<12} | {'Portfolio ($)':>12} | {'Benchmark ($)':>12} | {'# Trades':>8} | {'Trades Details':<40}")
    print("-" * 100)
    
    for date in dates:
        # Count trades for this day
        day_trades = [t for t in trades if pd.Timestamp(t['entry_date']).date() == date.date()]
        trade_count = len(day_trades)
        
        # Get trade details
        trade_details = ""
        if trade_count > 0:
            trade_details = ", ".join([f"{t['ticker']} ({t['direction']})" for t in day_trades])
        
        print(f"{date.strftime('%Y-%m-%d'):<12} | "
              f"{portfolio_values[date]:>12,.2f} | "
              f"{benchmark_values[date]:>12,.2f} | "
              f"{trade_count:>8} | "
              f"{trade_details:<40}")

    print("=" * 100)

if __name__ == "__main__":
    app.run(debug=True)
