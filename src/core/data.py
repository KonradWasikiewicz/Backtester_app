import pandas as pd
import os
import numpy as np
from typing import List, Dict, Optional
from .config import config
from .exceptions import DataError
from .constants import BENCHMARK_TICKER
import yfinance as yf
from datetime import datetime, timedelta

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
            print(f"Found tickers in CSV: {all_tickers}")
            available_tickers = [t for t in all_tickers if t != config.BENCHMARK_TICKER]
            print(f"Available trading tickers: {available_tickers}")
            return available_tickers
        except Exception as e:
            print(f"Error reading tickers from CSV: {str(e)}")
            raise DataError(f"Failed to load tickers: {str(e)}")

    @staticmethod
    def load_data(ticker: str = None, tickers: List[str] = None) -> Dict[str, pd.DataFrame]:
        """Load historical price data for one or multiple tickers"""
        try:
            df = pd.read_csv(config.DATA_FILE)
            data = {}

            if ticker:
                tickers = [ticker]
            elif tickers is None:
                tickers = DataLoader.get_available_tickers()

            for t in tickers:
                ticker_data = df[df['Ticker'] == t].copy()
                if ticker_data.empty:
                    print(f"No data found for ticker: {t}")
                    continue
                    
                ticker_data['Date'] = pd.to_datetime(ticker_data['Date'], utc=True)
                ticker_data.set_index('Date', inplace=True)
                ticker_data = ticker_data.sort_index()
                data[t] = ticker_data
                print(f"Loaded {len(ticker_data)} rows for {t}")

            return data if not ticker else next(iter(data.values())) if data else None

        except Exception as e:
            raise DataError(f"Error loading data: {str(e)}")

    def load_benchmark(self) -> pd.DataFrame:
        """Load S&P 500 data as benchmark"""
        return self.load_data(ticker=self.benchmark)
