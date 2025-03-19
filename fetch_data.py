import yfinance as yf
import pandas as pd
import datetime
import time

# Lista tickerów dla Magnificent 7
tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'TSLA']

# Ustalenie zakresu dat: ostatnie dwa lata
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=2*365)

all_data = []
failed_tickers = []

for ticker in tickers:
    try:
        print(f"Pobieram dane dla {ticker}...")
        # Ustawienie interwału na dzienny
        df = yf.download(ticker, start=start_date, end=end_date, interval='1d', progress=False)
        # Dodaj krótkie opóźnienie między zapytaniami
        time.sleep(1)
        if df.empty:
            print(f"Brak danych dla {ticker}")
            failed_tickers.append(ticker)
            continue
        df['Ticker'] = ticker
        df.index.name = 'Date'
        all_data.append(df)
        print(f"Pobrano dane dla {ticker}")
    except Exception as e:
        print(f"Nie udało się pobrać danych dla {ticker}. Powód: {e}")
        failed_tickers.append(ticker)

if all_data:
    data = pd.concat(all_data)
    data.reset_index(inplace=True)
    data = data[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]
    data.to_csv('data/historical_prices.csv', index=False)
    print("Plik data/historical_prices.csv został wygenerowany.")
else:
    print("Brak danych do zapisania.")

if failed_tickers:
    print(f"Nie udało się pobrać danych dla następujących tickerów: {failed_tickers}")
