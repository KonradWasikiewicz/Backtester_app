import numpy as np
import pandas as pd
from typing import Dict, Any, Callable, List, Union, Optional, Tuple
import logging

# Użyj loggera zdefiniowanego w app.py lub globalnie
logger = logging.getLogger(__name__)

# Importuj stałe, np. liczbę dni handlowych
try:
    from src.core.config import config # Użyj globalnego obiektu config
    TRADING_DAYS_PER_YEAR = config.TRADING_DAYS_PER_YEAR
except ImportError:
    logger.warning("Could not import config for metrics. Using default TRADING_DAYS_PER_YEAR=252.")
    TRADING_DAYS_PER_YEAR = 252


# --- Helper Functions ---

def _get_trading_periods_per_year(series_index: pd.DatetimeIndex) -> float:
    """Estimates trading periods per year based on data frequency."""
    if not isinstance(series_index, pd.DatetimeIndex) or len(series_index) < 2:
        return TRADING_DAYS_PER_YEAR # Return default if index is invalid

    # Detect frequency if possible
    freq = pd.infer_freq(series_index)
    if freq:
        if 'D' in freq or 'B' in freq: # Daily or Business Day
             return TRADING_DAYS_PER_YEAR
        elif 'W' in freq: # Weekly
            return 52
        elif 'M' in freq: # Monthly
            return 12
        elif 'Q' in freq: # Quarterly
             return 4
        elif 'A' in freq or 'Y' in freq: # Annual / Yearly
             return 1
        # Add more frequencies if needed (hourly, minutely etc.)

    # If frequency cannot be inferred, estimate based on time span
    time_span_years = (series_index.max() - series_index.min()).days / 365.25
    if time_span_years > 0:
        return len(series_index) / time_span_years
    else:
        return TRADING_DAYS_PER_YEAR # Fallback to daily if span is too short


def _handle_input_series(series: Optional[pd.Series], min_length: int = 2) -> Optional[pd.Series]:
    """Validates and cleans an input pandas Series for metric calculations."""
    if series is None or not isinstance(series, pd.Series) or series.empty:
        # logger.debug("Input series is None, not a Series, or empty.")
        return None
    if len(series) < min_length:
        # logger.debug(f"Input series has length {len(series)}, less than minimum {min_length}.")
        return None
    # Ensure numeric type and handle NaNs
    try:
        numeric_series = pd.to_numeric(series, errors='coerce')
        # Forward fill first to carry last valid observation, then backfill start
        cleaned_series = numeric_series.ffill().bfill()
        if cleaned_series.isnull().any(): # Still has NaNs after filling
             # logger.warning("Input series contains NaN values that could not be filled.")
             return None # Or handle differently, e.g., dropna()
        return cleaned_series
    except Exception as e:
        logger.error(f"Error cleaning input series: {e}")
        return None


# --- Return Calculation Functions ---

def calculate_return_series(series: pd.Series) -> Optional[pd.Series]:
    """Calculates the simple return series (price / prev_price - 1)."""
    cleaned_series = _handle_input_series(series, min_length=2)
    if cleaned_series is None: return None
    return cleaned_series.pct_change() # More direct way to calculate simple returns


def calculate_log_return_series(series: pd.Series) -> Optional[pd.Series]:
    """Calculates the log return series (ln(price / prev_price))."""
    cleaned_series = _handle_input_series(series, min_length=2)
    if cleaned_series is None: return None
    # Avoid log(0) or log(<0) errors
    if (cleaned_series <= 0).any():
        logger.warning("Series contains non-positive values, cannot calculate log returns accurately.")
        # Return simple returns instead or handle differently
        return calculate_return_series(series)
    return np.log(cleaned_series / cleaned_series.shift(1))


def calculate_cumulative_returns(return_series: pd.Series) -> Optional[pd.Series]:
    """Calculates cumulative returns from a series of simple returns."""
    cleaned_returns = _handle_input_series(return_series, min_length=1) # Need at least 1 return
    if cleaned_returns is None: return None
    # Drop first NaN if it exists (from pct_change)
    cleaned_returns = cleaned_returns.iloc[1:] if pd.isna(cleaned_returns.iloc[0]) else cleaned_returns
    if cleaned_returns.empty: return None
    cumulative = (1 + cleaned_returns).cumprod() - 1
    return cumulative


def calculate_total_return(series: pd.Series) -> Optional[float]:
    """Calculates the total percentage return over the series."""
    cleaned_series = _handle_input_series(series, min_length=2)
    if cleaned_series is None: return None
    if cleaned_series.iloc[0] == 0: return None # Avoid division by zero

    return (cleaned_series.iloc[-1] / cleaned_series.iloc[0] - 1)


# --- Annualized Metrics ---

def calculate_cagr(series: pd.Series) -> Optional[float]:
    """Calculates Compound Annual Growth Rate (CAGR)."""
    cleaned_series = _handle_input_series(series, min_length=2)
    if cleaned_series is None: return None

    start_value = cleaned_series.iloc[0]
    end_value = cleaned_series.iloc[-1]

    if start_value <= 0:
        logger.warning("CAGR calculation failed: Start value is non-positive.")
        return None # Cannot calculate CAGR if start value is zero or negative

    if not isinstance(cleaned_series.index, pd.DatetimeIndex):
         logger.warning("CAGR calculation failed: Series index is not DatetimeIndex.")
         return None

    time_span_years = (cleaned_series.index[-1] - cleaned_series.index[0]).days / 365.25

    if time_span_years <= 0:
        logger.warning(f"CAGR calculation failed: Time span is non-positive ({time_span_years:.2f} years).")
        return None # Return None for non-positive time span

    value_factor = end_value / start_value
    # Handle potential negative returns correctly
    if value_factor < 0:
         # CAGR is undefined for negative terminal value relative to start
         # We can return geometric mean - 1, but need to handle negative values carefully.
         # For simplicity, return None or log an error.
         logger.warning("CAGR calculation might be misleading: Negative value factor.")
         # Approximate using average annual return or return None
         # return None
         # Or return the raw calculation, user should be aware
         return (np.sign(value_factor) * (abs(value_factor)**(1/time_span_years))) - 1
    else:
        return (value_factor**(1 / time_span_years)) - 1


def calculate_annualized_volatility(return_series: pd.Series) -> Optional[float]:
    """Calculates the annualized volatility (standard deviation of returns)."""
    cleaned_returns = _handle_input_series(return_series, min_length=2)
    if cleaned_returns is None: return None

    # Drop first NaN if it exists (from pct_change)
    if pd.isna(cleaned_returns.iloc[0]):
        cleaned_returns = cleaned_returns.iloc[1:]
    if len(cleaned_returns) < 2: return None # Need at least 2 returns for std dev

    if not isinstance(cleaned_returns.index, pd.DatetimeIndex):
        logger.warning("Cannot annualize volatility: Return series index is not DatetimeIndex.")
        return None

    periods_per_year = _get_trading_periods_per_year(cleaned_returns.index)
    if periods_per_year <= 0:
        logger.warning("Could not determine valid periods per year for volatility annualization.")
        return None

    volatility = cleaned_returns.std()
    annualized_volatility = volatility * np.sqrt(periods_per_year)
    return annualized_volatility


# --- Risk-Adjusted Return Metrics ---

def calculate_sharpe_ratio(price_series: pd.Series, risk_free_rate: float = 0.0) -> Optional[float]:
    """Calculates the annualized Sharpe ratio."""
    cagr = calculate_cagr(price_series) # Returns None on error
    if cagr is None: return None

    return_series = calculate_return_series(price_series) # Returns None on error
    if return_series is None: return None

    volatility = calculate_annualized_volatility(return_series) # Returns None on error
    if volatility is None or volatility == 0:
        # Handle zero volatility case (e.g., flat returns)
        return 0.0 if cagr == risk_free_rate else (np.inf if cagr > risk_free_rate else -np.inf)

    return (cagr - risk_free_rate) / volatility


def calculate_sortino_ratio(price_series: pd.Series, risk_free_rate: float = 0.0) -> Optional[float]:
    """Calculates the annualized Sortino ratio."""
    cagr = calculate_cagr(price_series)
    if cagr is None: return None

    return_series = calculate_return_series(price_series)
    if return_series is None: return None

    # Drop first NaN if it exists
    if pd.isna(return_series.iloc[0]):
        return_series = return_series.iloc[1:]
    if len(return_series) < 2: return None

    if not isinstance(return_series.index, pd.DatetimeIndex):
        logger.warning("Cannot calculate Sortino Ratio: Return series index is not DatetimeIndex.")
        return None

    periods_per_year = _get_trading_periods_per_year(return_series.index)
    if periods_per_year <= 0: return None

    # Adjust risk-free rate to the period frequency
    periodic_rf_rate = (1 + risk_free_rate)**(1 / periods_per_year) - 1

    # Calculate downside returns relative to the periodic risk-free rate
    downside_returns = return_series[return_series < periodic_rf_rate]

    if downside_returns.empty:
        # No returns below the target rate, Sortino is theoretically infinite if CAGR > RF
        return np.inf if cagr > risk_free_rate else 0.0

    # Calculate downside deviation
    downside_deviation_periodic = np.sqrt((downside_returns - periodic_rf_rate).pow(2).sum() / len(return_series))
    annualized_downside_deviation = downside_deviation_periodic * np.sqrt(periods_per_year)

    if annualized_downside_deviation == 0:
        return np.inf if cagr > risk_free_rate else 0.0

    return (cagr - risk_free_rate) / annualized_downside_deviation


# --- Drawdown Metrics ---

def calculate_drawdown_series(series: pd.Series) -> Optional[pd.Series]:
    """Calculates the percentage drawdown series from peak equity."""
    cleaned_series = _handle_input_series(series, min_length=1)
    if cleaned_series is None: return None

    rolling_max = cleaned_series.cummax()
    # Avoid division by zero if rolling_max is zero
    rolling_max = rolling_max.replace(0, np.nan) # Replace 0 with NaN to avoid division issues
    drawdown = (cleaned_series - rolling_max) / rolling_max
    return drawdown.fillna(0) # Fill NaNs (e.g., at the start or where rolling_max was 0) with 0 drawdown


def calculate_max_drawdown(series: pd.Series) -> Optional[float]:
    """Calculates the maximum percentage drawdown."""
    drawdown_series = calculate_drawdown_series(series)
    if drawdown_series is None: return None
    # Max drawdown is the minimum value of the drawdown series (most negative)
    return drawdown_series.min()


def calculate_recovery_factor(total_return_pct: Optional[float], max_drawdown_pct: Optional[float]) -> Optional[float]:
    """Calculates the recovery factor (Total Return / Max Drawdown)."""
    if total_return_pct is None or max_drawdown_pct is None:
        return None
    if max_drawdown_pct == 0:
        # If no drawdown, factor is infinite if returns are positive, 0 otherwise
        return np.inf if total_return_pct > 0 else 0.0

    # Use absolute values for calculation
    return abs(total_return_pct) / abs(max_drawdown_pct)


# --- Benchmark Relative Metrics ---

def _align_series(series1: pd.Series, series2: pd.Series) -> Tuple[Optional[pd.Series], Optional[pd.Series]]:
    """Aligns two time series based on their common index."""
    if series1 is None or series2 is None: return None, None
    common_index = series1.index.intersection(series2.index)
    if len(common_index) < 2: # Need at least two common points for cov/var
        logger.warning("Could not align series or insufficient common data points.")
        return None, None
    return series1.loc[common_index], series2.loc[common_index]


def calculate_beta(portfolio_price_series: pd.Series, benchmark_price_series: pd.Series) -> Optional[float]:
    """Calculates the portfolio Beta relative to a benchmark."""
    portfolio_returns = calculate_return_series(portfolio_price_series)
    benchmark_returns = calculate_return_series(benchmark_price_series)

    if portfolio_returns is None or benchmark_returns is None: return None

    # Align return series
    portfolio_aligned, benchmark_aligned = _align_series(portfolio_returns.iloc[1:], benchmark_returns.iloc[1:]) # Skip first NaN

    if portfolio_aligned is None or benchmark_aligned is None or len(portfolio_aligned) < 2:
        return None

    # Calculate covariance and benchmark variance
    # Use numpy for potentially better NaN handling if needed, but pandas should be fine
    matrix = np.cov(portfolio_aligned, benchmark_aligned)
    covariance = matrix[0, 1]
    benchmark_variance = matrix[1, 1] # np.var(benchmark_aligned) gives biased estimator

    if benchmark_variance == 0:
        logger.warning("Benchmark variance is zero, cannot calculate Beta.")
        return None # Or return 0 or 1 depending on desired behavior

    beta = covariance / benchmark_variance
    return beta


def calculate_alpha(portfolio_price_series: pd.Series, benchmark_price_series: pd.Series,
                      risk_free_rate: float = 0.0) -> Optional[float]:
    """Calculates the annualized Jensen's Alpha."""
    cagr_portfolio = calculate_cagr(portfolio_price_series)
    cagr_benchmark = calculate_cagr(benchmark_price_series)
    beta = calculate_beta(portfolio_price_series, benchmark_price_series)

    if any(v is None for v in [cagr_portfolio, cagr_benchmark, beta]):
        logger.warning("Cannot calculate Alpha due to missing required metrics (CAGR portfolio/benchmark or Beta).")
        return None

    # Jensen's Alpha formula: Alpha = Portfolio Return - [Risk-Free Rate + Beta * (Benchmark Return - Risk-Free Rate)]
    alpha = cagr_portfolio - (risk_free_rate + beta * (cagr_benchmark - risk_free_rate))
    return alpha


def calculate_information_ratio(portfolio_price_series: pd.Series, benchmark_price_series: pd.Series) -> Optional[float]:
    """Calculates the Information Ratio."""
    portfolio_returns = calculate_return_series(portfolio_price_series)
    benchmark_returns = calculate_return_series(benchmark_price_series)

    if portfolio_returns is None or benchmark_returns is None: return None

    portfolio_aligned, benchmark_aligned = _align_series(portfolio_returns.iloc[1:], benchmark_returns.iloc[1:])

    if portfolio_aligned is None or benchmark_aligned is None or len(portfolio_aligned) < 2:
        return None

    # Calculate excess returns over benchmark (active returns)
    active_returns = portfolio_aligned - benchmark_aligned

    if len(active_returns) < 2: return None

    # Calculate annualized active return
    periods_per_year = _get_trading_periods_per_year(active_returns.index)
    if periods_per_year <= 0: return None
    annualized_active_return = active_returns.mean() * periods_per_year

    # Calculate tracking error (annualized standard deviation of active returns)
    tracking_error = active_returns.std() * np.sqrt(periods_per_year)

    if tracking_error == 0:
        logger.warning("Tracking error is zero, Information Ratio is undefined or infinite.")
        # Return Inf if positive active return, -Inf if negative, 0 if zero
        return np.inf if annualized_active_return > 0 else (-np.inf if annualized_active_return < 0 else 0.0)

    return annualized_active_return / tracking_error


# --- Trade Analysis Metrics ---

def calculate_trade_statistics(trades: List[Dict]) -> Dict[str, Any]:
    """
    Calculates various statistics based on a list of completed trades.

    Args:
        trades (List[Dict]): A list where each dict represents a trade and must contain
                             at least 'pnl' (float) and optionally 'pnl_pct' (float).

    Returns:
        Dict[str, Any]: A dictionary containing trade statistics.
    """
    stats = {
        'total_trades': 0, 'winning_trades': 0, 'losing_trades': 0,
        'win_rate': 0.0, 'profit_factor': 0.0,
        'total_pnl': 0.0, 'avg_trade_pnl': 0.0,
        'avg_win_pnl': 0.0, 'avg_loss_pnl': 0.0,
        'largest_win_pnl': 0.0, 'largest_loss_pnl': 0.0,
        # Add more stats if needed (e.g., avg duration, avg pnl_pct)
    }

    if not trades:
        return stats # Return defaults if no trades

    pnls = []
    win_pnls = []
    loss_pnls = []

    logger.debug(f"Calculating trade stats for {len(trades)} trades.") # DEBUG
    trade_count_processed = 0 # DEBUG

    for trade in trades:
        pnl = trade.get('pnl')
        if trade_count_processed < 5: # Log first 5 PnLs # DEBUG
            logger.debug(f"Processing trade {trade_count_processed + 1}, PnL: {pnl}") # DEBUG

        if pnl is None or not isinstance(pnl, (int, float)) or np.isnan(pnl):
            logger.warning(f"Skipping trade due to invalid PnL: {trade}")
            trade_count_processed += 1 # DEBUG
            continue

        pnls.append(pnl)
        if pnl > 0:
            win_pnls.append(pnl)
        elif pnl < 0:
            loss_pnls.append(pnl)
        # Trades with PnL == 0 are counted in total but not in win/loss counts here
        trade_count_processed += 1 # DEBUG

    total_trades = len(pnls)
    winning_trades = len(win_pnls)
    losing_trades = len(loss_pnls)

    # DEBUG: Log intermediate values
    logger.debug(f"Trade stats intermediate: total={total_trades}, wins={winning_trades}, losses={losing_trades}")

    if total_trades == 0: 
        logger.debug("No valid trades found for statistics.") # DEBUG
        return stats # No valid PnLs found

    stats['total_trades'] = total_trades
    stats['winning_trades'] = winning_trades
    stats['losing_trades'] = losing_trades
    stats['win_rate'] = (winning_trades / total_trades) * 100 if total_trades > 0 else 0.0

    gross_profit = sum(win_pnls)
    gross_loss = abs(sum(loss_pnls)) # Use absolute value for gross loss

    # DEBUG: Log profit/loss values
    logger.debug(f"Trade stats intermediate: gross_profit={gross_profit:.2f}, gross_loss={gross_loss:.2f}")

    stats['total_pnl'] = gross_profit - gross_loss # Same as sum(pnls)
    stats['avg_trade_pnl'] = stats['total_pnl'] / total_trades

    # Return None if gross_loss is 0, as infinity might cause issues downstream/in UI
    stats['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else None 

    stats['avg_win_pnl'] = gross_profit / winning_trades if winning_trades > 0 else 0.0
    stats['avg_loss_pnl'] = -gross_loss / losing_trades if losing_trades > 0 else 0.0 # Avg loss is negative

    stats['largest_win_pnl'] = max(win_pnls) if winning_trades > 0 else 0.0
    stats['largest_loss_pnl'] = min(loss_pnls) if losing_trades > 0 else 0.0 # Largest loss is most negative

    logger.debug(f"Calculated trade stats: {stats}") # DEBUG

    return stats