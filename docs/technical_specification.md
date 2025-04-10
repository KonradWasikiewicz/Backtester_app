# Backtester App - Specyfikacja Techniczna

## 1. Architektura Systemu

### 1.1 Przegląd architektury
Backtester App wykorzystuje architekturę warstwową z podziałem na moduły funkcjonalne. Głównym interfejsem użytkownika jest aplikacja webowa zbudowana z użyciem Dash (nakładka na React), natomiast logika biznesowa jest zaimplementowana w Pythonie.

### 1.2 Komponenty systemu

#### 1.2.1 Core
Zawiera podstawową logikę biznesową aplikacji:
- `backtest_manager.py` - Zarządzanie procesem backtestingu
- `data.py` - Wczytywanie i przetwarzanie danych historycznych
- `config.py` - Konfiguracja aplikacji
- `constants.py` - Stałe systemowe
- `engine.py` - Silnik symulacji
- `exceptions.py` - Niestandardowe wyjątki aplikacji

#### 1.2.2 Strategies
Implementacje strategii handlowych:
- `base.py` - Klasa bazowa dla wszystkich strategii
- `moving_average.py` - Strategia przecięcia średnich kroczących
- `rsi.py` - Strategia oparta na Relative Strength Index
- `bollinger.py` - Strategia wykorzystująca Bollinger Bands

#### 1.2.3 Portfolio
Zarządzanie portfelem i pozycjami:
- `portfolio_manager.py` - Zarządzanie stanem portfela
- `risk_manager.py` - Zarządzanie ryzykiem

#### 1.2.4 Analysis
Analiza wyników backtestów:
- `metrics.py` - Obliczanie wskaźników efektywności (CAGR, Sharpe, itp.)

#### 1.2.5 UI
Interfejs użytkownika:
- `app_factory.py` - Tworzenie instancji aplikacji Dash
- `components.py` - Reużywalne komponenty UI
- `callbacks/` - Implementacja callbacków Dash
- `layouts/` - Szablony layoutów

#### 1.2.6 Visualization
Generowanie wizualizacji:
- `visualizer.py` - Główna klasa do tworzenia wizualizacji
- `chart_utils.py` - Funkcje pomocnicze do tworzenia wykresów

### 1.3 Diagram przepływu danych

```
[Dane historyczne] --> [DataLoader] --> [BacktestManager] --> [Strategia] --> [PortfolioManager]
                                           |                                       |
                                           v                                       v
                                    [BacktestService] <-- [RiskManager] <-- [Pozycje/Transakcje]
                                           |
                                           v
                                    [Wizualizacja] --> [UI]
```

## 2. Technologie i biblioteki

### 2.1 Backend
- **Python 3.8+** - Język programowania
- **pandas** - Manipulacja danymi, analiza
- **numpy** - Obliczenia numeryczne
- **plotly** - Tworzenie interaktywnych wykresów

### 2.2 Frontend
- **Dash** - Framework dla aplikacji webowych w Pythonie
- **Bootstrap** - Framework CSS dla responsywnego designu
- **Plotly.js** - Biblioteka wykresów (używana przez Dash)

### 2.3 Narzędzia developerskie
- **Git** - Kontrola wersji
- **SemVer** - Standard wersjonowania semantycznego

## 3. Przepływ danych i algorytmy

### 3.1 Wczytywanie danych
```python
# Pseudokod
class DataLoader:
    def load_data(ticker):
        data = read_csv_file(f"data/{ticker}.csv")
        return process_data(data)
        
    def process_data(data):
        # Konwersja dat, sortowanie, czyszczenie
        return processed_data
```

### 3.2 Generowanie sygnałów
```python
# Pseudokod
class BaseStrategy:
    def generate_signals(self, data):
        # Implementacja w klasach pochodnych
        pass
        
class MovingAverageStrategy(BaseStrategy):
    def generate_signals(self, data):
        fast_ma = calculate_ma(data, self.fast_period)
        slow_ma = calculate_ma(data, self.slow_period)
        
        buy_signals = fast_ma > slow_ma & fast_ma.shift() <= slow_ma.shift()
        sell_signals = fast_ma < slow_ma & fast_ma.shift() >= slow_ma.shift()
        
        return create_signal_series(buy_signals, sell_signals)
```

### 3.3 Zarządzanie portfelem
```python
# Pseudokod
class PortfolioManager:
    def process_signals(self, signals, prices):
        for date, signal in signals.items():
            if signal > 0 and self.cash > 0:
                # Logika zakupu
                self.open_position(date, price, shares)
            elif signal < 0 and has_open_positions():
                # Logika sprzedaży
                self.close_position(date, price)
```

### 3.4 Wizualizacja wyników
```python
# Pseudokod
class BacktestVisualizer:
    def create_equity_curve(self, portfolio_values):
        fig = create_line_chart(portfolio_values)
        return fig
        
    def create_monthly_returns_heatmap(self, returns):
        monthly_returns = convert_to_monthly(returns)
        fig = create_heatmap(monthly_returns)
        return fig
```

## 4. Struktura interfejsu użytkownika

### 4.1 Układ główny
- Panel boczny (konfiguracja strategii)
- Panel główny (wyniki i wykresy)
- Nagłówek (nazwa aplikacji, wersja)
- Stopka (informacje, linki)

### 4.2 Panel konfiguracji strategii
- Selector strategii (dropdown)
- Parametry strategii (dynamiczne pola)
- Selektor instrumentów (multi-checkbox)
- Zakres dat (slider + date picker)
- Zarządzanie ryzykiem (expandable panel)
- Przycisk "Run Backtest"

### 4.3 Panel wyników
- Metryki podsumowujące (karty)
- Wykres portfela
- Heatmapa miesięcznych zwrotów
- Tabela transakcji
- Wykres sygnałów

## 5. Zarządzanie stanem aplikacji

### 5.1 Przepływ callbacków
W Dash, przepływ danych między komponentami odbywa się za pomocą callbacków, które reagują na zdarzenia użytkownika. Główne callbacky:

1. Aktualizacja parametrów strategii na podstawie wybranej strategii
2. Filtrowanie dostępnych instrumentów na podstawie wyszukiwania
3. Aktualizacja zakresu dat na podstawie slidera/pickerów
4. Uruchomienie backtestu i aktualizacja wyników
5. Aktualizacja wykresów na podstawie wyników

### 5.2 Podział callbacków w projekcie
Callbacki są grupowane według funkcjonalności:
- `strategy_callbacks.py` - Callbacki związane z konfiguracją strategii
- `backtest_callbacks.py` - Callbacki związane z uruchamianiem i wyświetlaniem wyników
- `risk_management_callbacks.py` - Callbacki do zarządzania ustawieniami ryzyka

## 6. Zarządzanie wersjami i migracjami

### 6.1 Wersjonowanie
Projekt wykorzystuje SemVer (Semantic Versioning) dla przejrzystego oznaczania wersji:
- **MAJOR** - zmiany łamiące kompatybilność wsteczną
- **MINOR** - nowe funkcjonalności (kompatybilne wstecz)
- **PATCH** - poprawki błędów (kompatybilne wstecz)

### 6.2 Proces wdrażania nowych wersji
1. Rozwój w branchu `develop`
2. Testy i stabilizacja
3. Aktualizacja wersji i changeloga
4. Merge do brancha `main`
5. Utworzenie tagu wersji

### 6.3 Przywracanie poprzednich wersji
Proces przywracania poprzedniej wersji aplikacji:
```bash
# Przykładowe komendy Git
git checkout tags/v1.0.0
```

### 6.4 Zarządzanie zależnościami
Zależności są zamrożone dla każdej wersji:
```bash
pip freeze > requirements.txt
```

Przywracanie zależności dla konkretnej wersji:
```bash
pip install -r requirements.txt
```

## 7. Znane problemy i ograniczenia techniczne

### 7.1 Problemy z callbackami Dash
Aplikacja obecnie wykorzystuje zaawansowane techniki monkey-patchingu do rozwiązania problemów z duplikującymi się callbackami. Jest to rozwiązanie tymczasowe, które powinno zostać zastąpione bardziej eleganckim podejściem w przyszłych wersjach.

### 7.2 Wydajność backtestów
Dla dużych zbiorów danych lub złożonych strategii, czas wykonania backtestów może być długi. Konieczna jest optymalizacja pod kątem wydajności, potencjalnie z wykorzystaniem przetwarzania równoległego.

### 7.3 Format tabel
Występują problemy z formatowaniem danych w tabelach Dash, szczególnie w przypadku procentów. Zastosowano obejście przez patch runtime.

## 8. Plan rozwoju technicznego

### 8.1 Refaktoryzacja UI
Planowana jest migracja z Dash do czystego React, aby zwiększyć elastyczność i wydajność interfejsu użytkownika.

### 8.2 Optymalizacja wydajności
- Implementacja przetwarzania równoległego dla backtestów
- Optymalizacja algorytmów strategii

### 8.3 Rozbudowa funkcjonalności
- Dodanie optymalizacji parametrów strategii
- Implementacja machine learning dla predykcji rynku
- Integracja z API brokerów dla tradingu algorytmicznego

---

*Dokument utworzony: 2025-04-10*
*Ostatnia aktualizacja: 2025-04-10*
*Wersja dokumentacji: 1.0*