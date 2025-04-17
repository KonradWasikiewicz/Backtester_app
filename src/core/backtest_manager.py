import pandas as pd
import numpy as np
import logging
import traceback
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# --- Konfiguracja Logowania ---
logger = logging.getLogger(__name__)

# --- Importy Lokalne ---
try:
    from src.core.constants import STRATEGY_CLASS_MAP, TRADING_DAYS_PER_YEAR
    from src.core.data import DataLoader
    from src.core.config import config
    from src.portfolio.portfolio_manager import PortfolioManager
    from src.portfolio.risk_manager import RiskManager
    from src.strategies.base import BaseStrategy
    from src.analysis.metrics import (
        calculate_cagr, calculate_sharpe_ratio, calculate_sortino_ratio,
        calculate_max_drawdown, calculate_annualized_volatility, calculate_return_series,
        calculate_alpha, calculate_beta, calculate_information_ratio,
        calculate_recovery_factor, calculate_trade_statistics
    )
except ImportError as e:
    logger.error(f"CRITICAL: Failed to import core/portfolio/analysis modules in BacktestManager: {e}", exc_info=True)
    raise ImportError("Core module import failed in BacktestManager") from e

class BacktestManager:
    """
    Manages the execution of backtests for trading strategies across multiple instruments.
    """

    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        try:
            self.data_loader = DataLoader(data_path=config.DATA_PATH)
            logger.info(f"BacktestManager initialized with initial capital: ${initial_capital:,.2f} and data path: {config.DATA_PATH}")
        except Exception as e:
            logger.error(f"CRITICAL: Failed to initialize DataLoader in BacktestManager: {e}", exc_info=True)
            raise RuntimeError("DataLoader initialization failed") from e

    def run_backtest(self, strategy_type: str, tickers: list[str], strategy_params: dict[str, Any] = None, risk_params: dict[str, Any] = None):
        """Runs a backtest for the specified strategy, tickers, and parameters."""
        logger.info(f"--- Starting New Backtest ---")
        logger.info(f"Strategy: {strategy_type}, Tickers: {tickers}")
        logger.info(f"Strategy Params: {strategy_params}, Risk Params: {risk_params}")

        try:
            # --- 1. Initialization ---
            # Find matching key in STRATEGY_CLASS_MAP (case-insensitive)
            strategy_key = next((k for k in STRATEGY_CLASS_MAP.keys() if k.lower() == strategy_type.lower()), None)
            if not strategy_key:
                logger.error(f"Strategy '{strategy_type}' not found in STRATEGY_CLASS_MAP.")
                return None, None, None
            strategy_class: type[BaseStrategy] = STRATEGY_CLASS_MAP[strategy_key]
            if not tickers: logger.error("No tickers provided."); return None, None, None

            strategy_params = strategy_params or {}
            try:
                # Instantiate strategy with only its specific parameters
                strategy = strategy_class(**strategy_params)
                logger.info(f"Initialized strategy '{strategy_type}' with params: {strategy_params}")
            except Exception as e: logger.error(f"Error initializing strategy '{strategy_type}': {e}", exc_info=True); return None, None, None

            # Initialize RiskManager with configuration dict (keys expected: apply_risk_rules, use_*, stop_loss_pct, risk_per_trade, max_open_positions, etc.)
            try:
                risk_manager = RiskManager(risk_params or {})
                logger.info("Initialized RiskManager with provided risk_params configuration.")
            except Exception as e:
                logger.error(f"Error initializing RiskManager with provided config: {e}. Using default RiskManager.", exc_info=True)
                risk_manager = RiskManager()
            portfolio_manager = PortfolioManager(initial_capital=self.initial_capital, risk_manager=risk_manager)

            # --- 2. Data Loading and Preparation ---
            all_ticker_data = self.data_loader.load_all_data()
            if not all_ticker_data: logger.error("Failed to load any ticker data."); return None, None, None

            valid_tickers = [t for t in tickers if t in all_ticker_data and not all_ticker_data[t].empty]
            if not valid_tickers: logger.error(f"None of selected tickers {tickers} have valid data."); return None, None, None
            logger.info(f"Using data for {len(valid_tickers)} tickers: {', '.join(valid_tickers)}")

            try:
                panel_data = {ticker: all_ticker_data[ticker][['Open', 'High', 'Low', 'Close', 'Volume']] for ticker in valid_tickers if all(col in all_ticker_data[ticker].columns for col in ['Open', 'High', 'Low', 'Close', 'Volume'])}
                if not panel_data: logger.error("No valid data panels created."); return None, None, None
                combined_df = pd.concat(panel_data, axis=1, keys=panel_data.keys()); combined_df.index = pd.to_datetime(combined_df.index).tz_localize(None); combined_df = combined_df.sort_index()
                start_date = pd.to_datetime(config.START_DATE).tz_localize(None); end_date = pd.to_datetime(config.END_DATE).tz_localize(None)
                combined_df_filtered = combined_df.loc[start_date:end_date]; backtest_range = combined_df_filtered.index.unique()
                if backtest_range.empty: logger.error(f"No data in date range: {start_date} to {end_date}"); return None, None, None
                logger.info(f"Combined data prepared. Shape: {combined_df_filtered.shape}. Date range: {backtest_range.min()} to {backtest_range.max()}")
            except Exception as e: logger.error(f"Error creating combined data panel: {e}", exc_info=True); return None, None, None

            # --- 3. Signal Generation (Pre-computation) ---
            all_signals = {}
            logger.info("Generating signals for all tickers...")
            for ticker in valid_tickers:
                try:
                    ticker_data_full = all_ticker_data[ticker]
                    # generate_signals expects only the data frame
                    signals_df = strategy.generate_signals(ticker_data_full)
                    if signals_df is not None and not signals_df.empty:
                         signals_df.index = pd.to_datetime(signals_df.index).tz_localize(None)
                         all_signals[ticker] = signals_df.reindex(combined_df.index).fillna(0)
                except Exception as e: logger.error(f"Error generating signals for {ticker}: {e}", exc_info=True)
            logger.info(f"Signal generation complete for {len(all_signals)} tickers.")

            # --- 4. Backtest Execution Loop ---
            logger.info("Starting backtest simulation loop...")
            portfolio_history = []

            # Market Filter Data Preparation
            market_filter_data = None
            apply_market_filter = bool(risk_params.get('use_market_filter', False))
            if apply_market_filter:
                 try:
                      spy_data_df = self.data_loader.load_benchmark_data_df() # Użyj nowej metody z DataLoader
                      if spy_data_df is not None and not spy_data_df.empty:
                            spy_data_df.index = pd.to_datetime(spy_data_df.index).tz_localize(None); spy_close = spy_data_df['Close']
                            market_filter_data_series = spy_close.rolling(window=risk_manager.market_trend_lookback).mean()
                            market_filter_data = market_filter_data_series.reindex(combined_df.index).ffill(); logger.info(f"Market filter data (MA {risk_manager.market_trend_lookback}) prepared.")
                      else: logger.warning("Benchmark data for market filter not found. Disabling filter."); apply_market_filter = False
                 except Exception as e: logger.warning(f"Error preparing market filter data: {e}. Disabling filter.", exc_info=True); apply_market_filter = False

            # Main Loop
            for current_date in backtest_range:
                try:
                    current_market_slice = combined_df_filtered.loc[[current_date]]

                    # Market Regime Check (bez zmian)
                    is_market_favorable = True
                    if apply_market_filter and market_filter_data is not None:
                         try:
                              current_spy_ma = market_filter_data.loc[current_date]
                              current_spy_close = spy_close.loc[current_date]
                              if pd.notna(current_spy_close) and pd.notna(current_spy_ma): is_market_favorable = current_spy_close >= current_spy_ma
                         except KeyError: is_market_favorable = True

                    # Process Exits and Update Stops (bez zmian)
                    current_prices_dict = {ticker: current_market_slice.loc[current_date, (ticker, 'Close')] for ticker in portfolio_manager.positions.keys() if (ticker, 'Close') in current_market_slice.columns and pd.notna(current_market_slice.loc[current_date, (ticker, 'Close')])}
                    # Dodaj fallback jeśli cena jest NaN dla otwartej pozycji
                    for ticker in portfolio_manager.positions.keys():
                         if ticker not in current_prices_dict:
                              last_known_price = portfolio_manager.positions[ticker].entry_price # Użyj ceny wejścia jako fallback
                              logger.warning(f"Using last known price (${last_known_price:.2f}) for stop/exit check for {ticker} on {current_date}")
                              current_prices_dict[ticker] = last_known_price

                    if current_prices_dict: portfolio_manager.update_positions_and_stops(current_prices_dict, current_date)

                    # Generate and Process Entry Signals
                    if is_market_favorable:
                        for ticker in valid_tickers:
                            if ticker in all_signals:
                                try: signal_value = all_signals[ticker].loc[current_date, 'Signal']
                                except (KeyError, IndexError): signal_value = 0

                                if signal_value > 0 and ticker not in portfolio_manager.positions:
                                    try:
                                        entry_price = combined_df_filtered.loc[current_date, (ticker, 'Close')]
                                        if pd.isna(entry_price) or entry_price <= 0: continue

                                        # <<<--- USUNIĘCIE OBLICZANIA ZMIENNOŚCI TUTAJ --->>>
                                        # Zamiast obliczać, przekazujemy None lub stałą
                                        calculated_volatility = None # Przekaż None, RiskManager sobie poradzi
                                        # LUB stała: calculated_volatility = 0.02

                                        signal_data = {
                                            'ticker': ticker, 'date': current_date, 'price': entry_price,
                                            'direction': 1, 'volatility': calculated_volatility
                                        }
                                        portfolio_manager.open_position(signal_data)

                                    except KeyError: logger.warning(f"Could not get price for {ticker} on {current_date} for buy signal."); continue
                                    except Exception as sig_proc_e: logger.error(f"Error processing buy signal for {ticker} on {current_date}: {sig_proc_e}", exc_info=True); continue

                                elif signal_value < 0 and ticker in portfolio_manager.positions:
                                    try:
                                        exit_price = combined_df_filtered.loc[current_date, (ticker, 'Close')]
                                        if pd.isna(exit_price) or exit_price <= 0: logger.warning(f"Invalid exit price ({exit_price}) for {ticker} on {current_date}. Skipping close."); continue
                                        portfolio_manager.close_position(ticker, exit_price, current_date, reason="signal")
                                    except KeyError: logger.warning(f"Could not get price for {ticker} on {current_date} for sell signal."); continue
                                    except Exception as sig_proc_e: logger.error(f"Error processing sell signal for {ticker} on {current_date}: {sig_proc_e}", exc_info=True); continue

                    # Update & Record Portfolio Value (bez zmian)
                    eod_prices_dict = {ticker: current_market_slice.loc[current_date, (ticker, 'Close')] for ticker in valid_tickers if (ticker, 'Close') in current_market_slice.columns and pd.notna(current_market_slice.loc[current_date, (ticker, 'Close')])}
                    # Dodaj fallback dla otwartych pozycji bez ceny EOD
                    for ticker in portfolio_manager.positions.keys():
                        if ticker not in eod_prices_dict:
                            last_known_price = portfolio_manager.positions[ticker].entry_price
                            logger.warning(f"Using last known price (${last_known_price:.2f}) for EOD valuation for {ticker} on {current_date}")
                            eod_prices_dict[ticker] = last_known_price
                    current_portfolio_value = portfolio_manager.update_portfolio_value(eod_prices_dict, current_date)

                except KeyError as date_err: logger.warning(f"Market data potentially missing for date {current_date}. Error: {date_err}. Carrying forward value."); last_value = portfolio_manager.portfolio_value_history[-1][1] if portfolio_manager.portfolio_value_history else self.initial_capital; portfolio_manager.portfolio_value_history.append((current_date, last_value)); continue
                except Exception as loop_err: logger.error(f"Error in backtest loop for date {current_date}: {loop_err}", exc_info=True); continue

            # --- End of Backtest Loop ---
            logger.info("Backtest simulation loop finished.")

            # Final position closure (bez zmian)
            final_date = backtest_range[-1]
            try:
                 final_market_data_slice = combined_df_filtered.loc[[final_date]]
                 final_prices_dict = {ticker: final_market_data_slice.loc[final_date, (ticker, 'Close')] if (ticker, 'Close') in final_market_data_slice.columns and pd.notna(final_market_data_slice.loc[final_date, (ticker, 'Close')]) else portfolio_manager.positions[ticker].entry_price for ticker in portfolio_manager.positions.keys()}
                 portfolio_manager.close_all_positions(final_prices_dict, final_date, reason="end_of_backtest")
            except Exception as final_close_err: logger.error(f"Error during final position closure: {final_close_err}", exc_info=True)

            # --- 5. Result Aggregation and Statistics ---
            if not portfolio_manager.portfolio_value_history: logger.error("Portfolio history empty."); return None, None, None

            portfolio_df = pd.DataFrame(portfolio_manager.portfolio_value_history, columns=['date', 'value']).set_index('date')
            portfolio_value_series = portfolio_df['value'].sort_index(); portfolio_value_series.name = "Portfolio"
            if portfolio_value_series.empty: logger.error("Portfolio value series empty."); return all_signals, {'trades': portfolio_manager.closed_trades}, {}

            benchmark_value_series = self._get_benchmark_data(portfolio_value_series.index)
            combined_results = {'Portfolio_Value': portfolio_value_series, 'Benchmark': benchmark_value_series, 'trades': portfolio_manager.closed_trades}
            stats = self._calculate_portfolio_stats(combined_results)
            final_pv_str = f"${stats.get('Final Capital', 0):,.2f}" if isinstance(stats.get('Final Capital'), (int, float)) else 'N/A'
            logger.info(f"Backtest analysis complete. Final Portfolio Value: {final_pv_str}, Total Trades: {stats.get('total_trades', 0)}")

            return all_signals, combined_results, stats

        except Exception as e:
            logger.error(f"CRITICAL error during backtest execution: {str(e)}", exc_info=True)
            return None, None, None

    def _get_benchmark_data(self, target_index: pd.DatetimeIndex) -> Optional[pd.Series]:
        """Get benchmark data aligned with the target portfolio index."""
        # (Bez zmian - jak w poprzedniej odpowiedzi)
        if target_index.empty: logger.warning("Cannot get benchmark data for empty target index."); return None
        try:
            benchmark_ticker = config.BENCHMARK_TICKER
            benchmark_data_df = self.data_loader.load_benchmark_data_df() # Używamy metody z DataLoader
            if benchmark_data_df is None or benchmark_data_df.empty: logger.warning(f"Benchmark ticker '{benchmark_ticker}' data not found."); return None
            benchmark_series = benchmark_data_df['Close']; benchmark_series.index = pd.to_datetime(benchmark_series.index).tz_localize(None); benchmark_series = benchmark_series.sort_index()
            aligned_benchmark = benchmark_series.reindex(target_index).ffill().bfill()
            if aligned_benchmark.isnull().all(): logger.warning(f"Benchmark data for {benchmark_ticker} could not be aligned."); return None
            initial_benchmark_price = aligned_benchmark.iloc[0]
            if initial_benchmark_price <= 0: logger.warning(f"Initial benchmark price non-positive."); return None
            shares = self.initial_capital / initial_benchmark_price; benchmark_portfolio = aligned_benchmark * shares; benchmark_portfolio.name = "Benchmark"; logger.info(f"Benchmark data ({benchmark_ticker}) processed and aligned.")
            return benchmark_portfolio
        except Exception as e: logger.error(f"Error loading/processing benchmark data: {str(e)}", exc_info=True); return None

    def _calculate_portfolio_stats(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate portfolio performance statistics."""
        # (Bez zmian - jak w poprzedniej odpowiedzi)
        portfolio_series = results.get('Portfolio_Value'); benchmark_series = results.get('Benchmark'); trades = results.get('trades', [])
        if portfolio_series is None or portfolio_series.empty or len(portfolio_series) < 2: logger.warning("Cannot calculate stats, Portfolio_Value series invalid."); base_stats = {'Initial Capital': self.initial_capital, 'Final Capital': self.initial_capital, 'total_trades': len(trades)}; base_stats.update(calculate_trade_statistics(trades)); return base_stats
        stats = {}; stats['Initial Capital'] = self.initial_capital; stats['Final Capital'] = portfolio_series.iloc[-1]; stats['Total Return'] = ((stats['Final Capital'] / stats['Initial Capital']) - 1) * 100; stats['CAGR'] = calculate_cagr(portfolio_series) * 100 if calculate_cagr(portfolio_series) is not None else None
        stats['Max Drawdown'] = calculate_max_drawdown(portfolio_series) * 100 if calculate_max_drawdown(portfolio_series) is not None else None
        returns_series = calculate_return_series(portfolio_series).dropna()
        if not returns_series.empty:
             risk_free_rate_annual = config.RISK_FREE_RATE; stats['Annualized Volatility'] = calculate_annualized_volatility(returns_series) * 100 if calculate_annualized_volatility(returns_series) is not None else None; stats['Sharpe Ratio'] = calculate_sharpe_ratio(portfolio_series, risk_free_rate=risk_free_rate_annual); stats['Sortino Ratio'] = calculate_sortino_ratio(portfolio_series, risk_free_rate=risk_free_rate_annual)
             if benchmark_series is not None and not benchmark_series.empty and len(benchmark_series) > 1:
                 common_index = portfolio_series.index.intersection(benchmark_series.index)
                 if len(common_index) > 1: portfolio_aligned, benchmark_aligned = portfolio_series[common_index], benchmark_series[common_index]; stats['Alpha'] = calculate_alpha(portfolio_aligned, benchmark_aligned, risk_free_rate=risk_free_rate_annual); stats['Beta'] = calculate_beta(portfolio_aligned, benchmark_aligned); stats['Information Ratio'] = calculate_information_ratio(portfolio_aligned, benchmark_aligned)
                 else: logger.warning("Could not align benchmark for Alpha/Beta/InfoRatio."); stats['Alpha'], stats['Beta'], stats['Information Ratio'] = None, None, None
             else: stats['Alpha'], stats['Beta'], stats['Information Ratio'] = None, None, None
        else: stats['Annualized Volatility'], stats['Sharpe Ratio'], stats['Sortino Ratio'], stats['Alpha'], stats['Beta'], stats['Information Ratio'] = 0.0, 0.0, 0.0, None, None, None
        trade_stats = calculate_trade_statistics(trades); stats.update(trade_stats)
        total_return_abs = abs(stats.get('Final Capital',0) - stats.get('Initial Capital',0)); rolling_max = portfolio_series.cummax(); drawdown_values = rolling_max - portfolio_series; max_drawdown_dollar = drawdown_values.max()
        if max_drawdown_dollar > 0: stats['Recovery Factor'] = total_return_abs / max_drawdown_dollar
        else: stats['Recovery Factor'] = np.inf if total_return_abs > 0 else 0.0
        final_stats = {k: v for k, v in stats.items() if not k.startswith('_')}
        logger.info("Portfolio statistics calculated.")
        return final_stats