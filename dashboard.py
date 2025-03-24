import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import plotly.express as px
from src.backtest_engine import BacktestEngine
from src.strategy import MovingAverageCrossover, RSIStrategy, BollingerBandsStrategy
from src.data_loader import DataLoader

# Initialize Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "Backtesting Dashboard"

def create_metric_card(title, value, prefix="", suffix=""):
    """Create a styled metric card component"""
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-subtitle text-muted"),
            html.H4(f"{prefix}{value}{suffix}", className="card-title")
        ]),
        className="mb-3"
    )

def create_chart(figure_data, layout_title):
    """Create a styled chart component"""
    return dcc.Graph(
        figure={
            "data": figure_data,
            "layout": go.Layout(
                title=layout_title,
                template="plotly_white",
                hovermode='x unified',
                xaxis={"showgrid": True, "gridwidth": 1, "gridcolor": "LightGrey"},
                yaxis={"showgrid": True, "gridwidth": 1, "gridcolor": "LightGrey"},
                margin=dict(l=40, r=40, t=40, b=40)
            )
        }
    )

def load_backtest_results():
    """Load and process backtest results"""
    default_stats = {
        'initial_capital': 100000,
        'final_capital': 100000,
        'total_return': 0.0,
        'max_drawdown': 0.0,
        'sharpe_ratio': 0.0,
        'win_rate': 0.0,
        'total_trades': 0
    }
    
    try:
        data = DataLoader.load_data('data/historical_prices.csv', 'AAPL')
        strategy = MovingAverageCrossover(short_window=50, long_window=200)
        data = strategy.generate_signals(data)
        engine = BacktestEngine(initial_capital=100000)
        results = engine.run_backtest(data)
        
        # Initialize stats with default values
        stats = default_stats.copy()
        
        # Update with calculated values
        stats.update({
            'final_capital': results['Portfolio_Value'].iloc[-1],
            'total_return': ((results['Portfolio_Value'].iloc[-1] / 100000) - 1) * 100,
            'max_drawdown': ((results['Portfolio_Value'] - results['Portfolio_Value'].cummax()) / 
                            results['Portfolio_Value'].cummax()).min()
        })
        
        # Update with engine statistics if available
        engine_stats = engine.get_statistics()
        if engine_stats:
            stats.update(engine_stats)
        
        return data, results, stats
    except Exception as e:
        print(f"Error loading backtest results: {str(e)}")
        return None, None, default_stats

# Load data with error handling
data, results, stats = load_backtest_results()

# Dashboard layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Backtesting Dashboard", className="text-center my-4")
        ])
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Strategy Controls"),
                dbc.CardBody([
                    dbc.Select(
                        id="strategy-selector",
                        options=[
                            {"label": "Moving Average Crossover", "value": "MA"},
                            {"label": "RSI", "value": "RSI"},
                            {"label": "Bollinger Bands", "value": "BB"}
                        ],
                        value="MA"
                    ),
                    html.Div(id="strategy-params", className="mt-3")
                ])
            ], className="mb-4")
        ], width=12)
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col(create_metric_card("Initial Capital", f"${stats['initial_capital']:,.2f}")),
                dbc.Col(create_metric_card("Final Capital", f"${stats['final_capital']:,.2f}")),
                dbc.Col(create_metric_card("Total Return", f"{stats['total_return']:.2f}%")),
                dbc.Col(create_metric_card("Sharpe Ratio", f"{stats['sharpe_ratio']:.2f}"))
            ])
        ], width=12)
    ]),

    dbc.Row([
        dbc.Col([
            create_chart(
                [go.Scatter(
                    x=results.index,
                    y=results["Portfolio_Value"],
                    mode="lines",
                    name="Portfolio Value",
                    line=dict(color="#17B897")
                )],
                "Equity Curve"
            )
        ], width=8),
        dbc.Col([
            create_chart(
                [go.Bar(
                    x=["Wins", "Losses"],
                    y=[stats.get("win_rate", 0) * stats.get("total_trades", 0),
                       (1 - stats.get("win_rate", 0)) * stats.get("total_trades", 0)],
                    marker_color=["#17B897", "#FF6B6B"]
                )],
                "Trade Analytics"
            )
        ], width=4)
    ]),

    dbc.Row([
        dbc.Col([
            create_chart(
                [go.Scatter(
                    x=results.index,
                    y=(results["Portfolio_Value"] - results["Portfolio_Value"].cummax()) / 
                      results["Portfolio_Value"].cummax(),
                    mode="lines",
                    fill="tozeroy",
                    line=dict(color="#FF6B6B"),
                    name="Drawdown"
                )],
                "Drawdown"
            )
        ], width=12)
    ])
], fluid=True)

@app.callback(
    Output("strategy-params", "children"),
    Input("strategy-selector", "value")
)
def update_strategy_params(strategy):
    """Update strategy parameters based on selection"""
    if strategy == "MA":
        return dbc.Row([
            dbc.Col(dbc.Input(id="short-ma", type="number", value=50, placeholder="Short MA")),
            dbc.Col(dbc.Input(id="long-ma", type="number", value=200, placeholder="Long MA"))
        ])
    # Add other strategy parameters as needed
    return []

if __name__ == "__main__":
    app.run(debug=True)
