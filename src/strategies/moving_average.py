import pandas as pd
import numpy as np
import logging
from .base import BaseStrategy # Importuj klasę bazową
from typing import Dict, Tuple, Optional, List

logger = logging.getLogger(__name__)

class MovingAverageCrossoverStrategy(BaseStrategy):
    """
    Implements a simple Moving Average Crossover trading strategy.

    Generates buy signals when a short-term moving average crosses above
    a long-term moving average, and sell signals when it crosses below.
    """

    def __init__(self, tickers: list[str], short_window: int = 20, long_window: int = 50):
        """
        Initializes the Moving Average Crossover strategy.

        Args:
            tickers (list[str]): A list of ticker symbols this strategy applies to.
            short_window (int): The lookback period for the short-term moving average.
                                 Defaults to 20. Must be a positive integer.
            long_window (int): The lookback period for the long-term moving average.
                                Defaults to 50. Must be a positive integer and greater than short_window.

        Raises:
            ValueError: If window parameters are invalid (not positive integers or short >= long).
        """
        super().__init__(tickers) # Wywołaj konstruktor klasy bazowej

        # --- Parameter Validation ---
        if not isinstance(short_window, int) or short_window <= 0:
            msg = f"MA Strategy: short_window must be a positive integer, got {short_window}"
            logger.error(msg)
            raise ValueError(msg)
        if not isinstance(long_window, int) or long_window <= 0:
            msg = f"MA Strategy: long_window must be a positive integer, got {long_window}"
            logger.error(msg)
            raise ValueError(msg)
        if short_window >= long_window:
            msg = f"MA Strategy: short_window ({short_window}) must be less than long_window ({long_window})"
            logger.error(msg)
            raise ValueError(msg)

        # --- Store Parameters ---
        self.short_window = short_window
        self.long_window = long_window
        logger.debug(f"MovingAverageCrossoverStrategy initialized for tickers {tickers} with short={short_window}, long={long_window}")


    def generate_signals(self, ticker: str, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Generates trading signals for a specific ticker based on MA crossover.

        Args:
            ticker (str): The ticker symbol for which to generate signals.
            data (pd.DataFrame): DataFrame containing historical OHLCV data for the ticker.
                                 Must include a 'Close' column and have a DatetimeIndex.

        Returns:
            Optional[pd.DataFrame]: A DataFrame with the same index as the input data,
                                    containing 'SMA_Short', 'SMA_Long', 'Signal', and 'Position' columns.
                                    Returns None if data is insufficient or signals cannot be generated.
        """
        required_data_length = self.long_window + 1 # Need one extra point to check crossover

        if data is None or data.empty or 'Close' not in data.columns:
            logger.warning(f"MA Strategy ({ticker}): Input data is missing or invalid.")
            return None
        if len(data) < required_data_length:
            logger.warning(f"MA Strategy ({ticker}): Insufficient data ({len(data)} rows) for long window {self.long_window}. Need at least {required_data_length}.")
            return None

        # --- Calculate Moving Averages ---
        # Use a copy to avoid modifying the original DataFrame passed to the function
        df = pd.DataFrame(index=data.index) # Create new DF with the same index
        try:
            df['Close'] = data['Close'] # Copy only the necessary column
            df['SMA_Short'] = df['Close'].rolling(window=self.short_window, min_periods=self.short_window).mean()
            df['SMA_Long'] = df['Close'].rolling(window=self.long_window, min_periods=self.long_window).mean()
        except Exception as e:
             logger.error(f"MA Strategy ({ticker}): Error calculating MAs: {e}")
             return None

        # Drop initial rows where MAs couldn't be calculated
        df.dropna(subset=['SMA_Short', 'SMA_Long'], inplace=True)
        if df.empty:
            logger.warning(f"MA Strategy ({ticker}): DataFrame empty after dropping NA values from MA calculation.")
            return None

        # --- Generate Crossover Signals ---
        # Signal: 1 for Buy (short crosses above long), -1 for Sell (short crosses below long), 0 otherwise
        # Compare current MAs with the previous day's MAs to detect the crossover event

        # Shifted values represent the *previous* day's MAs
        prev_short = df['SMA_Short'].shift(1)
        prev_long = df['SMA_Long'].shift(1)

        # Buy condition: short was below or equal long yesterday, and short is above long today
        buy_signal = (prev_short <= prev_long) & (df['SMA_Short'] > df['SMA_Long'])

        # Sell condition: short was above or equal long yesterday, and short is below long today
        sell_signal = (prev_short >= prev_long) & (df['SMA_Short'] < df['SMA_Long'])

        # Assign signals based on conditions
        df['Signal'] = 0.0
        df.loc[buy_signal, 'Signal'] = 1.0
        df.loc[sell_signal, 'Signal'] = -1.0

        # --- Determine Position ---
        # Position: Represents the desired state (1 for long, -1 for short, 0 for flat).
        # Here, we simply hold the position indicated by the last non-zero signal.
        # Fill forward the last signal to represent holding the position.
        df['Position'] = df['Signal'].replace(0.0, method='ffill').fillna(0.0)

        #logger.debug(f"MA Strategy ({ticker}): Generated {int(sum(abs(df['Signal'])))} signals.")

        # Return only the relevant columns
        return df[['SMA_Short', 'SMA_Long', 'Signal', 'Position']]