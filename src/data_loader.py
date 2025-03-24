import pandas as pd
import os

class DataLoader:
    @staticmethod
    def load_data(csv_path: str, ticker: str = None) -> pd.DataFrame:
        """Load and preprocess data from CSV"""
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"File not found: {csv_path}")
        
        df = pd.read_csv(csv_path)
        
        if ticker:
            df = df[df['Ticker'] == ticker]
            
        if df.empty:
            raise ValueError(f"No data found for {ticker}")
            
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        
        return df
