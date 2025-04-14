import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple, Optional, List

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Centralized risk management system for portfolio management.

    Handles position sizing, stop-loss/take-profit calculation, trailing stops,
    and checks against portfolio-level risk limits. Parameters are typically
    provided as percentages (e.g., 2.0 for 2%) or ratios in the UI/config,
    but are stored internally as decimal fractions (e.g., 0.02) for calculations.
    """
    def __init__(self, 
                 logger=None,
                 max_drawdown=0.2,
                 max_daily_loss=0.05,
                 continue_iterate=True,  # Changed default to True
                 use_position_sizing=True,
                 use_stop_loss=True,
                 use_take_profit=True,
                 risk_per_trade=0.02,
                 default_stop_loss_pct=0.05,
                 default_take_profit_pct=0.1):
        """
        Initialize the RiskManager class.
        
        Args:
            logger: Logger instance
            max_drawdown (float): Maximum allowed drawdown (decimal, e.g., 0.2 for 20%)
            max_daily_loss (float): Maximum allowed daily loss (decimal, e.g., 0.05 for 5%)
            continue_iterate (bool): Whether to continue iterations when risk limits are breached
            use_position_sizing (bool): Whether to use position sizing
            use_stop_loss (bool): Whether to use stop losses
            use_take_profit (bool): Whether to use take profits
            risk_per_trade (float): Risk per trade as a fraction of portfolio (decimal)
            default_stop_loss_pct (float): Default stop loss percentage if not provided by strategy
            default_take_profit_pct (float): Default take profit percentage if not provided by strategy
        """
        self.logger = logger or logging.getLogger(__name__)
        self.max_drawdown = max_drawdown
        self.max_daily_loss = max_daily_loss
        self.continue_iterate = continue_iterate
        
        # Feature flags
        self._use_position_sizing = use_position_sizing
        self._use_stop_loss = use_stop_loss
        self._use_take_profit = use_take_profit
        self._use_risk_per_trade = risk_per_trade > 0
        self._use_drawdown_protection = False  # Changed default to False
        
        # Parameters
        self.risk_per_trade = risk_per_trade
        self.default_stop_loss_pct = default_stop_loss_pct
        self.default_take_profit_pct = default_take_profit_pct

        # --- Parameter Validation and Storage ---
        self.max_position_size = max(0.0, min(1.0, float(max_position_size)))
        self.min_position_size = max(0.0, min(self.max_position_size, float(min_position_size)))
        self.max_open_positions = max(1, int(max_open_positions))

        self.stop_loss_pct = max(0.001, float(stop_loss_pct)) # Ensure stop loss is at least 0.1%
        self.risk_per_trade_pct = max(0.001, min(0.1, float(risk_per_trade_pct))) # Ensure risk per trade is at least 0.1% and at most 10%
        self.profit_target_ratio = max(0.1, float(profit_target_ratio)) # Ensure ratio is positive
        self.use_trailing_stop = bool(use_trailing_stop)
        self.trailing_stop_activation = max(0.0, float(trailing_stop_activation))
        self.trailing_stop_distance = max(0.001, float(trailing_stop_distance)) # Ensure trail distance is positive

        self.max_drawdown = max(0.0, min(1.0, float(max_drawdown)))
        self.max_daily_loss = max(0.0, min(1.0, float(max_daily_loss)))
        self.continue_iterate = bool(continue_iterate)

        self.use_market_filter = bool(use_market_filter) # Store the flag
        self.market_trend_lookback = max(10, int(market_trend_lookback)) # Min lookback of 10

        # --- Runtime Tracking Variables ---
        self.highest_portfolio_value = 0.0 # Tracks peak equity for drawdown calculation

        if kwargs:
             logger.warning(f"RiskManager received unused parameters: {kwargs.keys()}")

        # Log initialization with feature flags
        logger.info(f"RiskManager initialized with settings: max_pos_size={self.max_position_size:.2%}, "
                    f"min_pos_size={self.min_position_size:.2%}, max_open={self.max_open_positions}, "
                    f"stop={self.stop_loss_pct:.2%}, risk_per_trade={self.risk_per_trade_pct:.2%}, R:R={self.profit_target_ratio:.1f}, "
                    f"trailing={self.use_trailing_stop} (act: {self.trailing_stop_activation:.2%}, dist: {self.trailing_stop_distance:.2%}), "
                    f"max_dd={self.max_drawdown:.2%}, max_daily_loss={self.max_daily_loss:.2%}, "
                    f"continue_iterate={self.continue_iterate}, "
                    f"market_filter={self.use_market_filter} (lookback: {self.market_trend_lookback})")
        
        logger.info(f"Risk features enabled: position_sizing={self._use_position_sizing}, "
                    f"stop_loss={self._use_stop_loss}, take_profit={self._use_take_profit}, "
                    f"risk_per_trade={self._use_risk_per_trade}, "
                    f"drawdown_protection={self._use_drawdown_protection}")


    def calculate_position_size(self, current_portfolio_value: float, available_cash: float,
                                price: float, volatility: Optional[float] = None) -> int:
        """
        Calculate the number of shares to trade based on risk parameters.

        Args:
            current_portfolio_value (float): The current total value of the portfolio (cash + positions).
            available_cash (float): The current amount of cash available for trading.
            price (float): The entry price of the asset.
            volatility (Optional[float]): Estimated volatility (e.g., ATR or std dev) of the asset.
                                           If provided, can be used for volatility-adjusted sizing.

        Returns:
            int: The number of shares to trade. Returns 0 if position cannot be opened.
        """
        if isinstance(price, pd.Series):
            if price.empty or (price <= 0).any():
                logger.warning(f"Cannot calculate position size - invalid price (Series): {price}")
                return 0
        else:
            if price <= 0:
                logger.warning(f"Cannot calculate position size - invalid price: {price}")
                return 0

        # 1. Determine maximum capital allocation based on portfolio limits
        max_capital_per_position = current_portfolio_value * self.max_position_size

        # 2. Determine capital based on risk (stop-loss)
        # Amount to risk per trade ($) = Portfolio Value * Risk Per Trade % (as fraction)
        capital_at_risk = current_portfolio_value * self.risk_per_trade_pct
        # Implied position size based on stop loss distance
        stop_distance = price * self.stop_loss_pct
        
        # FIX HERE - Check if stop_distance is a Series
        if isinstance(stop_distance, pd.Series):
            if stop_distance.empty or stop_distance.isna().all():
                logger.warning("Stop distance is empty or all NaN. Using default.")
                stop_distance = price * 0.02  # Default 2% stop
            else:
                # Use item() if it's a single value Series
                stop_distance = stop_distance.iloc[0] if len(stop_distance) == 1 else stop_distance.mean()
        
        if stop_distance <= 0:
            logger.warning("Stop distance is zero or negative. Using default.")
            stop_distance = price * 0.02  # Default 2% stop
        
        if stop_distance <= 0:
             logger.warning("Stop distance is zero or negative, cannot use risk-based sizing.")
             size_based_on_risk = np.inf # Effectively no limit from risk sizing
        else:
             size_based_on_risk = capital_at_risk / stop_distance # Shares based on risk

        # 3. Determine capital based on volatility (optional)
        # if volatility is not None and volatility > 0:
        #     # Example: Target volatility-adjusted position size
        #     target_dollar_volatility = current_portfolio_value * 0.01 # Target 1% daily $ volatility per position
        #     shares_based_on_vol = target_dollar_volatility / (price * volatility)
        #     max_capital_per_position = min(max_capital_per_position, shares_based_on_vol * price)

        # 4. Determine final position size in shares
        # Calculate the maximum number of shares based on risk
        max_shares_risk = min(size_based_on_risk, max_capital_per_position / price)
        target_shares = max_shares_risk # Use risk-based position sizing as primary

        # Ensure it meets minimum size requirements
        min_shares = (current_portfolio_value * self.min_position_size) / price
        target_shares = max(min_shares, target_shares)

        # Ensure we have enough cash
        required_cash = target_shares * price
        if required_cash > available_cash:
            target_shares = available_cash / price # Reduce size to available cash
            logger.debug(f"Reduced position size due to insufficient cash. Required: ${required_cash:.2f}, Available: ${available_cash:.2f}")

        # Convert to integer shares (floor to be conservative)
        final_shares = int(np.floor(target_shares))

        # Final check: ensure shares are positive and meet minimum $ value if needed
        if final_shares <= 0:
            logger.debug(f"Calculated position size is zero or negative for price ${price:.2f}.")
            return 0
        # Optional: Check if minimum position value is met
        # min_value_required = current_portfolio_value * self.min_position_size
        # if final_shares * price < min_value_required:
        #     logger.debug(f"Calculated position value (${final_shares * price:.2f}) below minimum required (${min_value_required:.2f}).")
        #     return 0


        logger.debug(f"Calculated position size: {final_shares} shares for price ${price:.2f} "
                     f"(Max Cap: ${max_capital_per_position:.2f}, Risk Shares: {size_based_on_risk:.2f}, "
                     f"Min Shares: {min_shares:.2f}, Cash Limit Shares: {available_cash / price:.2f})")
        return final_shares


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