import pandas as pd
import pandas_ta as ta # Ensure pandas_ta library is installed
from src.strategies.base import BaseStrategy # Corrected path to base.py
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)

# --- CORRECTED CLASS NAME to match import in constants.py ---
class RSIStrategy(BaseStrategy):
    """
    | Characteristic | Description |
    |---------------|-------------|
    | **Idea** | Uses the RSI indicator to identify overbought and oversold conditions, suggesting price reversals (mean reversion). |
    | **Buy Signal** | RSI falls below the oversold level (`lower_bound`) and then crosses back above it (returns to the neutral zone). |
    | **Sell Signal** | RSI rises above the overbought level (`upper_bound`) and then crosses back below it (returns to the neutral zone). |
    | **Key Parameters** | `rsi_period` (RSI period), `lower_bound` (oversold level), `upper_bound` (overbought level). |
    | **Application** | Suitable for range-bound markets or markets without a clear trend (mean reversion strategy). |
    | **Limitations** | May generate premature signals in strong trends (RSI can remain in overbought/oversold zones for extended periods), sensitive to parameter selection. |
    """
    def __init__(self, tickers: list[str], rsi_period: int = 14, lower_bound: int = 30, upper_bound: int = 70):
        """
        Inicjalizuje strategię RSI.

        Args:
            tickers (list[str]): Lista tickerów dla strategii.
            rsi_period (int): Okres (liczba świec) do obliczenia RSI. Domyślnie 14.
            lower_bound (int): Dolny próg RSI wskazujący na wyprzedanie rynku. Domyślnie 30.
            upper_bound (int): Górny próg RSI wskazujący na wykupienie rynku. Domyślnie 70.

        Raises:
            ValueError: Jeśli parametry są nieprawidłowe (np. okres <= 1, progi poza zakresem 0-100, lower >= upper).
        """
        super().__init__() # Wywołanie konstruktora klasy bazowej bez argumentów
        if not (isinstance(rsi_period, int) and rsi_period > 1):
             logger.error(f"Invalid rsi_period: {rsi_period}. Must be an integer greater than 1.")
             raise ValueError("Okres RSI musi być liczbą całkowitą większą niż 1.")
        if not (isinstance(lower_bound, (int, float)) and isinstance(upper_bound, (int, float)) and 0 < lower_bound < upper_bound < 100):
             logger.error(f"Invalid RSI bounds: lower={lower_bound}, upper={upper_bound}. Must be between 0 and 100, and lower < upper.")
             raise ValueError("Poziomy RSI (lower_bound, upper_bound) muszą być liczbami między 0 a 100, a lower_bound musi być mniejszy niż upper_bound.")

        self.tickers = tickers
        self.rsi_period = rsi_period
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        # Przechowuj parametry również w słowniku
        self.parameters = {'rsi_period': rsi_period, 'lower_bound': lower_bound, 'upper_bound': upper_bound}
        logger.info(f"RSI Strategy initialized with parameters: {self.parameters}")

    def get_parameters(self) -> dict:
        """Zwraca słownik z aktualnymi parametrami strategii."""
        return self.parameters

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generuje sygnały transakcyjne na podstawie poziomów RSI.

        Args:
            data (pd.DataFrame): DataFrame zawierający co najmniej kolumnę 'Close'
                                 i wystarczającą historię do obliczenia RSI.

        Returns:
            pd.DataFrame: DataFrame z indeksem takim samym jak `data`, zawierający kolumny:
                          'Signal' (1 dla kupna, -1 dla sprzedaży, 0 dla braku sygnału w danym dniu)
                          'Positions' (1 dla pozycji długiej, -1 dla krótkiej (jeśli zaimplementowano), 0 dla braku pozycji)

        Raises:
            ValueError: Jeśli w danych brakuje kolumny 'Close'.
            KeyError: Jeśli obliczona kolumna RSI nie pojawi się w DataFrame.
        """
        required_column = 'Close'
        if required_column not in data.columns:
            logger.error(f"Required column '{required_column}' not found in input data.")
            raise ValueError(f"DataFrame must contain '{required_column}' column.")

        # Sprawdź, czy jest wystarczająco danych
        if len(data) <= self.rsi_period: # RSI potrzebuje `period` + 1 danych do pierwszego obliczenia
            logger.warning(f"Not enough data ({len(data)} rows) to calculate RSI ({self.rsi_period}). Returning no signals.")
            signals = pd.DataFrame(index=data.index)
            signals['Signal'] = 0
            signals['Positions'] = 0
            return signals

        # Utwórz kopię, aby uniknąć modyfikacji oryginalnego DataFrame
        df = data.copy()
        signals = pd.DataFrame(index=df.index)
        signals['Signal'] = 0  # Domyślnie brak sygnału
        rsi_col = f'RSI_{self.rsi_period}' # Nazwa kolumny dla RSI

        try:
            # Oblicz RSI używając pandas_ta
            df.ta.rsi(length=self.rsi_period, append=True, col_names=(rsi_col,))

            # Sprawdź, czy kolumna RSI została poprawnie dodane
            if rsi_col not in df.columns:
                 logger.error(f"RSI column ({rsi_col}) not found after pandas_ta calculation.")
                 raise KeyError(f"RSI column not found after calculation.")

            # --- Logika generowania sygnałów ---
            buy_condition = (df[rsi_col] > self.lower_bound) & (df[rsi_col].shift(1) <= self.lower_bound)
            sell_condition = (df[rsi_col] < self.upper_bound) & (df[rsi_col].shift(1) >= self.upper_bound)

            signals.loc[buy_condition, 'Signal'] = 1
            signals.loc[sell_condition, 'Signal'] = -1

            # --- Logika utrzymywania pozycji ---
            signals['Positions'] = signals['Signal'].replace(0, pd.NA).ffill().fillna(0).astype(int)
            signals['Positions'] = signals['Positions'].replace(-1, 0)  # Zakładamy brak pozycji krótkich

            logger.info(f"Generated {signals['Signal'].ne(0).sum()} signals for RSI strategy.")
            logger.info(f"Buy signals: {signals['Signal'].eq(1).sum()}, Sell signals: {signals['Signal'].eq(-1).sum()}")

            # Include price column for visualization
            signals['Close'] = df['Close']

        except Exception as e:
            logger.error(f"Error during RSI signal generation: {e}", exc_info=True)
            signals['Signal'] = 0
            signals['Positions'] = 0
            # raise e # Opcjonalnie

        return signals[['Signal', 'Positions', 'Close']]