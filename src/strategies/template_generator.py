"""
Strategy Template Generator

This module provides tools for generating template code for new trading strategies.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class StrategyTemplateGenerator:
    """
    Generates boilerplate code for new trading strategies to ensure consistency
    and adherence to the BaseStrategy interface.
    """
    
    def __init__(self):
        """
        Initialize the template generator
        """
        logger.info("Strategy template generator initialized")
    
    def generate_strategy_template(self, 
                                  strategy_name: str, 
                                  strategy_type: str = "basic", 
                                  description: str = "",
                                  parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a template for a new strategy class.
        
        Args:
            strategy_name: Name of the strategy (will be used for class name)
            strategy_type: Type of strategy template to generate (basic, indicator, ml, etc.)
            description: Description of what the strategy does
            parameters: Dictionary of strategy parameters with default values
            
        Returns:
            String containing the generated code
        """
        # Ensure strategy name is valid Python class name
        if not strategy_name[0].isalpha():
            strategy_name = "Strategy" + strategy_name
        
        # Convert to CamelCase if needed
        if "_" in strategy_name:
            parts = strategy_name.split("_")
            strategy_name = "".join(part.capitalize() for part in parts)
        else:
            strategy_name = strategy_name[0].upper() + strategy_name[1:]
            
        # If "strategy" is not in the name, append it
        if "Strategy" not in strategy_name:
            strategy_name += "Strategy"
            
        # Default parameters if none provided
        if parameters is None:
            if strategy_type == "moving_average":
                parameters = {
                    "short_window": 20,
                    "long_window": 50,
                    "signal_type": "crossover" 
                }
            elif strategy_type == "rsi":
                parameters = {
                    "rsi_period": 14,
                    "overbought_threshold": 70,
                    "oversold_threshold": 30
                }
            elif strategy_type == "bollinger":
                parameters = {
                    "window": 20,
                    "num_std_dev": 2.0
                }
            else:  # basic
                parameters = {
                    "param1": 10,
                    "param2": 20
                }
                
        # Get current date for the header
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Generate header comment
        header = f'''"""
{strategy_name}

{description if description else "A trading strategy based on " + strategy_type}

Created: {today}
"""'''

        # Generate imports
        imports = '''
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import logging

from src.strategies.base import BaseStrategy

# Set up logging
logger = logging.getLogger(__name__)
'''

        # Generate class definition and constructor
        class_def = f'''
class {strategy_name}(BaseStrategy):
    """
    {description if description else "A trading strategy implementation based on " + strategy_type}
    
    This strategy inherits from the BaseStrategy abstract base class and implements
    the required methods for signal generation.
    """
    
    def __init__(self, tickers: List[str], **params):
        """
        Initialize the {strategy_name}.
        
        Args:
            tickers: List of ticker symbols this strategy will operate on
            **params: Strategy-specific parameters
        """
        # Initialize the parent class
        super().__init__(tickers)
        
        # Initialize strategy parameters with defaults'''
        
        # Generate parameter initialization
        params_init = "\n"
        for param_name, default_value in parameters.items():
            if isinstance(default_value, str):
                params_init += f"        self.{param_name} = params.get('{param_name}', '{default_value}')\n"
            else:
                params_init += f"        self.{param_name} = params.get('{param_name}', {default_value})\n"
        
        # Generate get_strategy_params method
        params_method = '''
    def get_strategy_params(self) -> Dict[str, Any]:
        """
        Get the current strategy parameters.
        
        Returns:
            Dictionary of parameter names and values
        """
        return {'''
        
        for param_name in parameters.keys():
            params_method += f"\n            '{param_name}': self.{param_name},"
        
        params_method += '''
        }
'''
        
        # Generate different implementations based on strategy type
        if strategy_type == "moving_average":
            implementation = self._generate_ma_strategy()
        elif strategy_type == "rsi":
            implementation = self._generate_rsi_strategy()
        elif strategy_type == "bollinger":
            implementation = self._generate_bollinger_strategy()
        else:  # basic
            implementation = self._generate_basic_strategy()
        
        # Combine all parts
        template = (
            header + 
            imports + 
            class_def + 
            params_init + 
            params_method + 
            implementation
        )
        
        return template
    
    def _generate_basic_strategy(self) -> str:
        """Generate a basic strategy implementation"""
        return '''
    def generate_signals(self, ticker: str, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Generate trading signals for the given ticker based on historical data.
        
        Args:
            ticker: Ticker symbol
            data: DataFrame with historical OHLCV data
        
        Returns:
            DataFrame with signals and other calculated values, or None if signals
            could not be generated
        """
        if data is None or data.empty:
            logger.warning(f"No data provided for {ticker}")
            return None
            
        try:
            # Create a copy of the data to avoid modifying the original
            signals = data.copy()
            
            # Add a Signal column initialized to 0 (no signal)
            signals['Signal'] = 0
            
            # TODO: Add your signal generation logic here
            # Example:
            # signals.loc[signals['Close'] > signals['Open'], 'Signal'] = 1  # Buy when close > open
            # signals.loc[signals['Close'] < signals['Open'], 'Signal'] = -1  # Sell when close < open
            
            logger.info(f"Generated signals for {ticker}: {len(signals[signals['Signal'] != 0])} signals")
            return signals
            
        except Exception as e:
            logger.error(f"Error generating signals for {ticker}: {str(e)}")
            return None
'''
    
    def _generate_ma_strategy(self) -> str:
        """Generate a moving average crossover strategy implementation"""
        return '''
    def generate_signals(self, ticker: str, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Generate trading signals based on moving average crossover.
        
        Args:
            ticker: Ticker symbol
            data: DataFrame with historical OHLCV data
        
        Returns:
            DataFrame with signals and calculated moving averages
        """
        if data is None or data.empty:
            logger.warning(f"No data provided for {ticker}")
            return None
            
        if len(data) < self.long_window:
            logger.warning(f"Not enough data for {ticker} to calculate indicators. " +
                          f"Need at least {self.long_window} data points.")
            return None
            
        try:
            # Create a copy of the data
            signals = data.copy()
            
            # Calculate moving averages
            signals[f'SMA{self.short_window}'] = signals['Close'].rolling(window=self.short_window).mean()
            signals[f'SMA{self.long_window}'] = signals['Close'].rolling(window=self.long_window).mean()
            
            # Initialize signal column
            signals['Signal'] = 0
            
            # Generate signals based on crossover
            if self.signal_type == 'crossover':
                # Create a 'Position' column indicating a long position when short MA > long MA
                signals['Position'] = np.where(signals[f'SMA{self.short_window}'] > 
                                              signals[f'SMA{self.long_window}'], 1, -1)
                
                # Generate signals on position change
                signals['Signal'] = signals['Position'].diff()
                
            elif self.signal_type == 'above_below':
                # Generate buy signals when short MA crosses above long MA
                signals.loc[signals[f'SMA{self.short_window}'] > signals[f'SMA{self.long_window}'], 'Signal'] = 1
                
                # Generate sell signals when short MA crosses below long MA
                signals.loc[signals[f'SMA{self.short_window}'] <= signals[f'SMA{self.long_window}'], 'Signal'] = -1
                
            # Clean up NaN values
            signals.dropna(inplace=True)
            
            # Log summary
            buy_signals = (signals['Signal'] > 0).sum()
            sell_signals = (signals['Signal'] < 0).sum()
            logger.info(f"Generated signals for {ticker}: {buy_signals} buy, {sell_signals} sell signals")
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating signals for {ticker}: {str(e)}")
            return None
'''
    
    def _generate_rsi_strategy(self) -> str:
        """Generate an RSI-based strategy implementation"""
        return '''
    def generate_signals(self, ticker: str, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Generate trading signals based on RSI indicator.
        
        Args:
            ticker: Ticker symbol
            data: DataFrame with historical OHLCV data
        
        Returns:
            DataFrame with signals and calculated RSI values
        """
        if data is None or data.empty:
            logger.warning(f"No data provided for {ticker}")
            return None
            
        if len(data) < self.rsi_period * 2:
            logger.warning(f"Not enough data for {ticker} to calculate RSI. " +
                          f"Need at least {self.rsi_period * 2} data points.")
            return None
            
        try:
            # Create a copy of the data
            signals = data.copy()
            
            # Calculate price changes
            delta = signals['Close'].diff()
            
            # Separate gains and losses
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            # Calculate average gain and loss over the RSI period
            avg_gain = gain.rolling(window=self.rsi_period).mean()
            avg_loss = loss.rolling(window=self.rsi_period).mean()
            
            # Calculate RS and RSI
            rs = avg_gain / avg_loss
            signals['RSI'] = 100 - (100 / (1 + rs))
            
            # Initialize signal column
            signals['Signal'] = 0
            
            # Generate buy signals when RSI crosses below oversold threshold
            signals.loc[signals['RSI'] < self.oversold_threshold, 'Signal'] = 1
            
            # Generate sell signals when RSI crosses above overbought threshold
            signals.loc[signals['RSI'] > self.overbought_threshold, 'Signal'] = -1
            
            # Clean up NaN values
            signals.dropna(inplace=True)
            
            # Log summary
            buy_signals = (signals['Signal'] > 0).sum()
            sell_signals = (signals['Signal'] < 0).sum()
            logger.info(f"Generated signals for {ticker}: {buy_signals} buy, {sell_signals} sell signals")
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating signals for {ticker}: {str(e)}")
            return None
'''
    
    def _generate_bollinger_strategy(self) -> str:
        """Generate a Bollinger Bands strategy implementation"""
        return '''
    def generate_signals(self, ticker: str, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Generate trading signals based on Bollinger Bands.
        
        Args:
            ticker: Ticker symbol
            data: DataFrame with historical OHLCV data
        
        Returns:
            DataFrame with signals and calculated Bollinger Band values
        """
        if data is None or data.empty:
            logger.warning(f"No data provided for {ticker}")
            return None
            
        if len(data) < self.window:
            logger.warning(f"Not enough data for {ticker} to calculate Bollinger Bands. " +
                          f"Need at least {self.window} data points.")
            return None
            
        try:
            # Create a copy of the data
            signals = data.copy()
            
            # Calculate rolling mean and standard deviation
            signals['SMA'] = signals['Close'].rolling(window=self.window).mean()
            signals['STD'] = signals['Close'].rolling(window=self.window).std()
            
            # Calculate Bollinger Bands
            signals['Upper_Band'] = signals['SMA'] + (signals['STD'] * self.num_std_dev)
            signals['Lower_Band'] = signals['SMA'] - (signals['STD'] * self.num_std_dev)
            
            # Calculate Bandwidth and %B
            signals['Bandwidth'] = (signals['Upper_Band'] - signals['Lower_Band']) / signals['SMA']
            signals['%B'] = (signals['Close'] - signals['Lower_Band']) / (signals['Upper_Band'] - signals['Lower_Band'])
            
            # Initialize signal column
            signals['Signal'] = 0
            
            # Generate buy signals when price crosses below lower band
            signals.loc[signals['Close'] < signals['Lower_Band'], 'Signal'] = 1
            
            # Generate sell signals when price crosses above upper band
            signals.loc[signals['Close'] > signals['Upper_Band'], 'Signal'] = -1
            
            # Clean up NaN values
            signals.dropna(inplace=True)
            
            # Log summary
            buy_signals = (signals['Signal'] > 0).sum()
            sell_signals = (signals['Signal'] < 0).sum()
            logger.info(f"Generated signals for {ticker}: {buy_signals} buy, {sell_signals} sell signals")
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating signals for {ticker}: {str(e)}")
            return None
'''
    
    def create_strategy_file(self, 
                           strategy_name: str, 
                           output_dir: str, 
                           strategy_type: str = "basic", 
                           description: str = "",
                           parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate and save a new strategy file.
        
        Args:
            strategy_name: Name of the strategy (will be used for class name)
            output_dir: Directory to save the file in
            strategy_type: Type of strategy template to generate
            description: Description of what the strategy does
            parameters: Dictionary of strategy parameters with default values
            
        Returns:
            Path to the created file
        """
        # Generate the template code
        template = self.generate_strategy_template(
            strategy_name=strategy_name,
            strategy_type=strategy_type,
            description=description,
            parameters=parameters
        )
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert strategy name to snake case for filename
        if "Strategy" in strategy_name:
            filename = strategy_name.replace("Strategy", "")
        else:
            filename = strategy_name
            
        # Convert camel case to snake case
        filename = ''.join(['_'+c.lower() if c.isupper() else c for c in filename]).lstrip('_')
        
        # Ensure .py extension
        if not filename.endswith('.py'):
            filename += '.py'
            
        # Full path to output file
        file_path = os.path.join(output_dir, filename)
        
        # Write the template to the file
        with open(file_path, 'w') as f:
            f.write(template)
            
        logger.info(f"Created new strategy file: {file_path}")
        return file_path