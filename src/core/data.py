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
        self.backtest_start = datetime(2020, 1, 1)  # Main backtest period
        self.indicator_start = datetime(2019, 1, 1)  # Extra year for indicators
        self.end_date = end_date or datetime.now()

    @staticmethod
    def load_data(ticker: str) -> pd.DataFrame:
        """Load data for a specific ticker from existing CSV"""
        try:
            df = pd.read_csv(config.DATA_FILE)
            ticker_data = df[df['Ticker'] == ticker].copy()
            
            if ticker_data.empty:
                raise DataError(f"No data found for ticker {ticker}")
            
            ticker_data['Date'] = pd.to_datetime(ticker_data['Date'], utc=True)
            ticker_data.set_index('Date', inplace=True)
            return ticker_data.sort_index()
            
        except Exception as e:
            raise DataError(f"Error loading data: {str(e)}")

    @staticmethod
    def get_available_tickers() -> List[str]:
        """Get list of available tickers from CSV"""
        try:
            df = pd.read_csv(config.DATA_FILE)
            tickers = sorted(t for t in df['Ticker'].unique() if t != config.BENCHMARK_TICKER)
            return tickers
        except Exception as e:
            raise DataError(f"Error getting tickers: {str(e)}")

    @staticmethod
    def extend_historical_data() -> pd.DataFrame:
        """Load existing data without fetching new data"""
        try:
            df = pd.read_csv(config.DATA_FILE)
            df['Date'] = pd.to_datetime(df['Date'], utc=True)
            return df
        except Exception as e:
            raise DataError(f"Error loading historical data: {str(e)}")  # Fixed missing quote

    def load_benchmark(self) -> pd.DataFrame:
        """Load S&P 500 data as benchmark"""
        return self.load_data(ticker=self.benchmark)
