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
import plotly.graph_objects as go

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

    return html.Div([
        # First row - Capital metrics side by side with minimal spacing
        dbc.Row([
            dbc.Col(create_metric_card_with_tooltip("Initial Capital", f"${initial_capital:,.2f}", tooltip_texts['Initial Capital']), width=6, className="px-1"),
            dbc.Col(create_metric_card_with_tooltip("Final Capital", f"${final_capital:,.2f}", tooltip_texts['Final Capital']), width=6, className="px-1")
        ], className="g-0 mb-1"),  # Reduced gutters and margin
        
        # Performance metrics in a very compact grid
        dbc.Row([
            dbc.Col([
                create_metric_card_with_tooltip("CAGR", f"{stats.get('cagr', 0):.2f}%", tooltip_texts['CAGR']),
                create_metric_card_with_tooltip("Total Return", f"{stats.get('total_return', 0):.2f}%", tooltip_texts['Total Return']),
                create_metric_card_with_tooltip("Alpha", f"{alpha:.2f}%", tooltip_texts['Alpha'])
            ], width=4, className="px-1 py-0"),  # Reduced padding
            dbc.Col([
                create_metric_card_with_tooltip("Max Drawdown", f"{stats.get('max_drawdown', 0):.2f}%", tooltip_texts['Max Drawdown']),
                create_metric_card_with_tooltip("Sharpe Ratio", f"{stats.get('sharpe_ratio', 0):.2f}", tooltip_texts['Sharpe Ratio']),
                create_metric_card_with_tooltip("Beta", f"{beta:.2f}", tooltip_texts['Beta'])
            ], width=4, className="px-1 py-0"),  # Reduced padding
            dbc.Col([
                create_metric_card_with_tooltip("Info Ratio", f"{info_ratio:.2f}", tooltip_texts['Information Ratio']),
                create_metric_card_with_tooltip("Sortino Ratio", f"{stats.get('sortino_ratio', 0):.2f}", tooltip_texts['Sortino Ratio']),
                create_metric_card_with_tooltip("Recovery Factor", f"{recovery_factor:.2f}", tooltip_texts['Recovery Factor'])
            ], width=4, className="px-1 py-0")  # Reduced padding
        ], className="g-0")  # No gutters between columns
    ], className="mb-1")  # Reduced bottom margin

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
    
    # Create compact statistics table with tooltips (with all original metrics but tighter spacing)
    stats_table = html.Div([
        dbc.Row([
            dbc.Col(create_metric_card_with_tooltip("Total Trades", f"{stats['total_trades']}", tooltip_texts['Total Trades']), width=4, className="px-1"),
            dbc.Col(create_metric_card_with_tooltip("Win Rate", f"{stats['win_rate']:.1f}%", tooltip_texts['Win Rate']), width=4, className="px-1"),
            dbc.Col(create_metric_card_with_tooltip("Profit Factor", f"{stats['profit_factor']:.2f}", tooltip_texts['Profit Factor']), width=4, className="px-1")
        ], className="g-0 mb-1"),  # Reduced gutters and margin
        dbc.Row([
            dbc.Col(create_metric_card_with_tooltip("Winning Trades", f"{stats['winning_trades']}", tooltip_texts['Winning Trades']), width=4, className="px-1"),
            dbc.Col(create_metric_card_with_tooltip("Losing Trades", f"{stats['losing_trades']}", tooltip_texts['Losing Trades']), width=4, className="px-1"),
            dbc.Col(create_metric_card_with_tooltip("Largest Win", f"${stats['largest_win']:.2f}", tooltip_texts['Largest Win']), width=4, className="px-1")
        ], className="g-0 mb-1"),  # Reduced gutters and margin
        dbc.Row([
            dbc.Col(create_metric_card_with_tooltip("Avg Win", f"${stats['avg_win_pnl']:.2f}", tooltip_texts['Avg Win']), width=4, className="px-1"),
            dbc.Col(create_metric_card_with_tooltip("Avg Loss", f"${stats['avg_loss_pnl']:.2f}", tooltip_texts['Avg Loss']), width=4, className="px-1"),
            dbc.Col(create_metric_card_with_tooltip("Largest Loss", f"${stats['largest_loss']:.2f}", tooltip_texts['Largest Loss']), width=4, className="px-1")
        ], className="g-0")  # Reduced gutters
    ], className="mt-2")  # Small margin at top
    
    return html.Div([
        histogram,
        stats_table
    ], className="pb-0")  # Reduced padding

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

def create_allocation_chart(results):
    """Create portfolio allocation chart showing position values and cash over time"""
    if not results or 'trades' not in results:
        return html.Div("No allocation data available")
    
    # Get trade and portfolio data
    trades = results.get('trades', [])
    portfolio_series = results.get('Portfolio_Value', pd.Series())
    
    if len(trades) == 0 or len(portfolio_series) == 0:
        return html.Div("No allocation data available")
    
    # Add log to check what we're receiving
    logger.info(f"Creating allocation chart with {len(trades)} trades")
    
    # Get unique tickers from trades
    tickers = list(set(trade.get('ticker', '') for trade in trades if trade.get('ticker')))
    logger.info(f"Found tickers: {tickers}")
    
    # Create DataFrame to track positions for each ticker
    positions_df = pd.DataFrame(index=portfolio_series.index)
    
    # Fill positions with zeros - AS FLOAT (fixes type mismatch error)
    for ticker in tickers:
        positions_df[ticker] = 0.0
    
    # Add column for cash, starting with full initial capital - AS FLOAT
    positions_df['Cash'] = float(config.INITIAL_CAPITAL)
    
    # Update positions based on trades
    for trade in trades:
        try:
            entry_date = pd.to_datetime(trade.get('entry_date'))
            exit_date = pd.to_datetime(trade.get('exit_date'))
            ticker = trade.get('ticker', '')
            shares = float(trade.get('shares', 0))  # Convert to float
            entry_price = float(trade.get('entry_price', 0))
            exit_price = float(trade.get('exit_price', 0))
            
            if ticker not in tickers or entry_date is None or exit_date is None:
                continue
            
            # Find indices for entry and exit dates
            try:
                # Make sure dates are within index range
                if entry_date < positions_df.index[0] or entry_date > positions_df.index[-1]:
                    continue
                if exit_date < positions_df.index[0] or exit_date > positions_df.index[-1]:
                    continue
                    
                entry_idx = positions_df.index.get_indexer([entry_date], method='ffill')[0]
                exit_idx = positions_df.index.get_indexer([exit_date], method='ffill')[0]
            except Exception as e:
                logger.error(f"Date indexing error: {e}")
                continue
                
            # Subtract cost from cash at entry
            cost = shares * entry_price
            positions_df.iloc[entry_idx:, positions_df.columns.get_loc('Cash')] -= cost
            
            # Add shares to ticker position
            if ticker in positions_df.columns:
                positions_df.iloc[entry_idx:exit_idx+1, positions_df.columns.get_loc(ticker)] += shares
            
            # Add proceeds to cash after exit
            proceeds = shares * exit_price
            positions_df.iloc[exit_idx:, positions_df.columns.get_loc('Cash')] += proceeds
                
        except Exception as e:
            logger.error(f"Error processing trade for allocation chart: {e}")
            continue
    
    # Create columns with position values
    # Get closing prices for each ticker from data
    price_data = {}
    for ticker in tickers:
        try:
            # First try to get last price from trades
            last_price = None
            for trade in reversed(trades):
                if trade.get('ticker') == ticker:
                    last_price = trade.get('exit_price')
                    break
                    
            if last_price is not None:
                # Create constant series with this price
                price_data[ticker] = pd.Series([last_price] * len(positions_df.index), index=positions_df.index)
        except Exception as e:
            logger.error(f"Error getting price data for {ticker}: {e}")
    
    # Calculate value for each position
    value_columns = []
    for ticker in tickers:
        if ticker in price_data:
            positions_df[f'{ticker}_value'] = positions_df[ticker] * price_data[ticker]
            value_columns.append(ticker)
    
    # Prepare values for visualization
    values_df = pd.DataFrame(index=positions_df.index)
    values_df['Cash'] = positions_df['Cash'].clip(lower=0)  # Avoid negative values
    
    for ticker in tickers:
        if f'{ticker}_value' in positions_df.columns:
            values_df[ticker] = positions_df[f'{ticker}_value'].clip(lower=0)
    
    # Calculate sum and percentage values
    values_df['Total'] = values_df.sum(axis=1)
    
    # Create copy for percentages
    percentage_df = pd.DataFrame(index=values_df.index)
    for col in values_df.columns:
        if col != 'Total':
            percentage_df[col] = (values_df[col] / values_df['Total'] * 100).fillna(0)
    
    # Check if we have data to visualize
    if len(value_columns) == 0 and values_df['Cash'].sum() == 0:
        return html.Div("Insufficient data for allocation chart")
    
    # Create area charts
    traces_values = []
    traces_percentage = []
    
    colors = ['#17B897', '#FF6B6B', '#36A2EB', '#FFCE56', '#4BC0C0', 
              '#9966FF', '#FF9F40', '#8CD867', '#EA526F', '#9CAFB7']
    
    # Value chart
    for i, col in enumerate(value_columns + ['Cash']):
        if col in values_df.columns:
            color = colors[i % len(colors)]
            traces_values.append(
                go.Scatter(
                    x=values_df.index,
                    y=values_df[col],
                    name=col,
                    mode='lines',
                    line=dict(width=0.5),
                    stackgroup='one',
                    fillcolor=color,
                    hovertemplate='%{y:$,.2f}<extra>%{x|%Y-%m-%d}: ' + col + '</extra>'
                )
            )
    
    # Percentage chart
    for i, col in enumerate(value_columns + ['Cash']):
        if col in percentage_df.columns:
            color = colors[i % len(colors)]
            traces_percentage.append(
                go.Scatter(
                    x=percentage_df.index,
                    y=percentage_df[col],
                    name=col,
                    mode='lines',
                    line=dict(width=0.5),
                    stackgroup='one',
                    fillcolor=color,
                    hovertemplate='%{y:.1f}%<extra>%{x|%Y-%m-%d}: ' + col + '</extra>'
                )
            )
    
    # Layout for value chart
    fig_values = go.Figure(data=traces_values)
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
    fig_percentage = go.Figure(data=traces_percentage)
    fig_percentage.update_layout(
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
    
    return html.Div([
        dcc.Graph(figure=fig_values, config={'displayModeBar': False}),
        dcc.Graph(figure=fig_percentage, config={'displayModeBar': False})
    ])

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
        
        # Center column (Equity Curve & Portfolio Composition)
        dbc.Col([
            dbc.Row([
                dbc.Col(html.Div(id="equity-curve-container", style={"height": "400px"}), className="mb-3")
            ]),
            dbc.Row([
                dbc.Col(html.Div(id="metrics-container"), className="mb-3")
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Portfolio Composition"),
                        dbc.CardBody([
                            html.Div(id="portfolio-composition-container")
                        ])
                    ])
                ])
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
                ], className="p-2")  # Reduced padding
            ], className="mb-3"),  # Reduced margin
            dbc.Card([
                dbc.CardHeader("Trade History"),
                dbc.CardBody([
                    html.Div(id="trade-table-container")
                ], className="p-2")  # Reduced padding
            ])
        ], width=4)
    ], className="g-2")  # Reduced gutters
], fluid=True, style={"backgroundColor": "#131722"})

@app.callback(
    [Output("calculation-status", "children"),
     Output("equity-curve-container", "children"),
     Output("metrics-container", "children"),
     Output("additional-charts", "children"),
     Output("trade-distribution-container", "children"),
     Output("trade-table-container", "children"),
     Output("backtest-period", "children"),
     Output("portfolio-instruments", "children"),
     Output("portfolio-composition-container", "children")],  # New output
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
            "",
            html.Div("No allocation data available")  # Empty portfolio composition
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
                "",
                html.Div("No allocation data available")  # Empty portfolio composition
            )
        
        # Create equity curve
        portfolio_chart = create_styled_chart({
            'Portfolio': results.get('Portfolio_Value', pd.Series()),
            'Benchmark': results.get('Benchmark', pd.Series())
        }, "Portfolio Performance")
        
        # Create metric cards
        metrics = create_metric_cards(stats)
        
        # Process trades
        trades = results.get('trades', [])
        trade_dist = create_trade_histogram(trades)
        trade_history = create_trade_table(trades)
        
        # Create portfolio composition chart
        portfolio_composition = create_allocation_chart(results)
        
        # Get backtest period
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
            [],
            trade_dist,
            trade_history,
            backtest_period,
            instruments,
            portfolio_composition  # Portfolio composition chart
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
            "",
            html.Div("No allocation data available")  # Empty portfolio composition
        )

if __name__ == "__main__":
    app.run(debug=True)
