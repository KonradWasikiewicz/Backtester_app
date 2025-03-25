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
        """Get unique tickers from historical data excluding benchmark"""
        df = pd.read_csv(config.DATA_FILE)
        tickers = df['Ticker'].unique()
        return [t for t in tickers if t != BENCHMARK_TICKER]

    def load_data(self, ticker):
        """Load historical data for given ticker"""
        data = yf.download(ticker, start=self.start_date, end=self.end_date)
        return data

    def load_benchmark(self):
        """Load S&P 500 data as benchmark"""
        return self.load_data(self.benchmark)

    @staticmethod
    def load_data(tickers: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """Load price data for specified tickers"""
        try:
            df = pd.read_csv(config.DATA_FILE)
            
            if tickers is None:
                tickers = DataLoader.get_available_tickers()
                
            data = {}
            for ticker in tickers:
                ticker_data = df[df['Ticker'] == ticker].copy()
                if ticker_data.empty:
                    raise DataError(f"No data found for ticker {ticker}")
                ticker_data['Date'] = pd.to_datetime(ticker_data['Date'])
                ticker_data.set_index('Date', inplace=True)
                data[ticker] = ticker_data
                
            return data
        except Exception as e:
            raise DataError(f"Error loading data: {str(e)}")
