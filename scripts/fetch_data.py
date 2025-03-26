import sys
from pathlib import Path
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
import time
import random
import logging
from typing import Optional, Dict

# Configure yfinance logging
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.core.config import config

def fetch_ticker_data(ticker: str, start: str, end: str) -> Optional[pd.DataFrame]:
    """Fetch data for a single ticker in one attempt"""
    try:
        print(f"Fetching {ticker} from {start} to {end}...")
        df = yf.download(
            ticker,
            start=start,
            end=end,
            progress=False
        )
        
        if df is not None and not df.empty:
            df = df.reset_index()
            df['Ticker'] = ticker
            print(f"Got {len(df)} rows for {ticker}")
            return df
        print(f"No data returned for {ticker}")
            
    except Exception as e:
        print(f"Error fetching {ticker}: {str(e)}")
    
    return None

def update_historical_data():
    """Update historical price data with new rows"""
    
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    csv_path = data_dir / "historical_prices.csv"
    
    data_dir.mkdir(exist_ok=True)
    
    # Date ranges - shorter periods for better reliability
    date_ranges = [
        ('2019-01-01', '2019-12-31'),
        ('2020-01-01', '2020-12-31'),
        ('2021-01-01', '2021-12-31'),
        ('2022-01-01', '2022-12-31'),
        ('2023-01-01', (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
    ]
    
    if not csv_path.exists():
        print(f"Creating new data file at {csv_path}")
        
        all_data = []
        tickers = [*config.default_tickers, config.BENCHMARK_TICKER]

        for ticker in tickers:
            ticker_data = []
            
            for start, end in date_ranges:
                df = fetch_ticker_data(ticker, start, end)
                if df is not None:
                    ticker_data.append(df)
                time.sleep(1)  # Simple delay between requests

            if ticker_data:
                combined_df = pd.concat(ticker_data)
                combined_df = combined_df[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]
                combined_df['Date'] = pd.to_datetime(combined_df['Date']).dt.strftime('%Y-%m-%d %H:%M:%S%z')
                all_data.append(combined_df)
                print(f"Successfully fetched total {len(combined_df)} rows for {ticker}")
            else:
                print(f"No data retrieved for {ticker}")

        if all_data:
            combined_data = pd.concat(all_data)
            combined_data = combined_data.sort_values(['Date', 'Ticker'])
            combined_data.to_csv(csv_path, index=False)
            print(f"Created new data file with {len(combined_data)} rows")
            return
        else:
            print("Failed to fetch initial data")
            return
            
    # Read existing data
    existing_data = pd.read_csv(csv_path)
    existing_data['Date'] = pd.to_datetime(existing_data['Date'])
    
    # Get latest date in existing data
    latest_date = existing_data['Date'].max()
    
    # Calculate dates for new data fetch
    start_date = latest_date + timedelta(days=1)
    end_date = datetime.now() - timedelta(days=1)
    
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
