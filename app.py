import dash
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import sys
import traceback
from pathlib import Path
import logging

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backtest.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.append(str(project_root))

# Now import local modules
from src.core.config import config
from src.core.constants import AVAILABLE_STRATEGIES, CHART_THEME
from src.core.data import DataLoader
from src.core.backtest_manager import BacktestManager
from src.visualization.visualizer import BacktestVisualizer
from src.visualization.chart_utils import create_styled_chart, create_empty_chart, create_trade_histogram_figure
from src.ui.components import create_metric_card, create_metric_card_with_tooltip
from src.analysis.metrics import (
    calculate_trade_statistics, calculate_alpha, calculate_beta, 
    calculate_information_ratio, calculate_recovery_factor
)

# Initialize Dash app with dark theme
app = dash.Dash(
    __name__, 
    external_stylesheets=[
        dbc.themes.DARKLY,
        'https://use.fontawesome.com/releases/v5.15.4/css/all.css'
    ],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)
app.title = "Trading Strategy Backtester"
server = app.server  # For production deployment

# Initialize BacktestManager for handling all backtest operations
backtest_manager = BacktestManager(initial_capital=10000)

# Initialize visualizer
visualizer = BacktestVisualizer()

def create_empty_cards():
    """Create empty metric cards"""
    return dbc.Row([
        dbc.Col(create_metric_card("Initial Capital", "N/A")),
        dbc.Col(create_metric_card("Final Capital", "N/A")),
        dbc.Col(create_metric_card("Total Return", "N/A")),
        dbc.Col(create_metric_card("Total Trades", "N/A"))
    ])

def create_metric_cards(stats):
    """Create metric cards layout with advanced metrics and tooltips"""
    tooltip_texts = {
        'Initial Capital': "Starting capital at the beginning of the backtest period.",
        'Final Capital': "Ending portfolio value at the end of the backtest period.",
        'CAGR': "Compound Annual Growth Rate. Measures the mean annual growth rate of an investment over a specified time period longer than one year.",
        'Total Return': "The overall return of the portfolio from start to finish, expressed as a percentage of initial capital.",
        'Max Drawdown': "Largest peak-to-trough decline in portfolio value, expressed as a percentage. Measures the biggest historical loss.",
        'Sharpe Ratio': "Risk-adjusted return metric. Calculated as (Portfolio Return - Risk Free Rate) / Portfolio Standard Deviation. Assumes 2% Risk Free Rate.",
        'Sortino Ratio': "Similar to Sharpe ratio but only penalizes downside volatility. Calculated using 2% Risk Free Rate.",
        'Information Ratio': "Measures portfolio returns above the benchmark per unit of risk. Higher values indicate better risk-adjusted performance vs benchmark.",
        'Alpha': "Excess return of the investment relative to the return of the benchmark index. Expressed as percentage points.",
        'Beta': "Measure of portfolio's volatility compared to the market. Beta > 1 means more volatile than market, Beta < 1 means less volatile.",
        'Recovery Factor': "Absolute value of total profit divided by maximum drawdown. Higher values indicate better recovery from drawdowns."
    }
    
    # Calculate additional metrics
    alpha = calculate_alpha(stats.get('Portfolio_Value'), stats.get('Benchmark', None))
    beta = calculate_beta(stats.get('Portfolio_Value'), stats.get('Benchmark', None))
    info_ratio = calculate_information_ratio(stats.get('Portfolio_Value'), stats.get('Benchmark', None))
    recovery_factor = calculate_recovery_factor(
        stats.get('total_return', 0), 
        stats.get('max_drawdown', 1)
    )
    
    # Get initial and final capital values
    initial_capital = config.INITIAL_CAPITAL
    portfolio_values = stats.get('Portfolio_Value')
    final_capital = portfolio_values.iloc[-1] if portfolio_values is not None and len(portfolio_values) > 0 else initial_capital

    return dbc.Row([
        # First row - Capital metrics
        dbc.Col([
            create_metric_card_with_tooltip("Initial Capital", f"${initial_capital:,.2f}", tooltip_texts['Initial Capital']),
            create_metric_card_with_tooltip("Final Capital", f"${final_capital:,.2f}", tooltip_texts['Final Capital'])
        ], width=12, className="mb-3"),
        
        # Second row - Performance metrics
        dbc.Row([
            dbc.Col([
                create_metric_card_with_tooltip("CAGR", f"{stats.get('cagr', 0):.2f}%", tooltip_texts['CAGR']),
                create_metric_card_with_tooltip("Total Return", f"{stats.get('total_return', 0):.2f}%", tooltip_texts['Total Return']),
                create_metric_card_with_tooltip("Alpha", f"{alpha:.2f}%", tooltip_texts['Alpha'])
            ], width=4),
            dbc.Col([
                create_metric_card_with_tooltip("Max Drawdown", f"{stats.get('max_drawdown', 0):.2f}%", tooltip_texts['Max Drawdown']),
                create_metric_card_with_tooltip("Sharpe Ratio", f"{stats.get('sharpe_ratio', 0):.2f}", tooltip_texts['Sharpe Ratio']),
                create_metric_card_with_tooltip("Beta", f"{beta:.2f}", tooltip_texts['Beta'])
            ], width=4),
            dbc.Col([
                create_metric_card_with_tooltip("Info Ratio", f"{info_ratio:.2f}", tooltip_texts['Information Ratio']),
                create_metric_card_with_tooltip("Sortino Ratio", f"{stats.get('sortino_ratio', 0):.2f}", tooltip_texts['Sortino Ratio']),
                create_metric_card_with_tooltip("Recovery Factor", f"{recovery_factor:.2f}", tooltip_texts['Recovery Factor'])
            ], width=4)
        ])
    ])

def create_trade_histogram(trades):
    """Create enhanced trade return distribution histogram with statistics"""
    if not trades:
        return html.Div("No trades available")
    
    # Calculate trade statistics
    stats = calculate_trade_statistics(trades)
    
    # Create histogram figure
    histogram = create_trade_histogram_figure(trades, stats)
    
    # Define tooltips for each metric
    tooltip_texts = {
        'Win Rate': "Percentage of trades that resulted in a profit. Calculated as (Winning Trades / Total Trades) × 100.",
        'Total Trades': "Total number of completed trades (both winners and losers).",
        'Profit Factor': "Ratio of gross profits to gross losses. A value above 1 indicates overall profitability. Calculated as |Total Profits / Total Losses|.",
        'Avg Win': "Average profit of winning trades in dollar terms.",
        'Largest Win': "Largest single trade profit in dollar terms.",
        'Winning Trades': "Total number of trades that resulted in a profit.",
        'Avg Loss': "Average loss of losing trades in dollar terms.",
        'Largest Loss': "Largest single trade loss in dollar terms.",
        'Losing Trades': "Total number of trades that resulted in a loss."
    }
    
    # Create statistics table with tooltips
    stats_table = html.Div([
        dbc.Row([
            dbc.Col([
                create_metric_card_with_tooltip("Total Trades", f"{stats['total_trades']}", tooltip_texts['Total Trades']),
                create_metric_card_with_tooltip("Profit Factor", f"{stats['profit_factor']:.2f}", tooltip_texts['Profit Factor']),
                create_metric_card_with_tooltip("Win Rate", f"{stats['win_rate']:.1f}%", tooltip_texts['Win Rate'])
            ], width=4),
            dbc.Col([
                create_metric_card_with_tooltip("Avg Win", f"${stats['avg_win_pnl']:.2f}", tooltip_texts['Avg Win']),
                create_metric_card_with_tooltip("Largest Win", f"${stats['largest_win']:.2f}", tooltip_texts['Largest Win']),
                create_metric_card_with_tooltip("Winning Trades", f"{stats['winning_trades']}", tooltip_texts['Winning Trades'])
            ], width=4),
            dbc.Col([
                create_metric_card_with_tooltip("Avg Loss", f"${stats['avg_loss_pnl']:.2f}", tooltip_texts['Avg Loss']),
                create_metric_card_with_tooltip("Largest Loss", f"${stats['largest_loss']:.2f}", tooltip_texts['Largest Loss']),
                create_metric_card_with_tooltip("Losing Trades", f"{stats['losing_trades']}", tooltip_texts['Losing Trades'])
            ], width=4)
        ], className="mt-3")
    ])
    
    return html.Div([
        histogram,
        stats_table
    ])

def create_trade_table(trades):
    """Create unified trade history table with error handling"""
    if not trades:
        return html.Div("No trades available")
    
    trade_records = []
    for trade in trades:
        try:
            # Validate trade data
            if not isinstance(trade, dict):
                continue
                
            # Required fields with fallbacks
            entry_date = pd.to_datetime(trade.get('entry_date', pd.NaT))
            exit_date = pd.to_datetime(trade.get('exit_date', pd.NaT))
            ticker = trade.get('ticker', '')
            direction = trade.get('direction', '')
            shares = int(trade.get('shares', 0))
            entry_price = float(trade.get('entry_price', 0))
            exit_price = float(trade.get('exit_price', 0))
            pnl = float(trade.get('pnl', 0))
            
            # Skip invalid trades
            if pd.isna(entry_date) or pd.isna(exit_date) or shares <= 0:
                continue
                
            # Format for display
            record = {
                'Date In': entry_date.strftime('%Y-%m-%d'),
                'Date Out': exit_date.strftime('%Y-%m-%d'),
                'Ticker': ticker,
                'Type': direction,
                'Shares': f"{shares:,}",
                'Entry': f"${entry_price:.2f}",
                'Exit': f"${exit_price:.2f}",
                'P&L': f"${pnl:.2f}",
                'Return': f"{(pnl / (entry_price * shares) * 100):.1f}%" if entry_price * shares != 0 else "N/A"
            }
            trade_records.append(record)
        except (KeyError, ValueError, TypeError, AttributeError) as e:
            logger.error(f"Error processing trade for table: {e}")
            continue
    
    if not trade_records:
        return html.Div("No valid trades to display")
    
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
            'maxWidth': '100px',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'textAlign': 'left',
            'padding': '8px 12px'
        },
        style_cell_conditional=[
            {'if': {'column_id': 'Date In'}, 'width': '90px'},
            {'if': {'column_id': 'Date Out'}, 'width': '90px'},
            {'if': {'column_id': 'Ticker'}, 'width': '70px'},
            {'if': {'column_id': 'Type'}, 'width': '70px'},
            {'if': {'column_id': 'Shares'}, 'width': '80px'},
            {'if': {'column_id': 'Entry'}, 'width': '90px'},
            {'if': {'column_id': 'Exit'}, 'width': '90px'},
            {'if': {'column_id': 'P&L'}, 'width': '90px'},
            {'if': {'column_id': 'Return'}, 'width': '80px'}
        ],
        style_data={
            'whiteSpace': 'nowrap',
            'height': '30px',
            'lineHeight': '30px'
        },
        style_header={
            'backgroundColor': '#2a2e39',
            'fontWeight': 'bold',
            'border': '1px solid #2a2e39',
            'whiteSpace': 'nowrap',
            'height': '40px'
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

def run_backtest(strategy_type, strategy_params=None):
    """Run backtest with specified parameters"""
    try:
        signals, combined_results, stats = backtest_manager.run_backtest(
            strategy_type, **(strategy_params or {})
        )
        return signals, combined_results, stats
    except Exception as e:
        logger.error(f"Backtest error: {str(e)}")
        traceback.print_exc()
        return None, None, None

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Portfolio Backtester", className="text-center my-4")
        ])
    ]),

    dbc.Row([
        # Left column (Strategy Settings)
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
        ], width=2),
        
        # Center column (Equity Curve)
        dbc.Col([
            dbc.Row([
                dbc.Col(html.Div(id="equity-curve-container", style={"height": "450px"}), className="mb-5")
            ]),
            dbc.Row([
                dbc.Col(html.Div(id="metrics-container"), className="mb-5")
            ]),
            dbc.Row([
                dbc.Col(html.Div(id="additional-charts"))
            ])
        ], width=6),
        
        # Right column (Trade Distribution & History)
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
        ], width=4)
    ])
], fluid=True, style={"backgroundColor": "#131722"})

@app.callback(
    [Output("calculation-status", "children"),
     Output("equity-curve-container", "children"),
     Output("metrics-container", "children"),
     Output("additional-charts", "children"),
     Output("trade-distribution-container", "children"),
     Output("trade-table-container", "children"),
     Output("backtest-period", "children"),
     Output("portfolio-instruments", "children")],
    [Input("strategy-selector", "value")]
)
def update_backtest(strategy):
    # Add input validation
    if not strategy or strategy not in ["MA", "RSI", "BB"]:
        return (
            html.Div("Please select a valid strategy", className="text-warning"),
            [],
            create_empty_cards(),
            [],
            html.Div("No trades available"),
            html.Div("No trades available"),
            "",
            ""
        )
    
    try:
        signals, results, stats = run_backtest(strategy)
        
        if any(x is None for x in [signals, results, stats]):
            return (
                html.Div("Error running backtest", className="text-danger"),
                [],
                create_empty_cards(),
                [],
                html.Div("No trades available"),
                html.Div("No trades available"),
                "",
                ""
            )
            
        # Debug print statements to track progress
        logger.info(f"Backtest completed for {strategy}")
        logger.info(f"Results keys: {list(results.keys())}")
        logger.info(f"Number of trades: {len(results.get('trades', []))}")
        
        # Create equity curve with better error handling
        portfolio_chart = create_styled_chart({
            'Portfolio': results.get('Portfolio_Value', pd.Series()),
            'Benchmark': results.get('Benchmark', pd.Series())
        }, "Portfolio Performance")
        
        # Create metric cards with stats
        metrics = create_metric_cards(stats)
        
        # Process trades with better error handling
        trades = results.get('trades', [])
        
        # Create trade distribution if trades exist
        trade_dist = create_trade_histogram(trades)
        
        # Create trade table if trades exist
        trade_history = create_trade_table(trades)
        
        # Get backtest period with error handling
        portfolio_series = results.get('Portfolio_Value', pd.Series())
        if len(portfolio_series) > 0:
            start_date = portfolio_series.index[0].strftime('%Y-%m-%d')
            end_date = portfolio_series.index[-1].strftime('%Y-%m-%d')
            backtest_period = f"{start_date} to {end_date}"
        else:
            backtest_period = "N/A"
        
        # Get portfolio instruments
        instruments = ", ".join(sorted(signals.keys()))
        
        return (
            html.Div("Backtest completed successfully", className="text-success"),
            portfolio_chart,
            metrics,
            [],  # No additional charts needed
            trade_dist,
            trade_history,
            backtest_period,
            instruments
        )
        
    except Exception as e:
        logger.error(f"Callback error: {str(e)}")
        traceback.print_exc()
        return (
            html.Div(f"Error: {str(e)}", className="text-danger"),
            [],
            create_empty_cards(),
            [],
            html.Div("No trades available"),
            html.Div("No trades available"),
            "",
            ""
        )

if __name__ == "__main__":
    app.run(debug=True)
