import pandas as pd
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)

class BaseStrategy:
    """
    Base class for all trading strategies.
    
    This class defines the interface that all strategy implementations should follow.
    Specific strategies should inherit from this class and override its methods.
    """
    
    def __init__(self):
        """Initialize the strategy.""" # Removed parameters argument
        # No parameters needed for the base class itself
        logger.info(f"BaseStrategy initialized for {self.__class__.__name__}")
        
    def get_parameters(self) -> dict:
        """
        Returns the current parameters of the strategy.
        
        Returns:
            dict: A dictionary of strategy parameters
        """
        return self.parameters
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on the input data.
        
        Args:
            data (pd.DataFrame): Historical price data with at least 'Close' prices
            
        Returns:
            pd.DataFrame: DataFrame with 'signal' and 'positions' columns
            
        Raises:
            NotImplementedError: If the child class doesn't implement this method
        """
        raise NotImplementedError("Subclasses must implement the generate_signals method")