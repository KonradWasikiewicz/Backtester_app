import pandas as pd
import numpy as np
import logging
import traceback
from typing import Dict, Tuple, Any, Optional, List
from pathlib import Path
import sys

# --- Konfiguracja Logowania (przeniesiona z app.py dla spójności) ---
# Zakładamy, że główna konfiguracja logowania jest w app.py, tutaj tylko pobieramy logger
logger = logging.getLogger(__name__)

# --- Importy Lokalne ---
try:
    from src.core.constants import AVAILABLE_STRATEGIES, TRADING_DAYS_PER_YEAR
    from src.core.data import DataLoader
    from src.core.engine import BacktestEngine # Zakładając, że Engine jest nadal używany (choć to do refaktoryzacji)
    from src.core.config import config
    from src.portfolio.portfolio_manager import PortfolioManager # Import bezpośredni PortfolioManager
    from src.portfolio.risk_manager import RiskManager
    from src.strategies.base import BaseStrategy # Potrzebne do type hinting
    from src.analysis.metrics import (
        calculate_cagr, calculate_sharpe_ratio, calculate_sortino_ratio,
        calculate_max_drawdown, calculate_annualized_volatility, calculate_return_series, # Dodano potrzebne
        calculate_alpha, calculate_beta, calculate_information_ratio,
        calculate_recovery_factor, calculate_trade_statistics
    )
except ImportError as e:
    # Krytyczny błąd, jeśli nie można zaimportować podstawowych modułów
    logger.error(f"CRITICAL: Failed to import core/portfolio/analysis modules in BacktestManager: {e}")
    logger.error(traceback.format_exc())
    # Można rzucić wyjątek dalej lub zakończyć, aby zapobiec dalszym błędom
    raise ImportError("Core module import failed in BacktestManager") from e


class BacktestManager:
    """
    Manages the execution of backtests for trading strategies across multiple instruments,
    integrating data loading, strategy execution, portfolio management, risk control,
    and performance analysis.
    """

    def __init__(self, initial_capital: float = 100000.0):
        """
        Initializes the BacktestManager.

        Args:
            initial_capital (float): The starting capital for the backtest.
        """
        self.initial_capital = initial_capital
        try:
            # Inicjalizacja DataLoader z poprawną ścieżką
            self.data_loader = DataLoader(data_path=config.DATA_PATH)
            logger.info(f"BacktestManager initialized with initial capital: ${initial_capital:,.2f} and data path: {config.DATA_PATH}")
        except Exception as e:
            logger.error(f"CRITICAL: Failed to initialize DataLoader in BacktestManager: {e}")
            logger.error(traceback.format_exc())
            raise RuntimeError("DataLoader initialization failed") from e


    def run_backtest(self, strategy_type: str, tickers: List[str],
                     strategy_params: Optional[Dict[str, Any]] = None,
                     risk_params: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Dict[str, pd.DataFrame]], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Runs a backtest for the specified strategy, tickers, and parameters.

        This method orchestrates the entire backtesting process:
        1. Initializes the strategy and risk manager.
        2. Loads and prepares historical data.
        3. Iterates through the data day by day (or bar by bar).
        4. Generates trading signals using the strategy.
        5. Manages portfolio positions and cash using PortfolioManager, applying risk rules.
        6. Calculates performance statistics.

        Args:
            strategy_type (str): The name of the strategy class (key in AVAILABLE_STRATEGIES).
            tickers (List[str]): List of ticker symbols to include in the backtest.
            strategy_params (Optional[Dict[str, Any]]): Parameters for the strategy's constructor.
            risk_params (Optional[Dict[str, Any]]): Parameters for the RiskManager's constructor.
                                                    If None, default RiskManager settings are used.

        Returns:
            Tuple[Optional[Dict[str, pd.DataFrame]], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
            A tuple containing:
                - signals (dict): Dictionary mapping tickers to their generated signal DataFrames. None on error.
                - combined_results (dict): Dictionary containing 'Portfolio_Value' (pd.Series),
                  'Benchmark' (pd.Series or None), and 'trades' (list of dicts). None on error.
                - stats (dict): Dictionary of calculated performance metrics. None on error.
        """
        logger.info(f"--- Starting New Backtest ---")
        logger.info(f"Strategy: {strategy_type}, Tickers: {tickers}")
        logger.info(f"Strategy Params: {strategy_params}, Risk Params: {risk_params}")

        try:
            # --- 1. Initialization ---
            if strategy_type not in AVAILABLE_STRATEGIES:
                logger.error(f"Strategy type '{strategy_type}' not found in AVAILABLE_STRATEGIES.")
                return None, None, None
            strategy_class: type[BaseStrategy] = AVAILABLE_STRATEGIES[strategy_type]

            if not tickers:
                logger.error("No tickers provided for the backtest.")
                return None, None, None

            # Initialize Strategy
            strategy_params = strategy_params or {}
            try:
                strategy = strategy_class(tickers=tickers, **strategy_params)
                logger.info(f"Initialized strategy '{strategy_type}' with params: {strategy_params}")
            except Exception as e:
                logger.error(f"Error initializing strategy '{strategy_type}' with params {strategy_params}: {e}")
                logger.error(traceback.format_exc())
                return None, None, None

            # Initialize Risk Manager
            use_risk_management = risk_params is not None
            try:
                risk_manager = RiskManager(**(risk_params or {})) # Pass params if available
                log_msg = f"Initialized RiskManager with {'custom' if use_risk_management else 'default'} parameters."
                if use_risk_management: log_msg += f" Params: {risk_params}"
                logger.info(log_msg)
            except Exception as e:
                logger.error(f"Error initializing RiskManager with params {risk_params}: {e}. Using default.")
                risk_manager = RiskManager()

            # Initialize Portfolio Manager
            portfolio_manager = PortfolioManager(initial_capital=self.initial_capital, risk_manager=risk_manager)
            logger.info("Initialized PortfolioManager.")


            # --- 2. Data Loading and Preparation ---
            all_ticker_data = self.data_loader.load_all_data()
            if not all_ticker_data:
                logger.error("Failed to load any ticker data.")
                return None, None, None

            # Filter data for selected tickers and prepare combined DataFrame
            valid_tickers = [t for t in tickers if t in all_ticker_data and not all_ticker_data[t].empty]
            if not valid_tickers:
                logger.error(f"None of the selected tickers {tickers} have valid data.")
                return None, None, None
            logger.info(f"Using data for {len(valid_tickers)} tickers: {', '.join(valid_tickers)}")

            # Combine data into a single multi-index DataFrame (Dates x Tickers)
            # We need Open, High, Low, Close, Volume for each ticker
            try:
                panel_data = {}
                required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                for ticker in valid_tickers:
                     df_ticker = all_ticker_data[ticker]
                     if all(col in df_ticker.columns for col in required_cols):
                         panel_data[ticker] = df_ticker[required_cols]
                     else:
                         logger.warning(f"Data for ticker {ticker} is missing required columns. Skipping.")

                if not panel_data:
                    logger.error("No valid data panels could be created for selected tickers.")
                    return None, None, None

                # Use pd.concat for creating MultiIndex DataFrame
                combined_df = pd.concat(panel_data, axis=1, keys=panel_data.keys())
                combined_df.index = pd.to_datetime(combined_df.index) # Ensure index is datetime
                combined_df = combined_df.sort_index() # Sort by date

                # Get the date range for the backtest loop
                start_date = pd.to_datetime(config.START_DATE)
                end_date = pd.to_datetime(config.END_DATE)
                backtest_range = combined_df.loc[start_date:end_date].index.unique()

                if backtest_range.empty:
                    logger.error(f"No data available within the specified date range: {start_date} to {end_date}")
                    return None, None, None

                logger.info(f"Combined data prepared. Shape: {combined_df.shape}. Date range: {backtest_range.min()} to {backtest_range.max()}")

            except Exception as e:
                logger.error(f"Error creating combined data panel: {e}")
                logger.error(traceback.format_exc())
                return None, None, None


            # --- 3. Signal Generation (Pre-computation) ---
            # Generate signals for all tickers *before* the main loop for efficiency
            all_signals = {}
            logger.info("Generating signals for all tickers...")
            for ticker in valid_tickers:
                try:
                    # Pass the full historical data for the ticker to generate signals
                    ticker_data_full = all_ticker_data[ticker]
                    signals_df = strategy.generate_signals(ticker, ticker_data_full)
                    if signals_df is not None and not signals_df.empty:
                         # Ensure signals index is datetime
                         signals_df.index = pd.to_datetime(signals_df.index)
                         all_signals[ticker] = signals_df
                         logger.debug(f"Generated {len(signals_df)} signal points for {ticker}")
                    else:
                         logger.info(f"No signals generated for {ticker}")
                except Exception as e:
                    logger.error(f"Error generating signals for {ticker}: {e}")
                    # Continue without signals for this ticker, or handle error differently

            logger.info(f"Signal generation complete for {len(all_signals)} tickers.")


            # --- 4. Backtest Execution Loop ---
            logger.info("Starting backtest simulation loop...")
            portfolio_history = [] # To store daily portfolio values

            # Optional: Market Regime Filter Data (e.g., SPY data)
            market_filter_data = None
            apply_market_filter = risk_manager.use_market_filter # Check if filter is enabled in RiskManager
            if apply_market_filter:
                 try:
                      spy_data = all_ticker_data.get(config.BENCHMARK_TICKER)
                      if spy_data is not None and not spy_data.empty:
                            market_filter_data = spy_data['Close'].rolling(window=risk_manager.market_trend_lookback).mean()
                            logger.info(f"Market filter data (MA {risk_manager.market_trend_lookback}) prepared.")
                      else:
                            logger.warning("Benchmark data for market filter not found. Disabling filter.")
                            apply_market_filter = False
                 except Exception as e:
                      logger.warning(f"Error preparing market filter data: {e}. Disabling filter.")
                      apply_market_filter = False


            for current_date in backtest_range:
                # Reset daily risk limits if applicable
                # risk_manager.reset_daily_tracking() # Reset daily PnL tracking if implemented

                # Get data for the current day
                try:
                    current_market_data = combined_df.loc[current_date]
                    if isinstance(current_market_data, pd.Series): # Handle case where only one ticker remains
                         current_market_data = current_market_data.to_frame().T # Convert Series to DataFrame
                         current_market_data.columns = combined_df.columns # Restore MultiIndex columns
                except KeyError:
                    logger.warning(f"No market data for date {current_date}. Skipping.")
                    # Update portfolio value with previous day's prices if needed, or carry forward
                    last_value = portfolio_history[-1]['value'] if portfolio_history else self.initial_capital
                    portfolio_history.append({'date': current_date, 'value': last_value})
                    continue

                # --- a) Check Portfolio-Level Risk Limits ---
                # Implement checks for max drawdown, daily loss etc. based on portfolio_history
                # if not risk_manager.check_portfolio_risk(portfolio_history): # Needs implementation
                #     logger.warning(f"Portfolio risk limit breached on {current_date}. Stopping trades.")
                #     # Decide how to handle breach (e.g., liquidate all, stop new trades)
                #     pass # Placeholder

                # --- b) Check Market Regime ---
                is_market_favorable = True # Assume favorable by default
                if apply_market_filter and market_filter_data is not None:
                     try:
                          current_spy_close = all_ticker_data[config.BENCHMARK_TICKER].loc[current_date, 'Close']
                          current_spy_ma = market_filter_data.loc[current_date]
                          is_market_favorable = current_spy_close >= current_spy_ma
                          #logger.debug(f"Market filter {current_date}: Favorable={is_market_favorable} (Close={current_spy_close:.2f}, MA={current_spy_ma:.2f})")
                     except KeyError:
                           #logger.debug(f"Market filter data not available for {current_date}. Assuming favorable.")
                           is_market_favorable = True # Default to favorable if data missing


                # --- c) Process Exits and Update Stops (based on current prices) ---
                current_prices = {ticker: current_market_data[(ticker, 'Close')] for ticker in valid_tickers if (ticker, 'Close') in current_market_data}
                if current_prices:
                     portfolio_manager.update_positions_and_stops(current_prices, current_date)


                # --- d) Generate and Process Entry Signals for the day ---
                # Only consider new entries if market is favorable (or filter disabled)
                if is_market_favorable:
                    for ticker in valid_tickers:
                        # Check if we have a signal for this ticker today
                        if ticker in all_signals:
                            try:
                                signal_row = all_signals[ticker].loc[current_date]
                                signal_value = signal_row['Signal'] # Assuming 'Signal' column exists
                                position_value = signal_row.get('Position', signal_value) # Use Position if exists
                            except KeyError:
                                signal_value = 0 # No signal for this date
                                position_value = 0

                            if signal_value != 0: # We have an entry/exit signal
                                #logger.debug(f"Signal for {ticker} on {current_date}: {signal_value}")
                                entry_price = current_market_data.get((ticker, 'Open'), current_market_data.get((ticker, 'Close'))) # Use Open if available, else Close
                                if pd.isna(entry_price): continue # Skip if price is NaN

                                if signal_value > 0: # Buy Signal
                                    if ticker not in portfolio_manager.positions: # Only if not already in position
                                        # Prepare signal dict for PortfolioManager
                                        signal_data = {
                                            'ticker': ticker,
                                            'date': current_date,
                                            'price': entry_price,
                                            'direction': 1,
                                            # Add volatility if needed by risk manager (calculate from historical data)
                                            'volatility': all_ticker_data[ticker]['Close'].pct_change().rolling(risk_manager.volatility_lookback).std().loc[current_date] if risk_manager.volatility_lookback > 0 else 0.02 # Default vol
                                            # Add sector if available/needed
                                            # 'sector': get_sector(ticker)
                                        }
                                        portfolio_manager.open_position(signal_data)

                                elif signal_value < 0: # Sell Signal (to close position)
                                     if ticker in portfolio_manager.positions:
                                         exit_price = entry_price # Assume exit at the same price for simplicity (can be improved)
                                         portfolio_manager.close_position(ticker, exit_price, current_date, reason="signal")


                # --- e) Update Portfolio Value for the day ---
                # Use closing prices for end-of-day valuation
                eod_prices = {ticker: current_market_data[(ticker, 'Close')] for ticker in valid_tickers if (ticker, 'Close') in current_market_data and pd.notna(current_market_data[(ticker, 'Close')])}
                current_portfolio_value = portfolio_manager.update_portfolio_value(eod_prices)
                portfolio_history.append({'date': current_date, 'value': current_portfolio_value})

            # --- End of Backtest Loop ---
            logger.info("Backtest simulation loop finished.")

            # Final step: Close any remaining open positions at the end date price
            final_date = backtest_range[-1]
            final_market_data = combined_df.loc[final_date]
            final_prices = {ticker: final_market_data[(ticker, 'Close')] for ticker in portfolio_manager.positions if (ticker, 'Close') in final_market_data and pd.notna(final_market_data[(ticker, 'Close')])}
            portfolio_manager.close_all_positions(final_prices, final_date, reason="end_of_backtest")


            # --- 5. Result Aggregation and Statistics ---
            # Create Portfolio Value Series
            portfolio_df = pd.DataFrame(portfolio_history).set_index('date')
            portfolio_value_series = portfolio_df['value']
            portfolio_value_series.name = "Portfolio"

            # Get Benchmark Data aligned to portfolio index
            benchmark_value_series = self._get_benchmark_data(portfolio_value_series.index)

            # Prepare combined results dictionary
            combined_results = {
                'Portfolio_Value': portfolio_value_series,
                'Benchmark': benchmark_value_series,
                'trades': portfolio_manager.closed_trades # Get closed trades from portfolio manager
            }

            # Calculate statistics
            stats = self._calculate_portfolio_stats(combined_results)

            logger.info(f"Backtest analysis complete. Final Portfolio Value: ${stats.get('Final Capital', 0):,.2f}, Total Trades: {stats.get('total_trades', 0)}")

            return all_signals, combined_results, stats

        except Exception as e:
            logger.error(f"CRITICAL error during backtest execution: {str(e)}")
            logger.error(traceback.format_exc())
            return None, None, None


    def _get_benchmark_data(self, target_index: pd.DatetimeIndex) -> Optional[pd.Series]:
        """
        Get benchmark data aligned with the target portfolio index, normalized to initial capital.
        """
        if target_index.empty:
            logger.warning("Cannot get benchmark data for empty target index.")
            return None

        try:
            benchmark_ticker = config.BENCHMARK_TICKER
            # Use DataLoader to get benchmark data
            benchmark_data_df = self.data_loader.get_ticker_data(benchmark_ticker)
            if benchmark_data_df is None: # Try loading specifically if not in cache
                 benchmark_data_df = self.data_loader.load_benchmark_data_df() # Need this method in DataLoader

            if benchmark_data_df is None or benchmark_data_df.empty:
                 logger.warning(f"Benchmark ticker '{benchmark_ticker}' data not found.")
                 return None

            benchmark_series = benchmark_data_df['Close']
            benchmark_series.index = pd.to_datetime(benchmark_series.index).tz_localize(None)
            benchmark_series = benchmark_series.sort_index()

            # Reindex benchmark to the target index (portfolio dates)
            aligned_benchmark = benchmark_series.reindex(target_index).ffill()

            # Fill initial NaNs with the first available benchmark value within the target range
            first_valid_target_idx = target_index.min()
            aligned_subset = aligned_benchmark[aligned_benchmark.index >= first_valid_target_idx]
            first_valid_bm_value = aligned_subset.bfill().iloc[0] if not aligned_subset.empty else None

            if pd.isna(first_valid_bm_value):
                 logger.warning(f"Could not find valid benchmark data within the target range {target_index.min()} - {target_index.max()}.")
                 return None

            aligned_benchmark = aligned_benchmark.bfill() # Fill any remaining NaNs forward first
            aligned_benchmark = aligned_benchmark.ffill() # Then fill backward

            if aligned_benchmark.isnull().any():
                 logger.warning("Benchmark data contains NaNs after alignment and filling.")
                 return None

            # Calculate buy-and-hold portfolio value for benchmark, starting from initial capital
            initial_benchmark_price = aligned_benchmark.iloc[0]
            if initial_benchmark_price <= 0:
                logger.warning(f"Initial benchmark price for {benchmark_ticker} is zero or negative.")
                return None

            shares = self.initial_capital / initial_benchmark_price
            benchmark_portfolio = aligned_benchmark * shares
            benchmark_portfolio.name = "Benchmark"

            logger.info(f"Benchmark data ({benchmark_ticker}) processed and aligned.")
            return benchmark_portfolio

        except Exception as e:
            logger.error(f"Error loading or processing benchmark data: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def _calculate_portfolio_stats(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate portfolio performance statistics."""
        portfolio_series = results.get('Portfolio_Value')
        benchmark_series = results.get('Benchmark') # Może być None
        trades = results.get('trades', [])

        if portfolio_series is None or portfolio_series.empty or len(portfolio_series) < 2:
            logger.warning("Cannot calculate stats, Portfolio_Value series is missing, empty, or too short.")
            # Zwróć podstawowe info, jeśli jest dostępne
            base_stats = {'Initial Capital': self.initial_capital, 'Final Capital': self.initial_capital, 'total_trades': len(trades)}
            base_stats.update(calculate_trade_statistics(trades)) # Dodaj statystyki transakcji (mogą być zerowe)
            return base_stats


        stats = {}
        stats['Initial Capital'] = self.initial_capital
        stats['Final Capital'] = portfolio_series.iloc[-1]
        stats['Total Return'] = ((stats['Final Capital'] / stats['Initial Capital']) - 1) * 100
        stats['CAGR'] = calculate_cagr(portfolio_series) * 100

        stats['Max Drawdown'] = calculate_max_drawdown(portfolio_series, method='percent') * 100
        returns_series = calculate_return_series(portfolio_series).dropna()

        if not returns_series.empty:
             risk_free_rate_annual = config.RISK_FREE_RATE
             stats['Annualized Volatility'] = calculate_annualized_volatility(returns_series) * 100
             stats['Sharpe Ratio'] = calculate_sharpe_ratio(portfolio_series, benchmark_rate=risk_free_rate_annual)
             stats['Sortino Ratio'] = calculate_sortino_ratio(portfolio_series, benchmark_rate=risk_free_rate_annual)

             if benchmark_series is not None and not benchmark_series.empty and len(benchmark_series) > 1:
                 # Ensure alignment (should be done in _get_benchmark_data, but double check)
                 common_index = portfolio_series.index.intersection(benchmark_series.index)
                 if len(common_index) > 1:
                     portfolio_aligned = portfolio_series[common_index]
                     benchmark_aligned = benchmark_series[common_index]
                     stats['Alpha'] = calculate_alpha(portfolio_aligned, benchmark_aligned, risk_free_rate=risk_free_rate_annual)
                     stats['Beta'] = calculate_beta(portfolio_aligned, benchmark_aligned)
                     stats['Information Ratio'] = calculate_information_ratio(portfolio_aligned, benchmark_aligned)
                 else:
                     logger.warning("Could not align benchmark for Alpha/Beta/InfoRatio calculation.")
                     stats['Alpha'], stats['Beta'], stats['Information Ratio'] = None, None, None
             else:
                 stats['Alpha'], stats['Beta'], stats['Information Ratio'] = None, None, None # Explicitly None
        else:
             stats['Annualized Volatility'] = 0.0
             stats['Sharpe Ratio'] = 0.0
             stats['Sortino Ratio'] = 0.0
             stats['Alpha'], stats['Beta'], stats['Information Ratio'] = None, None, None

        # Calculate trade statistics
        trade_stats = calculate_trade_statistics(trades)
        stats.update(trade_stats) # Merge trade stats

        # Calculate Recovery Factor (use absolute values)
        total_return_abs = abs(stats['Final Capital'] - stats['Initial Capital'])
        max_drawdown_value_abs = abs(stats['Max Drawdown']/100.0 * stats['Initial Capital']) # Przybliżona wartość $ drawdown
        # Poprawka: Max Drawdown jest w %, obliczmy wartość $ drawdown
        rolling_max = portfolio_series.cummax()
        drawdown_values = rolling_max - portfolio_series
        max_drawdown_dollar = drawdown_values.max()

        if max_drawdown_dollar > 0:
             stats['Recovery Factor'] = total_return_abs / max_drawdown_dollar
        else:
             stats['Recovery Factor'] = np.inf if total_return_abs > 0 else 0.0 # Inf if profit with no drawdown


        # Usuń klucze zaczynające się od '_' jeśli takie by były
        final_stats = {k: v for k, v in stats.items() if not k.startswith('_')}
        #logger.debug(f"Calculated portfolio stats: {final_stats}")
        logger.info("Portfolio statistics calculated.")

        return final_stats

    # Ta funkcja jest teraz zbędna, bo run_backtest obsługuje wszystkie parametry
    # def run_portfolio_backtest(self, strategy_type, tickers, risk_params=None, strategy_params=None):
    #     """Wrapper for run_backtest, maintaining previous interface if needed."""
    #     logger.warning("run_portfolio_backtest is deprecated, use run_backtest directly.")
    #     return self.run_backtest(strategy_type, tickers, strategy_params, risk_params)