import sys
from pathlib import Path
import pandas as pd
import os
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.core.config import config
from src.core.exceptions import DataError
from src.core.constants import BENCHMARK_TICKER
import yfinance as yf

class DataLoader:
    """Data loading and preprocessing"""
    
    def __init__(self, start_date=None, end_date=None):
        self.start_date = start_date or (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')
        self.end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        self.benchmark = '^GSPC'

    @staticmethod
    def get_available_tickers() -> List[str]:
        """Get list of available tickers excluding benchmark"""
        try:
            df = pd.read_csv(config.DATA_FILE)
            all_tickers = sorted(df['Ticker'].unique())
            available_tickers = [t for t in all_tickers if t != config.BENCHMARK_TICKER]
            print(f"\nInitializing backtest with:")
            print(f"Trading instruments: {', '.join(available_tickers)}")
            print(f"Benchmark: {config.BENCHMARK_TICKER}")
            print(f"Data rows per instrument: {len(df) // len(all_tickers)}\n")
            return available_tickers
        except Exception as e:
            print(f"Error reading tickers from CSV: {str(e)}")
            raise DataError(f"Failed to load tickers: {str(e)}")

    @staticmethod
    def load_data(ticker: str) -> pd.DataFrame:
        """Load data for a specific ticker"""
        try:
            df = pd.read_csv(config.DATA_FILE)
            ticker_data = df[df['Ticker'] == ticker].copy()
            
            if ticker_data.empty:
                raise DataError(f"No data found for ticker {ticker}")
            
            # Fix datetime parsing warning by specifying utc=True
            ticker_data['Date'] = pd.to_datetime(ticker_data['Date'], utc=True)
            ticker_data.set_index('Date', inplace=True)
            return ticker_data.sort_index()
            
        except Exception as e:
            raise DataError(f"Error loading data: {str(e)}")

    def load_benchmark(self) -> pd.DataFrame:
        """Load S&P 500 data as benchmark"""
        return self.load_data(ticker=self.benchmark)

    @staticmethod
    def extend_historical_data():
        """Load and extend historical price data if needed"""
        try:
            # Get absolute path
            base_dir = Path(__file__).parent.parent.parent
            data_path = base_dir / "data" / "historical_prices.csv"
            
            # Update historical data
            from scripts.fetch_data import update_historical_data
            update_historical_data()
            
            # Load updated data
            data = pd.read_csv(data_path)
            data['Date'] = pd.to_datetime(data['Date'], utc=True)
            return data
            
        except Exception as e:
            print(f"Error extending historical data: {str(e)}")
            raise DataError("Failed to update historical data")
