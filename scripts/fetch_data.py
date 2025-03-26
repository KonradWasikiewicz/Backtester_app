import sys
from pathlib import Path
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

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

def update_historical_data():
    """Update historical price data with new rows"""
    
    # Use absolute path resolution
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    csv_path = data_dir / "historical_prices.csv"
    
    # Ensure data directory exists
    data_dir.mkdir(exist_ok=True)
    
    if not csv_path.exists():
        print(f"CSV file not found at {csv_path}")
        return
        
    # Read existing data
    existing_data = pd.read_csv(csv_path)
    existing_data['Date'] = pd.to_datetime(existing_data['Date'], utc=True)
    
    # Get latest date in existing data
    latest_date = existing_data['Date'].max()
    
    # Calculate dates for new data fetch
    start_date = latest_date + timedelta(days=1)
    end_date = datetime.now()
    
    if start_date >= end_date:
        print("Data is already up to date")
        return
        
    # Get list of tickers to update
    tickers = existing_data['Ticker'].unique()
    
    new_data_frames = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            new_data = stock.history(start=start_date, end=end_date)
            
            if not new_data.empty:
                new_data = new_data.reset_index()
                new_data['Ticker'] = ticker
                new_data = new_data[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]
                new_data_frames.append(new_data)
                print(f"Fetched new data for {ticker}")
                
        except Exception as e:
            print(f"Error fetching {ticker}: {str(e)}")
            continue
            
    if new_data_frames:
        new_data = pd.concat(new_data_frames)
        new_data['Date'] = pd.to_datetime(new_data['Date'], utc=True)
        
        # Combine and sort
        combined_data = pd.concat([existing_data, new_data])
        combined_data = combined_data.sort_values(['Date', 'Ticker'])
        combined_data = combined_data.drop_duplicates(['Date', 'Ticker'])
        
        # Save updated data
        combined_data.to_csv(csv_path, index=False)
        print(f"Added {len(new_data)} new rows to {csv_path}")
    else:
        print("No new data to add")

if __name__ == "__main__":
    update_historical_data()
