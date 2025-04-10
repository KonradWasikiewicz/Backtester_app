# Backtester App

Aplikacja do testowania strategii inwestycyjnych na danych historycznych.

## O projekcie

Backtester App to narzędzie pozwalające na testowanie i analizę strategii tradingowych na historycznych danych giełdowych. Umożliwia konfigurację różnych strategii, zarządzanie ryzykiem oraz wizualizację wyników w formie interaktywnych wykresów i tabel.

## Funkcjonalności

- Testowanie predefiniowanych strategii (Moving Average Crossover, RSI, Bollinger Bands)
- Konfiguracja parametrów strategii
- Zarządzanie ryzykiem z wieloma opcjami (sizing pozycji, stop-loss, take-profit)
- Analiza wyników z kluczowymi metrykami (CAGR, Sharpe Ratio, max drawdown)
- Interaktywne wizualizacje (wykresy equity, heatmapa zwrotów, wykresy sygnałów)

## Instalacja

1. Upewnij się, że masz zainstalowany Python 3.8 lub nowszy
2. Sklonuj repozytorium
   ```
   git clone [URL_REPOZYTORIUM]
   cd Backtester_app
   ```
3. Zainstaluj wymagane zależności
   ```
   pip install -r requirements.txt
   ```

## Uruchomienie aplikacji

```
python app.py
```

Aplikacja będzie dostępna pod adresem http://127.0.0.1:8050/ w przeglądarce.

## System wersjonowania

Projekt wykorzystuje **Semantic Versioning (SemVer)** w formacie MAJOR.MINOR.PATCH:
- **MAJOR**: Zmiany łamiące kompatybilność wsteczną
- **MINOR**: Nowe funkcje zachowujące kompatybilność wsteczną
- **PATCH**: Poprawki błędów zachowujące kompatybilność wsteczną

## Zarządzanie wersjami

Projekt zawiera zestaw skryptów do zarządzania wersjami, które ułatwiają pracę z SemVer i Git:

### Aktualizacja wersji

```
python scripts/update_version.py --minor --changes "Dodano nową strategię" "Poprawiono błędy interfejsu"
```

Dostępne opcje:
- `--major`: Zwiększa wersję główną (MAJOR)
- `--minor`: Zwiększa wersję pomniejszą (MINOR)
- `--patch`: Zwiększa wersję z poprawką (PATCH)
- `--pre`: Dodaje etykietę pre-release (np. alpha, beta, rc)
- `--pre-num`: Numer wersji pre-release (np. dla beta.1)
- `--build`: Metadane budowania
- `--changes`: Lista zmian do dodania do changeloga

### Tagowanie wersji w repozytorium Git

```
python scripts/tag_version.py
```

Skrypt automatycznie:
1. Pobiera aktualną wersję z `src/version.py`
2. Tworzy tag Git z prefiksem "v" (np. v1.2.3)
3. Dodaje informacje z changeloga do opisu tagu
4. Opcjonalnie publikuje tag w repozytorium zdalnym

### Przywracanie poprzedniej wersji

```
python scripts/restore_version.py --list
python scripts/restore_version.py --version v1.0.0 --deps
```

Dostępne opcje:
- `--list`: Wyświetla listę dostępnych wersji
- `--version`: Określa wersję do przywrócenia
- `--deps`: Instaluje zależności dla przywróconej wersji
- `--force`: Wymusza checkout (porzuca lokalne zmiany)

Bez podania wersji skrypt wyświetli interaktywne menu wyboru.

## Dokumentacja

Bardziej szczegółowa dokumentacja znajduje się w katalogu `docs/`:
- [Product Design Specification](docs/product_design_specification.md)
- [Specyfikacja Techniczna](docs/technical_specification.md)

## Licencja

[Informacja o licencji]

## Kontakt

[Dane kontaktowe]
