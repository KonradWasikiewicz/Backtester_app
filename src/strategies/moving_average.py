import pandas as pd
# pandas_ta - a technical analysis library built on Pandas
# Install with: pip install pandas_ta
try:
    import pandas_ta as ta
except ImportError:
    # Provide a clear error message if pandas_ta is not installed
    raise ImportError(
        "The 'pandas_ta' library is required for this strategy but is not installed. "
        "Please install it using: pip install pandas_ta"
    )
# Adjust the import path to match the actual location of BaseStrategy
from src.strategies.base import BaseStrategy
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)

# --- CLASS NAME REMAINS UNCHANGED (or adjust to yours) ---
class MovingAverageStrategy(BaseStrategy):
    """
    | Characteristic | Description |
    |---------------|-------------|
    | **Idea** | Uses crossovers between short-term and long-term moving averages to identify potential trend changes. |
    | **Buy Signal** | Short moving average crosses above the long moving average. |
    | **Sell Signal** | Short moving average crosses below the long moving average. |
    | **Key Parameters** | `short_window` (period for short-term MA), `long_window` (period for long-term MA). |
    | **Application** | Suitable for trending markets. May generate false signals during consolidation periods. |
    | **Limitations** | Delayed reaction to price changes, sensitivity to period selection, poor performance in sideways markets. |
    """
    def __init__(self, tickers: list[str], short_window: int = 20, long_window: int = 50):
        """
        Initializes the MA Cross strategy.

        Args:
            tickers (list[str]): List of tickers for the strategy.
            short_window (int): Period (number of candles) for the short-term moving average. Default 20.
            long_window (int): Period (number of candles) for the long-term moving average. Default 50.

        Raises:
            ValueError: If periods are not positive integers or short_window >= long_window.
        """
        super().__init__() # Call the base class constructor without arguments
        if not (isinstance(short_window, int) and isinstance(long_window, int) and short_window > 0 and long_window > 0):
            logger.error(f"Invalid window parameters: short={short_window}, long={long_window}. Must be positive integers.")
            raise ValueError("Moving average periods must be positive integers.")
        if short_window >= long_window:
            logger.error(f"Invalid window parameters: short={short_window}, long={long_window}. Short must be less than long.")
            raise ValueError("The short window must be smaller than the long window.")

        self.tickers = tickers
        self.short_window = short_window
        self.long_window = long_window
        # Store parameters also in a dictionary for easier access/logging
        self.parameters = {'short_window': short_window, 'long_window': long_window}
        logger.info(f"Moving Average Strategy initialized with parameters: {self.parameters}")

    def get_parameters(self) -> dict:
        """Returns a dictionary with the current strategy parameters."""
        return self.parameters

    def generate_signals(self, ticker: str, data: pd.DataFrame) -> pd.DataFrame: # Added 'ticker' argument
        """
        Generates trading signals based on moving average crossovers.

        Args:
            ticker (str): Instrument ticker (currently unused in this logic, but required by the interface).
            data (pd.DataFrame): DataFrame containing at least the 'Close' column
                                 and enough history to calculate the longest average.

        Returns:
            pd.DataFrame: DataFrame with the same index as `data`, containing columns:
                          'Signal' (1 for buy, -1 for sell, 0 for no signal on that day)
                          'Positions' (1 for long position, -1 for short (if implemented), 0 for no position)
                          'Reason' (descriptive reason for generating the signal)

        Raises:
            ValueError: If the 'Close' column is missing in the data.
            KeyError: If the calculated SMA columns do not appear in the DataFrame.
        """
        required_column = 'Close'
        if required_column not in data.columns:
            logger.error(f"Required column '{required_column}' not found in input data.")
            raise ValueError(f"DataFrame must contain '{required_column}' column.")

        # Check if there is enough data
        if len(data) < self.long_window:
            logger.warning(f"Not enough data ({len(data)} rows) to calculate the long SMA ({self.long_window}). Returning no signals for {ticker}.") # Added ticker to log
            signals = pd.DataFrame(index=data.index)
            signals['Signal'] = 0
            signals['Positions'] = 0
            signals['Reason'] = ''
            return signals

        # Create a copy to avoid modifying the original DataFrame (if required)
        df = data.copy()
        signals = pd.DataFrame(index=df.index)
        signals['Signal'] = 0  # Default to no signal
        signals['Reason'] = '' # New column for signal reason

        short_sma_col = f'SMA_{self.short_window}'
        long_sma_col = f'SMA_{self.long_window}'

        try:
            # Calculate moving averages using pandas_ta
            df.ta.sma(length=self.short_window, append=True, col_names=(short_sma_col,))
            df.ta.sma(length=self.long_window, append=True, col_names=(long_sma_col,))

            # Check if columns were added correctly
            if short_sma_col not in df.columns or long_sma_col not in df.columns:
                 logger.error(f"SMA columns ({short_sma_col}, {long_sma_col}) not found after pandas_ta calculation for {ticker}.") # Added ticker
                 raise KeyError(f"SMA columns not found after calculation for {ticker}.")

            # --- Signal Generation Logic ---
            # Buy condition: short SMA crosses above long SMA from below
            buy_condition = (df[short_sma_col] > df[long_sma_col]) & (df[short_sma_col].shift(1) <= df[long_sma_col].shift(1))
            # Sell condition: short SMA crosses below long SMA from above
            sell_condition = (df[short_sma_col] < df[long_sma_col]) & (df[short_sma_col].shift(1) >= df[long_sma_col].shift(1))

            # Assign signals and reasons
            signals.loc[buy_condition, 'Signal'] = 1
            signals.loc[buy_condition, 'Reason'] = f'SMA{self.short_window} Cross Above SMA{self.long_window}'
            
            signals.loc[sell_condition, 'Signal'] = -1
            signals.loc[sell_condition, 'Reason'] = f'SMA{self.short_window} Cross Below SMA{self.long_window}'

            # --- Position Holding Logic ---
            # Replace 0 with NA, forward fill, fill remaining NA with 0
            positions_series = signals['Signal'].replace(0, pd.NA)
            positions_series = positions_series.ffill()
            positions_series = positions_series.fillna(0)
            # Infer the best possible dtype after filling NAs, as suggested by the warning
            positions_series = positions_series.infer_objects(copy=False)
            # Ensure the final type is integer
            signals['Positions'] = positions_series.astype(int)
            signals['Positions'] = signals['Positions'].replace(-1, 0)  # No short positions

            # --- Updated log to match strategy name ---
            logger.debug(f"Generated {signals['Signal'].ne(0).sum()} signals for Moving Average strategy on {ticker}.") # Added ticker
            logger.debug(f"Buy signals: {signals['Signal'].eq(1).sum()}, Sell signals: {signals['Signal'].eq(-1).sum()} for {ticker}.") # Added ticker

        except Exception as e:
            # --- Updated log to match strategy name ---
            logger.error(f"Error during Moving Average signal generation for {ticker}: {e}", exc_info=True) # Added ticker
            signals['Signal'] = 0
            signals['Positions'] = 0
            signals['Reason'] = '' # Reset reason in case of error
            # raise e # Optionally re-raise

        # Return signals, positions, and reasons
        return signals[['Signal', 'Positions', 'Reason']]
