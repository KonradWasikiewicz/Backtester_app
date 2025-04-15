import pandas as pd
import numpy as np
import logging
from .base import BaseStrategy # Importuj klasę bazową
from typing import Dict, Tuple, Optional, List

logger = logging.getLogger(__name__)

class BollingerBandsStrategy(BaseStrategy):
    """
    | Characteristic | Description |
    |---------------|-------------|
    | **Idea** | Uses price movements relative to volatility bands to identify potential mean reversion opportunities. |
    | **Buy Signal** | Price touches or crosses below the lower band (oversold condition). |
    | **Sell Signal** | Price touches or crosses above the upper band (overbought condition). |
    | **Key Parameters** | `window` (period for calculating the moving average), `num_std` (number of standard deviations for band width). |
    | **Application** | Suitable for range-bound markets with mean-reverting price action. |
    | **Limitations** | May generate false signals in strong trending markets, requires careful parameter tuning based on market volatility. |
    """

    def __init__(self, tickers: list[str], window: int = 20, num_std: float = 2.0):
        """
        Initializes the Bollinger Bands strategy.

        Args:
            tickers (list[str]): A list of ticker symbols this strategy applies to.
            window (int): The lookback period for calculating the moving average
                          and standard deviation. Defaults to 20. Must be > 1.
            num_std (float): The number of standard deviations to use for the
                             upper and lower bands. Defaults to 2.0. Must be positive.

        Raises:
            ValueError: If parameters are invalid.
        """
        super().__init__(tickers) # Wywołaj konstruktor klasy bazowej

        # --- Parameter Validation ---
        if not isinstance(window, int) or window <= 1:
            msg = f"Bollinger Strategy: window must be an integer greater than 1, got {window}"
            logger.error(msg)
            raise ValueError(msg)
        if not isinstance(num_std, (int, float)) or num_std <= 0:
            msg = f"Bollinger Strategy: num_std must be a positive number, got {num_std}"
            logger.error(msg)
            raise ValueError(msg)

        # --- Store Parameters ---
        self.window = window
        self.num_std = num_std
        logger.debug(f"BollingerBandsStrategy initialized for tickers {tickers} with window={window}, num_std={num_std}")


    def generate_signals(self, ticker: str, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Generates trading signals for a specific ticker based on Bollinger Bands.

        Args:
            ticker (str): The ticker symbol for which to generate signals.
            data (pd.DataFrame): DataFrame containing historical OHLCV data for the ticker.
                                 Must include a 'Close' column and have a DatetimeIndex.

        Returns:
            Optional[pd.DataFrame]: A DataFrame with the same index as the input data,
                                    containing 'SMA', 'Upper_Band', 'Lower_Band',
                                    'Signal', and 'Position' columns.
                                    Returns None if data is insufficient or signals cannot be generated.
        """
        required_data_length = self.window # Need 'window' periods for calculation

        if data is None or data.empty or 'Close' not in data.columns:
            logger.warning(f"Bollinger Strategy ({ticker}): Input data is missing or invalid.")
            return None
        if len(data) < required_data_length:
            logger.warning(f"Bollinger Strategy ({ticker}): Insufficient data ({len(data)} rows) for window {self.window}. Need at least {required_data_length}.")
            return None

        # --- Calculate Bollinger Bands ---
        df = pd.DataFrame(index=data.index)
        try:
            df['Close'] = data['Close'] # Copy necessary column
            # Calculate rolling mean (Simple Moving Average - SMA)
            df['SMA'] = df['Close'].rolling(window=self.window, min_periods=self.window).mean()
            # Calculate rolling standard deviation
            rolling_std = df['Close'].rolling(window=self.window, min_periods=self.window).std()
            # Calculate bands
            df['Upper_Band'] = df['SMA'] + (rolling_std * self.num_std)
            df['Lower_Band'] = df['SMA'] - (rolling_std * self.num_std)
        except Exception as e:
            logger.error(f"Bollinger Strategy ({ticker}): Error calculating Bands: {e}")
            return None

        # Drop initial rows where bands couldn't be calculated
        df.dropna(subset=['SMA', 'Upper_Band', 'Lower_Band'], inplace=True)
        if df.empty:
            logger.warning(f"Bollinger Strategy ({ticker}): DataFrame empty after dropping NA values from band calculation.")
            return None

        # --- Generate Signals ---
        # Signal: 1 for Buy (Close crosses below Lower Band), -1 for Sell (Close crosses above Upper Band)
        # This version signals when *entering* the reversion zone (below lower / above upper)

        # Simple entry signals:
        buy_signal = df['Close'] < df['Lower_Band']
        sell_signal = df['Close'] > df['Upper_Band']

        # Alternative: Signals on crossing back *into* the bands (mean reversion trigger)
        # prev_close = df['Close'].shift(1)
        # buy_signal = (prev_close < df['Lower_Band'].shift(1)) & (df['Close'] >= df['Lower_Band']) # Crosses back above lower
        # sell_signal = (prev_close > df['Upper_Band'].shift(1)) & (df['Close'] <= df['Upper_Band']) # Crosses back below upper

        # Assign signals
        df['Signal'] = 0.0
        df.loc[buy_signal, 'Signal'] = 1.0
        df.loc[sell_signal, 'Signal'] = -1.0 # Assuming sell means exit long / enter short

        # --- Determine Position ---
        # Position: Hold the position indicated by the last signal.
        # For mean reversion, often you exit when price returns to the SMA.
        # Simple approach: Hold position based on last band touch signal.
        df['Position'] = df['Signal'].replace(0.0, np.nan).ffill().fillna(0.0)

        # Example Exit Logic (Mean Reversion): Exit when price crosses back over SMA
        # position_holding = df['Position'].shift(1).fillna(0.0)
        # exit_long = (position_holding == 1.0) & (df['Close'] >= df['SMA']) & (df['Close'].shift(1) < df['SMA'].shift(1))
        # exit_short = (position_holding == -1.0) & (df['Close'] <= df['SMA']) & (df['Close'].shift(1) > df['SMA'].shift(1))
        # df.loc[exit_long | exit_short, 'Signal'] = -position_holding[exit_long | exit_short] # Signal to exit
        # Re-calculate position based on entry and exit signals might be needed here.
        # For simplicity, we stick to the basic position logic for now.

        #logger.debug(f"Bollinger Strategy ({ticker}): Generated {int(sum(abs(df['Signal'])))} signals.")

        # Return relevant columns
        return df[['Close', 'SMA', 'Upper_Band', 'Lower_Band', 'Signal', 'Position']]