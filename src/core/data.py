import logging
import pandas as pd
import traceback
from pathlib import Path
from typing import Dict, Optional, List, Union, Tuple # Dodano Union, Tuple
import os

# Importuj konfigurację, aby uzyskać ścieżkę do danych i nazwę benchmarka
# Zakładamy, że config.py jest w tym samym katalogu (core) lub dostępny przez src.core
try:
    from .config import config
except ImportError:
    # Spróbuj importu z poziomu src, jeśli uruchamiane z głównego katalogu
    try:
        from src.core.config import config
    except ImportError:
         # Fallback na twardo zakodowane wartości, jeśli config nie jest dostępny
         # To nie jest idealne, ale pozwala na działanie modułu w izolacji
         logging.error("Could not import config for DataLoader. Using hardcoded defaults.")
         class MockConfig:
             DATA_PATH = "data/historical_prices.csv"
             BENCHMARK_TICKER = "SPY"
         config = MockConfig()


logger = logging.getLogger(__name__)

class DataLoader:
    """
    Handles loading and basic preprocessing of historical financial data
    from a CSV file. Caches loaded data for efficiency.
    """

    def __init__(self, data_path: Optional[Union[str, Path]] = None):
        """
        Initializes the DataLoader.

        Args:
            data_path (Optional[Union[str, Path]]): Path to the historical data CSV file.
                                                    If None, uses the path from the global config.
        """
        self.data_path = Path(data_path or config.DATA_PATH)
        self.benchmark_ticker = config.BENCHMARK_TICKER
        self._data_cache: Dict[str, pd.DataFrame] = {} # Cache dla danych tickerów
        self._full_data_cache: Optional[pd.DataFrame] = None # Cache dla całego wczytanego pliku
        self._available_tickers: Optional[List[str]] = None # Cache dla listy tickerów
        logger.debug(f"DataLoader initialized. Data path: '{self.data_path}', Benchmark: '{self.benchmark_ticker}'")


    def _load_and_cache_full_data(self) -> bool:
        """Loads the entire CSV data file into cache if not already loaded."""
        if self._full_data_cache is not None:
            return True # Already cached

        if not self.data_path.exists():
            logger.error(f"Data file not found at specified path: {self.data_path}")
            return False
        if not self.data_path.is_file():
             logger.error(f"Specified path is not a file: {self.data_path}")
             return False

        try:
            logger.debug(f"Loading historical data from: {self.data_path}...")
            # Kluczowe kolumny: Date, Ticker, Open, High, Low, Close, Volume
            # Upewnij się, że 'Date' jest parsowana poprawnie
            df = pd.read_csv(
                self.data_path,
                parse_dates=['Date'] # Powiedz pandas, która kolumna to data
            )
            logger.debug(f"CSV loaded successfully: {len(df)} rows, {len(df.columns)} columns.")

            # --- Podstawowa Walidacja Danych ---
            required_columns = ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_columns):
                 logger.error(f"Data file missing required columns. Expected: {required_columns}, Found: {list(df.columns)}")
                 return False

            # Sprawdź typy danych (opcjonalne, ale dobre dla pewności)
            if not pd.api.types.is_datetime64_any_dtype(df['Date']):
                 logger.warning("Column 'Date' was not parsed as datetime. Attempting conversion.")
                 try:
                     df['Date'] = pd.to_datetime(df['Date'])
                 except Exception as date_err:
                      logger.error(f"Failed to convert 'Date' column to datetime: {date_err}")
                      return False

            # Cache the full dataframe
            self._full_data_cache = df
            return True

        except pd.errors.EmptyDataError:
             logger.error(f"Data file is empty: {self.data_path}")
             return False
        except FileNotFoundError: # Już sprawdzane, ale na wszelki wypadek
            logger.error(f"Data file not found during read: {self.data_path}")
            return False
        except Exception as e:
            logger.error(f"Error loading or processing data file '{self.data_path}': {str(e)}")
            logger.error(traceback.format_exc())
            return False


    def _prepare_ticker_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """Prepares and caches data for a specific ticker from the full dataset."""
        if self._full_data_cache is None:
            if not self._load_and_cache_full_data():
                return None # Failed to load base data

        if ticker in self._data_cache:
            return self._data_cache[ticker] # Return from cache

        # Filter data for the specific ticker
        ticker_df = self._full_data_cache[self._full_data_cache['Ticker'].str.upper() == ticker.upper()].copy()

        if ticker_df.empty:
            # logger.warning(f"No data found for ticker '{ticker}' in the loaded file.")
            return None # Ticker not found or has no data

        try:
            # Set 'Date' as index
            ticker_df.set_index('Date', inplace=True)

            # Ensure index is DatetimeIndex (should be due to parse_dates)
            if not isinstance(ticker_df.index, pd.DatetimeIndex):
                 logger.warning(f"Index for ticker {ticker} is not DatetimeIndex after setting. Attempting conversion.")
                 ticker_df.index = pd.to_datetime(ticker_df.index)

            # Select standard OHLCV columns
            ohlcv_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in ticker_df.columns for col in ohlcv_cols):
                 logger.error(f"Data for {ticker} missing one or more OHLCV columns.")
                 return None

            ticker_df = ticker_df[ohlcv_cols]

            # Convert columns to numeric, coercing errors
            for col in ohlcv_cols:
                ticker_df[col] = pd.to_numeric(ticker_df[col], errors='coerce')

            # Sort by date (important for time series analysis)
            ticker_df.sort_index(inplace=True)

            # Handle potential NaNs introduced by coercion (optional: fill or drop?)
            # For now, let strategies handle NaNs if necessary.
            # num_nan = ticker_df.isnull().sum().sum()
            # if num_nan > 0:
            #     logger.warning(f"Ticker {ticker}: Found {num_nan} NaN values after numeric conversion.")

            # Cache the prepared data
            self._data_cache[ticker] = ticker_df
            # logger.debug(f"Prepared and cached data for ticker '{ticker}'. Shape: {ticker_df.shape}")
            return ticker_df

        except Exception as e:
            logger.error(f"Error preparing data for ticker '{ticker}': {str(e)}")
            logger.error(traceback.format_exc())
            return None


    def load_all_data(self) -> Dict[str, pd.DataFrame]:
        """
        Loads data for all available tickers (excluding benchmark) and caches them.

        Returns:
            Dict[str, pd.DataFrame]: A dictionary mapping ticker symbols to their
                                     prepared DataFrames. Returns an empty dict on failure.
        """
        if not self._load_and_cache_full_data():
            return {} # Failed to load base data

        tickers_to_load = self.get_available_tickers() # Get non-benchmark tickers
        if not tickers_to_load:
             logger.warning("No available tickers found after loading data.")
             return {}

        loaded_data = {}
        for ticker in tickers_to_load:
            prepared_data = self._prepare_ticker_data(ticker)
            if prepared_data is not None:
                loaded_data[ticker] = prepared_data

        logger.info(f"Finished loading data for {len(loaded_data)}/{len(tickers_to_load)} requested tickers.")
        return loaded_data


    def get_ticker_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """
        Retrieves prepared historical data for a specific ticker.
        Loads from file and prepares/caches data if not already in memory.

        Args:
            ticker (str): The ticker symbol (case-insensitive).

        Returns:
            Optional[pd.DataFrame]: A DataFrame with OHLCV data and DatetimeIndex,
                                    or None if the ticker is not found or data loading fails.
        """
        ticker = ticker.upper() # Standardize case
        if ticker in self._data_cache:
            return self._data_cache[ticker]
        else:
            # Attempt to load and prepare if not cached
            return self._prepare_ticker_data(ticker)


    def load_benchmark_data_df(self) -> Optional[pd.DataFrame]:
        """
        Loads and prepares data specifically for the benchmark ticker.

        Returns:
            Optional[pd.DataFrame]: DataFrame with OHLCV data for the benchmark,
                                    or None if not found or on error.
        """
        return self.get_ticker_data(self.benchmark_ticker) # Use the standard method


    def get_available_tickers(self) -> List[str]:
        """
        Returns a sorted list of unique ticker symbols available in the data file,
        excluding the benchmark ticker. Caches the list after first read.

        Returns:
            List[str]: Sorted list of available non-benchmark ticker symbols.
        """
        if self._available_tickers is not None:
            return self._available_tickers # Return from cache

        if self._full_data_cache is None:
            if not self._load_and_cache_full_data():
                return [] # Failed to load data

        try:
            all_tickers_in_file = self._full_data_cache['Ticker'].str.upper().unique()
            # Exclude the benchmark ticker
            non_benchmark_tickers = [t for t in all_tickers_in_file if t != self.benchmark_ticker.upper()]
            self._available_tickers = sorted(non_benchmark_tickers) # Cache the list
            return self._available_tickers
        except Exception as e:
            logger.error(f"Error extracting unique tickers from data: {e}")
            return []

    def get_date_range(self) -> Tuple[pd.Timestamp, pd.Timestamp]:
        """
        Returns the earliest and latest dates available in the dataset.
        
        Returns:
            Tuple[pd.Timestamp, pd.Timestamp]: A tuple containing (min_date, max_date)
                                               or (None, None) if data couldn't be loaded.
        """
        if self._full_data_cache is None:
            if not self._load_and_cache_full_data():
                logger.error("Failed to load data for date range retrieval")
                return (None, None)
        
        try:
            dates = pd.to_datetime(self._full_data_cache['Date'])
            min_date = dates.min()
            max_date = dates.max()
            return (min_date, max_date)
        except Exception as e:
            logger.error(f"Error getting date range from data: {e}")
            return (None, None)
