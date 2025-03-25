import dash
from dash import dcc, html, callback_context
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
from src.backtest_engine import BacktestEngine
from src.strategy import MovingAverageCrossover, RSIStrategy, BollingerBandsStrategy
from src.data_loader import DataLoader
from src.visualization import BacktestVisualizer, create_empty_chart
from src.metrics import (
    calculate_cagr, calculate_sharpe_ratio, calculate_sortino_ratio,
    calculate_max_drawdown, calculate_calmar_ratio, calculate_pure_profit_score
)
from src.portfolio.portfolio_manager import PortfolioManager
from src.portfolio.risk_manager import RiskManager
from src.analysis.trade_analyzer import TradeAnalyzer

# Initialize Dash app with dark theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "Trading Strategy Backtester"

# Default chart theme configuration
CHART_THEME = {
    'paper_bgcolor': '#1e222d',
    'plot_bgcolor': '#1e222d',
    'font_color': '#e1e1e1',
    'grid_color': '#2a2e39'
}

# Style dla dropdownów
DROPDOWN_STYLE = {
    'backgroundColor': '#1e222d',
    'color': '#e1e1e1',
    'option': {
        'backgroundColor': '#1e222d',
        'color': '#e1e1e1',
        'hover': '#2a2e39'
    }
}

# Available instruments
AVAILABLE_INSTRUMENTS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', '^GSPC']  # Add more as needed

def create_metric_card(title, value, prefix="", suffix=""):
    """Create a styled metric card component with dark theme"""
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-subtitle text-muted"),
            html.H4(f"{prefix}{value}{suffix}", className="card-title text-info")
        ]),
        className="mb-3 bg-dark"
    )

def create_chart(figure_data, layout_title):
    """Create a styled chart component"""
    # Zwracamy komponent Graph z figure jako props
    return dcc.Graph(
        id=f"chart-{layout_title}",  # Unique ID for each chart
        figure=figure_data if figure_data else create_empty_chart(layout_title),
        config={'displayModeBar': True}
    )

def run_backtest(ticker, strategy_type, strategy_params=None):
    """Run backtest with specified parameters"""
    try:
        # Load and validate source data
        source_data = DataLoader.load_data('data/historical_prices.csv', ticker)
        if source_data is None or len(source_data.index) == 0:
            raise ValueError("No data available for the selected instrument")
        
        source_data = source_data.ffill().bfill()
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
            
        # Generate signals and verify
        data = strategy.generate_signals(source_data)
        if 'Signal' not in data.columns:
            raise ValueError("Strategy failed to generate signals")
            
        # Run backtest
        engine = BacktestEngine(initial_capital=100000)
        results = engine.run_backtest(data)
        
        if not isinstance(results, pd.DataFrame) or len(results.index) == 0:
            raise ValueError("Backtest produced no results")
        
        # Calculate statistics
        portfolio_value = results['Portfolio_Value']
        if portfolio_value.isna().any():
            portfolio_value = portfolio_value.ffill().bfill()
            if portfolio_value.isna().any():
                raise ValueError("Invalid portfolio values")
        
        # Base statistics
        stats = {
            'initial_capital': 100000,
            'final_capital': float(portfolio_value.iloc[-1]),
            'total_return': ((float(portfolio_value.iloc[-1]) / 100000) - 1) * 100
        }
        
        # Additional metrics for valid data
        if len(source_data) >= 2:
            returns = source_data['Close'].pct_change().dropna()
            if len(returns) >= 2:
                metrics = {
                    'cagr': calculate_cagr(source_data['Close']) * 100,
                    'sharpe_ratio': calculate_sharpe_ratio(returns),
                    'sortino_ratio': calculate_sortino_ratio(returns),
                    'max_drawdown': calculate_max_drawdown(portfolio_value, method='percent') * 100,
                    'calmar_ratio': calculate_calmar_ratio(returns),
                    'pure_profit_score': calculate_pure_profit_score(returns)
                }
                stats.update(metrics)
        
        # Add engine statistics
        engine_stats = engine.get_statistics()
        if engine_stats:
            stats.update(engine_stats)
            
        return data, results, stats
            
    except Exception as e:
        print(f"Backtest error: {str(e)}")
        return None, None, None

def create_metric_cards(stats):
    """Create metric cards layout with advanced metrics"""
    return dbc.Row([
        dbc.Col([
            create_metric_card("CAGR", f"{stats['cagr']:.2f}%"),
            create_metric_card("Sharpe Ratio", f"{stats['sharpe_ratio']:.2f}"),
            create_metric_card("Sortino Ratio", f"{stats['sortino_ratio']:.2f}"),
        ]),
        dbc.Col([
            create_metric_card("Max Drawdown", f"{stats['max_drawdown']:.2f}%"),
            create_metric_card("Calmar Ratio", f"{stats['calmar_ratio']:.2f}"),
            create_metric_card("Pure Profit Score", f"{stats['pure_profit_score']:.2f}"),
        ]),
        dbc.Col([
            create_metric_card("Total Return", f"{stats['total_return']:.2f}%"),
            create_metric_card("Win Rate", f"{stats['win_rate']:.2f}%"),
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
        dbc.Col(create_metric_card("Sharpe Ratio", "N/A"))
    ])

def create_trade_table(trades):
    """Create trade history table"""
    if not trades:
        return html.Div("No trades available")
        
    df = pd.DataFrame([vars(t) for t in trades])
    return dash_table.DataTable(
        id='trade-table',
        columns=[
            {"name": "Entry Date", "id": "entry_date"},
            {"name": "Exit Date", "id": "exit_date"},
            {"name": "Symbol", "id": "ticker"},
            {"name": "Direction", "id": "direction"},
            {"name": "Entry", "id": "entry_price"},
            {"name": "Exit", "id": "exit_price"},
            {"name": "P&L", "id": "pnl"},
            {"name": "Return %", "id": "return_pct"}
        ],
        data=df.to_dict('records'),
        style_table={'overflowX': 'auto'},
        style_cell={
            'backgroundColor': '#1e222d',
            'color': '#e1e1e1'
        },
        style_header={
            'backgroundColor': '#2a2e39',
            'fontWeight': 'bold'
        }
    )

# Update layout to include containers for metric cards and charts
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Trading Strategy Backtester", className="text-center my-4")
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
                            html.Label("Select Instrument"),
                            dcc.Dropdown(
                                id="instrument-selector",
                                options=[{"label": i, "value": i} for i in AVAILABLE_INSTRUMENTS],
                                value="AAPL",
                                className="mb-3 dropdown-dark",
                                style=DROPDOWN_STYLE
                            )
                        ], width=12),
                        dbc.Col([
                            html.Label("Select Strategy"),
                            dcc.Dropdown(
                                id="strategy-selector",
                                options=[
                                    {"label": "Bollinger Bands", "value": "BB"},
                                    {"label": "Moving Average Crossover", "value": "MA"},
                                    {"label": "RSI", "value": "RSI"}
                                ],
                                value="BB",
                                className="mb-3 dropdown-dark",
                                style=DROPDOWN_STYLE
                            )
                        ], width=12)
                    ]),
                    html.Div(id="strategy-params", className="mt-3"),
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
     Output("trade-table-container", "children")],
    [Input("instrument-selector", "value"),
     Input("strategy-selector", "value")]
)
def update_backtest(instrument, strategy):
    if not instrument or not strategy:
        return "Please select an instrument and strategy", [], create_empty_cards(), [], "No trades available"
    
    try:
        data, results, stats = run_backtest(instrument, strategy)
        
        if any(x is None for x in [data, results, stats]):
            return (
                html.Div("Error running backtest", className="text-danger"),
                [],
                create_empty_cards(),
                [],
                "No trades available"
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
            trade_table
        )
        
    except Exception as e:
        print(f"Error in callback: {str(e)}")
        return (
            html.Div(f"Error: {str(e)}", className="text-danger"),
            [],
            create_empty_cards(),
            [],
            "No trades available"
        )

if __name__ == "__main__":
    app.run(debug=True)
