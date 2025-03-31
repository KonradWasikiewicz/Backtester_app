import pandas as pd
import numpy as np
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
import sys

# Setup logging
logger = logging.getLogger(__name__)

# Import local modules 
from .config import config
from .exceptions import DataError
from .constants import BENCHMARK_TICKER, DEFAULT_TICKERS

class DataLoader:
    """Handles loading and preprocessing of price data for backtesting"""
    
    def __init__(self, tickers=None, start_date=None, end_date=None):
        """
        Initialize DataLoader
        
        Args:
            tickers: List of ticker symbols to load
            start_date: Start date for data
            end_date: End date for data
        """
        self.tickers = tickers or DEFAULT_TICKERS
        self.start_date = start_date or "2019-01-01"  # Include extra data for lookback
        self.end_date = end_date or pd.Timestamp.now().strftime('%Y-%m-%d')
        self.data_path = Path(config.DATA_PATH)
        self._cached_data = None
        self._cached_benchmark = None
        
    def get_data(self) -> Dict[str, pd.DataFrame]:
        """
        Load and preprocess data for all tickers
        
        Returns:
            Dictionary mapping ticker symbols to DataFrames with OHLCV data
        """
        # Return cached data if available
        if self._cached_data is not None:
            return self._cached_data
            
        # Load data for each ticker
        data_dict = {}
        
        try:
            # Load full data from CSV
            csv_path = self.data_path / "historical_prices.csv"
            if not csv_path.exists():
                raise DataError(f"Data file not found: {csv_path}")
                
            # Read full data
            all_data = pd.read_csv(
                csv_path, 
                parse_dates=['Date'], 
                index_col='Date'
            )
            
            # Filter by date
            date_mask = (all_data.index >= self.start_date) & (all_data.index <= self.end_date)
            all_data = all_data[date_mask]
            
            # Split by ticker
            for ticker in self.tickers:
                ticker_mask = all_data['Ticker'] == ticker
                ticker_data = all_data[ticker_mask].copy()
                
                if len(ticker_data) == 0:
                    logger.warning(f"No data found for {ticker}")
                    continue
                
                # Drop the Ticker column and keep only OHLCV data
                ticker_data = ticker_data.drop(columns=['Ticker'])
                
                # Convert column types
                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    if col in ticker_data.columns:
                        ticker_data[col] = pd.to_numeric(ticker_data[col], errors='coerce')
                
                # Forward fill any missing data
                ticker_data = ticker_data.ffill()
                
                data_dict[ticker] = ticker_data
                
            # Store in cache
            self._cached_data = data_dict
            
            logger.info(f"Loaded data for {len(data_dict)} instruments")
            return data_dict
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}", exc_info=True)
            raise DataError(f"Failed to load data: {str(e)}")
    
    def get_benchmark_data(self) -> Optional[pd.DataFrame]:
        """
        Load benchmark data
        
        Returns:
            DataFrame with benchmark OHLCV data
        """
        # Return cached data if available
        if self._cached_benchmark is not None:
            return self._cached_benchmark
            
        try:
            # Check if benchmark is in loaded data
            all_data = self.get_data()
            if BENCHMARK_TICKER in all_data:
                self._cached_benchmark = all_data[BENCHMARK_TICKER]
                return self._cached_benchmark
            
            # Otherwise load from separate file
            csv_path = self.data_path / "historical_prices.csv"
            if not csv_path.exists():
                logger.warning(f"Benchmark data file not found: {csv_path}")
                return None
                
            # Read full data
            all_data = pd.read_csv(
                csv_path, 
                parse_dates=['Date'], 
                index_col='Date'
            )
            
            # Filter by date and ticker
            benchmark_mask = (all_data.index >= self.start_date) & (all_data.index <= self.end_date) & (all_data['Ticker'] == BENCHMARK_TICKER)
            benchmark_data = all_data[benchmark_mask].copy()
            
            if len(benchmark_data) == 0:
                logger.warning(f"No data found for benchmark {BENCHMARK_TICKER}")
                return None
            
            # Drop the Ticker column and keep only OHLCV data
            benchmark_data = benchmark_data.drop(columns=['Ticker'])
            
            # Convert column types
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                if col in benchmark_data.columns:
                    benchmark_data[col] = pd.to_numeric(benchmark_data[col], errors='coerce')
            
            # Forward fill any missing data
            benchmark_data = benchmark_data.ffill()
            
            # Store in cache
            self._cached_benchmark = benchmark_data
            
            logger.info(f"Loaded benchmark data for {BENCHMARK_TICKER}")
            return benchmark_data
            
        except Exception as e:
            logger.error(f"Error loading benchmark data: {str(e)}", exc_info=True)
            return None
