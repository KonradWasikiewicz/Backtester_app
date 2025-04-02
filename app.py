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

# Add this function at the beginning of the file (or in a utils section)

def get_available_tickers():
    """Dynamically load available tickers from CSV files, excluding benchmark"""
    import os
    import pandas as pd
    
    # Path to data directory
    data_dir = "data"
    
    # Get list of CSV files
    tickers = set()
    benchmark_ticker = "SPY"  # Define your benchmark ticker here to exclude it
    
    try:
        # Scan the data directory for CSV files
        for file in os.listdir(data_dir):
            if file.endswith('.csv'):
                ticker = file.split('.')[0]  # Extract ticker from filename
                if ticker != benchmark_ticker:
                    tickers.add(ticker)
    except Exception as e:
        logger.error(f"Error loading tickers from CSV: {e}")
    
    # Return list of unique tickers
    return sorted(list(tickers))

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

# Reduce verbosity for specific modules
logging.getLogger('src.portfolio.portfolio_manager').setLevel(logging.WARNING)
logging.getLogger('src.portfolio.risk_manager').setLevel(logging.WARNING)
logging.getLogger('src.core.backtest_manager').setLevel(logging.WARNING)

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
    calculate_information_ratio, calculate_recovery_factor,
    analyze_trade_metrics
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
    recovery_factor = calculate_recovery_factor(stats.get('total_return', 0), stats.get('max_drawdown', 1))
    
    # Hardcode initial capital to match the actual value used
    initial_capital = 10000
    
    # Get final capital from portfolio values
    portfolio_values = stats.get('Portfolio_Value')
    final_capital = portfolio_values.iloc[-1] if portfolio_values is not None and len(portfolio_values) > 0 else initial_capital

    # We're using html.Div as a container now, so we return a list of rows
    return html.Div([
        # First row - Capital metrics side by side with minimal spacing
        dbc.Row([
            dbc.Col(create_metric_card_with_tooltip("Initial Capital", f"${initial_capital:,.2f}", tooltip_texts['Initial Capital']), width=6, className="px-1"),
            dbc.Col(create_metric_card_with_tooltip("Final Capital", f"${final_capital:,.2f}", tooltip_texts['Final Capital']), width=6, className="px-1")
        ], className="g-0 mb-1"),  # Reduced gutters and margin
        
        # Second row - Three columns with metrics
        dbc.Row([
            dbc.Col([
                create_metric_card_with_tooltip("CAGR", f"{stats.get('cagr', 0):.2f}%", tooltip_texts['CAGR']),
                create_metric_card_with_tooltip("Total Return", f"{stats.get('total_return', 0):.2f}%", tooltip_texts['Total Return']),
                create_metric_card_with_tooltip("Alpha", f"{alpha:.2f}%", tooltip_texts['Alpha'])
            ], width=4, className="px-1 py-0"),
            
            dbc.Col([
                create_metric_card_with_tooltip("Max Drawdown", f"{stats.get('max_drawdown', 0):.2f}%", tooltip_texts['Max Drawdown']),
                create_metric_card_with_tooltip("Sharpe Ratio", f"{stats.get('sharpe_ratio', 0):.2f}", tooltip_texts['Sharpe Ratio']),
                create_metric_card_with_tooltip("Beta", f"{beta:.2f}", tooltip_texts['Beta'])
            ], width=4, className="px-1 py-0"),
            
            dbc.Col([
                create_metric_card_with_tooltip("Info Ratio", f"{info_ratio:.2f}", tooltip_texts['Information Ratio']),
                create_metric_card_with_tooltip("Sortino Ratio", f"{stats.get('sortino_ratio', 0):.2f}", tooltip_texts['Sortino Ratio']),
                create_metric_card_with_tooltip("Recovery Factor", f"{recovery_factor:.2f}", tooltip_texts['Recovery Factor'])
            ], width=4, className="px-1 py-0")  # Reduced padding
        ], className="g-0")  # No gutters between columns
    ], className="mb-1")  # Reduced bottom margin

def create_risk_management_section():
    """Create the risk management configuration UI section"""
    try:
        # Get all available tickers
        available_tickers = get_available_tickers()
        ticker_options = [{"label": ticker, "value": ticker} for ticker in available_tickers]
        
        # Default to first ticker if available, otherwise None
        default_ticker = available_tickers[0] if available_tickers else None
    except Exception as e:
        logger.error(f"Error getting tickers: {e}")
        available_tickers = []
        ticker_options = []
        default_ticker = None
    
    return html.Div([
        # Dynamic ticker selector
        html.H6("Select Tickers", className="mt-1 mb-2"),
        dcc.Dropdown(
            id="ticker-selector",
            options=ticker_options,
            value=default_ticker,
            multi=True,
            className="mb-3"
        ),
        
        # Radio buttons for enabling/disabling risk management
        dbc.RadioItems(
            id="risk-management-toggle",
            options=[
                {"label": "Do not apply additional risk management rules", "value": "disabled"},
                {"label": "Apply additional risk management rules", "value": "enabled"}
            ],
            value="disabled",
            className="mb-3"
        ),
        
        # Container for risk management options (initially hidden)
        html.Div([
            # Position limits
            html.H6("Position Limits", className="mt-2"),
            dbc.Row([
                dbc.Col([
                    dbc.Checkbox(id="use-max-position-size", className="mr-2"),
                    html.Label("Maximum position size (%):")
                ], width=6),
                dbc.Col([
                    dbc.Input(id="max-position-size", type="number", min=1, max=100, step=1, value=20, disabled=True)
                ], width=6)
            ], className="mb-2"),
            
            dbc.Row([ 
                dbc.Col([
                    dbc.Checkbox(id="use-min-position-size", className="mr-2"),
                    html.Label("Minimum position size (%):")
                ], width=6),
                dbc.Col([
                    dbc.Input(id="min-position-size", type="number", min=0.1, max=10, step=0.1, value=1, disabled=True)
                ], width=6)
            ], className="mb-2"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Checkbox(id="use-max-positions", className="mr-2"),
                    html.Label("Maximum open positions:")
                ], width=6),
                dbc.Col([
                    dbc.Input(id="max-open-positions", type="number", min=1, max=20, step=1, value=5, disabled=True)
                ], width=6)
            ], className="mb-3"),
            
            # Stop management
            html.H6("Stop Management", className="mt-2"),
            dbc.Row([
                dbc.Col([
                    dbc.Checkbox(id="use-stop-loss", className="mr-2"),
                    html.Label("Stop loss (%):")
                ], width=6),
                dbc.Col([
                    dbc.Input(id="stop-loss-pct", type="number", min=0.5, max=10, step=0.5, value=2, disabled=True)
                ], width=6)
            ], className="mb-2"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Checkbox(id="use-profit-target", className="mr-2"),
                    html.Label("Profit target ratio:")
                ], width=6),
                dbc.Col([
                    dbc.Input(id="profit-target-ratio", type="number", min=1, max=10, step=0.5, value=2, disabled=True)
                ], width=6)
            ], className="mb-2"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Checkbox(id="use-trailing-stop", className="mr-2"),
                    html.Label("Trailing stop:")
                ], width=6),
                dbc.Col([
                    dbc.Input(id="trailing-stop-activation", type="number", min=0.5, max=10, step=0.5, value=2, 
                            placeholder="Activation (%)", disabled=True, className="mb-1"),
                    dbc.Input(id="trailing-stop-distance", type="number", min=0.5, max=10, step=0.5, value=1.5, 
                            placeholder="Distance (%)", disabled=True)
                ], width=6)
            ], className="mb-3"),
            
            # Portfolio limits
            html.H6("Portfolio Limits", className="mt-2"),
            dbc.Row([
                dbc.Col([
                    dbc.Checkbox(id="use-max-drawdown", className="mr-2"),
                    html.Label("Maximum drawdown (%):")
                ], width=6),
                dbc.Col([
                    dbc.Input(id="max-drawdown", type="number", min=5, max=50, step=1, value=20, disabled=True)
                ], width=6)
            ], className="mb-2"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Checkbox(id="use-max-daily-loss", className="mr-2"),
                    html.Label("Maximum daily loss (%):")
                ], width=6),
                dbc.Col([
                    dbc.Input(id="max-daily-loss", type="number", min=1, max=20, step=0.5, value=5, disabled=True)
                ], width=6)
            ], className="mb-2"),
            
            # Market conditions
            html.H6("Market Conditions", className="mt-2"),
            dbc.Row([
                dbc.Col([
                    dbc.Checkbox(id="use-market-filter", className="mr-2"),
                    html.Label("Only trade in favorable market conditions:")
                ], width=6),
                dbc.Col([
                    dbc.Input(id="market-trend-lookback", type="number", min=20, max=200, step=10, value=100, 
                           placeholder="Lookback period (days)", disabled=True)
                ], width=6)
            ], className="mb-3"),
            
        ], id="risk-management-options", style={"display": "none"}),
        
        # Run backtest button
        dbc.Button("Run Backtest", id="run-backtest-button", color="primary", className="mt-3")
    ], className="p-3 border rounded bg-light")

# Add this function before the callback definitions - around line 350

def run_simple_backtest(strategy_type):
    """Run a simple backtest with default parameters - for strategy dropdown"""
    try:
        # Use the existing backtest manager to run a simple version (no risk management)
        return backtest_manager.run_backtest(strategy_type)
    except Exception as e:
        logger.error(f"Simple backtest error: {str(e)}")
        traceback.print_exc()
        return None, None, None

# Add this function before the create_backtest_results function - around line 590

def run_portfolio_backtest(strategy, tickers, risk_params=None, **kwargs):
    """Run a portfolio backtest with risk management parameters"""
    try:
        # Use the backtest manager with risk parameters
        # This is different from run_simple_backtest as it applies risk management
        return backtest_manager.run_portfolio_backtest(
            strategy_type=strategy,
            tickers=tickers, 
            risk_params=risk_params,
            **kwargs
        )
    except Exception as e:
        logger.error(f"Portfolio backtest error: {str(e)}")
        traceback.print_exc()
        return None

# Updated create_trade_histogram function with fixed statistics

def create_trade_histogram(trades):
    """Create a histogram of trade returns with statistics panel"""
    if not trades or len(trades) == 0:
        return html.Div("No trades available")
    
    # Calculate trade statistics directly instead of relying on analyze_trade_metrics
    win_trades = [t for t in trades if t.get('pnl', 0) > 0]
    loss_trades = [t for t in trades if t.get('pnl', 0) <= 0]
    
    total_trades = len(trades)
    win_count = len(win_trades)
    loss_count = len(loss_trades)
    
    # Calculate core statistics
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
    win_loss_ratio = (win_count / loss_count) if loss_count > 0 else float('inf')
    
    # Calculate PnL metrics
    total_pnl = sum(t.get('pnl', 0) for t in trades)
    win_pnl = sum(t.get('pnl', 0) for t in win_trades)
    loss_pnl = sum(t.get('pnl', 0) for t in loss_trades)
    
    avg_win_pnl = (win_pnl / win_count) if win_count > 0 else 0
    avg_loss_pnl = (loss_pnl / loss_count) if loss_count > 0 else 0
    
    # Calculate profit factor
    profit_factor = (win_pnl / abs(loss_pnl)) if loss_pnl < 0 else float('inf')
    
    # Get histogram figure with custom colors for positive/negative trades
    histogram = create_trade_histogram_figure(trades, {
        'colorscale': [
            [0, '#FF6B6B'],  # Red for negative returns
            [0.5, '#FF6B6B'],  # Red for negative returns
            [0.5, '#17B897'],  # Green for positive returns
            [1, '#17B897']    # Green for positive returns
        ]
    })
    
    # Create a statistics panel with Calibri font
    stats_panel = html.Div([
        dbc.Row([
            dbc.Col([
                html.H6("Trade Statistics", className="text-center mb-3")
            ], width=12)
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.P([html.Span("Win Rate: ", style={"fontWeight": "bold", "fontFamily": "Calibri"}), 
                           html.Span(f"{win_rate:.2f}%", style={"fontFamily": "Calibri"})], 
                           className="mb-1"),
                    html.P([html.Span("Profit Factor: ", style={"fontWeight": "bold", "fontFamily": "Calibri"}), 
                           html.Span(f"{profit_factor:.2f}", style={"fontFamily": "Calibri"})], 
                           className="mb-1"),
                    html.P([html.Span("Avg Win: ", style={"fontWeight": "bold", "fontFamily": "Calibri"}), 
                           html.Span(f"${avg_win_pnl:.2f}", style={"fontFamily": "Calibri"})], 
                           className="mb-1"),
                ], className="p-2")
            ], width=6),
            dbc.Col([
                html.Div([
                    html.P([html.Span("Total Trades: ", style={"fontWeight": "bold", "fontFamily": "Calibri"}), 
                           html.Span(f"{total_trades}", style={"fontFamily": "Calibri"})], 
                           className="mb-1"),
                    html.P([html.Span("Win/Loss Ratio: ", style={"fontWeight": "bold", "fontFamily": "Calibri"}), 
                           html.Span(f"{win_loss_ratio:.2f}", style={"fontFamily": "Calibri"})], 
                           className="mb-1"),
                    html.P([html.Span("Avg Loss: ", style={"fontWeight": "bold", "fontFamily": "Calibri"}), 
                           html.Span(f"${avg_loss_pnl:.2f}", style={"fontFamily": "Calibri"})], 
                           className="mb-1"),
                ], className="p-2")
            ], width=6)
        ], className="mb-3"),
    ], className="trade-stats-panel p-3 border rounded", 
    style={"backgroundColor": "#1e222d", "fontFamily": "Calibri"})
    
    # Combine histogram and statistics (histogram first, stats below)
    return html.Div([
        histogram,
        html.Div(className="mt-3"),
        stats_panel
    ])

# Updated create_allocation_chart function to add dollar value chart in addition to percentage chart

def create_allocation_chart(results):
    """Create charts showing portfolio allocation over time"""
    if not results or 'portfolio_values' not in results or results['portfolio_values'].empty:
        return html.Div("No allocation data available")
    
    portfolio_values = results.get('portfolio_values', pd.Series())
    trades = results.get('trades', [])
    
    if len(trades) == 0:
        return html.Div("No allocation data available")
    
    # Group trades by ticker and date
    positions = {}
    
    for trade in trades:
        ticker = trade.get('ticker', '')
        if not ticker:
            continue
            
        entry_date = pd.to_datetime(trade.get('entry_date'))
        exit_date = pd.to_datetime(trade.get('exit_date'))
        shares = float(trade.get('shares', 0))
        entry_price = float(trade.get('entry_price', 0))
        exit_price = float(trade.get('exit_price', 0))
        
        # Add position entry
        if ticker not in positions:
            positions[ticker] = []
        
        positions[ticker].append({
            'entry_date': entry_date,
            'exit_date': exit_date,
            'shares': shares,
            'entry_price': entry_price,
            'exit_price': exit_price
        })
    
    # Create allocation dataframe with daily values
    dates = portfolio_values.index
    allocation_df = pd.DataFrame(index=dates)
    
    # Create cash series (starting with full initial capital)
    initial_capital = portfolio_values.iloc[0]
    cash_series = pd.Series(initial_capital, index=dates)
    
    # For each position, calculate its value through time
    for ticker, position_list in positions.items():
        allocation_df[ticker] = 0.0
        
        for position in position_list:
            entry_date = position['entry_date']
            exit_date = position['exit_date']
            shares = position['shares']
            entry_price = position['entry_price']
            exit_price = position['exit_price']
            
            # Find positions in the date range
            in_position = (dates >= entry_date) & (dates <= exit_date)
            
            # Update position value
            if any(in_position):
                try:
                    # Calculate days since entry directly
                    position_dates = dates[in_position]
                    days_since_entry = [(d - entry_date).days for d in position_dates]
                    
                    max_days = (exit_date - entry_date).days
                    
                    if max_days > 0:
                        # Linear interpolation
                        price_range = [entry_price + (exit_price - entry_price) * day / max_days 
                                      for day in days_since_entry]
                    else:
                        price_range = [entry_price] * len(days_since_entry)
                    
                    # Update position value
                    for i, date in enumerate(position_dates):
                        allocation_df.loc[date, ticker] += shares * price_range[i]
                except Exception as e:
                    logger.error(f"Error calculating position allocation: {e}")
            
            # Update cash: subtract at entry, add at exit
            cash_indices = dates >= entry_date
            cash_series.loc[cash_indices] -= shares * entry_price
            
            cash_indices = dates >= exit_date
            cash_series.loc[cash_indices] += shares * exit_price
    
    # Add cash to allocation dataframe
    allocation_df['Cash'] = cash_series
    
    # Calculate total portfolio value
    allocation_df['Total'] = allocation_df.sum(axis=1)
    
    # Calculate percentages
    for col in allocation_df.columns:
        if col != 'Total':
            allocation_df[f"{col}_pct"] = allocation_df[col] / allocation_df['Total'] * 100
    
    # Create percentage chart
    pct_fig = go.Figure()
    
    # Add area chart for each ticker
    tickers = [col for col in allocation_df.columns if col not in ['Total', 'Cash'] and not col.endswith('_pct')]
    colors = ['#17B897', '#FF6B6B', '#36A2EB', '#FFCE56', '#8A2BE2', '#FF7F50', '#20B2AA', '#D2691E']
    
    # Add cash first (percentage)
    pct_fig.add_trace(
        go.Scatter(
            x=dates,
            y=allocation_df['Cash_pct'],
            mode='lines',
            stackgroup='one',
            name='Cash',
            line=dict(width=0),
            fillcolor='#777777'
        )
    )
    
    # Add other tickers (percentage)
    for i, ticker in enumerate(tickers):
        color = colors[i % len(colors)]
        pct_col = f"{ticker}_pct"
        
        pct_fig.add_trace(
            go.Scatter(
                x=dates,
                y=allocation_df[pct_col],
                mode='lines',
                stackgroup='one',
                name=ticker,
                line=dict(width=0),
                fillcolor=color
            )
        )
    
    # Update layout for percentage chart
    pct_fig.update_layout(
        title='Portfolio Allocation (Percentage)',
        template=CHART_THEME,
        xaxis=dict(
            title='Date',
            gridcolor='#2a2e39',
            type='date'
        ),
        yaxis=dict(
            title='Allocation (%)',
            gridcolor='#2a2e39',
            ticksuffix='%'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        hovermode='x unified',
        paper_bgcolor='#1e222d',
        plot_bgcolor='#1e222d',
        font=dict(color='white'),
        height=300,
        margin=dict(t=50, l=50, r=20, b=50)
    )
    
    # Create dollar value chart
    value_fig = go.Figure()
    
    # Add area chart for each ticker (dollar value)
    # Add cash first (dollar value)
    value_fig.add_trace(
        go.Scatter(
            x=dates,
            y=allocation_df['Cash'],
            mode='lines',
            stackgroup='one',
            name='Cash',
            line=dict(width=0),
            fillcolor='#777777'
        )
    )
    
    # Add other tickers (dollar value)
    for i, ticker in enumerate(tickers):
        color = colors[i % len(colors)]
        
        value_fig.add_trace(
            go.Scatter(
                x=dates,
                y=allocation_df[ticker],
                mode='lines',
                stackgroup='one',
                name=ticker,
                line=dict(width=0),
                fillcolor=color
            )
        )
    
    # Update layout for dollar value chart
    value_fig.update_layout(
        title='Portfolio Allocation (Dollar Value)',
        template=CHART_THEME,
        xaxis=dict(
            title='Date',
            gridcolor='#2a2e39',
            type='date'
        ),
        yaxis=dict(
            title='Allocation ($)',
            gridcolor='#2a2e39',
            ticksuffix='$'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        hovermode='x unified',
        paper_bgcolor='#1e222d',
        plot_bgcolor='#1e222d',
        font=dict(color='white'),
        height=300,
        margin=dict(t=50, l=50, r=20, b=50)
    )
    
    # Combine both charts
    return html.Div([
        dcc.Graph(figure=pct_fig, config={'displayModeBar': False}),
        dcc.Graph(figure=value_fig, config={'displayModeBar': False})
    ])

# Fix the incomplete update_backtest function (around line 704)

@app.callback(
    [Output("calculation-status", "children"),
     Output("equity-curve-container", "children"),
     Output("metrics-container", "children"),
     Output("additional-charts", "children"),
     Output("trade-distribution-container", "children"),
     Output("trade-table-container", "children"),
     Output("backtest-period", "children"),
     Output("portfolio-instruments", "children"),
     Output("portfolio-composition-container", "children")],
    [Input("run-backtest-button", "n_clicks")], 
    [State("strategy-selector", "value")]
)
def update_backtest(n_clicks, strategy):
    # Don't run backtest on page load (when n_clicks is None)
    if n_clicks is None:
        return (
            html.Div("Click 'Run Backtest' to start", className="text-warning"),
            [],
            create_empty_cards(),
            [],
            html.Div("No trades available"),
            html.Div("No trades available"),
            "",
            "",
            html.Div("No allocation data available")
        )
    
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
            html.Div("No allocation data available")
        )
    
    try:
        # Run the backtest
        signals, results, stats = run_simple_backtest(strategy)
        
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
                html.Div("No allocation data available")
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
        
        # Format results for allocation chart
        formatted_results = {
            'portfolio_values': results.get('Portfolio_Value', pd.Series()),
            'trades': trades
        }
        
        # Create portfolio composition chart
        portfolio_composition = create_allocation_chart(formatted_results)
        
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
            portfolio_composition
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
            html.Div("No allocation data available")
        )

# Add this function to app.py after create_trade_histogram

def create_trade_table(trades):
    """Create a table of trade history"""
    if not trades or len(trades) == 0:
        return html.Div("No trades available")
    
    # Process trades for display
    trade_data = []
    for trade in trades:
        # Format dates
        entry_date = pd.to_datetime(trade.get('entry_date')).strftime('%Y-%m-%d') if 'entry_date' in trade else 'N/A'
        exit_date = pd.to_datetime(trade.get('exit_date')).strftime('%Y-%m-%d') if 'exit_date' in trade else 'N/A'
        
        # Calculate holding period
        try:
            entry = pd.to_datetime(trade.get('entry_date'))
            exit = pd.to_datetime(trade.get('exit_date'))
            holding_days = (exit - entry).days
        except:
            holding_days = 'N/A'
        
        # Format P&L with colors
        pnl = trade.get('pnl', 0)
        pnl_pct = trade.get('pnl_pct', 0)
        
        trade_data.append({
            'Ticker': trade.get('ticker', 'N/A'),
            'Entry Date': entry_date,
            'Exit Date': exit_date,
            'Holding Days': holding_days,
            'Entry Price': f"${float(trade.get('entry_price', 0)):.2f}",
            'Exit Price': f"${float(trade.get('exit_price', 0)):.2f}",
            'Shares': trade.get('shares', 'N/A'),
            'P&L': f"${pnl:.2f}",
            'P&L %': f"{pnl_pct:.2f}%",
            'Direction': 'Long' if trade.get('direction', 1) > 0 else 'Short'
        })
    
    # Create the DataTable
    return dash_table.DataTable(
        id='trade-table',
        columns=[
            {'name': 'Ticker', 'id': 'Ticker'},
            {'name': 'Entry Date', 'id': 'Entry Date'},
            {'name': 'Exit Date', 'id': 'Exit Date'},
            {'name': 'Days', 'id': 'Holding Days'},
            {'name': 'Entry', 'id': 'Entry Price'},
            {'name': 'Exit', 'id': 'Exit Price'},
            {'name': 'Shares', 'id': 'Shares'},
            {'name': 'P&L', 'id': 'P&L'},
            {'name': 'P&L %', 'id': 'P&L %'},
            {'name': 'Dir', 'id': 'Direction'}
        ],
        data=trade_data,
        style_table={'overflowX': 'auto'},
        style_cell={
            'backgroundColor': '#1e222d',
            'color': 'white',
            'textAlign': 'center',
            'fontSize': '12px',
            'fontFamily': 'Calibri'
        },
        style_header={
            'backgroundColor': '#131722',
            'fontWeight': 'bold',
            'color': 'white',
            'fontFamily': 'Calibri'
        },
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{P&L} contains "-"',
                },
                'color': '#FF6B6B'  # Red for negative P&L
            },
            {
                'if': {
                    'filter_query': '{P&L} contains "$" && !({P&L} contains "-")',
                },
                'color': '#17B897'  # Green for positive P&L
            }
        ],
        page_size=10,
        sort_action='native',
        sort_mode='multi'
    )

# Update app layout to restore the proper 3-column structure

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Portfolio Backtester", className="text-center my-4")
        ])
    ]),

    dbc.Row([
        # Left column (Strategy Settings + Risk Management)
        dbc.Col([
            # Strategy settings card
            dbc.Card([
                dbc.CardHeader("Strategy Settings"),
                dbc.CardBody([
                    html.H6("Select Strategy", className="mb-2"),
                    dcc.Dropdown(
                        id="strategy-selector",
                        options=[
                            {"label": "Moving Average Crossover", "value": "MA"},
                            {"label": "RSI Strategy", "value": "RSI"},
                            {"label": "Bollinger Bands", "value": "BB"}
                        ],
                        value="MA",
                        className="mb-3"
                    ),
                ])
            ], className="mb-4"),
            
            # Risk management card
            dbc.Card([
                dbc.CardHeader("Risk Management"),
                dbc.CardBody([
                    create_risk_management_section()
                ])
            ])
        ], width=3),
        
        # Center column (Equity Curve & Portfolio Composition)
        dbc.Col([
            dbc.Card([
                dbc.CardBody([

                    # Status and info
                    html.Div(id="calculation-status", className="mb-2"),
                    dbc.Row([
                        dbc.Col([html.Span("Backtest Period: ", className="fw-bold")], width=3),
                        dbc.Col([html.Span(id="backtest-period")], width=9)
                    ], className="mb-1"),
                    dbc.Row([
                        dbc.Col([html.Span("Instruments: ", className="fw-bold")], width=3),
                        dbc.Col([html.Span(id="portfolio-instruments")], width=9)
                    ], className="mb-3"),
                    
                    # Equity curve
                    html.Div(id="equity-curve-container", className="mb-4"),
                    
                    # Portfolio composition
                    html.H5("Portfolio Composition", className="mt-3 mb-2"),
                    html.Div(id="portfolio-composition-container")
                ])
            ])
        ], width=6),
        
        # Right column (Metrics)
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Performance Metrics"),
                dbc.CardBody([
                    html.Div(id="metrics-container"),
                    html.Div(id="additional-charts")
                ])
            ])
        ], width=3)
    ], className="mb-4"),
    
    # Bottom section (Trade Distribution & Table)
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Trade Analysis"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H5("Trade Distribution", className="mb-2"),
                            html.Div(id="trade-distribution-container", className="mb-4")
                        ], width=12)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.H5("Trade History", className="mb-2"),
                            html.Div(id="trade-table-container")
                        ], width=12)
                    ])
                ])
            ])
        ], width=12)
    ])
], fluid=True, style={"backgroundColor": "#131722"})

# Add callback to show results when available
@app.callback(
    Output("backtest-results", "style"),
    [Input("calculation-status", "children")]
)
def show_results(status):
    if status and "successfully" in str(status):
        return {"display": "block"}
    return {"display": "none"}

# Replace the create_trade_histogram_figure function around line 970

def create_trade_histogram_figure(trades, options=None):
    """Create a histogram of trade returns with proper coloring and fewer bins"""
    if not trades or len(trades) == 0:
        return html.Div("No trades available")
    
    # Extract PnL percentages
    pnl_pcts = [trade.get('pnl_pct', 0) for trade in trades]
    
    # Determine outlier thresholds (using 2.0 * IQR method)
    q1 = np.percentile(pnl_pcts, 25)
    q3 = np.percentile(pnl_pcts, 75)
    iqr = q3 - q1
    upper_bound = q3 + 2.0 * iqr
    lower_bound = q1 - 2.0 * iqr
    
    # Clip outliers for binning purposes
    clipped_pnl = []
    for pnl in pnl_pcts:
        if pnl > upper_bound:
            clipped_pnl.append(upper_bound)
        elif pnl < lower_bound:
            clipped_pnl.append(lower_bound)
        else:
            clipped_pnl.append(pnl)
    
    # Create histogram bins - FEWER BINS FOR READABILITY
    bin_size = 2.0  # Use larger 2% bins instead of 0.5%
    min_bin = min(lower_bound, -10)
    max_bin = max(upper_bound, 10)
    bins = np.arange(min_bin, max_bin + bin_size, bin_size)
    
    # Create figure
    fig = go.Figure()
    
    # Add negative returns histogram (red)
    neg_pnl = [p for p in clipped_pnl if p < 0]
    if neg_pnl:
        fig.add_trace(go.Histogram(
            x=neg_pnl,
            xbins=dict(start=min_bin, end=0, size=bin_size),
            marker_color='#FF6B6B',
            name='Negative Returns',
            opacity=0.7
        ))
    
    # Add positive returns histogram (green)
    pos_pnl = [p for p in clipped_pnl if p >= 0]
    if pos_pnl:
        fig.add_trace(go.Histogram(
            x=pos_pnl,
            xbins=dict(start=0, end=max_bin, size=bin_size),
            marker_color='#17B897',
            name='Positive Returns',
            opacity=0.7
        ))
    
    # Update layout
    fig.update_layout(
        title=None,  # Remove title to save space
        template=CHART_THEME,
        xaxis=dict(
            title='Return (%)',
            gridcolor='#2a2e39',
            tickformat='.0f',  # Whole numbers to save space
            ticksuffix='%',
            # Fewer tick marks for readability
            tickmode='array',
            tickvals=list(range(int(min_bin), int(max_bin) + 1, 4)),
            ticktext=[f"{x}%" for x in range(int(min_bin), int(max_bin) + 1, 4)]
        ),
        yaxis=dict(
            title='Count',  # Shorter title
            gridcolor='#2a2e39'
        ),
        barmode='overlay',
        bargap=0.1,
        paper_bgcolor='#1e222d',
        plot_bgcolor='#1e222d',
        font=dict(color='white'),
        height=250,  # Shorter height
        margin=dict(t=20, l=40, r=20, b=40)  # Tighter margins
    )
    
    # Add annotation for outliers if they exist
    has_upper_outliers = any(pnl > upper_bound for pnl in pnl_pcts)
    has_lower_outliers = any(pnl < lower_bound for pnl in pnl_pcts)
    
    if has_upper_outliers:
        num_upper_outliers = sum(1 for pnl in pnl_pcts if pnl > upper_bound)
        fig.add_annotation(
            x=upper_bound, y=0,
            text=f"{num_upper_outliers} trades > {upper_bound:.0f}%",
            showarrow=True,
            arrowhead=1,
            ax=0, ay=-30,
            font=dict(color='#17B897', size=10)  # Smaller font
        )
    
    if has_lower_outliers:
        num_lower_outliers = sum(1 for pnl in pnl_pcts if pnl < lower_bound)
        fig.add_annotation(
            x=lower_bound, y=0,
            text=f"{num_lower_outliers} trades < {lower_bound:.0f}%",
            showarrow=True,
            arrowhead=1,
            ax=0, ay=-30,
            font=dict(color='#FF6B6B', size=10)  # Smaller font
        )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})

# Add this at the very end of your app.py file

if __name__ == '__main__':
    app.run(debug=True)
