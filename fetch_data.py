import yfinance as yf
import pandas as pd
import datetime

# Lista tickerów
tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'TSLA']

# Zakres dat: ostatnie 2 lata
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=2*365)

# Pobieranie danych w szerokim formacie (multi-index)
data = yf.download(
    tickers,
    start=start_date,
    end=end_date,
    interval='1d',
    auto_adjust=False,   # aby zachować kolumny Open/High/Low/Close/Adj Close
    group_by='column',   # lub 'ticker'; w nowszych wersjach bywa różnie interpretowane
    progress=False
)

# Jeśli `data` ma wielopoziomowe kolumny, możemy je „spłaszczyć” i przekształcić w long format:
data_long = data.stack(level=1, future_stack=True).reset_index()
# Teraz mamy kolumny: Date, level_1 (ticker), Open, High, Low, Close, Adj Close, Volume itd.

# Zmieniamy nazwę kolumny level_1 na 'Ticker'
data_long.rename(columns={'level_1': 'Ticker'}, inplace=True)

# Na koniec wybieramy tylko interesujące nas kolumny:
data_long = data_long[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]

# Zapisujemy do CSV
data_long.to_csv('data/historical_prices.csv', index=False)
print("Plik historical_prices.csv został zapisany w formacie long.")
