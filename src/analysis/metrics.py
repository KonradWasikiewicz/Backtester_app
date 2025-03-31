import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from typing import Dict, Any, Callable, List, Union, Optional, Tuple

def calculate_return_series(series: pd.Series) -> pd.Series:
    """
    Calculates the return series of a given time series.

    >>> data = load_eod_data('VBB')
    >>> close_series = data['close']
    >>> return_series = return_series(close_series)

    The first value will always be NaN.
    """

    shifted_series = series.shift(1, axis=0)
    return series / shifted_series - 1


def calculate_log_return_series(series: pd.Series) -> pd.Series:
    """
    Same as calculate_return_series but with log returns
    """
    shifted_series = series.shift(1, axis=0)
    return pd.Series(np.log(series / shifted_series))


def calculate_percent_return(series: pd.Series) -> float:
    """
    Takes the first and last value in a series to determine the percent return, 
    assuming the series is in date-ascending order
    """
    return series.iloc[-1] / series.iloc[0] - 1


def get_years_past(series: pd.Series) -> float:
    """
    Calculate the years past according to the index of the series for use with
    functions that require annualization   
    """
    start_date = series.index[0]
    end_date = series.index[-1]
    return (end_date - start_date).days / 365.25


def handle_nan_series(series: pd.Series) -> pd.Series:
    """Clean series by removing NaN values and ensuring float type"""
    return pd.Series(series, dtype=float).ffill().bfill()

def calculate_cagr(series: pd.Series) -> float:
    """Calculate compounded annual growth rate with better error handling"""
    try:
        series = handle_nan_series(series)
        if len(series) < 2:
            return 0.0
        
        start_price = series.iloc[0]
        end_price = series.iloc[-1]
        
        if start_price <= 0 or end_price <= 0:
            return 0.0
            
        value_factor = end_price / start_price
        year_past = get_years_past(series)
        
        if year_past <= 0:
            return 0.0
            
        return (value_factor ** (1 / year_past)) - 1
    except Exception:
        return 0.0


def calculate_annualized_volatility(return_series: pd.Series) -> float:
    """Calculate annualized volatility with error handling"""
    try:
        if len(return_series) < 2:
            return 0.0
            
        years_past = get_years_past(return_series)
        if years_past <= 0:
            return 0.0
            
        entries_per_year = return_series.shape[0] / years_past
        std = return_series.std()
        
        if pd.isna(std) or std == 0:
            return 0.0
            
        return std * np.sqrt(entries_per_year)
    except Exception:
        return 0.0


def calculate_sharpe_ratio(price_series: pd.Series, 
    benchmark_rate: float=0) -> float:
    """Calculates the Sharpe ratio with NaN handling"""
    try:
        price_series = handle_nan_series(price_series)
        if len(price_series) < 2:
            return 0.0
        cagr = calculate_cagr(price_series)
        return_series = calculate_return_series(price_series)
        volatility = calculate_annualized_volatility(return_series)
        return (cagr - benchmark_rate) / volatility if volatility != 0 else 0.0
    except Exception:
        return 0.0


def calculate_rolling_sharpe_ratio(price_series: pd.Series,
    n: float=20) -> pd.Series:
    """
    Compute an approximation of the Sharpe ratio on a rolling basis. 
    Intended for use as a preference value.
    """
    rolling_return_series = calculate_return_series(price_series).rolling(n)
    return rolling_return_series.mean() / rolling_return_series.std()


def calculate_annualized_downside_deviation(return_series: pd.Series,
    benchmark_rate: float=0) -> float:
    """
    Calculates the downside deviation for use in the Sortino ratio.

    Benchmark rate is assumed to be annualized. It will be adjusted according
    to the number of periods per year seen in the data.
    """

    # For both de-annualizing the benchmark rate and annualizing result
    years_past = get_years_past(return_series)
    entries_per_year = return_series.shape[0] / years_past

    adjusted_benchmark_rate = ((1+benchmark_rate) ** (1/entries_per_year)) - 1

    downside_series = adjusted_benchmark_rate - return_series
    downside_sum_of_squares = (downside_series[downside_series > 0] ** 2).sum()
    denominator = return_series.shape[0] - 1
    downside_deviation = np.sqrt(downside_sum_of_squares / denominator)

    return downside_deviation * np.sqrt(entries_per_year)


def calculate_sortino_ratio(price_series: pd.Series,
    benchmark_rate: float=0) -> float:
    """Calculates the Sortino ratio with NaN handling"""
    try:
        price_series = handle_nan_series(price_series)
        if len(price_series) < 2:
            return 0.0
        cagr = calculate_cagr(price_series)
        return_series = calculate_return_series(price_series)
        downside_deviation = calculate_annualized_downside_deviation(return_series)
        return (cagr - benchmark_rate) / downside_deviation if downside_deviation != 0 else 0.0
    except Exception:
        return 0.0


def calculate_pure_profit_score(price_series: pd.Series) -> float:
    """Calculates the pure profit score with NaN handling"""
    try:
        series = handle_nan_series(price_series)
        if len(series) < 2:
            return 0.0
            
        cagr = calculate_cagr(series)
        t = np.arange(0, len(series)).reshape(-1, 1)
        values = series.values.reshape(-1, 1)
        
        regression = LinearRegression().fit(t, values)
        r_squared = regression.score(t, values)
        
        return cagr * r_squared
    except Exception:
        return 0.0

def calculate_jensens_alpha(return_series: pd.Series, 
    benchmark_return_series: pd.Series) -> float: 
    """
    Calculates Jensen's alpha. Prefers input series have the same index. Handles
    NAs.
    """

    # Join series along date index and purge NAs
    df = pd.concat([return_series, benchmark_return_series], sort=True, axis=1)
    df = df.dropna()

    # Get the appropriate data structure for scikit learn
    clean_returns: pd.Series = df[df.columns.values[0]]
    clean_benchmarks = pd.DataFrame(df[df.columns.values[1]])

    # Fit a linear regression and return the alpha
    regression = LinearRegression().fit(clean_benchmarks, y=clean_returns)
    return regression.intercept_

def calculate_jensens_alpha_with_benchmark(return_series: pd.Series, benchmark_data: pd.Series) -> float: 
    """
    Calculates Jensen's alpha using provided benchmark data
    """
    benchmark_return_series = calculate_log_return_series(benchmark_data)
    return calculate_jensens_alpha(return_series, benchmark_return_series)
    

DRAWDOWN_EVALUATORS: Dict[str, Callable] = {
    'dollar': lambda price, peak: peak - price,
    'percent': lambda price, peak: -((price / peak) - 1),
    'log': lambda price, peak: np.log(peak) - np.log(price),
}

def calculate_drawdown_series(series: pd.Series, method: str='log') -> pd.Series:
    """
    Returns the drawdown series
    """
    assert method in DRAWDOWN_EVALUATORS, \
        f'Method "{method}" must by one of {list(DRAWDOWN_EVALUATORS.keys())}'

    evaluator = DRAWDOWN_EVALUATORS[method]
    return evaluator(series, series.cummax())

def calculate_max_drawdown(series: pd.Series, method: str='log') -> float:
    """
    Simply returns the max drawdown as a float
    """
    return calculate_drawdown_series(series, method).max()

def calculate_max_drawdown_with_metadata(series: pd.Series, 
    method: str='log') -> Dict[str, Any]:
    """
    Calculates max_drawndown and stores metadata about when and where. Returns 
    a dictionary of the form 
        {
            'max_drawdown': float,
            'peak_date': pd.Timestamp,
            'peak_price': float,
            'trough_date': pd.Timestamp,
            'trough_price': float,
        }
    """

    assert method in DRAWDOWN_EVALUATORS, \
        f'Method "{method}" must by one of {list(DRAWDOWN_EVALUATORS.keys())}'

    evaluator = DRAWDOWN_EVALUATORS[method]

    max_drawdown = 0
    local_peak_date = peak_date = trough_date = series.index[0]
    local_peak_price = peak_price = trough_price = series.iloc[0]

    for date, price in series.iteritems():

        # Keep track of the rolling max
        if price > local_peak_price:
            local_peak_date = date
            local_peak_price = price

        # Compute the drawdown
        drawdown = evaluator(price, local_peak_price)

        # Store new max drawdown values
        if drawdown > max_drawdown:
            max_drawdown = drawdown

            peak_date = local_peak_date
            peak_price = local_peak_price

            trough_date = date
            trough_price = price

    return {
        'max_drawdown': max_drawdown,
        'peak_date': peak_date,
        'peak_price': peak_price,
        'trough_date': trough_date,
        'trough_price': trough_price
    }

def calculate_log_max_drawdown_ratio(series: pd.Series) -> float:
    log_drawdown = calculate_max_drawdown(series, method='log')
    log_return = np.log(series.iloc[-1]) - np.log(series.iloc[0])
    return log_return - log_drawdown

def calculate_calmar_ratio(series: pd.Series, years_past: int=3) -> float:
    """
    Return the percent max drawdown ratio over the past three years, otherwise 
    known as the Calmar Ratio
    """

    # Filter series on past three years
    last_date = series.index[-1]
    three_years_ago = last_date - pd.Timedelta(days=years_past*365.25)
    series = series[series.index > three_years_ago]

    # Compute annualized percent max drawdown ratio
    percent_drawdown = calculate_max_drawdown(series, method='percent')
    cagr = calculate_cagr(series)
    return cagr / percent_drawdown

def calculate_alpha(portfolio_values: pd.Series, benchmark_values: Optional[pd.Series], risk_free_rate: float = 0.02) -> float:
    """Calculate portfolio alpha (Jensen's Alpha) relative to benchmark"""
    if benchmark_values is None or len(portfolio_values) < 2 or len(benchmark_values) < 2:
        return 0
        
    portfolio_returns = portfolio_values.pct_change().dropna()
    benchmark_returns = benchmark_values.pct_change().dropna()
    
    # Align dates
    common_dates = portfolio_returns.index.intersection(benchmark_returns.index)
    if len(common_dates) < 2:
        return 0
        
    portfolio_returns = portfolio_returns[common_dates]
    benchmark_returns = benchmark_returns[common_dates]
    
    # Calculate beta first
    beta = calculate_beta(portfolio_values, benchmark_values)
    
    # Calculate alpha
    portfolio_return = portfolio_returns.mean() * 252  # Annualized
    benchmark_return = benchmark_returns.mean() * 252  # Annualized
    alpha = portfolio_return - risk_free_rate - beta * (benchmark_return - risk_free_rate)
    
    return alpha * 100  # Convert to percentage

def calculate_beta(portfolio_values: pd.Series, benchmark_values: Optional[pd.Series]) -> float:
    """Calculate portfolio beta (volatility relative to benchmark)"""
    if benchmark_values is None or len(portfolio_values) < 2 or len(benchmark_values) < 2:
        return 1
        
    portfolio_returns = portfolio_values.pct_change().dropna()
    benchmark_returns = benchmark_values.pct_change().dropna()
    
    # Align dates
    common_dates = portfolio_returns.index.intersection(benchmark_returns.index)
    if len(common_dates) < 2:
        return 1
        
    portfolio_returns = portfolio_returns[common_dates]
    benchmark_returns = benchmark_returns[common_dates]
    
    # Calculate beta
    covariance = portfolio_returns.cov(benchmark_returns)
    variance = benchmark_returns.var()
    
    return covariance / variance if variance != 0 else 1

def calculate_information_ratio(portfolio_values: pd.Series, benchmark_values: Optional[pd.Series]) -> float:
    """Calculate information ratio (active return per unit of tracking error)"""
    if benchmark_values is None or len(portfolio_values) < 2 or len(benchmark_values) < 2:
        return 0
        
    portfolio_returns = portfolio_values.pct_change().dropna()
    benchmark_returns = benchmark_values.pct_change().dropna()
    
    # Align dates
    common_dates = portfolio_returns.index.intersection(benchmark_returns.index)
    if len(common_dates) < 2:
        return 0
        
    portfolio_returns = portfolio_returns[common_dates]
    benchmark_returns = benchmark_returns[common_dates]
    
    # Calculate tracking error
    excess_returns = portfolio_returns - benchmark_returns
    tracking_error = excess_returns.std() * np.sqrt(252)  # Annualized
    
    # Calculate information ratio
    active_return = (portfolio_returns.mean() - benchmark_returns.mean()) * 252  # Annualized
    
    return active_return / tracking_error if tracking_error != 0 else 0

def calculate_recovery_factor(total_return: float, max_drawdown: float) -> float:
    """Calculate recovery factor (total return divided by max drawdown)"""
    if max_drawdown == 0:
        return 0
    return abs(total_return) / abs(max_drawdown)

def calculate_trade_statistics(trades: List[Dict]) -> Dict:
    """Calculate detailed trade statistics with comprehensive error handling"""
    if not trades:
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'avg_return': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'avg_pnl': 0,
            'avg_win_pnl': 0,
            'avg_loss_pnl': 0,
            'largest_win': 0,
            'largest_loss': 0,
            'profit_factor': 0
        }
    
    # Calculate individual trade returns with error handling
    returns = []
    pnls = []
    
    for trade in trades:
        try:
            # Ensure we have valid numeric values
            entry_price = float(trade['entry_price'])
            exit_price = float(trade['exit_price'])
            pnl = float(trade['pnl'])
            
            # Only calculate return if entry price is not zero
            if entry_price > 0:
                returns.append((exit_price - entry_price) / entry_price * 100)
            pnls.append(pnl)
        except (KeyError, ValueError, TypeError, ZeroDivisionError) as e:
            print(f"Error processing trade: {e}")
            continue
    
    # Handle empty lists case
    if not returns or not pnls:
        return {
            'total_trades': len(trades),
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'avg_return': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'avg_pnl': 0,
            'avg_win_pnl': 0,
            'avg_loss_pnl': 0,
            'largest_win': 0,
            'largest_loss': 0,
            'profit_factor': 0
        }
    
    # Split into wins and losses
    wins = [r for r in returns if r > 0]
    losses = [r for r in returns if r <= 0]
    win_pnls = [p for p in pnls if p > 0]
    loss_pnls = [p for p in pnls if p <= 0]
    
    # Calculate statistics with safe operations
    stats = {
        'total_trades': len(trades),
        'winning_trades': len(wins),
        'losing_trades': len(losses),
        'win_rate': (len(wins) / len(trades) * 100) if trades else 0,
        'avg_return': sum(returns) / len(returns) if returns else 0,
        'avg_win': sum(wins) / len(wins) if wins else 0,
        'avg_loss': sum(losses) / len(losses) if losses else 0,
        'avg_pnl': sum(pnls) / len(pnls) if pnls else 0,
        'avg_win_pnl': sum(win_pnls) / len(win_pnls) if win_pnls else 0,
        'avg_loss_pnl': sum(loss_pnls) / len(loss_pnls) if loss_pnls else 0,
        'largest_win': max(win_pnls) if win_pnls else 0,
        'largest_loss': min(loss_pnls) if loss_pnls else 0,
        'profit_factor': abs(sum(win_pnls) / sum(loss_pnls)) if loss_pnls and sum(loss_pnls) != 0 else 1.0
    }
    
    return stats

def get_trade_bins_dynamic(returns: List[float]) -> Tuple[List[int], List[float], List[float]]:
    """Calculate dynamic histogram bins based on trade return distribution"""
    if not returns:
        return list(range(-50, 55, 5)), [], []
    
    min_ret = min(returns)
    max_ret = max(returns)
    
    # Base bin size of 5%
    bin_size = 5
    
    # Handle outliers
    lower_bound = max(min_ret, -50)  # Cap at -50%
    upper_bound = min(max_ret, 50)   # Cap at 50%
    
    # Create main bins
    bins = list(range(int(lower_bound - (lower_bound % bin_size)), 
                     int(upper_bound + bin_size + (bin_size - upper_bound % bin_size)), 
                     bin_size))
    
    # Add outlier bins if needed
    outliers_low = [r for r in returns if r < lower_bound]
    outliers_high = [r for r in returns if r > upper_bound]
    
    return bins, outliers_low, outliers_high


