import pandas as pd

class MovingAverageCrossover:
    def __init__(self, short_window: int = 20, long_window: int = 50):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generuje sygnały kupna (-1 sprzedaż, 1 kupno) na podstawie średnich kroczących.
        """
        data = data.copy()
        data['SMA_short'] = data['Close'].rolling(window=self.short_window).mean()
        data['SMA_long'] = data['Close'].rolling(window=self.long_window).mean()
        data['Signal'] = 0
        data.loc[data['SMA_short'] > data['SMA_long'], 'Signal'] = 1
        data.loc[data['SMA_short'] <= data['SMA_long'], 'Signal'] = -1
        return data
