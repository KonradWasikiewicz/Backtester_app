import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple, Optional, List

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Risk Manager class that handles all risk-related calculations and checks.
    
    This class is responsible for:
    1. Position sizing based on risk and portfolio parameters
    2. Risk checks on individual positions and overall portfolio
    3. Stop loss and take profit calculations
    """
    
    def __init__(self, config=None):
        """
        Initialize risk manager with configuration parameters.
        
        Args:
            config (dict, optional): Configuration parameters dictionary
        """
        # Set default values
        self.max_position_size = 0.20  # 20% of portfolio max per position
        self.min_position_size = 0.01  # 1% of portfolio min per position
        self.risk_per_trade = 0.01  # 1% of portfolio at risk per trade
        self.max_portfolio_risk = 0.05  # 5% maximum overall portfolio risk
        self.max_drawdown = 0.25  # 25% maximum drawdown
        self.max_correlated_positions = 0.30  # 30% maximum in correlated assets
        # Additional configuration defaults
        self.max_open_positions = float('inf')  # unlimited until configured
        self.stop_loss_pct = 0.0  # fraction of price for stop loss
        self.profit_target_ratio = 1.0  # risk:reward ratio for take profit
        
        # Feature flags for risk management
        self._apply_risk_rules = False  # Only apply risk rules when checkbox is checked
        self._use_position_sizing = True
        self._use_risk_per_trade = True
        self._use_max_drawdown = False
        self._use_max_correlated = False
        # Flags for stop loss, take profit, trailing stop
        self._use_stop_loss: bool = False
        self._use_take_profit: bool = False
        self._use_trailing_stop: bool = False
        
        # Load config if provided
        if config:
            self._load_config(config)
    
    def _load_config(self, config):
        """Load configuration parameters from dictionary"""
        if not config:
            return
            
        # Load risk parameters if they exist in config
        self.max_position_size = config.get('max_position_size', self.max_position_size)
        self.min_position_size = config.get('min_position_size', self.min_position_size)
        self.risk_per_trade = config.get('risk_per_trade', self.risk_per_trade)
        self.max_portfolio_risk = config.get('max_portfolio_risk', self.max_portfolio_risk)
        self.max_drawdown = config.get('max_drawdown', self.max_drawdown)
        self.max_correlated_positions = config.get('max_correlated_positions', 
                                                self.max_correlated_positions)
        
        # Load feature flags if they exist
        self._apply_risk_rules = config.get('apply_risk_rules', self._apply_risk_rules)
        self._use_position_sizing = config.get('use_position_sizing', self._use_position_sizing)
        self._use_risk_per_trade = config.get('use_risk_per_trade', self._use_risk_per_trade)
        self._use_max_drawdown = config.get('use_max_drawdown', self._use_max_drawdown)
        self._use_max_correlated = config.get('use_max_correlated', self._use_max_correlated)
        # Load additional settings
        self.max_open_positions = config.get('max_open_positions', self.max_open_positions)
        self.stop_loss_pct = config.get('stop_loss_pct', self.stop_loss_pct)
        self.profit_target_ratio = config.get('profit_target_ratio', self.profit_target_ratio)
        # Load feature flags for SL, TP, trailing
        self._use_stop_loss = config.get('use_stop_loss', self._use_stop_loss)
        self._use_take_profit = config.get('use_take_profit', self._use_take_profit)
        self._use_trailing_stop = config.get('use_trailing_stop', self._use_trailing_stop)

    def set_apply_risk_rules(self, apply_rules):
        """
        Set whether risk rules should be applied
        
        Args:
            apply_rules (bool): Whether to apply risk rules
        """
        self._apply_risk_rules = bool(apply_rules)
        
    def is_applying_risk_rules(self):
        """
        Check if risk rules are being applied
        
        Returns:
            bool: True if risk rules are being applied
        """
        return self._apply_risk_rules

    def calculate_position_size(self, current_portfolio_value: float, available_cash: float, price: float, volatility: Optional[float] = None) -> int:
        """
        Calculate the number of shares to trade based on portfolio value, cash,
        price, and optional volatility. When position sizing is disabled, allocate
        equally across max_open_positions. Otherwise use max_position_size rule.
        """
        if price <= 0:
            return 0
        # Disabled position sizing: allocate all available cash
        if not self._use_position_sizing:
            shares = int(available_cash // price)
            return max(shares, 0)
        # Use max_position_size fraction of portfolio
        max_units = int((current_portfolio_value * self.max_position_size) // price)
        if max_units <= 0:
            return 0
        # Optional risk-per-trade sizing if enabled and volatility provided
        if self._apply_risk_rules and self._use_risk_per_trade and volatility and volatility > 0:
            risk_amount = current_portfolio_value * self.risk_per_trade
            price_risk = price * volatility
            if price_risk > 0:
                risk_units = int(risk_amount // price_risk)
                max_units = min(max_units, risk_units)
        return max_units
    
    def check_position_risk(self, portfolio, position):
        """
        Check if a position meets risk criteria.
        
        Args:
            portfolio: Portfolio object
            position: Position object to check
            
        Returns:
            dict: Dictionary with risk metrics and status
        """
        # Skip risk checks if rules are not applied
        if not self._apply_risk_rules:
            return {
                "passes": True,
                "messages": [],
                "metrics": {
                    "position_size_pct": 0,
                    "risk_amount": 0
                }
            }
            
        portfolio_value = portfolio.get_total_value()
        if portfolio_value <= 0:
            return {"passes": False, "messages": ["Invalid portfolio value"]}
            
        position_value = position.get_value()
        position_size_pct = position_value / portfolio_value if portfolio_value > 0 else 0
        
        messages = []
        passes = True
        
        # NOTE: We no longer force-exit positions that have grown beyond max size
        # Instead, we just report the issue but return passes=True
        if position_size_pct > self.max_position_size and self._use_position_sizing:
            messages.append(
                f"Position size ({position_size_pct:.1%}) exceeds maximum allowed ({self.max_position_size:.1%})"
            )
            # passes remains True - no longer stopping iteration
        
        if position_size_pct < self.min_position_size and self._use_position_sizing:
            messages.append(
                f"Position size ({position_size_pct:.1%}) below minimum threshold ({self.min_position_size:.1%})"
            )
            # passes remains True - no longer stopping iteration
            
        return {
            "passes": passes,
            "messages": messages,
            "metrics": {
                "position_size_pct": position_size_pct,
                "risk_amount": position_value * self.risk_per_trade if self._use_risk_per_trade else 0
            }
        }

    def calculate_stops(self, entry_price: float, direction: int) -> Tuple[float, float]:
        """
        Calculate initial stop-loss and take-profit prices.

        Args:
            entry_price (float): Price at which the position is entered.
            direction (int): Direction of the trade (1 for long, -1 for short).

        Returns:
            Tuple[float, float]: (stop_loss_price, take_profit_price).
                                 Take-profit might be infinity if ratio is not applicable.
        """
        if entry_price <= 0: return 0.0, 0.0 # Avoid division by zero

        stop_loss_distance = entry_price * self.stop_loss_pct
        stop_loss_price = entry_price - (stop_loss_distance * direction)

        # Calculate take profit based on risk:reward ratio
        take_profit_distance = stop_loss_distance * self.profit_target_ratio
        take_profit_price = entry_price + (take_profit_distance * direction)

        # Ensure stops are logical (e.g., stop loss below entry for long)
        if direction > 0: # Long
            stop_loss_price = min(stop_loss_price, entry_price * 0.999) # Ensure slightly below entry
            take_profit_price = max(take_profit_price, entry_price * 1.001) # Ensure slightly above entry
        else: # Short
            stop_loss_price = max(stop_loss_price, entry_price * 1.001) # Ensure slightly above entry
            take_profit_price = min(take_profit_price, entry_price * 0.999) # Ensure slightly below entry


        logger.debug(f"Calculated Stops for Entry=${entry_price:.2f} (Dir={direction}): "
                     f"SL=${stop_loss_price:.2f} ({self.stop_loss_pct:.2%}), TP=${take_profit_price:.2f} (R:R={self.profit_target_ratio:.1f})")
        return stop_loss_price, take_profit_price


    def update_trailing_stop(self, entry_price: float, highest_price_since_entry: float,
                             lowest_price_since_entry: float, current_stop: float, direction: int) -> float:
        """
        Update trailing stop level based on price movement since entry.

        Args:
            entry_price (float): Original entry price of the position.
            highest_price_since_entry (float): The highest price reached since the position was opened.
            lowest_price_since_entry (float): The lowest price reached since the position was opened.
            current_stop (float): The current stop-loss price level.
            direction (int): Direction of the trade (1 for long, -1 for short).

        Returns:
            float: Updated stop-loss price. Returns `current_stop` if no update is needed.
        """
        if not self.use_trailing_stop:
            return current_stop # Trailing stop disabled

        if direction > 0: # Long position
            # Check if activation profit is reached
            activation_price = entry_price * (1 + self.trailing_stop_activation)
            if highest_price_since_entry >= activation_price:
                # Calculate new potential stop based on the highest price reached
                potential_new_stop = highest_price_since_entry * (1 - self.trailing_stop_distance)
                # Only move the stop up, never down
                if potential_new_stop > current_stop:
                    logger.debug(f"Trailing stop (Long) updated: Entry=${entry_price:.2f}, High=${highest_price_since_entry:.2f}, New SL=${potential_new_stop:.2f} (Prev SL=${current_stop:.2f})")
                    return potential_new_stop
        else: # Short position
            # Check if activation profit is reached (price moved down)
            activation_price = entry_price * (1 - self.trailing_stop_activation)
            if lowest_price_since_entry <= activation_price:
                # Calculate new potential stop based on the lowest price reached
                potential_new_stop = lowest_price_since_entry * (1 + self.trailing_stop_distance)
                # Only move the stop down, never up
                if potential_new_stop < current_stop:
                    logger.debug(f"Trailing stop (Short) updated: Entry=${entry_price:.2f}, Low=${lowest_price_since_entry:.2f}, New SL=${potential_new_stop:.2f} (Prev SL=${current_stop:.2f})")
                    return potential_new_stop

        return current_stop # No update


    def can_open_new_position(self, open_position_count: int) -> bool:
        """
        Check if a new position can be opened based on the max positions limit.

        Args:
            open_position_count (int): Current number of open positions.

        Returns:
            bool: True if a new position can be opened, False otherwise.
        """
        can_open = open_position_count < self.max_open_positions
        if not can_open:
            logger.debug(f"Cannot open new position: Limit of {self.max_open_positions} reached (currently {open_position_count}).")
        return can_open

    # --- Portfolio Level Checks (Placeholder - need integration with portfolio history) ---

    def check_portfolio_risk(self, current_date, portfolio):
        """
        Check if portfolio risk limits have been exceeded.
        Returns True if portfolio risk limits are acceptable.
        Returns False if risk limits are breached (and continue_iterate=False).
        
        Note: As of April 2025, this method has been modified to always return True
        to ensure backtests only stop when the period ends or capital is depleted,
        while still logging warnings when risk limits are breached.
        """
        # If no drawdown protection is enabled, just return True
        if not self._use_drawdown_protection:
            return True
            
        # Calculate current drawdown
        max_drawdown_pct = portfolio.current_drawdown * 100
        
        # Calculate daily P&L as percentage
        daily_change_pct = portfolio.get_daily_change_percent(current_date)

        # Check max drawdown
        if max_drawdown_pct > self.max_drawdown * 100:
            warning_msg = (f"RISK WARNING: Maximum drawdown exceeded: {max_drawdown_pct:.2f}% > "
                         f"{self.max_drawdown * 100:.2f}% (limit)")
            self.logger.warning(warning_msg)
            # Log but continue anyway (modified to not stop backtest)
        
        # Check daily loss limit
        if daily_change_pct < -1 * self.max_daily_loss * 100:
            warning_msg = (f"RISK WARNING: Daily loss limit exceeded: {daily_change_pct:.2f}% < "
                         f"-{self.max_daily_loss * 100:.2f}% (limit)")
            self.logger.warning(warning_msg)
            # Log but continue anyway (modified to not stop backtest)
        
        # Always return True to ensure backtests continue regardless of risk limits
        return True

    @property
    def use_stop_loss(self) -> bool:
        """Public getter for stop loss feature flag"""
        return self._use_stop_loss

    @property
    def use_take_profit(self) -> bool:
        """Public getter for take profit feature flag"""
        return self._use_take_profit

    @property
    def use_trailing_stop(self) -> bool:
        """Public getter for trailing stop feature flag"""
        return self._use_trailing_stop