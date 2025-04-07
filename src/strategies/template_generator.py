import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class StrategyTemplateGenerator:
    """
    Generator szablonów dla nowych strategii tradingowych.
    Ułatwia tworzenie nowych klas strategii zgodnych z interfejsem bazowej strategii.
    """
    
    def __init__(self, strategies_dir: Optional[str] = None):
        """
        Inicjalizuje generator szablonów strategii.
        
        Args:
            strategies_dir: Ścieżka do katalogu strategii (opcjonalnie)
        """
        if strategies_dir is None:
            # Domyślna ścieżka do katalogu strategii
            self.strategies_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "strategies"
            )
        else:
            self.strategies_dir = strategies_dir
        
        logger.info(f"Strategy template generator initialized. Strategies directory: {self.strategies_dir}")
    
    def generate_strategy_template(self, 
                                  strategy_name: str,
                                  strategy_type: str = "custom",
                                  description: str = "",
                                  parameters: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Generuje szablon dla nowej strategii tradingowej.
        
        Args:
            strategy_name: Nazwa strategii (CamelCase)
            strategy_type: Typ strategii (np. "trend_following", "mean_reversion", "custom")
            description: Opis strategii
            parameters: Lista parametrów strategii w formacie:
                [{"name": "param_name", "type": "float", "default": 0.0, "description": "Opis parametru"}]
                
        Returns:
            str: Ścieżka do utworzonego pliku strategii lub informacja o błędzie
        """
        # Walidacja nazwy strategii
        if not strategy_name or not strategy_name[0].isalpha():
            return "Błąd: Nazwa strategii musi zaczynać się od litery."
        
        # Konwersja nazwy strategii do CamelCase i snake_case
        strategy_class_name = ''.join(word.capitalize() for word in strategy_name.split())
        strategy_class_name = strategy_class_name.replace('-', '').replace('_', '')
        
        # Nazwa pliku w formacie snake_case
        file_name = strategy_class_name.lower()
        file_name = ''.join(['_' + c.lower() if c.isupper() else c for c in file_name]).lstrip('_')
        file_path = os.path.join(self.strategies_dir, f"{file_name}.py")
        
        # Sprawdzenie czy plik już istnieje
        if os.path.exists(file_path):
            return f"Błąd: Plik {file_path} już istnieje."
        
        # Przygotowanie domyślnych parametrów, jeśli nie zostały podane
        if parameters is None:
            parameters = [
                {"name": "fast_period", "type": "int", "default": 12, 
                 "description": "Okres dla szybkiej średniej kroczącej"},
                {"name": "slow_period", "type": "int", "default": 26, 
                 "description": "Okres dla wolnej średniej kroczącej"},
                {"name": "signal_period", "type": "int", "default": 9, 
                 "description": "Okres dla sygnału"}
            ]
        
        # Generowanie kodu klasy strategii
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Generowanie kodu importów
        imports_code = """import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Union, Tuple, Optional, Any

from src.strategies.base import BaseStrategy
from src.core.constants import SignalType

logger = logging.getLogger(__name__)
"""

        # Generowanie kodu parametrów klasy
        params_code = ""
        init_params_code = "        \"\"\"\n        Inicjalizuje strategię.\n        \n        Args:\n            tickers: Lista tickerów do analizy\n"
        init_body_code = "        super().__init__(tickers=tickers)\n        # Inicjalizacja parametrów strategii\n"
        
        for param in parameters:
            param_name = param["name"]
            param_type = param["type"]
            param_default = param["default"]
            param_desc = param.get("description", "")
            
            # Dodawanie do listy parametrów __init__
            params_code += f"            {param_name}: {param_type} = {param_default},\n"
            
            # Dodawanie do dokumentacji __init__
            init_params_code += f"            {param_name}: {param_desc}\n"
            
            # Dodawanie do ciała __init__
            init_body_code += f"        self.{param_name} = {param_name}\n"
        
        # Zamykanie dokumentacji __init__
        init_params_code += "        \"\"\"\n"
        
        # Generowanie kodu całej klasy strategii
        class_code = f'''
class {strategy_class_name}Strategy(BaseStrategy):
    """
    {description}
    
    Typ strategii: {strategy_type}
    Utworzona: {current_date}
    """
    
    def __init__(
        self,
        tickers: List[str],
{params_code}    ):
{init_params_code}
{init_body_code}
        logger.info(f"{strategy_class_name}Strategy initialized with parameters: " + 
                   f"{', '.join([f'{{{p['name']}={{self.{p['name']}}}' for p in parameters])}")
    
    def generate_signals(self, ticker: str, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generuje sygnały transakcyjne dla danego tickera na podstawie danych historycznych.
        
        Args:
            ticker: Symbol tickera
            data: DataFrame z danymi historycznymi (OHLCV)
            
        Returns:
            DataFrame z sygnałami handlowymi
        """
        try:
            # Kopiowanie danych wejściowych, aby uniknąć modyfikacji oryginału
            df = data.copy()
            
            # Sprawdzenie dostępności wymaganych kolumn
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_columns):
                logger.error(f"Brakujące kolumny w danych dla {{ticker}}. Wymagane: {{required_columns}}")
                return pd.DataFrame()  # Zwraca pustą ramkę
            
            # ======= LOGIKA STRATEGII ZACZYNA SIĘ TUTAJ =======
            
            # Przykładowa logika: Przecięcie średnich kroczących
            # Można zastąpić własną logiką strategii
            
            # Obliczanie wskaźników
            df['fast_ma'] = df['Close'].rolling(window=self.fast_period).mean()
            df['slow_ma'] = df['Close'].rolling(window=self.slow_period).mean()
            
            # Inicjalizacja kolumny sygnałów
            df['Signal'] = 0
            
            # Generowanie sygnałów
            # Sygnał kupna: szybka MA przebija wolną MA od dołu
            buy_signals = (df['fast_ma'] > df['slow_ma']) & (df['fast_ma'].shift() <= df['slow_ma'].shift())
            # Sygnał sprzedaży: szybka MA przebija wolną MA od góry
            sell_signals = (df['fast_ma'] < df['slow_ma']) & (df['fast_ma'].shift() >= df['slow_ma'].shift())
            
            # Ustawienie sygnałów w ramce danych
            df.loc[buy_signals, 'Signal'] = SignalType.BUY.value
            df.loc[sell_signals, 'Signal'] = SignalType.SELL.value
            
            # ======= LOGIKA STRATEGII KOŃCZY SIĘ TUTAJ =======
            
            # Usunięcie pierwszych wierszy z NaN (wynikających z okresów obliczeniowych)
            df = df.dropna()
            
            logger.info(f"Wygenerowano sygnały dla {{ticker}} używając {strategy_class_name}Strategy")
            return df
            
        except Exception as e:
            logger.error(f"Błąd generowania sygnałów dla {{ticker}}: {{e}}", exc_info=True)
            return pd.DataFrame()
    
    def get_strategy_params(self) -> Dict[str, Any]:
        """
        Zwraca parametry strategii jako słownik.
        
        Returns:
            Słownik parametrów strategii
        """
        return {{
{', '.join([f"            '{p['name']}': self.{p['name']}" for p in parameters])}
        }}
'''
        
        # Generowanie pliku strategii
        try:
            # Tworzenie katalogu strategii, jeśli nie istnieje
            os.makedirs(self.strategies_dir, exist_ok=True)
            
            # Zapisywanie pliku strategii
            with open(file_path, 'w') as f:
                f.write(imports_code + class_code)
            
            logger.info(f"Utworzono szablon strategii: {file_path}")
            return f"Utworzono szablon strategii: {file_path}"
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania szablonu strategii: {e}", exc_info=True)
            return f"Błąd podczas generowania szablonu strategii: {str(e)}"
    
    def generate_strategy_combiner(self,
                                  combiner_name: str,
                                  strategy_types: List[str] = None,
                                  combination_method: str = "voting") -> str:
        """
        Generuje szablon dla kombinatora strategii, który może łączyć sygnały z wielu strategii.
        
        Args:
            combiner_name: Nazwa kombinatora
            strategy_types: Lista typów strategii do połączenia (np. ["MA", "RSI"])
            combination_method: Metoda kombinacji sygnałów (np. "voting", "weighted", "sequential")
            
        Returns:
            str: Ścieżka do utworzonego pliku kombinatora lub informacja o błędzie
        """
        # Walidacja nazwy kombinatora
        if not combiner_name or not combiner_name[0].isalpha():
            return "Błąd: Nazwa kombinatora musi zaczynać się od litery."
        
        # Konwersja nazwy kombinatora do CamelCase
        combiner_class_name = ''.join(word.capitalize() for word in combiner_name.split())
        combiner_class_name = combiner_class_name.replace('-', '').replace('_', '')
        
        # Nazwa pliku w formacie snake_case
        file_name = combiner_class_name.lower()
        file_name = ''.join(['_' + c.lower() if c.isupper() else c for c in file_name]).lstrip('_')
        file_path = os.path.join(self.strategies_dir, f"{file_name}_combiner.py")
        
        # Sprawdzenie czy plik już istnieje
        if os.path.exists(file_path):
            return f"Błąd: Plik {file_path} już istnieje."
        
        # Domyślna lista strategii, jeśli nie podano
        if not strategy_types:
            strategy_types = ["MA", "RSI"]
        
        # Generowanie kodu kombinatora
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Kod importów
        imports_code = """import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Union, Tuple, Optional, Any

from src.strategies.base import BaseStrategy
from src.core.constants import SignalType, AVAILABLE_STRATEGIES

logger = logging.getLogger(__name__)
"""
        
        # Generowanie kodu klasy kombinatora
        class_code = f'''
class {combiner_class_name}Combiner(BaseStrategy):
    """
    Kombinator strategii łączący sygnały z wielu strategii tradingowych.
    
    Metoda kombinacji: {combination_method}
    Utworzony: {current_date}
    """
    
    def __init__(
        self,
        tickers: List[str],
        strategy_configs: List[Dict[str, Any]] = None,
        weights: List[float] = None
    ):
        """
        Inicjalizuje kombinator strategii.
        
        Args:
            tickers: Lista tickerów do analizy
            strategy_configs: Lista konfiguracji strategii w formacie:
                [
                    {{"type": "MA", "params": {{"fast_period": 10, "slow_period": 30}}}},
                    {{"type": "RSI", "params": {{"period": 14, "overbought": 70, "oversold": 30}}}}
                ]
            weights: Lista wag dla każdej strategii (używana w metodzie "weighted")
        """
        super().__init__(tickers=tickers)
        
        # Konfiguracja domyślna, jeśli nie podano
        if strategy_configs is None:
            strategy_configs = [
                {{"type": "{strategy_types[0]}", "params": {{}}}},
                {{"type": "{strategy_types[1] if len(strategy_types) > 1 else 'RSI'}", "params": {{}}}}
            ]
        
        self.strategy_configs = strategy_configs
        
        # Inicjalizacja wag - domyślnie równe wagi
        if weights is None:
            self.weights = [1.0 / len(strategy_configs)] * len(strategy_configs)
        else:
            # Normalizacja wag
            total = sum(weights)
            self.weights = [w / total for w in weights]
        
        # Inicjalizacja strategii
        self.strategies = []
        for config in strategy_configs:
            strategy_type = config["type"]
            strategy_params = config.get("params", {{}})
            
            if strategy_type in AVAILABLE_STRATEGIES:
                strategy_class = AVAILABLE_STRATEGIES[strategy_type]
                # Tworzenie instancji strategii z parametrami
                strategy = strategy_class(tickers=tickers, **strategy_params)
                self.strategies.append(strategy)
            else:
                logger.warning(f"Nieznany typ strategii: {{strategy_type}}")
        
        # Metoda kombinacji sygnałów
        self.combination_method = "{combination_method}"
        
        logger.info(f"{combiner_class_name}Combiner initialized with {{len(self.strategies)}} strategies")
    
    def generate_signals(self, ticker: str, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generuje sygnały tradingowe kombinując wyniki wielu strategii.
        
        Args:
            ticker: Symbol tickera
            data: DataFrame z danymi historycznymi (OHLCV)
            
        Returns:
            DataFrame z sygnałami handlowymi
        """
        if not self.strategies:
            logger.error("Brak skonfigurowanych strategii.")
            return pd.DataFrame()
        
        try:
            # Kopiowanie danych wejściowych
            df = data.copy()
            
            # Sprawdzenie dostępności wymaganych kolumn
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_columns):
                logger.error(f"Brakujące kolumny w danych dla {{ticker}}. Wymagane: {{required_columns}}")
                return pd.DataFrame()
            
            # Generowanie sygnałów dla każdej strategii
            all_signals = []
            for i, strategy in enumerate(self.strategies):
                signals_df = strategy.generate_signals(ticker, df)
                if signals_df is not None and not signals_df.empty and 'Signal' in signals_df.columns:
                    # Zachowanie tylko kolumny sygnałów
                    signals_series = signals_df['Signal']
                    all_signals.append((signals_series, self.weights[i]))
            
            if not all_signals:
                logger.warning(f"Żadna strategia nie wygenerowała sygnałów dla {{ticker}}")
                return pd.DataFrame()
            
            # Kombinowanie sygnałów z różnych strategii
            if self.combination_method == "voting":
                combined_signals = self._combine_signals_voting(all_signals, df)
            elif self.combination_method == "weighted":
                combined_signals = self._combine_signals_weighted(all_signals, df)
            elif self.combination_method == "sequential":
                combined_signals = self._combine_signals_sequential(all_signals, df)
            else:
                logger.warning(f"Nieznana metoda kombinacji: {{self.combination_method}}. Używanie metody voting.")
                combined_signals = self._combine_signals_voting(all_signals, df)
            
            # Dodawanie skombinowanych sygnałów do ramki danych
            df['Signal'] = combined_signals
            
            logger.info(f"Wygenerowano skombinowane sygnały dla {{ticker}} używając {combiner_class_name}Combiner")
            return df
            
        except Exception as e:
            logger.error(f"Błąd generowania sygnałów kombinowanych dla {{ticker}}: {{e}}", exc_info=True)
            return pd.DataFrame()
    
    def _combine_signals_voting(self, all_signals: List[Tuple[pd.Series, float]], df: pd.DataFrame) -> pd.Series:
        """
        Kombinuje sygnały metodą głosowania (większość decyduje).
        
        Args:
            all_signals: Lista krotek (seria sygnałów, waga)
            df: Oryginalna ramka danych
            
        Returns:
            Series z skombinowanymi sygnałami
        """
        # Tworzenie pustej serii sygnałów z indeksem z oryginalnych danych
        combined = pd.Series(0, index=df.index)
        
        # Dla każdej pozycji (daty), kombinuj sygnały
        for idx in combined.index:
            buy_votes = 0
            sell_votes = 0
            
            for signals, weight in all_signals:
                if idx in signals.index:
                    if signals[idx] == SignalType.BUY.value:
                        buy_votes += 1
                    elif signals[idx] == SignalType.SELL.value:
                        sell_votes += 1
            
            # Decyzja większościowa
            if buy_votes > sell_votes and buy_votes > len(all_signals) / 2:
                combined[idx] = SignalType.BUY.value
            elif sell_votes > buy_votes and sell_votes > len(all_signals) / 2:
                combined[idx] = SignalType.SELL.value
        
        return combined
    
    def _combine_signals_weighted(self, all_signals: List[Tuple[pd.Series, float]], df: pd.DataFrame) -> pd.Series:
        """
        Kombinuje sygnały metodą ważoną (suma ważonych sygnałów).
        
        Args:
            all_signals: Lista krotek (seria sygnałów, waga)
            df: Oryginalna ramka danych
            
        Returns:
            Series z skombinowanymi sygnałami
        """
        # Tworzenie pustej serii sygnałów z indeksem z oryginalnych danych
        combined = pd.Series(0, index=df.index)
        
        # Dla każdej pozycji (daty), oblicz ważoną sumę sygnałów
        for idx in combined.index:
            weighted_sum = 0
            
            for signals, weight in all_signals:
                if idx in signals.index:
                    weighted_sum += signals[idx] * weight
            
            # Konwersja ważonej sumy na sygnały
            if weighted_sum > 0.5:
                combined[idx] = SignalType.BUY.value
            elif weighted_sum < -0.5:
                combined[idx] = SignalType.SELL.value
        
        return combined
    
    def _combine_signals_sequential(self, all_signals: List[Tuple[pd.Series, float]], df: pd.DataFrame) -> pd.Series:
        """
        Kombinuje sygnały sekwencyjnie (druga strategia może anulować sygnały pierwszej).
        
        Args:
            all_signals: Lista krotek (seria sygnałów, waga)
            df: Oryginalna ramka danych
            
        Returns:
            Series z skombinowanymi sygnałami
        """
        # Tworzenie pustej serii sygnałów z indeksem z oryginalnych danych
        combined = pd.Series(0, index=df.index)
        
        # Dla każdej strategii, aktualizuj sygnały sekwencyjnie
        for signals, _ in all_signals:
            for idx in combined.index:
                if idx in signals.index and signals[idx] != 0:
                    combined[idx] = signals[idx]
        
        return combined
    
    def get_strategy_params(self) -> Dict[str, Any]:
        """
        Zwraca parametry kombinatora jako słownik.
        
        Returns:
            Słownik parametrów kombinatora
        """
        return {{
            'strategy_configs': self.strategy_configs,
            'weights': self.weights,
            'combination_method': self.combination_method
        }}
'''
        
        # Generowanie pliku kombinatora
        try:
            # Tworzenie katalogu strategii, jeśli nie istnieje
            os.makedirs(self.strategies_dir, exist_ok=True)
            
            # Zapisywanie pliku kombinatora
            with open(file_path, 'w') as f:
                f.write(imports_code + class_code)
            
            logger.info(f"Utworzono szablon kombinatora strategii: {file_path}")
            return f"Utworzono szablon kombinatora strategii: {file_path}"
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania szablonu kombinatora strategii: {e}", exc_info=True)
            return f"Błąd podczas generowania szablonu kombinatora strategii: {str(e)}"