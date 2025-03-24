# Backtester App

A Python-based backtesting application for trading strategies.

## Setup

1. Make sure you have Python 3.8+ installed
2. Run the setup script:
   ```
   python setup.py
   ```
3. Activate the virtual environment:
   - Windows:
     ```
     .venv\Scripts\activate
     ```
   - Linux/Mac:
     ```
     source .venv/bin/activate
     ```

## Usage

1. First, fetch historical data:
   ```
   python fetch_data.py
   ```

2. Run the backtester:
   ```
   python run_backtest.py
   ```

## Project Structure

- `src/` - Source code for the backtesting engine and strategies
- `data/` - Directory for storing historical price data
- `requirements.txt` - Python package dependencies

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
