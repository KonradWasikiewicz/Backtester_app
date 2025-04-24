import pandas as pd
import pandas_ta as ta # type: ignore
import logging
from .base import BaseStrategy

logger = logging.getLogger(__name__)

class RSIStrategy(BaseStrategy):
    """
    Implements a trading strategy based on the Relative Strength Index (RSI) indicator.

    Signals are generated when RSI crosses specified overbought or oversold levels.
    """
    def __init__(self, tickers: list[str], parameters: dict):
        """
        Initializes the RSI strategy.

        Args:
            tickers (list[str]): List of tickers (unused in this specific strategy but part of standard signature).
            parameters (dict): Dictionary of strategy parameters. Expected keys:
                               'rsi_period' (int): RSI period.
                               'lower_bound' (int): Lower RSI threshold (oversold).
                               'upper_bound' (int): Upper RSI threshold (overbought).
        """
        super().__init__() # Call base init without arguments
        self.tickers = tickers # Store tickers even if unused
        self.rsi_period = parameters.get('rsi_period', 14)
        self.lower_bound = parameters.get('lower_bound', 30)
        self.upper_bound = parameters.get('upper_bound', 70)
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
        signals['Reason'] = '' # Nowa kolumna na powód sygnału

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
            positions_series = signals['Signal'].replace(0, pd.NA).ffill().fillna(0)
            # Infer the best possible dtype after filling NAs
            positions_series = positions_series.infer_objects(copy=False)
            # Ensure the final type is integer
            signals['Positions'] = positions_series.astype(int)
            signals['Positions'] = signals['Positions'].replace(-1, 0) # No short positions

            logger.debug(f"Generated {signals['Signal'].ne(0).sum()} signals for RSI strategy on {ticker}.") # Added ticker
            logger.debug(f"Buy signals: {signals['Signal'].eq(1).sum()}, Sell signals: {signals['Signal'].eq(-1).sum()} for {ticker}.") # Added ticker

        except Exception as e:
            logger.error(f"Error during RSI signal generation for {ticker}: {e}", exc_info=True) # Added ticker
            signals['Signal'] = 0
            signals['Positions'] = 0
            signals['Reason'] = '' # Resetuj powód w razie błędu
            # raise e # Optional

        # Zwróć sygnały, pozycje i powody
        return signals[['Signal', 'Positions', 'Reason']]