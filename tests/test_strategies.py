from src.core.data import DataLoader
from src.strategies import MovingAverageCrossover, RSIStrategy, BollingerBandsStrategy
from src.core.engine import BacktestEngine
import pandas as pd

def test_strategy(strategy_name: str = "BB"):
    """Test strategy execution without visualization"""
    print(f"\nTesting {strategy_name} strategy...")
    
    # 1. Load data
    data_dict = {}
    tickers = ['AAPL', 'MSFT']  # Użyjmy na początek tylko 2 tickerów dla przejrzystości
    
    print("\nLoading data...")
    for ticker in tickers:
        try:
            df = DataLoader.load_data([ticker])
            if ticker in df and len(df[ticker].index) > 0:
                data_dict[ticker] = df[ticker]
                print(f"Loaded {len(df[ticker])} rows for {ticker}")
        except Exception as e:
            print(f"Error loading {ticker}: {str(e)}")
    
    # 2. Initialize strategy
    print("\nInitializing strategy...")
    if strategy_name == "BB":
        strategy = BollingerBandsStrategy(window=20, num_std=2)
    elif strategy_name == "MA":
        strategy = MovingAverageCrossover(short_window=20, long_window=50)
    elif strategy_name == "RSI":
        strategy = RSIStrategy(period=14)
    
    # 3. Generate signals
    print("\nGenerating signals...")
    try:
        signals = strategy.generate_signals(data_dict)
        for ticker, df in signals.items():
            signal_count = (df['Signal'] != 0).sum()
            print(f"\n{ticker} generated {signal_count} signals")
            
            # Show first 5 signals
            signal_rows = df[df['Signal'] != 0].head()
            print(f"\nFirst 5 signals for {ticker}:")
            for idx, row in signal_rows.iterrows():
                print(f"Date: {idx}")
                print(f"Price: ${row['Close']:.2f}")

    except Exception as e:
        print(f"Error generating signals: {str(e)}")
    
    # 4. Run backtest
    print("\nRunning backtest...")

if __name__ == "__main__":
    # Test each strategy
    for strategy_name in ["BB", "MA", "RSI"]:
        test_strategy(strategy_name)
