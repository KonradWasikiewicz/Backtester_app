from src.data_loader import load_data
from src.strategy import MovingAverageCrossover
from src.backtest_engine import BacktestEngine
import matplotlib.pyplot as plt

if __name__ == '__main__':
    # Wczytaj dane z CSV
    data = load_data('data/historical_prices.csv')
    
    # Ponieważ plik zawiera dane dla wielu spółek, filtrujemy dla wybranego tickeru, np. 'MSFT'
    data = data[data['Ticker'] == 'MSFT']
    
    # Generowanie sygnałów strategii (np. crossover średnich kroczących)
    strategy = MovingAverageCrossover(short_window=20, long_window=50)
    data_with_signals = strategy.generate_signals(data)
    
    # Uruchomienie backtestu – symulacja portfela, uwzględniająca opłaty
    engine = BacktestEngine(initial_capital=100000, commission=0.001)
    results = engine.run_backtest(data_with_signals)
    
    # Wizualizacja wyników: wykres portfela w czasie
    # Po otrzymaniu wyników z backtestu
    results.reset_index(inplace=True)  # Przywrócenie kolumny "Date"
    plt.figure(figsize=(12, 6))
    plt.plot(results['Date'], results['Portfolio_Value'], label='Wartość portfela')
    plt.xlabel('Data')
    plt.ylabel('Wartość portfela')
    plt.title('Wyniki backtestu strategii dla MSFT')
    plt.legend()
    plt.show()
    print(results[['Date', 'Close', 'Signal', 'Return', 'Strategy_Return', 'Portfolio_Value']].head(10))
    print(results[['Portfolio_Value']].describe())
