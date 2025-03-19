import pandas as pd

class BacktestEngine:
    def __init__(self, initial_capital: float = 100000, commission: float = 0.0):
        """
        initial_capital: kapitał początkowy.
        commission: opłata transakcyjna (procentowa, np. 0.001 = 0.1%).
        """
        self.initial_capital = initial_capital
        self.commission = commission

    def run_backtest(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Przeprowadza backtesting strategii na danych z wygenerowanymi sygnałami.
        Zakłada, że sygnały znajdują się w kolumnie 'Signal'.
        """
        data = data.copy()
        data['Return'] = data['Close'].pct_change()
        # Unikamy lookahead bias – sygnał użyty z dnia poprzedniego:
        data['Strategy_Return'] = data['Return'] * data['Signal'].shift(1)
        # Uwzględnienie opłat transakcyjnych przy zmianie sygnału
        data['Trade'] = data['Signal'].diff().fillna(0).abs()
        data['Strategy_Return'] -= data['Trade'] * self.commission
        data['Portfolio_Value'] = (1 + data['Strategy_Return']).cumprod() * self.initial_capital
        return data
