import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple, Optional, List

class RiskManager:
    """
    Centralized risk management system for portfolio management.
    Handles position sizing, stops, and portfolio risk metrics.
    """
    def __init__(self, 
                 # Position limits
                 max_position_size: float = 0.2,     # Maximum allocation per position (20%)
                 min_position_size: float = 0.01,    # Minimum position size (1%)
                 max_open_positions: int = 5,        # Maximum number of concurrent positions
                 
                 # Stop management
                 stop_loss_pct: float = 0.02,        # Default stop loss percentage (2%)
                 profit_target_ratio: float = 2.0,   # Risk:Reward ratio (2:1)
                 trailing_stop_activation: float = 0.02,  # Activate trailing stop after 2% gain
                 trailing_stop_distance: float = 0.015,   # Trailing stop follows at 1.5%
                 
                 # Portfolio-level limits
                 max_drawdown: float = 0.20,         # Maximum portfolio drawdown allowed (20%)
                 max_daily_loss: float = 0.05,       # Maximum daily loss limit (5%)
                 max_sector_exposure: float = 0.40,  # Maximum exposure to a single sector (40%)
                 
                 # Volatility management
                 volatility_lookback: int = 20,      # Days to measure volatility
                 volatility_cap: float = 0.03,       # Cap on position size during high volatility
                 
                 # Market condition filters
                 use_market_filter: bool = True,     # Use market condition filter
                 market_trend_lookback: int = 100    # Days to determine market trend
                ):
        
        # Position limits
        self.max_position_size = max_position_size
        self.min_position_size = min_position_size
        self.max_open_positions = max_open_positions
        
        # Stop management
        self.stop_loss_pct = stop_loss_pct
        self.profit_target_ratio = profit_target_ratio
        self.trailing_stop_activation = trailing_stop_activation
        self.trailing_stop_distance = trailing_stop_distance
        
        # Portfolio-level limits
        self.max_drawdown = max_drawdown
        self.max_daily_loss = max_daily_loss
        self.max_sector_exposure = max_sector_exposure
        
        # Volatility management
        self.volatility_lookback = volatility_lookback
        self.volatility_cap = volatility_cap
        
        # Market condition filters
        self.use_market_filter = use_market_filter
        self.market_trend_lookback = market_trend_lookback
        
        # Runtime tracking
        self.sector_exposure = {}
        self.daily_pnl = 0.0
        self.highest_portfolio_value = 0.0
        
        # Add a logger
        self.logger = logging.getLogger(__name__)
        
    def calculate_position_size(self, capital: float, price: float, 
                                volatility: float, sector: Optional[str] = None) -> float:
        """
        Calculate optimal position size based on risk parameters.
        
        Args:
            capital: Current portfolio capital
            price: Entry price of the asset
            volatility: Measured volatility of the asset (std dev of returns)
            sector: Optional sector identifier for sector exposure management
            
        Returns:
            Optimal position size in shares
        """
        # Risk-based position sizing
        risk_amount = capital * self.stop_loss_pct
        
        # Adjust for volatility (higher volatility = smaller position)
        vol_factor = min(self.volatility_cap, volatility) / self.volatility_cap
        position_size_risk = risk_amount / (price * max(0.005, volatility))
        
        # Apply maximum position limit
        max_size = capital * self.max_position_size / price
        
        # Apply sector limit if provided
        if sector and sector in self.sector_exposure:
            sector_limit = (self.max_sector_exposure - self.sector_exposure.get(sector, 0)) * capital / price
            max_size = min(max_size, sector_limit)
        
        # Ensure minimum viable position size
        min_size = capital * self.min_position_size / price
        
        # Return the optimal position size
        return max(min_size, min(position_size_risk, max_size))
    
    def calculate_stops(self, entry_price: float, signal: int) -> Tuple[float, float]:
        """
        Calculate stop-loss and take-profit levels.
        
        Args:
            entry_price: Price at which position is entered
            signal: Direction of trade (positive for long, negative for short)
            
        Returns:
            Tuple of (stop_loss_price, take_profit_price)
        """
        direction = 1 if signal > 0 else -1
        stop_loss = entry_price * (1 - self.stop_loss_pct * direction)
        take_profit = entry_price * (1 + self.stop_loss_pct * self.profit_target_ratio * direction)
        return stop_loss, take_profit
    
    def update_trailing_stop(self, entry_price: float, current_price: float, 
                           current_stop: float, signal: int) -> float:
        """
        Update trailing stop level based on price movement.
        
        Args:
            entry_price: Original entry price
            current_price: Current market price
            current_stop: Current stop level
            signal: Direction of trade (positive for long, negative for short)
            
        Returns:
            Updated stop price
        """
        direction = 1 if signal > 0 else -1
        
        # Calculate profit percentage
        profit_pct = (current_price - entry_price) * direction / entry_price
        
        # Only trail if we've reached activation threshold
        if profit_pct > self.trailing_stop_activation:
            # Calculate new trailing stop
            ideal_stop = current_price * (1 - self.trailing_stop_distance * direction)
            
            # For long positions, raise stop if new stop is higher
            # For short positions, lower stop if new stop is lower
            if (direction > 0 and ideal_stop > current_stop) or \
               (direction < 0 and ideal_stop < current_stop):
                return ideal_stop
                
        return current_stop
    
    def check_risk_limits(self, portfolio_value: pd.Series, daily_change: float = 0) -> bool:
        """
        Check if portfolio is within risk limits.
        
        Args:
            portfolio_value: Series of portfolio values over time
            daily_change: Today's P&L in percentage terms
            
        Returns:
            True if within limits, False if limits exceeded
        """
        if len(portfolio_value) < 2:
            return True
            
        # Update highest portfolio value
        self.highest_portfolio_value = max(
            self.highest_portfolio_value, 
            portfolio_value.max()
        )
        
        # Calculate drawdown
        current_value = portfolio_value.iloc[-1]
        drawdown = (current_value - self.highest_portfolio_value) / self.highest_portfolio_value
        
        # Track daily P&L
        self.daily_pnl += daily_change
        
        # Check risk limit violations
        if abs(drawdown) > self.max_drawdown:
            return False
            
        if self.daily_pnl < -self.max_daily_loss:
            return False
            
        return True
    
    def update_sector_exposure(self, sector: str, exposure: float):
        """
        Update current sector exposure.
        
        Args:
            sector: Industry sector identifier
            exposure: Percentage of portfolio exposed to this sector (0-1)
        """
        self.sector_exposure[sector] = exposure
    
    def can_open_new_position(self, open_position_count: int) -> bool:
        """
        Check if we can open a new position based on portfolio limits.
        
        Args:
            open_position_count: Current number of open positions
            
        Returns:
            True if a new position can be opened, False otherwise
        """
        return open_position_count < self.max_open_positions
    
    def check_market_condition(self, market_data: pd.DataFrame) -> bool:
        """
        Check if overall market conditions are favorable for trading.
        
        Args:
            market_data: DataFrame with market index data
            
        Returns:
            True if market conditions are good for trading
        """
        if not self.use_market_filter or len(market_data) < self.market_trend_lookback:
            return True
            
        # Simple trend detection - above 100-day moving average
        market_data['MA'] = market_data['Close'].rolling(window=self.market_trend_lookback).mean()
        market_trend = market_data['Close'].iloc[-1] > market_data['MA'].iloc[-1]
        
        return market_trend
    
    def reset_daily_tracking(self):
        """Reset daily tracking metrics (call at start of each trading day)"""
        self.daily_pnl = 0.0
