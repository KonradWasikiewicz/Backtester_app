from src.data_loader import DataLoader
from src.strategy import MovingAverageCrossover, RSIStrategy, BollingerBandsStrategy
from src.backtest_engine import BacktestEngine
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
            df = DataLoader.load_data('data/historical_prices.csv', ticker)
            if df is not None and len(df.index) > 0:
                data_dict[ticker] = df
                print(f"Loaded {len(df)} rows for {ticker}")
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
                print(f"Signal: {'LONG' if row['Signal'] > 0 else 'SHORT'}")
                if 'Volatility' in row:
                    print(f"Volatility: {row['Volatility']:.4f}")
                print("---")
    except Exception as e:
        print(f"Error generating signals: {str(e)}")
        return
    
    # 4. Run backtest
    print("\nRunning backtest...")
    try:
        engine = BacktestEngine(initial_capital=100000)
        results = engine.run_backtest(signals)
        
        # Print backtest statistics
        stats = engine.get_statistics()
        print("\nBacktest Statistics:")
        for key, value in stats.items():
            print(f"{key}: {value}")
            
        # Print trade summary
        print("\nTrade Summary:")
        for trade in engine.trades[:5]:  # Show first 5 trades
            print(f"\nTicker: {trade.ticker}")
            print(f"Entry Date: {trade.entry_date}")
            print(f"Exit Date: {trade.exit_date}")
            print(f"Entry Price: ${trade.entry_price:.2f}")
            print(f"Exit Price: ${trade.exit_price:.2f}")
            print(f"Shares: {trade.shares}")
            print(f"P&L: ${trade.pnl:.2f}")
            print(f"Direction: {'LONG' if trade.signal > 0 else 'SHORT'}")
            
    except Exception as e:
        print(f"Error in backtest execution: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test each strategy
    for strategy_name in ["BB", "MA", "RSI"]:
        test_strategy(strategy_name)
