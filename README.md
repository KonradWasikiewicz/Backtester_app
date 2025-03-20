# Backtester App

A flexible Python-based backtesting framework for testing trading strategies on historical market data.

## Features

- Multiple built-in trading strategies:
  - Moving Average Crossover
  - RSI (Relative Strength Index)
  - Bollinger Bands
- Interactive strategy and ticker selection through GUI
- Detailed performance visualization
- Risk management capabilities
- Historical data fetching from Yahoo Finance
- Comprehensive performance metrics

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Backtester_app
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Fetch historical data:
```bash
python fetch_data.py
```

2. Run the backtester:
```bash
python run_backtest.py
```

3. Follow the GUI prompts to:
   - Select a trading strategy
   - Choose a ticker
   - Configure strategy parameters
   - View backtest results

## Project Structure

```
Backtester_app/
├── data/                  # Historical price data
├── src/
│   ├── backtest_engine.py # Core backtesting logic
│   ├── strategy.py        # Trading strategies
│   ├── visualization.py   # Results visualization
│   ├── risk_manager.py    # Risk management
│   └── strategy_selector.py # GUI for strategy selection
├── fetch_data.py         # Data acquisition script
└── run_backtest.py       # Main execution script
```

## Available Strategies

### Moving Average Crossover
- Uses two moving averages (short and long-term)
- Generates buy signals when short MA crosses above long MA
- Generates sell signals when short MA crosses below long MA

### RSI Strategy
- Uses Relative Strength Index
- Generates buy signals at oversold levels
- Generates sell signals at overbought levels

### Bollinger Bands Strategy
- Uses price movement in relation to Bollinger Bands
- Generates buy signals when price touches lower band
- Generates sell signals when price touches upper band

## Performance Metrics

- Total Return
- Win Rate
- Average Profit
- Maximum Drawdown
- Total Number of Trades
- Profit Factor

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit pull requests.
