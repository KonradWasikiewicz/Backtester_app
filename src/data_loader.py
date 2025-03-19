import pandas as pd

def load_data(filepath: str) -> pd.DataFrame:
    """
    Wczytuje dane historyczne z pliku CSV.
    Zakłada, że plik zawiera kolumny: 'Date', 'Open', 'High', 'Low', 'Close', 'Volume'.
    """
    data = pd.read_csv(filepath, parse_dates=['Date'])
    data.sort_values('Date', inplace=True)
    data.set_index('Date', inplace=True)
    return data
