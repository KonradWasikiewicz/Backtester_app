"""
Data Service Module

This service handles data acquisition, processing, and management for the backtester.
It acts as a data access layer between the application and various data sources.
"""

import os
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple, Any
import csv
import json

# Local imports
from src.core.exceptions import DataError
from src.core.constants import DATA_DIR

# Set up logging
logger = logging.getLogger(__name__)

class DataService:
    """
    Service for handling data operations in the backtesting application.
    
    This class provides methods for loading, processing, and manipulating
    market data used in backtesting simulations.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the DataService.
        
        Args:
            data_dir: Optional path to the data directory
        """
        self.data_dir = data_dir or DATA_DIR
        self.data_cache = {}  # Cache for loaded data
        logger.info(f"DataService initialized with data directory: {self.data_dir}")
        
        # Ensure data directory exists
        if not os.path.exists(self.data_dir):
            try:
                os.makedirs(self.data_dir)
                logger.info(f"Created data directory at {self.data_dir}")
            except Exception as e:
                logger.error(f"Failed to create data directory: {e}")
                
    def get_available_tickers(self) -> List[str]:
        """
        Get list of available ticker symbols in the data directory.
        
        Returns:
            List of ticker symbols with data files
        """
        try:
            # Get all CSV files in the data directory
            files = [f for f in os.listdir(self.data_dir) 
                    if f.endswith('.csv') and os.path.isfile(os.path.join(self.data_dir, f))]
            
            # Extract ticker symbols from filenames
            tickers = [f.split('.')[0].upper() for f in files]
            logger.debug(f"Found {len(tickers)} tickers in data directory")
            return sorted(tickers)
        except Exception as e:
            logger.error(f"Error retrieving available tickers: {e}")
            return []
            
    def load_data(self, 
                 ticker: str, 
                 start_date: Optional[Union[str, datetime]] = None,
                 end_date: Optional[Union[str, datetime]] = None,
                 use_cache: bool = True) -> Optional[pd.DataFrame]:
        """
        Load historical price data for a given ticker.
        
        Args:
            ticker: Ticker symbol
            start_date: Start date for the data (optional)
            end_date: End date for the data (optional)
            use_cache: Whether to use cached data if available
            
        Returns:
            DataFrame with OHLCV data or None if loading fails
        """
        cache_key = f"{ticker}"
        
        # Check if data is in cache
        if use_cache and cache_key in self.data_cache:
            data = self.data_cache[cache_key].copy()
            logger.debug(f"Using cached data for {ticker}")
        else:
            # Load data from file
            try:
                file_path = os.path.join(self.data_dir, f"{ticker.lower()}.csv")
                if not os.path.isfile(file_path):
                    logger.warning(f"Data file for {ticker} not found at {file_path}")
                    return None
                
                # Read the CSV file
                data = pd.read_csv(file_path, parse_dates=['Date'], index_col='Date')
                
                # Standardize column names
                data.columns = [col.capitalize() for col in data.columns]
                
                # Ensure required columns exist
                required_cols = ['Open', 'High', 'Low', 'Close']
                if not all(col in data.columns for col in required_cols):
                    logger.error(f"Missing required columns in {ticker} data file")
                    return None
                
                # Cache the data for future use
                if use_cache:
                    self.data_cache[cache_key] = data.copy()
                    
                logger.info(f"Successfully loaded data for {ticker} with {len(data)} rows")
            
            except Exception as e:
                logger.error(f"Error loading data for {ticker}: {e}")
                return None
        
        # Apply date filtering if provided
        if start_date or end_date:
            data = self._filter_data_by_date(data, start_date, end_date)
            
        return data
        
    def load_data_for_tickers(self, 
                            tickers: List[str], 
                            start_date: Optional[Union[str, datetime]] = None,
                            end_date: Optional[Union[str, datetime]] = None,
                            use_cache: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Load data for multiple tickers.
        
        Args:
            tickers: List of ticker symbols
            start_date: Start date for the data (optional)
            end_date: End date for the data (optional)
            use_cache: Whether to use cached data
            
        Returns:
            Dictionary mapping ticker symbols to their respective dataframes
        """
        data_dict = {}
        
        for ticker in tickers:
            data = self.load_data(ticker, start_date, end_date, use_cache)
            if data is not None:
                data_dict[ticker] = data
        
        logger.info(f"Loaded data for {len(data_dict)}/{len(tickers)} tickers")
        return data_dict
    
    def _filter_data_by_date(self, 
                           data: pd.DataFrame, 
                           start_date: Optional[Union[str, datetime]] = None,
                           end_date: Optional[Union[str, datetime]] = None) -> pd.DataFrame:
        """
        Filter a dataframe by date range.
        
        Args:
            data: DataFrame with DatetimeIndex
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            Filtered DataFrame
        """
        if start_date is not None:
            if isinstance(start_date, str):
                start_date = pd.to_datetime(start_date)
            data = data[data.index >= start_date]
            
        if end_date is not None:
            if isinstance(end_date, str):
                end_date = pd.to_datetime(end_date)
            data = data[data.index <= end_date]
            
        return data
    
    def save_data(self, 
                ticker: str, 
                data: pd.DataFrame,
                overwrite: bool = False) -> bool:
        """
        Save data for a ticker to CSV file.
        
        Args:
            ticker: Ticker symbol
            data: DataFrame with OHLCV data
            overwrite: Whether to overwrite existing file
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            file_path = os.path.join(self.data_dir, f"{ticker.lower()}.csv")
            
            # Check if file exists and overwrite flag is False
            if os.path.isfile(file_path) and not overwrite:
                logger.warning(f"File {file_path} already exists and overwrite is False")
                return False
                
            # Ensure data has a DatetimeIndex
            if not isinstance(data.index, pd.DatetimeIndex):
                if 'date' in data.columns or 'Date' in data.columns:
                    date_col = 'date' if 'date' in data.columns else 'Date'
                    data = data.set_index(date_col)
                    logger.info(f"Set index to {date_col} column")
                else:
                    logger.error(f"Cannot save data for {ticker}: No date column or DatetimeIndex")
                    return False
            
            # Reset index to make Date a column
            data.reset_index(inplace=True)
            data.rename(columns={'index': 'Date'}, inplace=True)
            
            # Save to CSV
            data.to_csv(file_path, index=False)
            logger.info(f"Saved data for {ticker} to {file_path}")
            
            # Update cache if present
            cache_key = f"{ticker}"
            if cache_key in self.data_cache:
                self.data_cache[cache_key] = data.set_index('Date')
                
            return True
            
        except Exception as e:
            logger.error(f"Error saving data for {ticker}: {e}")
            return False
            
    def get_merged_data(self, 
                      tickers: List[str], 
                      column: str = 'Close',
                      start_date: Optional[Union[str, datetime]] = None,
                      end_date: Optional[Union[str, datetime]] = None) -> pd.DataFrame:
        """
        Get merged data for multiple tickers into a single DataFrame.
        
        Args:
            tickers: List of ticker symbols
            column: Which price column to extract (default: 'Close')
            start_date: Start date for the data (optional)
            end_date: End date for the data (optional)
            
        Returns:
            DataFrame with each ticker as a column and dates as index
        """
        merged_data = None
        column = column.capitalize()  # Standardize column name
        
        for ticker in tickers:
            data = self.load_data(ticker, start_date, end_date)
            if data is not None and column in data.columns:
                ticker_data = data[column]
                
                if merged_data is None:
                    merged_data = pd.DataFrame(ticker_data)
                    merged_data.columns = [ticker]
                else:
                    merged_data[ticker] = ticker_data
            else:
                logger.warning(f"Could not include {ticker} in merged data")
                
        if merged_data is None or merged_data.empty:
            logger.error("No data available for merging")
            return pd.DataFrame()
            
        # Forward fill missing values (for different trading days in different markets)
        merged_data = merged_data.fillna(method='ffill')
        
        return merged_data
    
    def generate_synthetic_data(self, 
                              tickers: List[str], 
                              days: int = 252,
                              volatility: float = 0.015,
                              save: bool = False) -> Dict[str, pd.DataFrame]:
        """
        Generate synthetic OHLCV data for testing.
        
        Args:
            tickers: List of ticker symbols
            days: Number of days to generate
            volatility: Price volatility parameter
            save: Whether to save the data to files
            
        Returns:
            Dictionary mapping ticker symbols to generated dataframes
        """
        np.random.seed(42)  # For reproducibility
        data_dict = {}
        
        # Generate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        dates = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days
        
        for ticker in tickers:
            try:
                # Generate random returns with different mean for each ticker
                mean_return = np.random.uniform(-0.0002, 0.0002)  # Different mean daily returns
                returns = np.random.normal(mean_return, volatility, len(dates))
                
                # Start price between $10 and $200
                start_price = np.random.uniform(10, 200)
                prices = start_price * np.cumprod(1 + returns)
                
                # Generate OHLC from close prices
                df = pd.DataFrame(index=dates)
                df['Close'] = prices
                df['Open'] = df['Close'].shift(1) * (1 + np.random.normal(0, volatility/2, len(df)))
                df.loc[df.index[0], 'Open'] = prices[0] * (1 + np.random.normal(0, volatility/2))
                
                # High is max of open, close, plus some random amount
                df['High'] = np.maximum(df['Open'], df['Close']) * (1 + np.abs(np.random.normal(0, volatility/2, len(df))))
                
                # Low is min of open, close, minus some random amount
                df['Low'] = np.minimum(df['Open'], df['Close']) * (1 - np.abs(np.random.normal(0, volatility/2, len(df))))
                
                # Volume has mild correlation with absolute returns
                abs_returns = np.abs(returns)
                volume_base = np.random.uniform(50000, 500000)  # Base volume different for each ticker
                df['Volume'] = volume_base * (1 + 2 * abs_returns) * np.random.lognormal(0, 0.5, len(df))
                
                # Ensure price columns are positive
                for col in ['Open', 'High', 'Low', 'Close']:
                    df[col] = np.maximum(df[col], 0.01)
                    
                # Ensure High >= Open, Close and Low <= Open, Close
                df['High'] = df[['High', 'Open', 'Close']].max(axis=1)
                df['Low'] = df[['Low', 'Open', 'Close']].min(axis=1)
                
                # Round to 2 decimal places
                for col in ['Open', 'High', 'Low', 'Close']:
                    df[col] = round(df[col], 2)
                    
                df['Volume'] = df['Volume'].astype(int)
                
                data_dict[ticker] = df
                
                if save:
                    self.save_data(ticker, df, overwrite=True)
                    
                logger.info(f"Generated synthetic data for {ticker}")
                
            except Exception as e:
                logger.error(f"Error generating synthetic data for {ticker}: {e}")
                
        return data_dict
    
    def clear_cache(self) -> None:
        """
        Clear the data cache.
        """
        self.data_cache = {}
        logger.info("Data cache cleared")
        
    def get_data_summary(self, tickers: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get a summary of available data.
        
        Args:
            tickers: Optional list of tickers to summarize (if None, use all available)
            
        Returns:
            Dictionary with data summaries for each ticker
        """
        if tickers is None:
            tickers = self.get_available_tickers()
            
        summary = {}
        
        for ticker in tickers:
            data = self.load_data(ticker)
            if data is not None:
                summary[ticker] = {
                    "start_date": data.index.min().strftime('%Y-%m-%d'),
                    "end_date": data.index.max().strftime('%Y-%m-%d'),
                    "days": len(data),
                    "years": round(len(data) / 252, 1),  # Approximate trading days per year
                    "last_close": data['Close'].iloc[-1],
                    "avg_volume": int(data['Volume'].mean()) if 'Volume' in data.columns else None
                }
                
        return summary