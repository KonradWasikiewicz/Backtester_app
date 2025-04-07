import pandas as pd
import numpy as np
import logging
import inspect
from typing import Dict, List, Any, Optional, Union, Type, Tuple
from datetime import datetime, timedelta

from src.strategies.base import BaseStrategy
from src.core.exceptions import StrategyValidationError

logger = logging.getLogger(__name__)

class StrategyValidator:
    """
    Klasa do walidacji strategii tradingowych.
    Weryfikuje poprawność implementacji strategii i zgodność z bazowym interfejsem.
    """
    
    def __init__(self):
        """
        Inicjalizuje walidator strategii.
        """
        self.sample_data = None
        logger.info("Strategy validator initialized")
    
    def generate_sample_data(self, days: int = 252, volatility: float = 0.015) -> pd.DataFrame:
        """
        Generuje syntetyczne dane OHLCV dla testowania strategii.
        
        Args:
            days: Liczba dni danych historycznych
            volatility: Zmienność dzienna ceny
            
        Returns:
            DataFrame z syntetycznymi danymi OHLCV
        """
        # Generowanie daty startowej (rok wstecz)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Generowanie listy dni handlowych (tylko dni robocze)
        dates = []
        curr_date = start_date
        while curr_date <= end_date:
            # Tylko dni od poniedziałku (0) do piątku (4)
            if curr_date.weekday() < 5:
                dates.append(curr_date)
            curr_date += timedelta(days=1)
        
        # Generowanie losowych zmian cen jako ruch Browna
        np.random.seed(42)  # Dla powtarzalności testów
        returns = np.random.normal(0, volatility, len(dates))
        
        # Zaczynamy od ceny 100 i generujemy pozostałe ceny
        close_prices = 100 * np.cumprod(1 + returns)
        
        # Generowanie innych kolumn OHLCV
        high_prices = close_prices * np.exp(np.random.normal(0, volatility/2, len(dates)))
        low_prices = close_prices * np.exp(np.random.normal(0, -volatility/2, len(dates)))
        # Upewnij się, że high >= close >= low
        high_prices = np.maximum(high_prices, close_prices)
        low_prices = np.minimum(low_prices, close_prices)
        
        # Open między low i high
        open_prices = low_prices + (high_prices - low_prices) * np.random.random(len(dates))
        
        # Losowe wolumeny - losowa zmienna z rozkładu log-normalnego
        volumes = np.exp(np.random.normal(10, 1, len(dates)))
        
        # Tworzenie DataFrame
        df = pd.DataFrame({
            'Open': open_prices,
            'High': high_prices,
            'Low': low_prices,
            'Close': close_prices,
            'Volume': volumes
        }, index=dates)
        
        # Zapisywanie wygenerowanych danych
        self.sample_data = df
        
        logger.info(f"Generated synthetic OHLCV data with {len(df)} trading days")
        return df
    
    def validate_strategy_interface(self, strategy_class: Type[BaseStrategy]) -> Dict[str, Any]:
        """
        Waliduje interfejs klasy strategii.
        
        Args:
            strategy_class: Klasa strategii do walidacji
            
        Returns:
            Dictionary z wynikami walidacji
        """
        results = {
            "name": strategy_class.__name__,
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Sprawdzenie czy klasa dziedziczy po BaseStrategy
        if not issubclass(strategy_class, BaseStrategy):
            results["is_valid"] = False
            results["errors"].append(f"Klasa {strategy_class.__name__} nie dziedziczy po BaseStrategy")
            return results
        
        # Sprawdzenie wymaganych metod
        required_methods = ["generate_signals", "get_strategy_params"]
        
        for method_name in required_methods:
            if not hasattr(strategy_class, method_name):
                results["is_valid"] = False
                results["errors"].append(f"Brak wymaganej metody {method_name}")
            else:
                # Sprawdzenie sygnatur metod
                if method_name == "generate_signals":
                    method = getattr(strategy_class, method_name)
                    sig = inspect.signature(method)
                    if len(sig.parameters) != 3:  # self, ticker, data
                        results["is_valid"] = False
                        results["errors"].append(
                            f"Niepoprawna sygnatura metody {method_name}. " +
                            f"Oczekiwano: (self, ticker: str, data: pd.DataFrame)"
                        )
                elif method_name == "get_strategy_params":
                    method = getattr(strategy_class, method_name)
                    sig = inspect.signature(method)
                    if len(sig.parameters) != 1:  # self
                        results["warnings"].append(
                            f"Nietypowa sygnatura metody {method_name}. " +
                            f"Oczekiwano: (self) -> Dict[str, Any]"
                        )
        
        # Sprawdzenie konstruktora
        init_method = strategy_class.__init__
        sig = inspect.signature(init_method)
        if "tickers" not in sig.parameters:
            results["warnings"].append(
                "Konstruktor powinien przyjmować parametr 'tickers'"
            )
        
        return results
    
    def validate_strategy_implementation(self, 
                                         strategy: BaseStrategy, 
                                         sample_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Waliduje implementację strategii poprzez sprawdzenie czy poprawnie generuje sygnały.
        
        Args:
            strategy: Instancja strategii do walidacji
            sample_data: Opcjonalnie dane do testowania
            
        Returns:
            Dictionary z wynikami walidacji
        """
        results = {
            "name": strategy.__class__.__name__,
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Użyj przekazanych danych lub wygeneruj nowe
        if sample_data is None:
            if self.sample_data is None:
                sample_data = self.generate_sample_data()
            else:
                sample_data = self.sample_data
        
        # Testowy ticker
        ticker = "TEST"
        
        try:
            # Próba generowania sygnałów
            signals_df = strategy.generate_signals(ticker, sample_data)
            
            # Sprawdzenie czy zwrócono DataFrame
            if not isinstance(signals_df, pd.DataFrame):
                results["is_valid"] = False
                results["errors"].append(
                    f"Metoda generate_signals zwraca {type(signals_df)} zamiast pd.DataFrame"
                )
                return results
            
            # Sprawdzenie czy sygnały są puste
            if signals_df.empty and not sample_data.empty:
                results["warnings"].append(
                    "Metoda generate_signals zwraca pustą ramkę danych, mimo że dane wejściowe nie są puste"
                )
            
            # Sprawdzenie obecności kolumny 'Signal'
            if 'Signal' not in signals_df.columns:
                results["is_valid"] = False
                results["errors"].append(
                    "Brak kolumny 'Signal' w danych wyjściowych z generate_signals"
                )
            else:
                # Sprawdzenie typów sygnałów
                unique_signals = signals_df['Signal'].unique()
                non_standard_signals = [s for s in unique_signals if s not in [-1, 0, 1]]
                if non_standard_signals:
                    results["warnings"].append(
                        f"Niestandardowe wartości sygnałów: {non_standard_signals}. " +
                        f"Oczekiwane wartości: -1 (sprzedaż), 0 (brak), 1 (kupno)"
                    )
            
            # Sprawdzenie metody get_strategy_params
            try:
                params = strategy.get_strategy_params()
                if not isinstance(params, dict):
                    results["warnings"].append(
                        f"Metoda get_strategy_params zwraca {type(params)} zamiast Dict[str, Any]"
                    )
            except Exception as e:
                results["warnings"].append(
                    f"Błąd wywołania get_strategy_params: {str(e)}"
                )
            
        except Exception as e:
            results["is_valid"] = False
            results["errors"].append(f"Błąd wykonania generate_signals: {str(e)}")
        
        return results
    
    def validate_strategy_signals(self, 
                                  strategy: BaseStrategy,
                                  ticker: str,
                                  data: pd.DataFrame) -> Dict[str, Any]:
        """
        Waliduje sygnały generowane przez strategię dla rzeczywistych danych.
        
        Args:
            strategy: Instancja strategii do walidacji
            ticker: Symbol tickera dla danych
            data: DataFrame z danymi OHLCV
            
        Returns:
            Dictionary z analizą sygnałów
        """
        results = {
            "name": strategy.__class__.__name__,
            "ticker": ticker,
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "signals_summary": {}
        }
        
        try:
            # Generowanie sygnałów
            signals_df = strategy.generate_signals(ticker, data)
            
            if signals_df.empty:
                results["warnings"].append("Strategia nie wygenerowała żadnych sygnałów")
                results["signals_summary"] = {
                    "total": 0,
                    "buy": 0,
                    "sell": 0,
                    "signal_ratio": 0
                }
                return results
            
            if 'Signal' not in signals_df.columns:
                results["is_valid"] = False
                results["errors"].append("Brak kolumny 'Signal' w wygenerowanych danych")
                return results
            
            # Analiza sygnałów
            buy_signals = (signals_df['Signal'] > 0).sum()
            sell_signals = (signals_df['Signal'] < 0).sum()
            total_signals = buy_signals + sell_signals
            total_bars = len(signals_df)
            
            # Stosunek sygnałów do liczby okresów
            signal_ratio = total_signals / total_bars if total_bars > 0 else 0
            
            results["signals_summary"] = {
                "total": int(total_signals),
                "buy": int(buy_signals),
                "sell": int(sell_signals),
                "signal_ratio": round(signal_ratio, 4)
            }
            
            # Sprawdzenie gęstości sygnałów
            if signal_ratio > 0.3:
                results["warnings"].append(
                    f"Wysoka gęstość sygnałów: {round(signal_ratio * 100, 2)}% okresów zawiera sygnały. " +
                    "Może to prowadzić do nadmiernego tradingu."
                )
            elif signal_ratio < 0.01 and total_bars >= 100:
                results["warnings"].append(
                    f"Bardzo niska gęstość sygnałów: tylko {round(signal_ratio * 100, 2)}% okresów zawiera sygnały. " +
                    "Może to prowadzić do zbyt małej liczby transakcji."
                )
            
            # Sprawdzenie rozkładu sygnałów
            if buy_signals > 0 and sell_signals == 0:
                results["warnings"].append(
                    "Strategia generuje tylko sygnały kupna, bez sygnałów sprzedaży."
                )
            elif sell_signals > 0 and buy_signals == 0:
                results["warnings"].append(
                    "Strategia generuje tylko sygnały sprzedaży, bez sygnałów kupna."
                )
            
            # Sprawdzanie luk w danych sygnałów
            max_gap = 0
            current_gap = 0
            for signal in signals_df['Signal']:
                if signal == 0:
                    current_gap += 1
                else:
                    max_gap = max(max_gap, current_gap)
                    current_gap = 0
            
            max_gap = max(max_gap, current_gap)  # Dla przypadku, gdy końcowy ciąg zer jest najdłuższy
            
            results["signals_summary"]["max_days_without_signal"] = int(max_gap)
            
            if max_gap > 100 and signal_ratio > 0:
                results["warnings"].append(
                    f"Wykryto długą lukę ({max_gap} dni) bez żadnych sygnałów. " +
                    "Może to wskazywać na problemy z logiką strategii."
                )
            
            # Sprawdzenie redundancji sygnałów (sygnały kupna po sygnałach kupna bez sygnałów sprzedaży między nimi)
            prev_signal = 0
            redundant_buys = 0
            redundant_sells = 0
            
            for signal in signals_df['Signal']:
                if signal > 0 and prev_signal > 0:
                    redundant_buys += 1
                elif signal < 0 and prev_signal < 0:
                    redundant_sells += 1
                
                if signal != 0:
                    prev_signal = signal
            
            results["signals_summary"]["redundant_buys"] = int(redundant_buys)
            results["signals_summary"]["redundant_sells"] = int(redundant_sells)
            
            if redundant_buys > 0 or redundant_sells > 0:
                results["warnings"].append(
                    f"Wykryto redundantne sygnały: {redundant_buys} nadmiarowych kupna, " +
                    f"{redundant_sells} nadmiarowych sprzedaży. Może to wpływać na wyniki backtestów."
                )
            
        except Exception as e:
            results["is_valid"] = False
            results["errors"].append(f"Błąd podczas walidacji sygnałów: {str(e)}")
        
        return results
    
    def run_quick_test(self, strategy_class: Type[BaseStrategy], ticker: str = "TEST") -> Dict[str, Any]:
        """
        Przeprowadza szybki test strategii z użyciem danych syntetycznych.
        
        Args:
            strategy_class: Klasa strategii do przetestowania
            ticker: Symbol tickera dla testów
            
        Returns:
            Dictionary z wynikami testów
        """
        # Generowanie danych testowych, jeśli jeszcze nie istnieją
        if self.sample_data is None:
            sample_data = self.generate_sample_data()
        else:
            sample_data = self.sample_data
        
        results = {
            "strategy_name": strategy_class.__name__,
            "interface_valid": True,
            "implementation_valid": True,
            "signals_valid": True,
            "interface_details": {},
            "implementation_details": {},
            "signals_details": {},
            "overall_status": "PASS"
        }
        
        # Walidacja interfejsu
        interface_results = self.validate_strategy_interface(strategy_class)
        results["interface_valid"] = interface_results["is_valid"]
        results["interface_details"] = interface_results
        
        if not interface_results["is_valid"]:
            results["overall_status"] = "FAIL"
            logger.error(f"Strategy interface validation failed: {interface_results['errors']}")
            return results
        
        # Tworzenie instancji strategii
        try:
            strategy = strategy_class(tickers=[ticker])
        except Exception as e:
            results["implementation_valid"] = False
            results["implementation_details"] = {
                "name": strategy_class.__name__,
                "is_valid": False,
                "errors": [f"Błąd tworzenia instancji strategii: {str(e)}"],
                "warnings": []
            }
            results["overall_status"] = "FAIL"
            logger.error(f"Strategy instantiation failed: {str(e)}")
            return results
        
        # Walidacja implementacji
        implementation_results = self.validate_strategy_implementation(strategy, sample_data)
        results["implementation_valid"] = implementation_results["is_valid"]
        results["implementation_details"] = implementation_results
        
        if not implementation_results["is_valid"]:
            results["overall_status"] = "FAIL"
            logger.error(f"Strategy implementation validation failed: {implementation_results['errors']}")
            return results
        
        # Walidacja sygnałów
        signals_results = self.validate_strategy_signals(strategy, ticker, sample_data)
        results["signals_valid"] = signals_results["is_valid"]
        results["signals_details"] = signals_results
        
        if not signals_results["is_valid"]:
            results["overall_status"] = "FAIL"
            logger.error(f"Strategy signals validation failed: {signals_results['errors']}")
        elif signals_results["warnings"]:
            results["overall_status"] = "PASS WITH WARNINGS"
            logger.warning(f"Strategy passed with warnings: {signals_results['warnings']}")
        
        logger.info(f"Quick test for {strategy_class.__name__} completed. Status: {results['overall_status']}")
        return results
    
    def analyze_strategy(self, strategy: BaseStrategy, ticker: str, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Przeprowadza szczegółową analizę strategii na rzeczywistych danych.
        
        Args:
            strategy: Instancja strategii do analizy
            ticker: Symbol tickera
            data: DataFrame z danymi OHLCV
            
        Returns:
            Dictionary z wynikami analizy
        """
        results = {
            "strategy_name": strategy.__class__.__name__,
            "ticker": ticker,
            "data_period": f"{data.index.min()} to {data.index.max()}",
            "data_points": len(data),
            "validation_results": {},
            "signal_statistics": {},
            "performance_metrics": {}
        }
        
        # Walidacja sygnałów
        validation_results = self.validate_strategy_signals(strategy, ticker, data)
        results["validation_results"] = validation_results
        
        # Generowanie sygnałów dla dalszej analizy
        try:
            signals_df = strategy.generate_signals(ticker, data)
            
            if signals_df.empty or 'Signal' not in signals_df.columns:
                logger.warning(f"No valid signals generated for {ticker}")
                return results
            
            # Analiza występowania sygnałów w czasie
            buy_dates = signals_df[signals_df['Signal'] > 0].index
            sell_dates = signals_df[signals_df['Signal'] < 0].index
            
            # Obliczanie średniego czasu między sygnałami
            if len(buy_dates) > 1:
                avg_days_between_buys = (buy_dates[-1] - buy_dates[0]).days / (len(buy_dates) - 1) if len(buy_dates) > 1 else float('nan')
            else:
                avg_days_between_buys = float('nan')
                
            if len(sell_dates) > 1:
                avg_days_between_sells = (sell_dates[-1] - sell_dates[0]).days / (len(sell_dates) - 1) if len(sell_dates) > 1 else float('nan')
            else:
                avg_days_between_sells = float('nan')
            
            # Symulacja prostej strategii buy-hold-sell (bez uwzględnienia wielkości pozycji, kosztów itp.)
            buy_hold_sell_returns = []
            current_position = None
            entry_price = None
            
            for idx, row in signals_df.iterrows():
                signal = row['Signal']
                price = row['Close']
                
                if signal > 0 and current_position is None:  # Sygnał kupna, brak pozycji
                    current_position = 'long'
                    entry_price = price
                elif signal < 0 and current_position == 'long':  # Sygnał sprzedaży, mamy pozycję
                    if entry_price is not None:
                        returns_pct = (price - entry_price) / entry_price * 100
                        buy_hold_sell_returns.append(returns_pct)
                    current_position = None
                    entry_price = None
            
            # Statystyki sygnałów
            results["signal_statistics"] = {
                "buy_signals": len(buy_dates),
                "sell_signals": len(sell_dates),
                "avg_days_between_buys": round(avg_days_between_buys, 2) if not pd.isna(avg_days_between_buys) else None,
                "avg_days_between_sells": round(avg_days_between_sells, 2) if not pd.isna(avg_days_between_sells) else None,
                "signal_to_noise_ratio": round(len(buy_dates) / len(data) if len(data) > 0 else 0, 4)
            }
            
            # Podstawowe metryki wydajności
            if buy_hold_sell_returns:
                avg_trade_return = sum(buy_hold_sell_returns) / len(buy_hold_sell_returns)
                winning_trades = sum(1 for r in buy_hold_sell_returns if r > 0)
                win_rate = winning_trades / len(buy_hold_sell_returns) if buy_hold_sell_returns else 0
                
                results["performance_metrics"] = {
                    "simulated_trades": len(buy_hold_sell_returns),
                    "avg_trade_return_pct": round(avg_trade_return, 2),
                    "win_rate": round(win_rate, 2) if buy_hold_sell_returns else None,
                    "best_trade_pct": round(max(buy_hold_sell_returns), 2) if buy_hold_sell_returns else None,
                    "worst_trade_pct": round(min(buy_hold_sell_returns), 2) if buy_hold_sell_returns else None
                }
            else:
                results["performance_metrics"] = {
                    "note": "No complete trades (buy followed by sell) to analyze"
                }
            
        except Exception as e:
            logger.error(f"Error analyzing strategy: {str(e)}", exc_info=True)
            results["error"] = str(e)
        
        return results