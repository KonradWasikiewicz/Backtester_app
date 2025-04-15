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

# --- NAZWA KLASY POZOSTAJE BEZ ZMIAN (lub dostosuj do swojej) ---
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
    def __init__(self, short_window: int = 20, long_window: int = 50):
        """
        Inicjalizuje strategię MA Cross.

        Args:
            short_window (int): Okres (liczba świec) dla krótkoterminowej średniej kroczącej. Domyślnie 20.
            long_window (int): Okres (liczba świec) dla długoterminowej średniej kroczącej. Domyślnie 50.

        Raises:
            ValueError: Jeśli okresy nie są dodatnimi liczbami całkowitymi lub short_window >= long_window.
        """
        super().__init__() # Wywołanie konstruktora klasy bazowej
        if not (isinstance(short_window, int) and isinstance(long_window, int) and short_window > 0 and long_window > 0):
            logger.error(f"Invalid window parameters: short={short_window}, long={long_window}. Must be positive integers.")
            raise ValueError("Okresy średnich kroczących muszą być dodatnimi liczbami całkowitymi.")
        if short_window >= long_window:
            logger.error(f"Invalid window parameters: short={short_window}, long={long_window}. Short must be less than long.")
            raise ValueError("Krótki okres (short_window) musi być mniejszy niż długi okres (long_window).")

        self.short_window = short_window
        self.long_window = long_window
        # Przechowuj parametry również w słowniku dla łatwiejszego dostępu/logowania
        self.parameters = {'short_window': short_window, 'long_window': long_window}
        # --- Zaktualizowano log, aby pasował do nazwy klasy ---
        logger.info(f"Moving Average Strategy initialized with parameters: {self.parameters}")

    def get_parameters(self) -> dict:
        """Zwraca słownik z aktualnymi parametrami strategii."""
        return self.parameters

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generuje sygnały transakcyjne na podstawie przecięć średnich kroczących.

        Args:
            data (pd.DataFrame): DataFrame zawierający co najmniej kolumnę 'Close'
                                 i wystarczającą historię do obliczenia najdłuższej średniej.

        Returns:
            pd.DataFrame: DataFrame z indeksem takim samym jak `data`, zawierający kolumny:
                          'signal' (1 dla kupna, -1 dla sprzedaży, 0 dla braku sygnału w danym dniu)
                          'positions' (1 dla pozycji długiej, -1 dla krótkiej (jeśli zaimplementowano), 0 dla braku pozycji)

        Raises:
            ValueError: Jeśli w danych brakuje kolumny 'Close'.
            KeyError: Jeśli obliczone kolumny SMA nie pojawią się w DataFrame.
        """
        required_column = 'Close'
        if required_column not in data.columns:
            logger.error(f"Required column '{required_column}' not found in input data.")
            raise ValueError(f"DataFrame must contain '{required_column}' column.")

        # Sprawdź, czy jest wystarczająco danych
        if len(data) < self.long_window:
            logger.warning(f"Not enough data ({len(data)} rows) to calculate the long SMA ({self.long_window}). Returning no signals.")
            signals = pd.DataFrame(index=data.index)
            signals['signal'] = 0
            signals['positions'] = 0
            return signals

        # Utwórz kopię, aby uniknąć modyfikacji oryginalnego DataFrame (jeśli jest to wymagane)
        df = data.copy()
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0 # Domyślnie brak sygnału

        short_sma_col = f'SMA_{self.short_window}'
        long_sma_col = f'SMA_{self.long_window}'

        try:
            # Oblicz średnie kroczące używając pandas_ta
            df.ta.sma(length=self.short_window, append=True, col_names=(short_sma_col,))
            df.ta.sma(length=self.long_window, append=True, col_names=(long_sma_col,))

            # Sprawdź, czy kolumny zostały poprawnie dodane
            if short_sma_col not in df.columns or long_sma_col not in df.columns:
                 logger.error(f"SMA columns ({short_sma_col}, {long_sma_col}) not found after pandas_ta calculation.")
                 raise KeyError(f"SMA columns not found after calculation.")

            # --- Logika generowania sygnałów ---
            buy_condition = (df[short_sma_col] > df[long_sma_col]) & (df[short_sma_col].shift(1) <= df[long_sma_col].shift(1))
            sell_condition = (df[short_sma_col] < df[long_sma_col]) & (df[short_sma_col].shift(1) >= df[long_sma_col].shift(1))

            signals.loc[buy_condition, 'signal'] = 1
            signals.loc[sell_condition, 'signal'] = -1

            # --- Logika utrzymywania pozycji ---
            signals['positions'] = signals['signal'].replace(0, pd.NA).ffill().fillna(0)
            signals['positions'] = signals['positions'].replace(-1, 0) # Zakładamy brak pozycji krótkich

            # --- Zaktualizowano log, aby pasował do nazwy strategii ---
            logger.debug(f"Generated {signals['signal'].ne(0).sum()} signals for Moving Average strategy.")
            logger.debug(f"Buy signals: {signals['signal'].eq(1).sum()}, Sell signals: {signals['signal'].eq(-1).sum()}")

        except Exception as e:
            # --- Zaktualizowano log, aby pasował do nazwy strategii ---
            logger.error(f"Error during Moving Average signal generation: {e}", exc_info=True)
            signals['signal'] = 0
            signals['positions'] = 0
            # raise e # Opcjonalnie

        return signals[['signal', 'positions']]
