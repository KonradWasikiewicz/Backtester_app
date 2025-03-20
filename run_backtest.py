import pandas as pd
import numpy as np
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

if __name__ == '__main__':
    try:
        # 1. Wczytaj dane
        data = load_data('data/historical_prices.csv', 'MSFT')

        # Dodaj sprawdzenie czy dane nie są puste
        if data.empty:
            raise ValueError("Pobrane dane są puste")

        # 2. Dodaj prostą strategię (przykład: Moving Average Crossover)
        data['SMA20'] = data['Close'].rolling(window=20).mean()
        data['SMA50'] = data['Close'].rolling(window=50).mean()
        data['Signal'] = np.where(data['SMA20'] > data['SMA50'], 1, -1)

        # 3. Uruchom backtest
        engine = BacktestEngine(initial_capital=100000)
        results = engine.run_backtest(data)

        # 4. Wizualizuj wyniki
        visualizer = BacktestVisualizer()
        visualizer.plot_strategy_performance(results)

        # 5. Wyświetl statystyki
        stats = engine.get_statistics()
        print("\nStatystyki backtesta:")
        for key, value in stats.items():
            print(f"{key}: {value}")

    except Exception as e:
        print(f"Wystąpił błąd: {str(e)}")