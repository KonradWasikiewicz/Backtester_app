import pandas as pd
import numpy as np
import logging
from .base import BaseStrategy # Importuj klasę bazową
from typing import Dict, Tuple, Optional, List

logger = logging.getLogger(__name__)

class RSIStrategy(BaseStrategy):
    """
    Implements a Relative Strength Index (RSI) trading strategy.

    Generates buy signals when RSI enters the oversold region and
    sell signals when RSI enters the overbought region.
    Note: This is a simple implementation; often RSI strategies look for
    crossings *out* of these regions or divergences.
    """

    def __init__(self, tickers: list[str], period: int = 14, overbought: int = 70, oversold: int = 30):
        """
        Initializes the RSI strategy.

        Args:
            tickers (list[str]): A list of ticker symbols this strategy applies to.
            period (int): The lookback period for RSI calculation. Defaults to 14. Must be > 1.
            overbought (int): The RSI level considered overbought. Defaults to 70. Must be > oversold.
            oversold (int): The RSI level considered oversold. Defaults to 30. Must be < overbought.

        Raises:
            ValueError: If parameters are invalid.
        """
        super().__init__(tickers) # Wywołaj konstruktor klasy bazowej

        # --- Parameter Validation ---
        if not isinstance(period, int) or period <= 1:
            msg = f"RSI Strategy: period must be an integer greater than 1, got {period}"
            logger.error(msg)
            raise ValueError(msg)
        if not isinstance(overbought, int) or not (0 < overbought < 100):
            msg = f"RSI Strategy: overbought level must be an integer between 0 and 100, got {overbought}"
            logger.error(msg)
            raise ValueError(msg)
        if not isinstance(oversold, int) or not (0 < oversold < 100):
            msg = f"RSI Strategy: oversold level must be an integer between 0 and 100, got {oversold}"
            logger.error(msg)
            raise ValueError(msg)
        if oversold >= overbought:
            msg = f"RSI Strategy: oversold level ({oversold}) must be less than overbought level ({overbought})"
            logger.error(msg)
            raise ValueError(msg)

        # --- Store Parameters ---
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        logger.debug(f"RSIStrategy initialized for tickers {tickers} with period={period}, overbought={overbought}, oversold={oversold}")


    def _calculate_rsi(self, series: pd.Series) -> pd.Series:
        """
        Calculates the Relative Strength Index (RSI) for a given price series.

        Args:
            series (pd.Series): A pandas Series of prices (e.g., 'Close').

        Returns:
            pd.Series: A pandas Series containing the RSI values.
        """
        delta = series.diff()

        # Separate gains and losses
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0) # Loss is positive

        # Calculate exponential moving average (EMA) - common for RSI
        # Use adjust=False for traditional EMA calculation
        avg_gain = gain.ewm(com=self.period - 1, min_periods=self.period, adjust=False).mean()
        avg_loss = loss.ewm(com=self.period - 1, min_periods=self.period, adjust=False).mean()

        # Calculate Relative Strength (RS)
        # Avoid division by zero if avg_loss is zero
        rs = avg_gain / avg_loss.replace(0, 1e-9) # Replace 0 with a very small number

        # Calculate RSI
        rsi = 100.0 - (100.0 / (1.0 + rs))

        return rsi


    def generate_signals(self, ticker: str, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Generates trading signals for a specific ticker based on RSI levels.

        Args:
            ticker (str): The ticker symbol for which to generate signals.
            data (pd.DataFrame): DataFrame containing historical OHLCV data for the ticker.
                                 Must include a 'Close' column and have a DatetimeIndex.

        Returns:
            Optional[pd.DataFrame]: A DataFrame with the same index as the input data,
                                    containing 'RSI', 'Signal', and 'Position' columns.
                                    Returns None if data is insufficient or signals cannot be generated.
        """
        # Need enough data for RSI calculation plus one previous day
        required_data_length = self.period + 1

        if data is None or data.empty or 'Close' not in data.columns:
            logger.warning(f"RSI Strategy ({ticker}): Input data is missing or invalid.")
            return None
        if len(data) < required_data_length:
            logger.warning(f"RSI Strategy ({ticker}): Insufficient data ({len(data)} rows) for RSI period {self.period}. Need at least {required_data_length}.")
            return None

        # --- Calculate RSI ---
        df = pd.DataFrame(index=data.index)
        try:
            df['RSI'] = self._calculate_rsi(data['Close'])
            df['Close'] = data['Close']  # Add Close column to output for visualization
        except Exception as e:
            logger.error(f"RSI Strategy ({ticker}): Error calculating RSI: {e}")
            return None

        df.dropna(subset=['RSI'], inplace=True)
        if df.empty:
            logger.warning(f"RSI Strategy ({ticker}): DataFrame empty after dropping NA values from RSI calculation.")
            return None

        # --- Generate Signals ---
        # Signal: 1 for Buy (RSI crosses below oversold), -1 for Sell (RSI crosses above overbought)
        # This version generates signal *when entering* the zone.
        # Often, strategies wait for a cross *back out* of the zone.

        # Simple entry signals:
        buy_signal = df['RSI'] < self.oversold
        sell_signal = df['RSI'] > self.overbought

        # Alternative: Signals on crossing back *out* of the zones
        # prev_rsi = df['RSI'].shift(1)
        # buy_signal = (prev_rsi < self.oversold) & (df['RSI'] >= self.oversold) # Crosses back above oversold
        # sell_signal = (prev_rsi > self.overbought) & (df['RSI'] <= self.overbought) # Crosses back below overbought

        # Assign signals
        df['Signal'] = 0.0
        df.loc[buy_signal, 'Signal'] = 1.0
        df.loc[sell_signal, 'Signal'] = -1.0

        # --- Determine Position ---
        # Position: Hold the position indicated by the last signal.
        df['Position'] = df['Signal'].replace(0.0, np.nan).ffill().fillna(0.0)

        #logger.debug(f"RSI Strategy ({ticker}): Generated {int(sum(abs(df['Signal'])))} signals.")

        # Return relevant columns
        return df[['Close', 'RSI', 'Signal', 'Position']]  # Include Close column in output