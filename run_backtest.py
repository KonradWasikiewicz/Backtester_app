import pandas as pd
import numpy as np
from src.backtest_engine import BacktestEngine
from src.visualization import BacktestVisualizer
from src.strategy import MovingAverageCrossover, RSIStrategy, BollingerBandsStrategy
from src.strategy_selector import StrategySelector
import warnings
warnings.filterwarnings('ignore')

def load_data(csv_path: str, ticker: str) -> pd.DataFrame:
    try:
        # Wczytaj dane z CSV
        df = pd.read_csv(csv_path)

        # Filtruj dla wybranego tickera
        df = df[df['Ticker'] == ticker]

        # Ustaw index na Date
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

        # Sortuj po dacie
        df.sort_index(inplace=True)

        if df.empty:
            raise ValueError(f"Brak danych dla {ticker}")

        return df

    except FileNotFoundError:
        raise FileNotFoundError(f"Nie znaleziono pliku {csv_path}. Upewnij się, że uruchomiłeś fetch_data.py")

def select_strategy():
    strategies = {
        1: ("Moving Average Crossover", MovingAverageCrossover),
        2: ("RSI", RSIStrategy),
        3: ("Bollinger Bands", BollingerBandsStrategy)
    }

    print("\nDostępne strategie:")
    for key, (name, _) in strategies.items():
        print(f"{key}. {name}")

    choice = int(input("\nWybierz strategię (1-3): "))
    if choice not in strategies:
        raise ValueError("Nieprawidłowy wybór strategii")

    return strategies[choice]

if __name__ == '__main__':
    try:
        # Wybór strategii i tickera przez okno dialogowe
        selector = StrategySelector()
        strategy_name, ticker = selector.get_selection()

        # 1. Wczytaj dane
        data = load_data('data/historical_prices.csv', ticker)
        print(f"Załadowano dane w zakresie dat: {data.index.min()} - {data.index.max()}")
        print(f"Liczba rekordów: {len(data)}")

        # Dodaj sprawdzenie czy dane nie są puste
        if data.empty:
            raise ValueError("Pobrane dane są puste")

        # Inicjalizacja wybranej strategii
        strategy_class = {
            "Moving Average Crossover": MovingAverageCrossover,
            "RSI": RSIStrategy,
            "Bollinger Bands": BollingerBandsStrategy
        }[strategy_name]

        if strategy_name == "Moving Average Crossover":
            short_window = int(input("Podaj okres krótkiej średniej (default=20): ") or "20")
            long_window = int(input("Podaj okres długiej średniej (default=50): ") or "50")
            strategy = strategy_class(short_window=short_window, long_window=long_window)
            strategy_params = {"Short MA": short_window, "Long MA": long_window}
        elif strategy_name == "RSI":
            period = int(input("Podaj okres RSI (default=14): ") or "14")
            strategy = strategy_class(period=period)
            strategy_params = {"Period": period}
        else:  # Bollinger Bands
            window = int(input("Podaj okres (default=20): ") or "20")
            num_std = float(input("Podaj liczbę odchyleń standardowych (default=2.0): ") or "2.0")
            strategy = strategy_class(window=window, num_std=num_std)
            strategy_params = {"Window": window, "Std Dev": num_std}

        # Generowanie sygnałów
        data = strategy.generate_signals(data)

        # 3. Uruchom backtest
        engine = BacktestEngine(initial_capital=100000)
        results = engine.run_backtest(data)

        # Dodaj informacje o strategii
        strategy_params["Symbol"] = ticker

        # Rozszerz statystyki o dodatkowe informacje
        stats = engine.get_statistics()
        stats.update({
            'initial_capital': 100000,
            'final_capital': results['Portfolio_Value'].iloc[-1],
            'total_return': ((results['Portfolio_Value'].iloc[-1] / 100000) - 1) * 100,
            'max_drawdown': ((results['Portfolio_Value'] - results['Portfolio_Value'].cummax()) /
                            results['Portfolio_Value'].cummax()).min()
        })

        # 4. Wizualizuj wyniki
        visualizer = BacktestVisualizer()
        visualizer.plot_strategy_performance(
            data=results,
            strategy_name=strategy_name,
            strategy_params=strategy_params,
            stats=stats
        )

        # 5. Wyświetl statystyki
        print("\nStatystyki backtesta:")
        for key, value in stats.items():
            print(f"{key}: {value}")

        # Po wykonaniu backtesta
        print(f"\nWyniki dla strategii {strategy_name}:")
        print(f"Kapitał początkowy: $100,000")
        print(f"Kapitał końcowy: ${results['Portfolio_Value'].iloc[-1]:,.2f}")
        print(f"Zwrot całkowity: {((results['Portfolio_Value'].iloc[-1] / 100000) - 1) * 100:.2f}%")

    except Exception as e:
        print(f"Wystąpił błąd: {str(e)}")