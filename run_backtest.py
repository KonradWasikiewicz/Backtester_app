from src.data_loader import load_data
from src.strategy import MovingAverageCrossover
from src.backtest_engine import BacktestEngine
import quantstats as qs
import pandas as pd
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

if __name__ == '__main__':
    # 1. Wczytaj dane (dla przykładowego tickeru MSFT)
    data = load_data('data/historical_prices.csv')

    # Upewnij się, że kolumna Date jest właściwie zinterpretowana
    print("Typy kolumn w data:", data.dtypes)

    # Filtruj dane dla MSFT
    data = data[data['Ticker'] == 'MSFT']

    # 2. Generowanie sygnałów strategii
    strategy = MovingAverageCrossover(short_window=20, long_window=50)
    data_with_signals = strategy.generate_signals(data)

    # 3. Uruchomienie backtestu
    engine = BacktestEngine(initial_capital=100000, commission=0.001)
    results = engine.run_backtest(data_with_signals)

    # 4. Przygotowanie danych dla QuantStats
    print("Dostępne kolumny:", results.columns.tolist())

    # Ustawienie indeksu na Date
    results.set_index('Date', inplace=True)

    # Konwersja zwrotów na format wymagany przez QuantStats
    strategy_returns = pd.Series(
        results['Strategy_Return'].values,
        index=results.index,
        name='Strategy'
    ).dropna()

    # Upewnij się, że zwroty są w formacie dziennym
    strategy_returns = strategy_returns.resample('D').sum().fillna(0)

    # 5. Generowanie raportu QuantStats
    try:
        # Rozszerzenie funkcjonalności pandas
        qs.extend_pandas()

        # Generowanie raportu HTML
        qs.reports.html(
            returns=strategy_returns,
            benchmark=None,  # Usunięto benchmark dla uproszczenia
            output='quantstats_report.html',
            title='Raport strategii MSFT',
            download_filename='quantstats_report.html'
        )
        print("Wygenerowano raport QuantStats: quantstats_report.html")

    except Exception as e:
        print(f"Błąd podczas generowania raportu: {str(e)}")
        print("\nPodstawowe statystyki:")
        print(f"Całkowity zwrot: {(strategy_returns + 1).prod() - 1:.2%}")
        print(f"Roczna zmienność: {strategy_returns.std() * (252 ** 0.5):.2%}")