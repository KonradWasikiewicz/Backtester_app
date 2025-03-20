import pandas as pd

def load_data(filepath):
    return pd.read_csv(filepath, parse_dates=['Date'])
