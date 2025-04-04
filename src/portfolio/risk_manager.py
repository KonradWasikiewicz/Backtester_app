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
                 # Position limits (as fractions, e.g., 0.2 = 20%)
                 max_position_size: float = 0.20,
                 min_position_size: float = 0.01,
                 max_open_positions: int = 5,

                 # Stop management (as fractions or ratios)
                 stop_loss_pct: float = 0.02,        # Stop loss as fraction of entry price
                 profit_target_ratio: float = 2.0,   # Risk:Reward ratio (e.g., 2.0 means target is 2x stop loss distance)
                 use_trailing_stop: bool = False,    # Flag to enable/disable trailing stop logic
                 trailing_stop_activation: float = 0.02,  # Activate trailing stop after % gain (as fraction)
                 trailing_stop_distance: float = 0.015,   # Trail distance % below peak (as fraction)

                 # Portfolio-level limits (as fractions)
                 max_drawdown: float = 0.20,         # Max allowed portfolio drawdown fraction
                 max_daily_loss: float = 0.05,       # Max allowed daily loss fraction

                 # Market condition filters
                 use_market_filter: bool = False,    # Flag to enable/disable market filter logic
                 market_trend_lookback: int = 100,   # Lookback period for market trend calculation

                 # Volatility management (can be added later if needed)
                 # volatility_lookback: int = 20,
                 # volatility_cap: float = 0.03,
                 **kwargs # Catch any unexpected parameters
                ):
        """
        Initializes the RiskManager with specified parameters.

        Args:
            max_position_size (float): Max allocation per position (e.g., 0.2 for 20%).
            min_position_size (float): Min allocation per position (e.g., 0.01 for 1%).
            max_open_positions (int): Max number of concurrent open positions.
            stop_loss_pct (float): Default stop loss as fraction (e.g., 0.02 for 2%).
            profit_target_ratio (float): Desired risk:reward ratio (e.g., 2.0).
            use_trailing_stop (bool): Whether to use the trailing stop logic.
            trailing_stop_activation (float): Profit % (as fraction) to activate trailing stop.
            trailing_stop_distance (float): Trail distance % (as fraction) below the peak.
            max_drawdown (float): Max allowed portfolio drawdown (as fraction, e.g., 0.2 for 20%).
            max_daily_loss (float): Max allowed daily portfolio loss (as fraction, e.g., 0.05 for 5%).
            use_market_filter (bool): Whether the backtest loop should consider market conditions.
                                      (Actual filtering logic happens outside RiskManager, this is a flag).
            market_trend_lookback (int): Lookback period for external market trend calculation.
            kwargs: Allows for extra parameters that might be passed but not used by this version.
        """

        # --- Parameter Validation and Storage ---
        self.max_position_size = max(0.0, min(1.0, float(max_position_size)))
        self.min_position_size = max(0.0, min(self.max_position_size, float(min_position_size)))
        self.max_open_positions = max(1, int(max_open_positions))

        self.stop_loss_pct = max(0.001, float(stop_loss_pct)) # Ensure stop loss is at least 0.1%
        self.profit_target_ratio = max(0.1, float(profit_target_ratio)) # Ensure ratio is positive
        self.use_trailing_stop = bool(use_trailing_stop)
        self.trailing_stop_activation = max(0.0, float(trailing_stop_activation))
        self.trailing_stop_distance = max(0.001, float(trailing_stop_distance)) # Ensure trail distance is positive

        self.max_drawdown = max(0.0, min(1.0, float(max_drawdown)))
        self.max_daily_loss = max(0.0, min(1.0, float(max_daily_loss)))

        self.use_market_filter = bool(use_market_filter) # Store the flag
        self.market_trend_lookback = max(10, int(market_trend_lookback)) # Min lookback of 10

        # Volatility params (can be uncommented and validated if used)
        # self.volatility_lookback = max(2, int(kwargs.get('volatility_lookback', 20)))
        # self.volatility_cap = max(0.001, float(kwargs.get('volatility_cap', 0.03)))

        # --- Runtime Tracking Variables ---
        self.highest_portfolio_value = 0.0 # Tracks peak equity for drawdown calculation
        # self.daily_pnl_tracker = 0.0 # Tracks PnL within a single day (needs reset logic)
        # self.sector_exposure = {} # Tracks exposure per sector (needs external updates)

        if kwargs:
             logger.warning(f"RiskManager received unused parameters: {kwargs.keys()}")

        logger.info(f"RiskManager initialized with settings: max_pos_size={self.max_position_size:.2%}, "
                    f"min_pos_size={self.min_position_size:.2%}, max_open={self.max_open_positions}, "
                    f"stop={self.stop_loss_pct:.2%}, R:R={self.profit_target_ratio:.1f}, "
                    f"trailing={self.use_trailing_stop} (act: {self.trailing_stop_activation:.2%}, dist: {self.trailing_stop_distance:.2%}), "
                    f"max_dd={self.max_drawdown:.2%}, max_daily_loss={self.max_daily_loss:.2%}, "
                    f"market_filter={self.use_market_filter} (lookback: {self.market_trend_lookback})")


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
        # Amount to risk per trade ($) = Portfolio Value * Stop Loss % (as fraction)
        # This assumes the stop loss % applies to the entry value of this specific trade.
        # A more common approach is % of *portfolio* value risked per trade.
        # Let's use % of portfolio value risked:
        capital_at_risk = current_portfolio_value * self.stop_loss_pct
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
        target_capital = max_capital_per_position # Start with the max allocation limit
        # Note: We aren't directly using size_based_on_risk to set target_capital here,
        # because max_capital_per_position already limits the overall exposure.
        # The stop loss % mainly determines the *actual dollar risk* once the position is sized.

        # Calculate target shares based on capital and price
        target_shares = target_capital / price

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

    def check_portfolio_risk(self, portfolio_value_history: pd.Series) -> bool:
        """
        Checks if the portfolio violates max drawdown or daily loss limits.
        NOTE: This requires the caller (BacktestManager/Engine) to maintain and pass
              the portfolio value history.

        Args:
            portfolio_value_history (pd.Series): Time series of portfolio values.

        Returns:
            bool: True if within limits, False if a limit is breached.
        """
        if portfolio_value_history is None or portfolio_value_history.empty or len(portfolio_value_history) < 2:
            return True # Not enough data to check

        # Update peak value
        current_peak = portfolio_value_history.cummax().iloc[-1]
        self.highest_portfolio_value = max(self.highest_portfolio_value, current_peak) # Track overall peak

        # Check Max Drawdown
        current_value = portfolio_value_history.iloc[-1]
        if self.highest_portfolio_value > 0:
             current_drawdown = (self.highest_portfolio_value - current_value) / self.highest_portfolio_value
             if current_drawdown > self.max_drawdown:
                 logger.warning(f"Portfolio Risk Breach: Max Drawdown limit ({self.max_drawdown:.2%}) exceeded. Current DD: {current_drawdown:.2%}")
                 return False

        # Check Max Daily Loss
        # Requires comparing today's value with yesterday's
        if len(portfolio_value_history) >= 2:
            yesterday_value = portfolio_value_history.iloc[-2]
            if yesterday_value > 0:
                 daily_loss_pct = (yesterday_value - current_value) / yesterday_value
                 if daily_loss_pct > self.max_daily_loss:
                      logger.warning(f"Portfolio Risk Breach: Max Daily Loss limit ({self.max_daily_loss:.2%}) exceeded. Today's Loss: {daily_loss_pct:.2%}")
                      return False

        return True # Within limits

    # Reset daily PnL tracking - Requires modification if used
    # def reset_daily_tracking(self):
    #     self.daily_pnl_tracker = 0.0

    # Update sector exposure - Requires external call with sector info
    # def update_sector_exposure(self, sector_allocations: Dict[str, float]):
    #     self.sector_exposure = sector_allocations
    #     for sector, exposure in sector_allocations.items():
    #         if exposure > self.max_sector_exposure:
    #             logger.warning(f"Portfolio Risk Alert: Sector exposure for '{sector}' ({exposure:.2%}) exceeds limit ({self.max_sector_exposure:.2%})")
    #             # Action could be taken here or flagged to the main loop