import yfinance as yf
import pandas as pd
import datetime
import os

def fetch_data():
    """Fetch historical data for predefined tickers"""
    TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', '^GSPC']
    end_date = datetime.date.today()
    start_date = datetime.date(2020, 1, 1)
    csv_path = 'data/historical_prices.csv'
    
    os.makedirs('data', exist_ok=True)
    
    all_data = []
    for ticker in TICKERS:
        print(f"Fetching data for {ticker}...")
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date, interval='1d')
        if not df.empty:
            df = df.reset_index()
            df['Ticker'] = ticker
            all_data.append(df)
    
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df.to_csv(csv_path, index=False)
        print(f"Data saved to {csv_path}")
    else:
        print("No data fetched")

if __name__ == "__main__":
    fetch_data()
