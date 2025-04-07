import pandas as pd
import numpy as np
import logging
import time
import itertools
from typing import Dict, List, Any, Optional, Union, Type, Tuple, Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import plotly.graph_objects as go
import plotly.express as px

from src.strategies.base import BaseStrategy
from src.core.backtest_manager import BacktestManager
from src.core.constants import SignalType

logger = logging.getLogger(__name__)

class StrategyOptimizer:
    """
    Klasa do optymalizacji parametrów strategii tradingowych.
    Wykonuje grid search i inne metody optymalizacji dla parametrów strategii.
    """
    
    def __init__(self, backtest_manager: Optional[BacktestManager] = None):
        """
        Inicjalizuje optymalizator strategii.
        
        Args:
            backtest_manager: Instancja BacktestManager do przeprowadzania backtestów
        """
        self.backtest_manager = backtest_manager or BacktestManager()
        logger.info("Strategy optimizer initialized")
    
    def generate_parameter_grid(self, param_ranges: Dict[str, Union[List, np.ndarray, range]]) -> List[Dict[str, Any]]:
        """
        Generuje siatkę parametrów dla grid search.
        
        Args:
            param_ranges: Słownik z zakresami parametrów. 
                          Każdy klucz to nazwa parametru, a wartość to lista możliwych wartości.
                          
        Returns:
            Lista słowników z kombinacjami parametrów
        """
        # Przekształcenie zakresów parametrów do list wartości
        param_lists = {}
        for param_name, param_range in param_ranges.items():
            if isinstance(param_range, (list, np.ndarray, range)):
                param_lists[param_name] = list(param_range)
            else:
                param_lists[param_name] = [param_range]  # Pojedyncza wartość

        # Generowanie wszystkich kombinacji parametrów
        param_names = list(param_lists.keys())
        param_values = [param_lists[name] for name in param_names]
        
        # Używanie itertools.product do tworzenia kombinacji
        result = []
        for combination in itertools.product(*param_values):
            result.append({name: value for name, value in zip(param_names, combination)})
        
        logger.info(f"Generated parameter grid with {len(result)} combinations")
        return result
    
    def _run_backtest_with_params(self, 
                                 strategy_class: Type[BaseStrategy], 
                                 tickers: List[str],
                                 start_date: str,
                                 end_date: str,
                                 strategy_params: Dict[str, Any],
                                 risk_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Uruchamia pojedynczy backtest z określonymi parametrami.
        
        Args:
            strategy_class: Klasa strategii
            tickers: Lista tickerów
            start_date: Data początkowa
            end_date: Data końcowa
            strategy_params: Parametry strategii
            risk_params: Parametry zarządzania ryzykiem
            
        Returns:
            Wyniki backtestu i użyte parametry
        """
        try:
            # Uruchomienie backtestu
            signals, results, stats = self.backtest_manager.run_backtest(
                strategy_type=strategy_class.__name__.replace("Strategy", ""),
                tickers=tickers,
                strategy_params=strategy_params,
                risk_params=risk_params,
                start_date=start_date,
                end_date=end_date
            )
            
            if not stats:
                logger.warning(f"No stats returned for parameters: {strategy_params}")
                return {
                    "success": False,
                    "params": strategy_params,
                    "error": "No statistics returned from backtest"
                }
            
            # Zwracanie wyników wraz z parametrami
            return {
                "success": True,
                "params": strategy_params,
                "stats": stats,
                "n_trades": len(results.get("trades", [])),
                "date_range": f"{start_date} to {end_date}"
            }
            
        except Exception as e:
            logger.error(f"Error running backtest with params {strategy_params}: {e}", exc_info=True)
            return {
                "success": False,
                "params": strategy_params,
                "error": str(e)
            }
    
    def grid_search(self, 
                   strategy_class: Type[BaseStrategy],
                   param_ranges: Dict[str, Union[List, np.ndarray, range]],
                   tickers: List[str],
                   start_date: str,
                   end_date: str,
                   risk_params: Optional[Dict[str, Any]] = None,
                   metric: str = "Sharpe Ratio",
                   n_jobs: int = 1,
                   use_processes: bool = False) -> List[Dict[str, Any]]:
        """
        Przeprowadza grid search dla parametrów strategii.
        
        Args:
            strategy_class: Klasa strategii
            param_ranges: Zakresy parametrów do przeszukania
            tickers: Lista tickerów
            start_date: Data początkowa
            end_date: Data końcowa
            risk_params: Parametry zarządzania ryzykiem
            metric: Metryka do optymalizacji (np. "Sharpe Ratio", "Total Return", "Max Drawdown")
            n_jobs: Liczba równoległych zadań (1 = sekwencyjnie)
            use_processes: Czy używać procesów zamiast wątków (True = procesy)
            
        Returns:
            Lista wyników dla wszystkich kombinacji parametrów, posortowana wg metryki
        """
        # Generowanie siatki parametrów
        param_grid = self.generate_parameter_grid(param_ranges)
        total_combinations = len(param_grid)
        
        logger.info(f"Starting grid search with {total_combinations} parameter combinations")
        logger.info(f"Optimizing for metric: {metric}")
        
        start_time = time.time()
        results = []
        
        # Uruchamianie backtestów sekwencyjnie lub równolegle
        if n_jobs == 1:
            # Sekwencyjne uruchamianie
            for i, params in enumerate(param_grid):
                logger.info(f"Running backtest {i+1}/{total_combinations} with params: {params}")
                result = self._run_backtest_with_params(
                    strategy_class, tickers, start_date, end_date, params, risk_params
                )
                results.append(result)
                
        else:
            # Równoległe uruchamianie
            executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
            
            with executor_class(max_workers=n_jobs) as executor:
                futures = []
                
                for params in param_grid:
                    future = executor.submit(
                        self._run_backtest_with_params,
                        strategy_class, tickers, start_date, end_date, params, risk_params
                    )
                    futures.append(future)
                
                # Zbieranie wyników w miarę ich ukończenia
                for i, future in enumerate(as_completed(futures)):
                    try:
                        result = future.result()
                        results.append(result)
                        logger.info(f"Completed backtest {i+1}/{total_combinations} with params: {result['params']}")
                    except Exception as e:
                        logger.error(f"Error in backtest future {i+1}: {e}", exc_info=True)
                        results.append({
                            "success": False,
                            "params": "Unknown params",
                            "error": str(e)
                        })
        
        # Obliczenie czasu wykonania
        elapsed_time = time.time() - start_time
        logger.info(f"Grid search completed in {elapsed_time:.2f} seconds")
        
        # Sortowanie wyników według metryki (jeśli istnieje)
        successful_results = [r for r in results if r["success"]]
        
        # Metryki, które są "im mniejsze, tym lepsze" (np. drawdown)
        reverse_metrics = ["Max Drawdown", "Maximum Drawdown", "Volatility"]
        is_reverse = any(m.lower() in metric.lower() for m in reverse_metrics)
        
        sorted_results = sorted(
            successful_results, 
            key=lambda x: self._extract_metric(x, metric),
            reverse=not is_reverse  # Jeśli metryka jest z reverse_metrics, sortuj rosnąco
        )
        
        # Dodawanie rankingu do wyników
        for i, result in enumerate(sorted_results):
            result["rank"] = i + 1
        
        logger.info(f"Grid search sorted {len(sorted_results)} successful results by {metric}")
        
        # Dla metryk, gdzie mniejsza wartość jest lepsza, najpierw jest najlepsza
        if sorted_results and is_reverse:
            logger.info(f"Best params: {sorted_results[0]['params']} with {metric}: {self._extract_metric(sorted_results[0], metric)}")
        elif sorted_results:
            logger.info(f"Best params: {sorted_results[0]['params']} with {metric}: {self._extract_metric(sorted_results[0], metric)}")
        
        return sorted_results
    
    def _extract_metric(self, result: Dict[str, Any], metric: str) -> float:
        """
        Wyciąga wartość metryki z wyników. Obsługuje różne nazewnictwo metryk.
        
        Args:
            result: Słownik z wynikami
            metric: Nazwa metryki
            
        Returns:
            Wartość metryki lub -float('inf') dla maksymalizacji lub float('inf') dla minimalizacji
        """
        # Niekompletne wyniki
        if not result["success"] or "stats" not in result:
            return -float('inf')  # Dla maksymalizacji
        
        stats = result["stats"]
        
        # Metryki, które są "im mniejsze, tym lepsze"
        reverse_metrics = ["Max Drawdown", "Maximum Drawdown", "Volatility"]
        is_reverse = any(m.lower() in metric.lower() for m in reverse_metrics)
        
        # Mapowanie różnych nazw metryk
        metric_mapping = {
            "sharpe ratio": ["Sharpe Ratio", "Sharpe", "sharpe_ratio"],
            "sortino ratio": ["Sortino Ratio", "Sortino", "sortino_ratio"],
            "calmar ratio": ["Calmar Ratio", "Calmar", "calmar_ratio"],
            "total return": ["Total Return", "Return", "total_return"],
            "max drawdown": ["Max Drawdown", "Maximum Drawdown", "drawdown", "max_drawdown"],
            "volatility": ["Volatility", "vol"],
            "win rate": ["Win Rate", "win_rate"],
            "profit factor": ["Profit Factor", "profit_factor"]
        }
        
        # Znalezienie odpowiedniej metryki
        for key, alternatives in metric_mapping.items():
            if any(m.lower() == metric.lower() for m in alternatives):
                for alt in alternatives:
                    if alt in stats:
                        return stats[alt]
        
        # Jeśli nie znaleziono metryki, zwróć NaN i zaloguj ostrzeżenie
        logger.warning(f"Metric {metric} not found in results. Available metrics: {list(stats.keys())}")
        return float('nan')
    
    def plot_optimization_results(self, results: List[Dict[str, Any]], 
                                 param_x: str, 
                                 param_y: Optional[str] = None,
                                 metric: str = "Sharpe Ratio") -> go.Figure:
        """
        Tworzy wykres wyników optymalizacji dla jednego lub dwóch parametrów.
        
        Args:
            results: Lista wyników z grid search
            param_x: Nazwa parametru dla osi X
            param_y: Nazwa parametru dla osi Y (opcjonalnie, dla heat map)
            metric: Metryka do wizualizacji
            
        Returns:
            go.Figure: Figura plotly z wykresem
        """
        # Filtrowanie tylko udanych wyników
        successful_results = [r for r in results if r["success"]]
        
        if not successful_results:
            fig = go.Figure()
            fig.add_annotation(
                text="No successful optimization results to plot",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False
            )
            return fig
        
        # Sprawdzenie czy parametry istnieją w wynikach
        if param_x not in successful_results[0]["params"]:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Parameter {param_x} not found in results",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False
            )
            return fig
        
        # Wykres 2D (liniowy) dla jednego parametru
        if param_y is None:
            # Grupowanie wyników według wartości param_x
            grouped_data = {}
            for result in successful_results:
                x_value = result["params"][param_x]
                metric_value = self._extract_metric(result, metric)
                
                if x_value not in grouped_data:
                    grouped_data[x_value] = []
                grouped_data[x_value].append(metric_value)
            
            # Dla każdej wartości param_x, oblicz średnią metryki
            x_values = []
            y_values = []
            for x_value, metric_values in grouped_data.items():
                x_values.append(x_value)
                y_values.append(sum(metric_values) / len(metric_values))
            
            # Sortowanie punktów według wartości X
            points = sorted(zip(x_values, y_values))
            x_values = [p[0] for p in points]
            y_values = [p[1] for p in points]
            
            # Tworzenie wykresu liniowego
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=x_values,
                y=y_values,
                mode='lines+markers',
                name=metric
            ))
            
            fig.update_layout(
                title=f"{metric} vs {param_x}",
                xaxis_title=param_x,
                yaxis_title=metric,
                template="plotly_dark"
            )
        
        # Wykres 3D (heatmapa) dla dwóch parametrów
        else:
            if param_y not in successful_results[0]["params"]:
                fig = go.Figure()
                fig.add_annotation(
                    text=f"Parameter {param_y} not found in results",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False
                )
                return fig
            
            # Tworzenie danych dla heatmapy
            # Zbieranie unikalnych wartości dla obu parametrów
            x_values = sorted(set(r["params"][param_x] for r in successful_results))
            y_values = sorted(set(r["params"][param_y] for r in successful_results))
            
            # Tworzenie siatki z wartościami metryki
            z_values = np.full((len(y_values), len(x_values)), np.nan)
            
            # Wypełnianie siatki wartościami
            for result in successful_results:
                x_idx = x_values.index(result["params"][param_x])
                y_idx = y_values.index(result["params"][param_y])
                z_values[y_idx, x_idx] = self._extract_metric(result, metric)
            
            # Tworzenie heatmapy
            fig = go.Figure(data=go.Heatmap(
                z=z_values,
                x=x_values,
                y=y_values,
                colorscale='Viridis',
                hoverongaps=False
            ))
            
            fig.update_layout(
                title=f"{metric} by {param_x} and {param_y}",
                xaxis_title=param_x,
                yaxis_title=param_y,
                template="plotly_dark"
            )
        
        return fig
    
    def optimize_walk_forward(self, 
                             strategy_class: Type[BaseStrategy],
                             param_ranges: Dict[str, Union[List, np.ndarray, range]],
                             tickers: List[str],
                             start_date: str,
                             end_date: str,
                             window_size: int = 252,
                             step_size: int = 126,
                             metric: str = "Sharpe Ratio",
                             risk_params: Optional[Dict[str, Any]] = None,
                             n_jobs: int = 1) -> Dict[str, Any]:
        """
        Przeprowadza optymalizację walk-forward, optymalizując parametry na oknie 
        i testując na okresie poza oknem.
        
        Args:
            strategy_class: Klasa strategii
            param_ranges: Zakresy parametrów do przeszukania
            tickers: Lista tickerów
            start_date: Data początkowa
            end_date: Data końcowa
            window_size: Rozmiar okna optymalizacyjnego (w dniach)
            step_size: Rozmiar kroku przesuwania okna (w dniach)
            metric: Metryka do optymalizacji
            risk_params: Parametry zarządzania ryzykiem
            n_jobs: Liczba równoległych zadań
            
        Returns:
            Wyniki optymalizacji walk-forward
        """
        # Konwersja dat do obiektów datetime
        from datetime import datetime, timedelta
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Inicjalizacja wyników
        wf_results = {
            "windows": [],
            "best_params": [],
            "in_sample_metrics": [],
            "out_of_sample_metrics": [],
            "robustness_ratio": []  # Stosunek wyników out-of-sample do in-sample
        }
        
        current_start = start
        window_id = 1
        
        while current_start + timedelta(days=window_size) < end:
            # Definicja okna in-sample i out-of-sample
            in_sample_end = current_start + timedelta(days=window_size)
            out_sample_end = min(in_sample_end + timedelta(days=step_size), end)
            
            in_sample_start_str = current_start.strftime("%Y-%m-%d")
            in_sample_end_str = in_sample_end.strftime("%Y-%m-%d")
            out_sample_start_str = in_sample_end.strftime("%Y-%m-%d")
            out_sample_end_str = out_sample_end.strftime("%Y-%m-%d")
            
            logger.info(f"Walk-forward window {window_id}:")
            logger.info(f"  In-sample:  {in_sample_start_str} to {in_sample_end_str}")
            logger.info(f"  Out-sample: {out_sample_start_str} to {out_sample_end_str}")
            
            # Optymalizacja parametrów na oknie in-sample
            in_sample_results = self.grid_search(
                strategy_class=strategy_class,
                param_ranges=param_ranges,
                tickers=tickers,
                start_date=in_sample_start_str,
                end_date=in_sample_end_str,
                risk_params=risk_params,
                metric=metric,
                n_jobs=n_jobs
            )
            
            if not in_sample_results:
                logger.warning(f"No valid results for in-sample window {window_id}")
                current_start = current_start + timedelta(days=step_size)
                window_id += 1
                continue
            
            # Najlepsze parametry z in-sample
            best_params = in_sample_results[0]["params"]
            in_sample_metric = self._extract_metric(in_sample_results[0], metric)
            
            # Test najlepszych parametrów na out-of-sample
            out_sample_result = self._run_backtest_with_params(
                strategy_class=strategy_class,
                tickers=tickers,
                start_date=out_sample_start_str,
                end_date=out_sample_end_str,
                strategy_params=best_params,
                risk_params=risk_params
            )
            
            # Zapisywanie wyników
            out_sample_metric = self._extract_metric(out_sample_result, metric)
            
            # Obliczanie współczynnika odporności (stosunek out-of-sample do in-sample)
            # Jeśli in-sample jest 0 lub blisko 0, ustawiamy na NaN
            if abs(in_sample_metric) < 0.00001:
                robustness = float('nan')
            else:
                robustness = out_sample_metric / in_sample_metric
            
            wf_results["windows"].append({
                "id": window_id,
                "in_sample_start": in_sample_start_str,
                "in_sample_end": in_sample_end_str,
                "out_sample_start": out_sample_start_str,
                "out_sample_end": out_sample_end_str
            })
            wf_results["best_params"].append(best_params)
            wf_results["in_sample_metrics"].append(in_sample_metric)
            wf_results["out_of_sample_metrics"].append(out_sample_metric)
            wf_results["robustness_ratio"].append(robustness)
            
            logger.info(f"  Best params: {best_params}")
            logger.info(f"  In-sample {metric}: {in_sample_metric}")
            logger.info(f"  Out-sample {metric}: {out_sample_metric}")
            logger.info(f"  Robustness ratio: {robustness}")
            
            # Przesunięcie okna
            current_start = current_start + timedelta(days=step_size)
            window_id += 1
        
        # Łączenie wyników
        wf_results["summary"] = {
            "avg_in_sample_metric": np.mean(wf_results["in_sample_metrics"]),
            "avg_out_of_sample_metric": np.mean(wf_results["out_of_sample_metrics"]),
            "avg_robustness_ratio": np.mean([r for r in wf_results["robustness_ratio"] if not np.isnan(r)]),
            "windows_count": len(wf_results["windows"]),
            "most_common_params": self._get_most_common_params(wf_results["best_params"])
        }
        
        logger.info(f"Walk-forward optimization completed with {len(wf_results['windows'])} windows")
        logger.info(f"Average in-sample {metric}: {wf_results['summary']['avg_in_sample_metric']}")
        logger.info(f"Average out-of-sample {metric}: {wf_results['summary']['avg_out_of_sample_metric']}")
        logger.info(f"Most common parameter set: {wf_results['summary']['most_common_params']}")
        
        return wf_results
    
    def _get_most_common_params(self, param_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Znajduje najczęściej występujące parametry w liście parametrów.
        
        Args:
            param_list: Lista słowników z parametrami
            
        Returns:
            Najczęściej występujący zestaw parametrów
        """
        if not param_list:
            return {}
        
        # Konwersja słowników na tuple, żeby można je było zliczać
        param_tuples = []
        for params in param_list:
            # Sortowanie kluczy dla spójności
            items = sorted(params.items())
            param_tuples.append(tuple(items))
        
        # Zliczanie wystąpień
        from collections import Counter
        counts = Counter(param_tuples)
        most_common = counts.most_common(1)[0][0]
        
        # Konwersja z powrotem na słownik
        return dict(most_common)
    
    def plot_walk_forward_results(self, wf_results: Dict[str, Any], metric: str) -> go.Figure:
        """
        Tworzy wykres wyników optymalizacji walk-forward.
        
        Args:
            wf_results: Wyniki optymalizacji walk-forward
            metric: Nazwa metryki
            
        Returns:
            go.Figure: Figura plotly z wykresem
        """
        if not wf_results["windows"]:
            fig = go.Figure()
            fig.add_annotation(
                text="No walk-forward results to plot",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False
            )
            return fig
        
        # Przygotowanie danych do wykresu
        window_ids = [w["id"] for w in wf_results["windows"]]
        in_sample = wf_results["in_sample_metrics"]
        out_sample = wf_results["out_of_sample_metrics"]
        robustness = wf_results["robustness_ratio"]
        
        # Tworzenie wykresu z dwiema osiami Y
        fig = go.Figure()
        
        # Dane dla metryki
        fig.add_trace(go.Scatter(
            x=window_ids,
            y=in_sample,
            mode='lines+markers',
            name=f'In-Sample {metric}',
            line=dict(color='#17BECF')
        ))
        
        fig.add_trace(go.Scatter(
            x=window_ids,
            y=out_sample,
            mode='lines+markers',
            name=f'Out-of-Sample {metric}',
            line=dict(color='#7F7F7F')
        ))
        
        # Dane dla współczynnika odporności na drugiej osi Y
        fig.add_trace(go.Scatter(
            x=window_ids,
            y=robustness,
            mode='lines+markers',
            name='Robustness Ratio',
            yaxis='y2',
            line=dict(color='#BCBD22')
        ))
        
        # Konfiguracja układu z dwiema osiami Y
        fig.update_layout(
            title=f'Walk-Forward Optimization Results for {metric}',
            xaxis=dict(title='Window ID'),
            yaxis=dict(title=metric, side='left'),
            yaxis2=dict(
                title='Robustness Ratio',
                side='right',
                overlaying='y',
                showgrid=False
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            template="plotly_dark"
        )
        
        # Dodawanie linii referencyjnej dla robustness = 1.0
        fig.add_shape(
            type="line",
            x0=min(window_ids),
            y0=1.0,
            x1=max(window_ids),
            y1=1.0,
            xref='x',
            yref='y2',
            line=dict(
                color="red",
                width=1,
                dash="dot",
            )
        )
        
        return fig
    
    def monte_carlo_optimization(self, 
                                strategy_class: Type[BaseStrategy],
                                param_ranges: Dict[str, Union[List, tuple]],
                                n_trials: int = 100,
                                tickers: List[str] = None,
                                start_date: str = None,
                                end_date: str = None,
                                risk_params: Optional[Dict[str, Any]] = None,
                                metric: str = "Sharpe Ratio",
                                n_jobs: int = 1) -> List[Dict[str, Any]]:
        """
        Przeprowadza optymalizację Monte Carlo, losowo próbkując parametry.
        
        Args:
            strategy_class: Klasa strategii
            param_ranges: Zakresy parametrów w formacie {nazwa: (min, max, typ)}
            n_trials: Liczba losowych prób
            tickers: Lista tickerów
            start_date: Data początkowa
            end_date: Data końcowa
            risk_params: Parametry zarządzania ryzykiem
            metric: Metryka do optymalizacji
            n_jobs: Liczba równoległych zadań
            
        Returns:
            Lista wyników z losowo próbkowanych parametrów
        """
        import random
        
        logger.info(f"Starting Monte Carlo optimization with {n_trials} trials")
        
        # Generowanie losowych kombinacji parametrów
        random_params_list = []
        for _ in range(n_trials):
            params = {}
            for param_name, param_range in param_ranges.items():
                # Obsługa różnych typów zakresów
                if isinstance(param_range, (list, np.ndarray, range)):
                    # Jeśli to lista wartości, wybierz losowo jedną
                    params[param_name] = random.choice(param_range)
                elif isinstance(param_range, tuple) and len(param_range) >= 2:
                    min_val, max_val = param_range[0], param_range[1]
                    # Jeśli podano typ (np. int), użyj go
                    param_type = param_range[2] if len(param_range) > 2 else None
                    
                    if param_type == int:
                        params[param_name] = random.randint(min_val, max_val)
                    elif param_type == bool:
                        params[param_name] = random.choice([True, False])
                    else:  # domyślnie float
                        params[param_name] = random.uniform(min_val, max_val)
                else:
                    # Jeśli to pojedyncza wartość
                    params[param_name] = param_range
            
            random_params_list.append(params)
        
        # Uruchamianie backtestów z losowymi parametrami
        results = []
        
        # Jeśli n_jobs > 1, użyj równoległości
        if n_jobs > 1:
            with ThreadPoolExecutor(max_workers=n_jobs) as executor:
                futures = []
                
                for params in random_params_list:
                    future = executor.submit(
                        self._run_backtest_with_params,
                        strategy_class, tickers, start_date, end_date, params, risk_params
                    )
                    futures.append(future)
                
                for i, future in enumerate(as_completed(futures)):
                    try:
                        result = future.result()
                        results.append(result)
                        logger.info(f"Completed Monte Carlo trial {i+1}/{n_trials}")
                    except Exception as e:
                        logger.error(f"Error in Monte Carlo trial {i+1}: {e}")
        else:
            # Sekwencyjne wykonanie
            for i, params in enumerate(random_params_list):
                logger.info(f"Running Monte Carlo trial {i+1}/{n_trials} with params: {params}")
                result = self._run_backtest_with_params(
                    strategy_class, tickers, start_date, end_date, params, risk_params
                )
                results.append(result)
        
        # Sortowanie wyników według metryki optymalizacji
        successful_results = [r for r in results if r.get("success", False)]
        
        # Metryki, które są "im mniejsze, tym lepsze" (np. drawdown)
        reverse_metrics = ["Max Drawdown", "Maximum Drawdown", "Volatility"]
        is_reverse = any(m.lower() in metric.lower() for m in reverse_metrics)
        
        sorted_results = sorted(
            successful_results, 
            key=lambda x: self._extract_metric(x, metric),
            reverse=not is_reverse
        )
        
        # Dodawanie rankingu do wyników
        for i, result in enumerate(sorted_results):
            result["rank"] = i + 1
        
        logger.info(f"Monte Carlo optimization completed with {len(sorted_results)} successful trials")
        if sorted_results:
            logger.info(f"Best params: {sorted_results[0]['params']} with {metric}: {self._extract_metric(sorted_results[0], metric)}")
        
        return sorted_results