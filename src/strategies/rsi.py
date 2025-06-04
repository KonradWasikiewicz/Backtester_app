import pandas as pd
import pandas_ta as ta  # type: ignore
import logging
from typing import List
# --- MODIFIED: Use absolute import ---
from src.strategies.base import BaseStrategy
# --- END MODIFIED ---

logger = logging.getLogger(__name__)

class RSIStrategy(BaseStrategy):
    """
    Implements a trading strategy based on the Relative Strength Index (RSI) indicator.

    Signals are generated when RSI crosses specified overbought or oversold levels.
    """
    def __init__(self, tickers: List[str], rsi_period: int = 14, lower_bound: int = 30, upper_bound: int = 70):
        """
        Initializes the RSI strategy.

        Args:
            tickers (list[str]): List of tickers (unused in this specific strategy but part of standard signature).
            rsi_period (int): RSI period. Defaults to 14.
            lower_bound (int): Lower RSI threshold (oversold). Defaults to 30.
            upper_bound (int): Upper RSI threshold (overbought). Defaults to 70.
        """
        super().__init__() # Call base init without arguments
        self.tickers = tickers # Store tickers even if unused
        # CORRECTED: Assign parameters directly from arguments
        self.rsi_period = rsi_period
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        # Store parameters dict as well
        self.parameters = {
            'rsi_period': self.rsi_period,
            'lower_bound': self.lower_bound,
            'upper_bound': self.upper_bound
        }
        logger.info(f"RSI Strategy initialized with parameters: {self.parameters}")

    def get_parameters(self) -> dict:
        """Returns a dictionary with the current strategy parameters."""
        return self.parameters

    def generate_signals(self, ticker: str, data: pd.DataFrame) -> pd.DataFrame: # Added 'ticker' argument
        """
        Generates trading signals based on the RSI indicator.

        Args:
            ticker (str): The instrument ticker (currently unused in this logic).
            data (pd.DataFrame): DataFrame containing at least the 'Close' column.

        Returns:
            pd.DataFrame: DataFrame with signals ('Signal'), positions ('Positions'), and reasons ('Reason').
        """
        required_column = 'Close'
        if required_column not in data.columns:
            logger.error(f"Required column '{required_column}' not found in input data for {ticker}.") # Added ticker
            raise ValueError(f"DataFrame must contain '{required_column}' column.")

        # Check if there is enough data
        if len(data) < self.rsi_period:
            logger.warning(f"Not enough data ({len(data)} rows) to calculate RSI ({self.rsi_period}) for {ticker}. Returning no signals.") # Added ticker
            signals = pd.DataFrame(index=data.index)
            signals['Signal'] = 0
            signals['Positions'] = 0
            signals['Reason'] = ''
            return signals

        df = data.copy()
        signals = pd.DataFrame(index=df.index)
        signals['Signal'] = 0
        signals['Reason'] = '' # New column for signal reason

        rsi_col = f'RSI_{self.rsi_period}'

        try:
            # Calculate RSI using pandas_ta
            df.ta.rsi(length=self.rsi_period, append=True, col_names=(rsi_col,))

            if rsi_col not in df.columns:
                logger.error(f"RSI column '{rsi_col}' not found after pandas_ta calculation for {ticker}.") # Added ticker
                raise KeyError(f"RSI column not found after calculation for {ticker}.")

            # --- Signal generation logic ---
            # Buy signal: RSI crosses the lower bound from below
            buy_condition = (df[rsi_col] > self.lower_bound) & (df[rsi_col].shift(1) <= self.lower_bound)
            # Sell signal: RSI crosses the upper bound from above
            sell_condition = (df[rsi_col] < self.upper_bound) & (df[rsi_col].shift(1) >= self.upper_bound)

            signals.loc[buy_condition, 'Signal'] = 1
            signals.loc[buy_condition, 'Reason'] = f'RSI Cross Above {self.lower_bound}'
            
            signals.loc[sell_condition, 'Signal'] = -1
            signals.loc[sell_condition, 'Reason'] = f'RSI Cross Below {self.upper_bound}'

            # --- Position holding logic ---
            # Replace 0 with NA, forward fill, fill remaining NA with 0
            # FIXED: Use .where instead of .replace to avoid RecursionError with pandas 1.5.3
            positions_series = signals['Signal'].where(signals['Signal'] != 0, pd.NA)
            # --- END FIXED ---
            positions_series = positions_series.ffill()
            positions_series = positions_series.fillna(0)
            # Infer the best possible dtype after filling NAs, as suggested by the warning
            # FIXED: Removed copy=False argument for pandas 1.5.3 compatibility
            positions_series = positions_series.infer_objects()
            # --- END FIXED ---
            # Ensure the final type is integer
            signals['Positions'] = positions_series.astype(int)
            signals['Positions'] = signals['Positions'].replace(-1, 0) # No short positions

            logger.debug(f"Generated {signals['Signal'].ne(0).sum()} signals for RSI strategy on {ticker}.") # Added ticker
            logger.debug(f"Buy signals: {signals['Signal'].eq(1).sum()}, Sell signals: {signals['Signal'].eq(-1).sum()} for {ticker}.") # Added ticker

            # Ensure 'Close' column is present in the signals DataFrame before returning
            if 'Close' not in signals.columns and 'Close' in data.columns:
                 signals['Close'] = data['Close'] # Add Close from original data
            elif 'Close' not in signals.columns:
                 signals['Close'] = pd.NA # Fallback

        except Exception as e:
            logger.error(f"Error during RSI signal generation for {ticker}: {e}", exc_info=True) # Added ticker
            # Ensure essential columns exist even on error, fill with defaults
            signals['Signal'] = 0
            signals['Positions'] = 0
            signals['Reason'] = 'Error generating signals'
            # Add Close column if missing, using original data if possible
            if 'Close' not in signals.columns and 'Close' in data.columns:
                 signals['Close'] = data['Close']
            elif 'Close' not in signals.columns:
                 signals['Close'] = pd.NA # Or some other placeholder

            # raise e # Optional

        # Return signals, positions, reasons, and the Close price
        required_cols = ['Signal', 'Positions', 'Reason', 'Close']
        # Add RSI column if it exists
        if rsi_col in df.columns:
            signals[rsi_col] = df[rsi_col]
            required_cols.append(rsi_col)

        # Ensure all required columns are present before returning
        for col in required_cols:
            if col not in signals.columns:
                # If 'Close' was missing even after trying to add it, add NA
                if col == 'Close' and 'Close' not in signals.columns:
                     signals['Close'] = pd.NA
                elif col != 'Close': # Log warning for other missing columns
                    logger.warning(f"Column '{col}' missing in final RSI signals DataFrame for {ticker}. Adding with NAs.")
                    signals[col] = pd.NA # Add missing columns with NAs

        # Ensure columns exist before subsetting
        final_cols = [col for col in required_cols if col in signals.columns]
        if len(final_cols) != len(required_cols):
             missing = set(required_cols) - set(final_cols)
             logger.error(f"Critical: Columns {missing} could not be added to RSI signals DataFrame for {ticker}.")
             # Decide how to handle this - return empty or partial? For now, return what we have.

        return signals[final_cols] # Return only existing required columns