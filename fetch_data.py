import yfinance as yf
import pandas as pd
import datetime
import os
from typing import List
import time
import random

def check_existing_data(file_path: str) -> bool:
    """Sprawdza czy plik z danymi istnieje i czy nie jest pusty"""
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            return not df.empty
        except:
            return False
    return False

def fetch_single_ticker(ticker: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
    """Pobiera dane dla pojedynczego tickera z obsługą błędów"""
    try:
        # Create Ticker object
        stock = yf.Ticker(ticker)

        # Download data
        df = stock.history(
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval='1d'
        )

        if not df.empty:
            df = df.reset_index()
            df['Ticker'] = ticker
            # Ensure consistent column names and order
            df = df[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]
            print(f"Pobrano {len(df)} rekordów dla {ticker}")
            return df

    except Exception as e:
        print(f"Błąd podczas pobierania {ticker}: {str(e)}")

    return pd.DataFrame()

def fetch_stock_data(tickers: List[str], start_date: datetime.date, end_date: datetime.date, csv_path: str) -> None:
    """Pobiera dane dla wszystkich tickerów"""
    if check_existing_data(csv_path):
        print(f"Znaleziono istniejące dane w {csv_path}")
        return

    print("Pobieranie nowych danych...")
    all_data = []
    failed_tickers = []

    for ticker in tickers:
        print(f"\nPróba pobrania danych dla {ticker}...")

        # Add delay between requests
        time.sleep(2)

        ticker_data = fetch_single_ticker(ticker, start_date, end_date)

        if not ticker_data.empty:
            all_data.append(ticker_data)
        else:
            failed_tickers.append(ticker)
            print(f"Nie udało się pobrać danych dla {ticker}")

    if all_data:
        # Combine all data
        final_df = pd.concat(all_data, ignore_index=True)

        # Ensure directory exists
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)

        # Save to CSV
        final_df.to_csv(csv_path, index=False)
        print(f"\nZapisano dane do {csv_path}")
        print(f"Pobrano dane dla {len(all_data)} z {len(tickers)} tickerów")

        if failed_tickers:
            print("\nNie udało się pobrać danych dla:")
            for ticker in failed_tickers:
                print(f"- {ticker}")
    else:
        print("\nNie udało się pobrać żadnych danych")

if __name__ == "__main__":
    TICKERS = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'TSLA', '^GSPC']

    # Set date range
    end_date = datetime.date.today()
    start_date = datetime.date(2020, 1, 1)
    csv_path = 'data/historical_prices.csv'

    print(f"Pobieranie danych od {start_date} do {end_date}")

    # Delete existing file if it exists
    if os.path.exists(csv_path):
        os.remove(csv_path)
        print(f"Usunięto istniejący plik {csv_path}")

    fetch_stock_data(TICKERS, start_date, end_date, csv_path)
