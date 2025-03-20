from src.data_loader import load_data
from src.strategy import MovingAverageCrossover
from src.backtest_engine import BacktestEngine
import matplotlib.pyplot as plt
import quantstats as qs
import pandas as pd

if __name__ == '__main__':
    # 1. Wczytaj dane (dla przykładowego tickeru MSFT)
    data = load_data('data/historical_prices.csv')
    data = data[data['Ticker'] == 'MSFT']

    # 2. Generowanie sygnałów strategii
    strategy = MovingAverageCrossover(short_window=20, long_window=50)
    data_with_signals = strategy.generate_signals(data)

    # 3. Uruchomienie backtestu
    engine = BacktestEngine(initial_capital=100000, commission=0.001)
    results = engine.run_backtest(data_with_signals)

    # 4. Wizualizacja krzywej kapitału
    # (pamiętaj, by zresetować indeks jeśli chcesz używać results['Date'])
    results.reset_index(inplace=True)
    plt.figure(figsize=(12, 6))
    plt.plot(results['Date'], results['Portfolio_Value'], label='Wartość portfela')
    plt.xlabel('Data')
    plt.ylabel('Wartość portfela')
    plt.title('Wyniki backtestu strategii dla MSFT')
    plt.legend()
    plt.show()

        # 5. Integracja z QuantStats
    # a) Upewnij się, że masz daty w indeksie i w formacie daty
    results.set_index('Date', inplace=True)
    results.index = pd.to_datetime(results.index)

    # b) Wyodrębnij dzienne stopy zwrotu strategii i przekształć na serię
    strategy_returns = pd.Series(
        results['Strategy_Return'].values,
        index=results.index,
        name='Strategy'
    ).dropna()

    # c) Rozszerz Pandas o metody quantstats
    qs.extend_pandas()

    # d) Wygeneruj raport HTML
    try:
        qs.reports.html(
            returns=strategy_returns,
            output='my_quantstats_report.html',
            title='Raport strategii MSFT',
            download_filename='my_quantstats_report.html'
        )
        print("Wygenerowano raport QuantStats: my_quantstats_report.html")
    except Exception as e:
        print(f"Błąd podczas generowania raportu: {str(e)}")
        # Alternatywnie, pokaż podstawowe statystyki
        print("\nPodstawowe statystyki:")
        print(f"Całkowity zwrot: {(strategy_returns + 1).prod() - 1:.2%}")
        print(f"Roczna zmienność: {strategy_returns.std() * (252 ** 0.5):.2%}")