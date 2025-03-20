import yfinance as yf
import pandas as pd
import datetime
import os
from typing import List
import time

def check_existing_data(file_path: str) -> bool:
    """Sprawdza czy plik z danymi istnieje i czy nie jest pusty"""
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            return not df.empty
        except:
            return False
    return False

def fetch_stock_data(tickers: List[str], start_date: datetime.date, end_date: datetime.date, csv_path: str) -> None:
    # Najpierw sprawdź czy mamy już dane
    if check_existing_data(csv_path):
        print(f"Znaleziono istniejące dane w {csv_path}")
        return

    print("Pobieranie nowych danych...")
    all_data = []

    for ticker in tickers:
        try:
            print(f"Pobieranie danych dla {ticker}...")
            # Próba pobrania danych
            for attempt in range(3):  # 3 próby dla każdego tickera
                try:
                    ticker_data = yf.download(
                        ticker,
                        start=start_date,
                        end=end_date,
                        interval='1d',
                        progress=False
                    )
                    if not ticker_data.empty:
                        ticker_data = ticker_data.reset_index()
                        ticker_data['Ticker'] = ticker
                        all_data.append(ticker_data)
                        break
                    time.sleep(2)  # Większe opóźnienie między próbami
                except Exception as e:
                    print(f"Próba {attempt + 1} nie powiodła się dla {ticker}")
                    time.sleep(5)  # Jeszcze większe opóźnienie po błędzie

        except Exception as e:
            print(f"Nie udało się pobrać danych dla {ticker}: {str(e)}")

    if all_data:
        data_long = pd.concat(all_data, ignore_index=True)
        data_long = data_long[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        data_long.to_csv(csv_path, index=False)
        print(f"\nDane zostały zapisane do {csv_path}")
    else:
        print("Nie udało się pobrać żadnych danych. Sprawdź połączenie internetowe lub użyj istniejących danych.")

if __name__ == "__main__":
    TICKERS = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'TSLA']
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=2*365)
    csv_path = 'data/historical_prices.csv'

    fetch_stock_data(TICKERS, start_date, end_date, csv_path)
