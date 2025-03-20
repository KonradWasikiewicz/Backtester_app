import yfinance as yf
import pandas as pd
import datetime
import os
from typing import List
import time
import random
import requests
from requests.exceptions import RequestException
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

def check_existing_data(file_path: str) -> bool:
    """Sprawdza czy plik z danymi istnieje i czy nie jest pusty"""
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            return not df.empty
        except:
            return False
    return False

def create_session():
    """Creates a requests session with retry strategy"""
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def fetch_single_ticker(ticker: str, start_date: datetime.date, end_date: datetime.date,
                       session: requests.Session, max_retries: int = 5) -> pd.DataFrame:
    """Pobiera dane dla pojedynczego tickera z obsługą błędów"""
    for attempt in range(max_retries):
        try:
            # Create Ticker object with custom session
            ticker_obj = yf.Ticker(ticker, session=session)

            # Add delay between attempts
            time.sleep(2 + random.random() * 3)

            # Download data
            ticker_data = ticker_obj.history(
                start=start_date,
                end=end_date,
                interval='1d'
            )

            if not ticker_data.empty:
                ticker_data = ticker_data.reset_index()
                ticker_data['Ticker'] = ticker
                return ticker_data

        except Exception as e:
            print(f"Próba {attempt + 1} nie powiodła się dla {ticker}: {str(e)}")
            time.sleep(5 + attempt * 2)  # Increasing delay with each attempt

    return pd.DataFrame()

def fetch_stock_data(tickers: List[str], start_date: datetime.date, end_date: datetime.date, csv_path: str) -> None:
    """Pobiera dane dla wszystkich tickerów z obsługą błędów"""
    if check_existing_data(csv_path):
        print(f"Znaleziono istniejące dane w {csv_path}")
        return

    print("Pobieranie nowych danych...")
    all_data = []
    failed_tickers = []

    # Create a single session for all requests
    session = create_session()

    for ticker in tickers:
        print(f"Pobieranie danych dla {ticker}...")
        ticker_data = fetch_single_ticker(ticker, start_date, end_date, session)

        if not ticker_data.empty:
            all_data.append(ticker_data)
            print(f"Pobrano {len(ticker_data)} rekordów dla {ticker}")
        else:
            failed_tickers.append(ticker)
            print(f"Nie udało się pobrać danych dla {ticker}")

        # Add delay between tickers
        time.sleep(random.uniform(1, 3))

    if failed_tickers:
        print("\nNie udało się pobrać danych dla następujących tickerów:")
        for ticker in failed_tickers:
            print(f"- {ticker}")

    if all_data:
        data_long = pd.concat(all_data, ignore_index=True)
        data_long = data_long[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]

        # Upewnij się, że katalog istnieje
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)

        # Zapisz dane
        data_long.to_csv(csv_path, index=False)
        print(f"\nDane zostały zapisane do {csv_path}")
        print(f"Pobrano dane dla {len(all_data)} z {len(tickers)} tickerów")
    else:
        print("\nNie udało się pobrać żadnych danych. Sprawdź połączenie internetowe.")

if __name__ == "__main__":
    # Split tickers into smaller batches
    TICKERS = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'TSLA', '^GSPC']
    BATCH_SIZE = 3

    end_date = datetime.date.today()
    start_date = datetime.date(2018, 1, 1)
    csv_path = 'data/historical_prices.csv'

    # Process tickers in batches
    for i in range(0, len(TICKERS), BATCH_SIZE):
        batch = TICKERS[i:i+BATCH_SIZE]
        print(f"\nPrzetwarzanie batch {i//BATCH_SIZE + 1}...")
        fetch_stock_data(batch, start_date, end_date, csv_path)
        time.sleep(10)  # Delay between batches
