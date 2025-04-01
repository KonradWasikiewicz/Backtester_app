import logging
import pandas as pd
import traceback
from pathlib import Path
from src.core.config import config

class DataLoader:
    """Data loading and preprocessing for backtesting"""
    
    def __init__(self, data_path=None):
        """Initialize with optional data path override"""
        self.data_path = data_path or config.DATA_PATH
        self.benchmark_ticker = config.BENCHMARK_TICKER
        self.logger = logging.getLogger(__name__)
        self._data_cache = {}
        
    def load_all_data(self):
        """Load all available data from CSV, excluding benchmark ticker"""
        try:
            # Log the path we're trying to use
            self.logger.info(f"Attempting to load data from: {self.data_path}")
            
            # Check if file exists
            if not Path(self.data_path).exists():
                self.logger.error(f"Data file not found at: {self.data_path}")
                return {}
            
            # Load all historical price data
            df = pd.read_csv(
                self.data_path,
                parse_dates=['Date']
            )
            
            self.logger.info(f"CSV loaded successfully with {len(df)} rows and {len(df.columns)} columns")
            
            # Get unique tickers from the Ticker column
            available_tickers = df['Ticker'].unique().tolist()
            
            # Remove benchmark from trading universe if present
            if self.benchmark_ticker in available_tickers:
                available_tickers.remove(self.benchmark_ticker)
                
            # Sort tickers for consistency
            self.available_tickers = sorted(available_tickers)
            
            # Process each ticker's data
            ticker_data = {}
            ticker_row_counts = {}
            
            for ticker in self.available_tickers:
                # Filter data for this ticker
                ticker_df = df[df['Ticker'] == ticker].copy()
                
                # Set date as index
                ticker_df.set_index('Date', inplace=True)
                
                # Select only OHLCV columns
                ticker_df = ticker_df[['Open', 'High', 'Low', 'Close', 'Volume']]
                
                # Sort by date
                ticker_df.sort_index(inplace=True)
                
                # Store in cache
                ticker_data[ticker] = ticker_df
                ticker_row_counts[ticker] = len(ticker_df)
            
            # Log summarized info instead of per-ticker
            self.logger.info(f"Found tickers: {', '.join(self.available_tickers)}")
            self.logger.info(f"All tickers have {list(ticker_row_counts.values())[0]} rows of data")
            self.logger.info(f"Loaded data for {len(ticker_data)} instruments")
            
            self._data_cache = ticker_data
            return ticker_data
            
        except Exception as e:
            self.logger.error(f"Error loading price data: {str(e)}")
            traceback.print_exc()
            return {}
    
    def get_ticker_data(self, ticker):
        """Get data for a specific ticker, loading if necessary"""
        if not self._data_cache:
            self.load_all_data()
            
        return self._data_cache.get(ticker)
    
    def load_benchmark_data(self):
        """Load benchmark data specifically"""
        try:
            # Check if data is already loaded
            if not self._data_cache:
                self.load_all_data()
            
            # Load full dataset again to include benchmark
            df = pd.read_csv(
                self.data_path,
                parse_dates=['Date']
            )
            
            # Filter for benchmark ticker
            benchmark_df = df[df['Ticker'] == self.benchmark_ticker].copy()
            
            if len(benchmark_df) == 0:
                self.logger.warning(f"Benchmark ticker {self.benchmark_ticker} not found in data")
                return None
                
            # Set date as index
            benchmark_df.set_index('Date', inplace=True)
            
            # Select only Close price for benchmark
            benchmark_series = benchmark_df['Close']
            
            # Sort by date
            benchmark_series.sort_index(inplace=True)
            
            return benchmark_series
            
        except Exception as e:
            self.logger.error(f"Error loading benchmark data: {str(e)}")
            return None
    
    def get_available_tickers(self):
        """Return list of all available tickers"""
        if not hasattr(self, 'available_tickers') or not self.available_tickers:
            self.load_all_data()
            
        return self.available_tickers
