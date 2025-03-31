import pandas as pd
import os
import numpy as np
from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta

# Zamienić absolute import:
from .config import config
from .exceptions import DataError
from .constants import BENCHMARK_TICKER

class DataLoader:
    """
    Data loading and preprocessing.
    
    Handles loading financial data from CSV files and preparing it for backtesting.
    """
    
    def __init__(self):
        self.backtest_start = datetime(2020, 1, 1)  # Main backtest period
        self.indicator_start = datetime(2019, 1, 1)  # Extra year for indicators
        self.end_date = datetime.now()
        self.benchmark = config.BENCHMARK_TICKER
    
    @staticmethod
    def load_data(ticker: str) -> pd.DataFrame:
        """Load data for a specific ticker from existing CSV
        
        Args:
            ticker: The ticker symbol to load data for
            
        Returns:
            DataFrame containing OHLCV data for the ticker
            
        Raises:
            DataError: If data cannot be loaded or ticker not found
        """
        if not ticker:
            raise DataError("Ticker cannot be empty")
            
        try:
            # Check if file exists first
            if not os.path.exists(config.DATA_FILE):
                raise DataError(f"Data file not found: {config.DATA_FILE}")
                
            df = pd.read_csv(config.DATA_FILE)
            ticker_data = df[df['Ticker'] == ticker].copy()
            
            if ticker_data.empty:
                raise DataError(f"No data found for ticker {ticker}")
                        
            ticker_data['Date'] = pd.to_datetime(ticker_data['Date'], utc=True)
            ticker_data.set_index('Date', inplace=True)
            return ticker_data.sort_index()
            
        except pd.errors.ParserError:
            raise DataError(f"CSV file format error: {config.DATA_FILE}")
        except Exception as e:
            raise DataError(f"Error loading data: {str(e)}")

    @staticmethod
    def get_available_tickers() -> List[str]:
        """Get list of available tickers from CSV
        
        Returns:
            List of ticker symbols available in the data file
            
        Raises:
            DataError: If tickers cannot be retrieved
        """
        try:
            df = pd.read_csv(config.DATA_FILE)
            tickers = sorted(t for t in df['Ticker'].unique() if t != config.BENCHMARK_TICKER)
            return tickers
        except Exception as e:
            raise DataError(f"Error getting tickers: {str(e)}")

    @staticmethod
    def extend_historical_data() -> pd.DataFrame:
        """Load existing data without fetching new data
        
        Returns:
            DataFrame containing all historical data
            
        Raises:
            DataError: If historical data cannot be loaded
        """
        try:
            df = pd.read_csv(config.DATA_FILE)
            df['Date'] = pd.to_datetime(df['Date'], utc=True)
            return df
        except Exception as e:
            raise DataError(f"Error loading historical data: {str(e)}")

    def load_benchmark(self) -> pd.DataFrame:
        """Load S&P 500 data as benchmark
        
        Returns:
            DataFrame containing benchmark data
            
        Raises:
            DataError: If benchmark data cannot be loaded
        """
        return self.load_data(ticker=self.benchmark)
