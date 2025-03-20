import yfinance as yf
import pandas as pd
import datetime
import os
from typing import List
import time

def fetch_stock_data(tickers: List[str], start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
    all_data = []
    for ticker in tickers:
        try:
            print(f"Pobieranie danych dla {ticker}...")
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
            else:
                print(f"Brak danych dla {ticker}")
            time.sleep(1)  # Dodanie opóźnienia między zapytaniami
        except Exception as e:
            print(f"Błąd podczas pobierania {ticker}: {str(e)}")

    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

if __name__ == "__main__":
    # Lista tickerów
    TICKERS = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'TSLA']

    # Zakres dat: ostatnie 2 lata
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=2*365)

    try:
        # Utworzenie katalogu data jeśli nie istnieje
        os.makedirs('data', exist_ok=True)

        # Pobieranie danych
        data_long = fetch_stock_data(TICKERS, start_date, end_date)

        if not data_long.empty:
            # Wybór potrzebnych kolumn i zapis do CSV
            data_long = data_long[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]
            data_long.to_csv('data/historical_prices.csv', index=False)
            print("\nPlik historical_prices.csv został zapisany pomyślnie.")
        else:
            print("Nie udało się pobrać żadnych danych.")

    except Exception as e:
        print(f"Wystąpił błąd: {str(e)}")
