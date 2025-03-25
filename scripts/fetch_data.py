import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
from src.core.config import config

def fetch_data(start_date: str = None, end_date: str = None):
    """
    Fetch historical data for all available tickers
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
        
    os.makedirs(config.DATA_DIR, exist_ok=True)
    
    existing_tickers = []
    if os.path.exists(config.DATA_FILE):
        df = pd.read_csv(config.DATA_FILE)
        existing_tickers = df['Ticker'].unique().tolist()
        
    all_data = []
    for ticker in [*config.available_tickers, config.BENCHMARK_TICKER]:
        if ticker in existing_tickers:
            continue
            
        print(f"Fetching data for {ticker}...")
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date, interval='1d')
        
        if not df.empty:
            df = df.reset_index()
            df['Ticker'] = ticker
            all_data.append(df)
            
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df.to_csv(config.DATA_FILE, index=False)
        print(f"Data saved to {config.DATA_FILE}")
    else:
        print("No new data fetched")

if __name__ == "__main__":
    fetch_data()
