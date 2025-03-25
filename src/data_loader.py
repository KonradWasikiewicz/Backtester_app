import pandas as pd
import os
import numpy as np

class DataLoader:
    @staticmethod
    def load_data(csv_path: str, ticker: str) -> pd.DataFrame:
        """Load data from CSV with validation"""
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Historical data file not found: {csv_path}")
        
        try:
            df = pd.read_csv(csv_path)
            df = df[df['Ticker'] == ticker].copy()
            
            if df.empty:
                raise ValueError(f"No data found for ticker {ticker}")
            
            # Fix datetime parsing with explicit UTC handling
            df['Date'] = pd.to_datetime(df['Date'], utc=True)
            df.set_index('Date', inplace=True)
            # Convert to naive datetime after standardizing to UTC
            df.index = df.index.tz_convert(None)
            df.sort_index(inplace=True)
            
            # Ensure all required columns exist and are numeric
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Convert price columns to numeric and handle potential errors
            for col in ['Open', 'High', 'Low', 'Close']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Replace infinite values with NaN
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            
            # Fill NaN values using forward/backward fill
            df = df.ffill().bfill()
            
            # Verify data quality
            if df['Close'].isna().any() or (df['Close'] <= 0).any():
                raise ValueError("Invalid price data detected")
                
            return df
            
        except Exception as e:
            raise Exception(f"Error loading data: {str(e)}")
