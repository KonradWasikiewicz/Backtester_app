import dash
import dash_bootstrap_components as dbc
import pandas as pd  # Add pandas import
from dash import dcc, html, callback_context, dash_table
from dash.dependencies import Input, Output, State

from src.core.config import config, VISUALIZATION_CONFIG, BACKTEST_CONFIG
from src.core.constants import AVAILABLE_STRATEGIES, CHART_THEME, DROPDOWN_STYLE  # usuwamy DEFAULT_TICKERS z importu
from src.core.data import DataLoader

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
from src.strategies.moving_average import MovingAverageStrategy
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
    """Create a styled chart component
    
    Args:
        figure_data: Plotly figure data or None
        layout_title: String title for the chart
    
    Returns:
        dcc.Graph: A styled Dash core components Graph
    """
    if figure_data is None:
        figure = create_empty_chart(layout_title)
    else:
        figure = {
            'data': figure_data if isinstance(figure_data, list) else [figure_data],
            'layout': {
                'title': layout_title,
                'template': CHART_THEME,
                'paper_bgcolor': '#1e222d',
                'plot_bgcolor': '#1e222d',
                'font': {'color': '#ffffff'},
                'xaxis': {'gridcolor': '#2a2e39'},
                'yaxis': {'gridcolor': '#2a2e39'},
                'margin': {'t': 50, 'l': 40, 'r': 40, 'b': 40},
                'showlegend': True,
                'legend': {'font': {'color': '#ffffff'}}
            }
        }

    return dcc.Graph(
        id=f"chart-{layout_title.lower().replace(' ', '-')}",
        figure=figure,
        config={
            'displayModeBar': True,
            'responsive': True,
            'scrollZoom': True
        },
        style={'height': '100%', 'width': '100%'}
    )

def run_backtest(strategy_type, strategy_params=None):
    """Run backtest with specified parameters"""
    try:
        # Load data for trading instruments and benchmark
        data_dict = {}
        available_tickers = DataLoader.get_available_tickers()  # Pobieramy dynamicznie tickery
        
        for ticker in available_tickers:
            df = DataLoader.load_data('data/historical_prices.csv', ticker)
            if df is not None and len(df.index) > 0:
                data_dict[ticker] = df.ffill().bfill()

        # Load benchmark data separately
        benchmark_data = DataLoader.load_data('data/historical_prices.csv', BENCHMARK)
        if benchmark_data is not None:
            benchmark_data = benchmark_data.ffill().bfill()
        
        if not data_dict:
            raise ValueError("No data available for any instrument")
        
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
        
        # Initialize portfolio manager and risk manager
        risk_manager = RiskManager()
        portfolio_manager = PortfolioManager(initial_capital=100000, risk_manager=risk_manager)
        
        # Run backtest
        engine = BacktestEngine(initial_capital=100000)
        all_results = {}
        for ticker, data in signals.items():
            ticker_results = engine.run_backtest(data)
            all_results[ticker] = ticker_results
        
        # Combine results
        combined_results = pd.DataFrame()
        combined_results['Portfolio_Value'] = sum(result['Portfolio_Value'] for result in all_results.values())
        
        # Calculate benchmark returns
        if benchmark_data is not None:
            benchmark_returns = benchmark_data['Close'].pct_change()
            benchmark_performance = (1 + benchmark_returns).cumprod() * 100000  # Scale to initial capital
            combined_results['Benchmark'] = benchmark_performance
        
        # Calculate portfolio statistics
        stats = {
            'initial_capital': 100000,
            'final_capital': float(combined_results['Portfolio_Value'].iloc[-1]),
            'total_return': ((float(combined_results['Portfolio_Value'].iloc[-1]) / 100000) - 1) * 100
        }
        
        # Additional metrics for valid data
        if len(combined_results) >= 2:
            portfolio_returns = combined_results['Portfolio_Value'].pct_change().dropna()
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
    return visualizer.create_backtest_charts(results)

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
        
    df = pd.DataFrame([trade.to_dict() for trade in trades])
    
    return dash_table.DataTable(
        id='trade-table',
        columns=[
            {"name": "ID", "id": "ID"},
            {"name": "Ticker", "id": "Ticker"},
            {"name": "Direction", "id": "Direction"},
            {"name": "Entry Date", "id": "Entry Date"},
            {"name": "Exit Date", "id": "Exit Date"},
            {"name": "Shares", "id": "Shares", "type": "numeric"},
            {"name": "Entry Price", "id": "Entry Price"},
            {"name": "Exit Price", "id": "Exit Price"},
            {"name": "P&L", "id": "P&L"},
            {"name": "Return %", "id": "Return %"},
            {"name": "Duration", "id": "Duration"},
            {"name": "Exit Reason", "id": "Exit Reason"}
        ],
        data=df.to_dict('records'),
        sort_action="native",
        filter_action="native",
        style_table={'overflowX': 'auto'},
        style_cell={
            'backgroundColor': '#1e222d',
            'color': '#e1e1e1',
            'minWidth': '100px'
        },
        style_header={
            'backgroundColor': '#2a2e39',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{P&L} contains "+"'
                },
                'color': '#17B897'
            },
            {
                'if': {
                    'filter_query': '{P&L} contains "-"'
                },
                'color': '#FF6B6B'
            }
        ]
    )

# Update layout to include containers for metric cards and charts
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Portfolio Backtester", className="text-center my-4")
        ])
    ]),

    dbc.Row([
        # Left column (1/3)
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Strategy Settings"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Select Strategy"),
                            dcc.Dropdown(
                                id="strategy-selector",
                                options=[
                                    {"label": "Bollinger Bands", "value": "BB"},
                                    {"label": "Moving Average Crossover", "value": "MA"},
                                    {"label": "RSI", "value": "RSI"}
                                ],
                                value="MA",
                                className="mb-3 dropdown-dark",
                                style=DROPDOWN_STYLE
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
        ], width=3),
        
        # Center column (charts & metrics)
        dbc.Col([
            # Row 1: Equity Curve
            dbc.Row([
                dbc.Col(html.Div(id="equity-curve-container"), className="mb-4")
            ]),
            # Row 2: Metrics
            dbc.Row([
                dbc.Col(html.Div(id="metrics-container"), className="mb-4")
            ]),
            # Row 3: Additional Charts
            dbc.Row([
                dbc.Col(html.Div(id="additional-charts"))
            ])
        ], width=6),
        
        # Right column (1/3)
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Trade History"),
                dbc.CardBody([
                    html.Div(id="trade-table-container")
                ])
            ], className="mb-4"),
            dbc.Card([
                dbc.CardHeader("Position Analysis"),
                dbc.CardBody([
                    html.Div(id="position-analysis")
                ])
            ])
        ], width=3)
    ])
], fluid=True, style={"backgroundColor": "#131722"})

@app.callback(
    [Output("calculation-status", "children"),
     Output("equity-curve-container", "children"),
     Output("metrics-container", "children"),
     Output("additional-charts", "children"),
     Output("trade-table-container", "children"),
     Output("backtest-period", "children"),
     Output("portfolio-instruments", "children")],
    [Input("strategy-selector", "value")]
)
def update_backtest(strategy):
    if not strategy:
        return "Please select a strategy", [], create_empty_cards(), [], "No trades available", "", ""
    
    try:
        data, results, stats = run_backtest(strategy)  # Placeholder for portfolio backtest
        
        if any(x is None for x in [data, results, stats]):
            return (
                html.Div("Error running backtest", className="text-danger"),
                [],
                create_empty_cards(),
                [],
                "No trades available",
                "",
                ""
            )
        
        # Create components
        equity_curve = create_chart(results, "Equity Curve")
        metric_cards = create_metric_cards(stats)
        additional_charts = create_charts(results)[1:]
        trade_table = create_trade_table(results.get('trades', []))
        
        return (
            html.Div("Calculation complete", className="text-success"),
            equity_curve,
            metric_cards,
            additional_charts,
            trade_table,
            "2021-01-01 to 2021-12-31",  # Placeholder for backtest period
            "AAPL, MSFT, GOOGL"  # Placeholder for portfolio instruments
        )
        
    except Exception as e:
        print(f"Error in callback: {str(e)}")
        return (
            html.Div(f"Error: {str(e)}", className="text-danger"),
            [],
            create_empty_cards(),
            [],
            "No trades available",
            "",
            ""
        )

def main():
    # Create strategy instance
    strategy = MovingAverageStrategy()  # or RSIStrategy() or BollingerBandsStrategy()
    
    # Initialize backtesting engine
    engine = BacktestEngine(strategy=strategy)
    
    # Run backtest for a ticker
    ticker = input("Enter ticker symbol: ")
    results = engine.run(ticker)
    
    # Print basic results
    print("\nBacktest Results:")
    print(f"Total Return: {(results['returns'] + 1).prod() - 1:.2%}")
    print(f"Benchmark Return: {(results['benchmark_returns'] + 1).prod() - 1:.2%}")

if __name__ == "__main__":
    main()
    app.run(debug=True)
