import pandas as pd
import os
from typing import Optional

class DataLoader:
    @staticmethod
    def load_data(csv_path: str, ticker: Optional[str] = None) -> pd.DataFrame:
        """Load and preprocess data from CSV"""
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"File not found: {csv_path}")
        
        try:
            df = pd.read_csv(csv_path)
            
            if ticker:
                df = df[df['Ticker'] == ticker]
                
            if df.empty:
                raise ValueError(f"No data found for {ticker}")
                
            # Convert dates with explicit UTC handling
            df['Date'] = pd.to_datetime(df['Date'], utc=True).dt.tz_localize(None)
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)
            
            return df
        except Exception as e:
            raise Exception(f"Error loading data: {str(e)}")
