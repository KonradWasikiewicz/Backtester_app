class BacktestError(Exception):
    """Base exception for backtesting errors"""
    pass

class DataError(BacktestError):
    """Raised when there are issues with input data"""
    pass

class StrategyError(BacktestError):
    """Raised when there are issues with strategy execution"""
    pass

class ValidationError(BacktestError):
    """Raised when validation fails"""
    pass