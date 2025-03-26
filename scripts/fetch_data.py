import sys
from pathlib import Path
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('yfinance').setLevel(logging.ERROR)

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.core.config import config

def fetch_ticker_data(ticker: str) -> pd.DataFrame:
    """Fetch historical data for a ticker"""
    try:
        logging.info(f"Fetching data for {ticker}...")
        
        # Create Ticker object
        stock = yf.Ticker(ticker)
        
        # Fetch data in one request
        df = stock.history(
            start="2019-01-01",
            end=datetime.now().strftime('%Y-%m-%d'),
            interval="1d",
            auto_adjust=True
        )
        
        if not df.empty:
            # Process the dataframe
            df = df.reset_index()
            df['Ticker'] = ticker
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
            
            # Select and rename columns
            result = df[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]
            
            logging.info(f"✓ Retrieved {len(result)} rows for {ticker}")
            return result
        else:
            logging.error(f"No data returned for {ticker}")
            return pd.DataFrame()
            
    except Exception as e:
        logging.error(f"Error fetching {ticker}: {str(e)}")
        return pd.DataFrame()

def update_historical_data():
    """Update historical price data"""
    # Setup paths
    data_dir = project_root / "data"
    csv_path = data_dir / "historical_prices.csv"
    
    # Create data directory if needed
    data_dir.mkdir(exist_ok=True)
    
    # Get list of tickers
    tickers = [*config.default_tickers, config.BENCHMARK_TICKER]
    logging.info(f"\nFetching data for tickers: {', '.join(tickers)}")
    
    # Fetch data for all tickers
    all_data = []
    for ticker in tickers:
        df = fetch_ticker_data(ticker)
        if not df.empty:
            all_data.append(df)
            time.sleep(1)  # Rate limiting
    
    if all_data:
        # Combine all data
        combined_data = pd.concat(all_data, ignore_index=True)
        combined_data = combined_data.sort_values(['Date', 'Ticker'])
        
        # Save to CSV
        combined_data.to_csv(csv_path, index=False)
        logging.info(f"\nSaved {len(combined_data)} rows to {csv_path}")
        
        # Print summary
        summary = combined_data.groupby('Ticker').agg({
            'Date': ['min', 'max'],
            'Close': 'count'
        })
        logging.info("\nData Summary:")
        logging.info(f"\n{summary}")
    else:
        logging.error("No data was retrieved")

if __name__ == "__main__":
    update_historical_data()
