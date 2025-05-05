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
    Class for validating trading strategies.
    Verifies the correctness of strategy implementation and compliance with the base interface.
    """
    
    def __init__(self):
        """
        Initializes the strategy validator.
        """
        self.sample_data = None
        logger.info("Strategy validator initialized")
    
    def generate_sample_data(self, days: int = 252, volatility: float = 0.015) -> pd.DataFrame:
        """
        Generates synthetic OHLCV data for strategy testing.
        
        Args:
            days: Number of historical data days
            volatility: Daily price volatility
            
        Returns:
            DataFrame with synthetic OHLCV data
        """
        # Generate start date (one year back)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Generate list of trading days (only weekdays)
        dates = []
        curr_date = start_date
        while curr_date <= end_date:
            # Only days from Monday (0) to Friday (4)
            if curr_date.weekday() < 5:
                dates.append(curr_date)
            curr_date += timedelta(days=1)
        
        # Generate random price changes as Brownian motion
        np.random.seed(42)  # For test repeatability
        returns = np.random.normal(0, volatility, len(dates))
        
        # Start with price 100 and generate remaining prices
        close_prices = 100 * np.cumprod(1 + returns)
        
        # Generate other OHLCV columns
        high_prices = close_prices * np.exp(np.random.normal(0, volatility/2, len(dates)))
        low_prices = close_prices * np.exp(np.random.normal(0, -volatility/2, len(dates)))
        # Ensure high >= close >= low
        high_prices = np.maximum(high_prices, close_prices)
        low_prices = np.minimum(low_prices, close_prices)
        
        # Open between low and high
        open_prices = low_prices + (high_prices - low_prices) * np.random.random(len(dates))
        
        # Random volumes - random variable from log-normal distribution
        volumes = np.exp(np.random.normal(10, 1, len(dates)))
        
        # Create DataFrame
        df = pd.DataFrame({
            'Open': open_prices,
            'High': high_prices,
            'Low': low_prices,
            'Close': close_prices,
            'Volume': volumes
        }, index=dates)
        
        # Save generated data
        self.sample_data = df
        
        logger.info(f"Generated synthetic OHLCV data with {len(df)} trading days")
        return df
    
    def validate_strategy_interface(self, strategy_class: Type[BaseStrategy]) -> Dict[str, Any]:
        """
        Validates the interface of the strategy class.
        
        Args:
            strategy_class: The strategy class to validate
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "name": strategy_class.__name__,
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check if the class inherits from BaseStrategy
        if not issubclass(strategy_class, BaseStrategy):
            results["is_valid"] = False
            results["errors"].append(f"Class {strategy_class.__name__} does not inherit from BaseStrategy")
            return results
        
        # Check required methods
        required_methods = ["generate_signals", "get_strategy_params"]
        
        for method_name in required_methods:
            if not hasattr(strategy_class, method_name):
                results["is_valid"] = False
                results["errors"].append(f"Missing required method {method_name}")
            else:
                # Check method signatures
                if method_name == "generate_signals":
                    method = getattr(strategy_class, method_name)
                    sig = inspect.signature(method)
                    if len(sig.parameters) != 3:  # self, ticker, data
                        results["is_valid"] = False
                        results["errors"].append(
                            f"Incorrect signature for method {method_name}. " +
                            f"Expected: (self, ticker: str, data: pd.DataFrame)"
                        )
                elif method_name == "get_strategy_params":
                    method = getattr(strategy_class, method_name)
                    sig = inspect.signature(method)
                    if len(sig.parameters) != 1:  # self
                        results["warnings"].append(
                            f"Unusual signature for method {method_name}. " +
                            f"Expected: (self) -> Dict[str, Any]"
                        )
        
        # Check constructor
        init_method = strategy_class.__init__
        sig = inspect.signature(init_method)
        if "tickers" not in sig.parameters:
            results["warnings"].append(
                "Constructor should accept a 'tickers' parameter"
            )
        
        return results
    
    def validate_strategy_implementation(self, 
                                         strategy: BaseStrategy, 
                                         sample_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Validates the strategy implementation by checking if it correctly generates signals.
        
        Args:
            strategy: Strategy instance to validate
            sample_data: Optional data for testing
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "name": strategy.__class__.__name__,
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Use provided data or generate new data
        if sample_data is None:
            if self.sample_data is None:
                sample_data = self.generate_sample_data()
            else:
                sample_data = self.sample_data
        
        # Test ticker
        ticker = "TEST"
        
        try:
            # Attempt to generate signals
            signals_df = strategy.generate_signals(ticker, sample_data)
            
            # Check if DataFrame was returned
            if not isinstance(signals_df, pd.DataFrame):
                results["is_valid"] = False
                results["errors"].append(
                    f"Method generate_signals returns {type(signals_df)} instead of pd.DataFrame"
                )
                return results
            
            # Check if signals are empty
            if signals_df.empty and not sample_data.empty:
                results["warnings"].append(
                    "Method generate_signals returns an empty DataFrame, even though input data is not empty"
                )
            
            # Check for 'Signal' column presence
            if 'Signal' not in signals_df.columns:
                results["is_valid"] = False
                results["errors"].append(
                    "Missing 'Signal' column in the output data from generate_signals"
                )
            else:
                # Check signal types
                unique_signals = signals_df['Signal'].unique()
                non_standard_signals = [s for s in unique_signals if s not in [-1, 0, 1]]
                if non_standard_signals:
                    results["warnings"].append(
                        f"Non-standard signal values: {non_standard_signals}. " +
                        f"Expected values: -1 (sell), 0 (hold), 1 (buy)"
                    )
            
            # Check get_strategy_params method
            try:
                params = strategy.get_strategy_params()
                if not isinstance(params, dict):
                    results["warnings"].append(
                        f"Method get_strategy_params returns {type(params)} instead of Dict[str, Any]"
                    )
            except Exception as e:
                results["warnings"].append(
                    f"Error calling get_strategy_params: {str(e)}"
                )
            
        except Exception as e:
            results["is_valid"] = False
            results["errors"].append(f"Error executing generate_signals: {str(e)}")
        
        return results
    
    def validate_strategy_signals(self, 
                                  strategy: BaseStrategy,
                                  ticker: str,
                                  data: pd.DataFrame) -> Dict[str, Any]:
        """
        Validates signals generated by the strategy for real data.
        
        Args:
            strategy: Strategy instance to validate
            ticker: Ticker symbol for the data
            data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with signal analysis
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
            # Generate signals
            signals_df = strategy.generate_signals(ticker, data)
            
            if signals_df.empty:
                results["warnings"].append("Strategy did not generate any signals")
                results["signals_summary"] = {
                    "total": 0,
                    "buy": 0,
                    "sell": 0,
                    "signal_ratio": 0
                }
                return results
            
            if 'Signal' not in signals_df.columns:
                results["is_valid"] = False
                results["errors"].append("Missing 'Signal' column in the generated data")
                return results
            
            # Signal analysis
            buy_signals = (signals_df['Signal'] > 0).sum()
            sell_signals = (signals_df['Signal'] < 0).sum()
            total_signals = buy_signals + sell_signals
            total_bars = len(signals_df)
            
            # Ratio of signals to the number of periods
            signal_ratio = total_signals / total_bars if total_bars > 0 else 0
            
            results["signals_summary"] = {
                "total": int(total_signals),
                "buy": int(buy_signals),
                "sell": int(sell_signals),
                "signal_ratio": round(signal_ratio, 4)
            }
            
            # Check signal density
            if signal_ratio > 0.3:
                results["warnings"].append(
                    f"High signal density: {round(signal_ratio * 100, 2)}% of periods contain signals. " +
                    "This might lead to excessive trading."
                )
            elif signal_ratio < 0.01 and total_bars >= 100:
                results["warnings"].append(
                    f"Very low signal density: only {round(signal_ratio * 100, 2)}% of periods contain signals. " +
                    "This might lead to too few trades."
                )
            
            # Check signal distribution
            if buy_signals > 0 and sell_signals == 0:
                results["warnings"].append(
                    "Strategy generates only buy signals, with no sell signals."
                )
            elif sell_signals > 0 and buy_signals == 0:
                results["warnings"].append(
                    "Strategy generates only sell signals, with no buy signals."
                )
            
            # Check for gaps in signal data
            max_gap = 0
            current_gap = 0
            for signal in signals_df['Signal']:
                if signal == 0:
                    current_gap += 1
                else:
                    max_gap = max(max_gap, current_gap)
                    current_gap = 0
            
            max_gap = max(max_gap, current_gap)  # For the case where the trailing sequence of zeros is the longest
            
            results["signals_summary"]["max_days_without_signal"] = int(max_gap)
            
            if max_gap > 100 and signal_ratio > 0:
                results["warnings"].append(
                    f"Detected a long gap ({max_gap} days) without any signals. " +
                    "This might indicate issues with the strategy logic."
                )
            
            # Check for signal redundancy (buy signals after buy signals without sell signals in between)
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
                    f"Detected redundant signals: {redundant_buys} redundant buys, " +
                    f"{redundant_sells} redundant sells. This might affect backtest results."
                )
            
        except Exception as e:
            results["is_valid"] = False
            results["errors"].append(f"Error during signal validation: {str(e)}")
        
        return results
    
    def run_quick_test(self, strategy_class: Type[BaseStrategy], ticker: str = "TEST") -> Dict[str, Any]:
        """
        Performs a quick test of the strategy using synthetic data.
        
        Args:
            strategy_class: The strategy class to test
            ticker: Ticker symbol for tests
            
        Returns:
            Dictionary with test results
        """
        # Generate test data if it doesn't exist yet
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
        
        # Validate interface
        interface_results = self.validate_strategy_interface(strategy_class)
        results["interface_valid"] = interface_results["is_valid"]
        results["interface_details"] = interface_results
        
        if not interface_results["is_valid"]:
            results["overall_status"] = "FAIL"
            logger.error(f"Strategy interface validation failed: {interface_results['errors']}")
            return results
        
        # Create strategy instance
        try:
            strategy = strategy_class(tickers=[ticker])
        except Exception as e:
            results["implementation_valid"] = False
            results["implementation_details"] = {
                "name": strategy_class.__name__,
                "is_valid": False,
                "errors": [f"Error creating strategy instance: {str(e)}"],
                "warnings": []
            }
            results["overall_status"] = "FAIL"
            logger.error(f"Strategy instantiation failed: {str(e)}")
            return results
        
        # Validate implementation
        implementation_results = self.validate_strategy_implementation(strategy, sample_data)
        results["implementation_valid"] = implementation_results["is_valid"]
        results["implementation_details"] = implementation_results
        
        if not implementation_results["is_valid"]:
            results["overall_status"] = "FAIL"
            logger.error(f"Strategy implementation validation failed: {implementation_results['errors']}")
            return results
        
        # Validate signals
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
        Performs a detailed analysis of the strategy on real data.
        
        Args:
            strategy: Strategy instance to analyze
            ticker: Ticker symbol
            data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with analysis results
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
        
        # Validate signals
        validation_results = self.validate_strategy_signals(strategy, ticker, data)
        results["validation_results"] = validation_results
        
        # Generate signals for further analysis
        try:
            signals_df = strategy.generate_signals(ticker, data)
            
            if signals_df.empty or 'Signal' not in signals_df.columns:
                logger.warning(f"No valid signals generated for {ticker}")
                return results
            
            # Analyze signal occurrence over time
            buy_dates = signals_df[signals_df['Signal'] > 0].index
            sell_dates = signals_df[signals_df['Signal'] < 0].index
            
            # Calculate average time between signals
            if len(buy_dates) > 1:
                avg_days_between_buys = (buy_dates[-1] - buy_dates[0]).days / (len(buy_dates) - 1) if len(buy_dates) > 1 else float('nan')
            else:
                avg_days_between_buys = float('nan')
                
            if len(sell_dates) > 1:
                avg_days_between_sells = (sell_dates[-1] - sell_dates[0]).days / (len(sell_dates) - 1) if len(sell_dates) > 1 else float('nan')
            else:
                avg_days_between_sells = float('nan')
            
            # Simulate a simple buy-hold-sell strategy (without considering position size, costs, etc.)
            buy_hold_sell_returns = []
            current_position = None
            entry_price = None
            
            for idx, row in signals_df.iterrows():
                signal = row['Signal']
                price = row['Close'] # Assuming Close price for simplicity
                
                if signal > 0 and current_position is None:  # Buy signal, no position
                    current_position = 'long'
                    entry_price = price
                elif signal < 0 and current_position == 'long':  # Sell signal, have position
                    if entry_price is not None:
                        returns_pct = (price - entry_price) / entry_price * 100
                        buy_hold_sell_returns.append(returns_pct)
                    current_position = None
                    entry_price = None
            
            # Signal statistics
            results["signal_statistics"] = {
                "buy_signals": len(buy_dates),
                "sell_signals": len(sell_dates),
                "avg_days_between_buys": round(avg_days_between_buys, 2) if not pd.isna(avg_days_between_buys) else None,
                "avg_days_between_sells": round(avg_days_between_sells, 2) if not pd.isna(avg_days_between_sells) else None,
                # Example: Signal-to-noise ratio (buy signals / total bars)
                "signal_to_noise_ratio": round(len(buy_dates) / len(data) if len(data) > 0 else 0, 4) 
            }
            
            # Basic performance metrics
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