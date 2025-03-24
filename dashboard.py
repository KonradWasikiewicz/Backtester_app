import dash
from dash import dcc, html, callback_context
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from src.backtest_engine import BacktestEngine
from src.strategy import MovingAverageCrossover, RSIStrategy, BollingerBandsStrategy
from src.data_loader import DataLoader
from src.visualization import BacktestVisualizer, create_empty_chart

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
        data = DataLoader.load_data('data/historical_prices.csv', ticker)
        
        # Default to Bollinger Bands if no strategy specified
        if strategy_type == "BB" or not strategy_type:
            strategy = BollingerBandsStrategy(window=20, num_std=2)
        elif strategy_type == "MA":
            strategy = MovingAverageCrossover(
                short_window=strategy_params.get('short_window', 50),
                long_window=strategy_params.get('long_window', 200)
            )
        elif strategy_type == "RSI":
            strategy = RSIStrategy(period=strategy_params.get('period', 14))
            
        data = strategy.generate_signals(data)
        engine = BacktestEngine(initial_capital=100000)
        results = engine.run_backtest(data)
        
        # Calculate statistics
        stats = {
            'initial_capital': 100000,
            'final_capital': results['Portfolio_Value'].iloc[-1],
            'total_return': ((results['Portfolio_Value'].iloc[-1] / 100000) - 1) * 100,
            'max_drawdown': ((results['Portfolio_Value'] - results['Portfolio_Value'].cummax()) / 
                            results['Portfolio_Value'].cummax()).min(),
            'sharpe_ratio': 0.0,
            'win_rate': 0.0,
            'total_trades': 0
        }
        
        engine_stats = engine.get_statistics()
        if engine_stats:
            stats.update(engine_stats)
            
        return data, results, stats
    except Exception as e:
        print(f"Backtest error: {str(e)}")
        return None, None, None

def create_metric_cards(stats):
    """Create metric cards layout"""
    return dbc.Row([
        dbc.Col(create_metric_card("Initial Capital", f"${stats['initial_capital']:,.2f}")),
        dbc.Col(create_metric_card("Final Capital", f"${stats['final_capital']:,.2f}")),
        dbc.Col(create_metric_card("Total Return", f"{stats['total_return']:.2f}%")),
        dbc.Col(create_metric_card("Sharpe Ratio", f"{stats['sharpe_ratio']:.2f}"))
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

# Update layout to include containers for metric cards and charts
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Trading Strategy Backtester", className="text-center my-4")
        ])
    ]),

    dbc.Row([
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
                        ], width=6),
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
                        ], width=6)
                    ]),
                    html.Div(id="strategy-params", className="mt-3"),
                    dbc.Spinner(html.Div(id="calculation-status"))
                ])
            ], className="mb-4")
        ], width=12)
    ]),
    
    html.Div(id="metric-cards"),
    html.Div(id="charts"),
    
], fluid=True, style={"backgroundColor": "#131722"})

@app.callback(
    [Output("calculation-status", "children"),
     Output("metric-cards", "children"),
     Output("charts", "children")],
    [Input("instrument-selector", "value"),
     Input("strategy-selector", "value")]
)
def update_backtest(instrument, strategy):
    """Update backtest results when instrument or strategy changes"""
    if not instrument:
        return "Please select an instrument", create_empty_cards(), []
    
    try:
        # Show loading status
        status = html.Div("Calculating...", className="text-info")
        
        # Run backtest
        data, results, stats = run_backtest(instrument, strategy)
        
        if data is None or results is None:
            return (
                html.Div("Error running backtest", className="text-danger"),
                create_empty_cards(),
                [create_empty_chart("No Data Available")]
            )
        
        # Update components
        metric_cards = create_metric_cards(stats)
        charts = create_charts(results)
        
        return (
            html.Div("Calculation complete", className="text-success"),
            metric_cards,
            charts
        )
        
    except Exception as e:
        return (
            html.Div(f"Error: {str(e)}", className="text-danger"),
            create_empty_cards(),
            [create_empty_chart("Error Running Backtest")]
        )

if __name__ == "__main__":
    app.run(debug=True)
