# Backtester App - Product Design Specification

## 1. Wprowadzenie

### 1.1 Cel dokumentu
Niniejszy dokument stanowi kompletną specyfikację produktu Backtester App. Zawiera opis funkcjonalności, architektury systemu, interfejsu użytkownika oraz technicznych aspektów implementacji.

### 1.2 Zakres produktu
Backtester App to aplikacja do testowania strategii inwestycyjnych na historycznych danych finansowych. Pozwala na definiowanie, parametryzację i ewaluację strategii tradingowych w celu oceny ich skuteczności przed zastosowaniem na rynkach rzeczywistych.

### 1.3 Definicje, akronimy i skróty
- **Backtest** - proces testowania strategii handlowej na danych historycznych
- **Strategia** - zbiór reguł określających warunki wejścia i wyjścia z rynku
- **Drawdown** - maksymalny spadek wartości portfela z punktu szczytowego
- **CAGR** - Compound Annual Growth Rate (skumulowana roczna stopa zwrotu)
- **SemVer** - Semantic Versioning, system wersjonowania produktu (MAJOR.MINOR.PATCH)

## 2. Opis ogólny produktu

### 2.1 Perspektywa produktu
Backtester App jest samodzielną aplikacją webową opartą na Dash/Python, oferującą kompleksowe możliwości testowania strategii tradingowych. Aplikacja może być rozwijana w kierunku pełnej platformy tradingowej z integracją z brokerami.

### 2.2 Funkcje produktu
- Definiowanie parametrów strategii inwestycyjnych
- Wybór zestawu instrumentów finansowych do testowania
- Przeprowadzanie backtestów na danych historycznych
- Wizualizacja wyników w postaci wykresów i tabel
- Analiza wskaźników efektywności (CAGR, Sharpe Ratio, itp.)
- Zarządzanie ryzykiem i symulacja różnych scenariuszy

### 2.3 Charakterystyka użytkowników
Aplikacja skierowana jest do inwestorów indywidualnych, traderów i analityków finansowych. Użytkownicy powinni posiadać podstawową wiedzę z zakresu rynków finansowych i inwestowania.

### 2.4 Ograniczenia
- Aplikacja działa w środowisku lokalnym, bez dodatkowej konfiguracji serwerowej
- Jakość backtestów zależy od dostępności i jakości danych historycznych
- Optymalizacja strategii może wymagać znaczących zasobów obliczeniowych

### 2.5 Założenia i zależności
- Python 3.8 lub nowszy
- Dash i Plotly do wizualizacji
- Pandas dla analizy danych
- NumPy do obliczeń matematycznych

## 3. Architektura systemu

### 3.1 Struktura modułowa
```
src/
  ├── analysis/        - Analiza wyników i obliczanie metryk
  ├── core/            - Podstawowa logika biznesowa
  ├── portfolio/       - Zarządzanie portfelem i pozycjami
  ├── services/        - Usługi aplikacyjne
  ├── strategies/      - Implementacje strategii tradingowych
  ├── ui/              - Interfejs użytkownika
  ├── visualization/   - Komponenty wizualizacyjne
  └── version.py       - Informacje o wersji produktu
```

### 3.2 Przepływ danych
1. Wczytanie danych historycznych
2. Konfiguracja parametrów strategii przez użytkownika
3. Uruchomienie backtestów
4. Symulacja transakcji na podstawie sygnałów strategii
5. Analiza wyników i obliczenie metryk wydajności
6. Wizualizacja rezultatów

### 3.3 Interfejsy zewnętrzne
- System plików: do zapisu/odczytu danych historycznych
- Przyszłe wersje mogą zawierać API do komunikacji z brokerami

## 4. Wymagania szczegółowe

### 4.1 Wymagania funkcjonalne

#### 4.1.1 Konfiguracja strategii
- System umożliwia wybór predefiniowanych strategii: Moving Average Crossover, RSI, Bollinger Bands
- Użytkownik może dostosować parametry każdej strategii
- System umożliwia wybór instrumentów finansowych do testów

#### 4.1.2 Zarządzanie ryzykiem
- Definiowanie maksymalnej wielkości pozycji
- Ustawianie stop-loss i take-profit
- Konfiguracja filtrów rynkowych
- Ochrona przed maksymalnym drawdownem

#### 4.1.3 Backtesting
- Uruchamianie testów na wybranym zakresie dat
- Symulowanie transakcji z uwzględnieniem slippage i kosztów
- Obliczanie metryk wydajności i statystyk

#### 4.1.4 Wizualizacja wyników
- Wykres rozwoju portfela
- Heatmapa miesięcznych zwrotów
- Tabela transakcji
- Wykresy sygnałów wejścia i wyjścia

### 4.2 Wymagania niefunkcjonalne

#### 4.2.1 Wydajność
- Backtesty powinny być wykonywane w czasie poniżej 30s dla standardowego zestawu danych
- Interfejs użytkownika powinien pozostać responsywny podczas obliczeń

#### 4.2.2 Niezawodność
- Aplikacja powinna obsługiwać błędy bez crashowania
- System zapisuje logi działania

#### 4.2.3 Skalowalność
- Architektura pozwala na łatwe dodawanie nowych strategii
- Możliwość rozszerzenia o nowe źródła danych

#### 4.2.4 Użyteczność
- Nowoczesny, przejrzysty interfejs
- Intuicyjna nawigacja
- Wykresy interaktywne z możliwością powiększania

## 5. Wersjonowanie i kontrola zmian

### 5.1 System wersjonowania
Projekt wykorzystuje Semantic Versioning (SemVer) w formacie MAJOR.MINOR.PATCH:
- **MAJOR**: zmiany niekompatybilne z poprzednimi wersjami
- **MINOR**: nowe funkcjonalności, kompatybilne wstecz
- **PATCH**: poprawki błędów, kompatybilne wstecz

### 5.2 Proces aktualizacji wersji
1. Aktualizacja numeru wersji w `src/version.py`
2. Aktualizacja changeloga z opisem zmian
3. Tworzenie tagu w repozytorium git

### 5.3 Powrót do poprzednich wersji
Proces powrotu do poprzedniej stabilnej wersji:
1. Checkout odpowiedniego tagu/brancha z repozytorium git
2. Instalacja wymaganych zależności dla tej wersji
3. Uruchomienie aplikacji ze starszą wersją kodu

## 6. Rozwój produktu

### 6.1 Krótkoterminowe cele (6 miesięcy)
- Optymalizacja wydajności backtestów
- Dodanie nowych strategii
- Rozszerzona analiza statystyczna wyników

### 6.2 Długoterminowe cele (12+ miesięcy)
- Migracja frontendu do frameworka React
- Integracja z API brokerów
- Mechanizmy uczenia maszynowego do optymalizacji strategii

### 6.3 Planowane zmiany techniczne
- Refaktoryzacja systemu callbacków
- Poprawa architektury zarządzania stanem aplikacji
- Modernizacja interfejsu użytkownika

## 7. Załączniki

### 7.1 Schemat bazy danych
Nie dotyczy w obecnej wersji (dane przechowywane w plikach CSV)

### 7.2 Specyfikacje API
Brak zewnętrznych API w obecnej wersji

### 7.3 Mockupy UI
Do dodania w przyszłych wersjach dokumentacji

---

*Dokument utworzony: 2025-04-10*
*Ostatnia aktualizacja: 2025-04-10*
*Wersja dokumentacji: 1.0*