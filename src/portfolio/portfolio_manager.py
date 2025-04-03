from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from .risk_manager import RiskManager # Importuj RiskManager

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Represents an active trading position."""
    ticker: str
    entry_date: pd.Timestamp
    entry_price: float
    shares: int
    direction: int  # 1 for long, -1 for short

    # Risk management attributes
    stop_loss_price: float
    take_profit_price: float
    initial_stop_price: float # Store the initial SL for reference / trailing calculation base
    use_trailing: bool = False # Determined by RiskManager settings at entry

    # Tracking for trailing stops
    highest_price_since_entry: float = field(init=False, default=0.0)
    lowest_price_since_entry: float = field(init=False, default=np.inf)

    # Optional metadata
    # allocation_pct: float = 0.0 # % of portfolio value at time of entry
    # volatility_at_entry: Optional[float] = None

    def __post_init__(self):
        """Initialize tracking prices after creation."""
        # Initialize high/low trackers with the entry price
        self.highest_price_since_entry = self.entry_price
        self.lowest_price_since_entry = self.entry_price

    def update_peak_prices(self, current_price: float):
        """Updates the highest/lowest price seen since entry."""
        self.highest_price_since_entry = max(self.highest_price_since_entry, current_price)
        self.lowest_price_since_entry = min(self.lowest_price_since_entry, current_price)


class PortfolioManager:
    """
    Manages the portfolio's state, including cash, open positions,
    trade execution based on signals and risk management rules.
    """

    def __init__(self, initial_capital: float = 10000.0, risk_manager: Optional[RiskManager] = None):
        """
        Initializes the PortfolioManager.

        Args:
            initial_capital (float): The starting cash balance.
            risk_manager (Optional[RiskManager]): An instance of RiskManager.
                                                  If None, a default RiskManager is created.
        """
        if initial_capital <= 0:
            raise ValueError("Initial capital must be positive.")

        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}  # Ticker -> Position object
        self.closed_trades: List[Dict] = []      # Stores details of completed trades
        self.portfolio_value_history: List[Tuple[pd.Timestamp, float]] = [] # Track EOD values

        # Assign or create RiskManager
        self.risk_manager = risk_manager if risk_manager is not None else RiskManager()
        logger.info(f"PortfolioManager initialized with capital ${initial_capital:,.2f} and linked RiskManager.")


    def get_current_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculates the total current value of the portfolio (cash + open positions)."""
        position_value = 0.0
        for ticker, position in self.positions.items():
            current_price = current_prices.get(ticker, position.entry_price) # Use last known price if current not available
            if pd.notna(current_price): # Check for NaN prices
                 position_value += position.shares * current_price
            else:
                 logger.warning(f"NaN price encountered for open position {ticker}. Using entry price for valuation.")
                 position_value += position.shares * position.entry_price


        total_value = self.cash + position_value
        return total_value


    def update_portfolio_value(self, current_prices: Dict[str, float], current_date: Optional[pd.Timestamp] = None) -> float:
        """
        Calculates the current portfolio value and optionally records it.

        Args:
            current_prices (Dict[str, float]): Dictionary mapping tickers to their current prices.
            current_date (Optional[pd.Timestamp]): The current date for recording history.

        Returns:
            float: The calculated total portfolio value.
        """
        total_value = self.get_current_portfolio_value(current_prices)

        if current_date is not None:
            self.portfolio_value_history.append((current_date, total_value))
            # Optionally, update RiskManager's peak value here if needed for real-time checks
            # self.risk_manager.highest_portfolio_value = max(self.risk_manager.highest_portfolio_value, total_value)

        return total_value


    def open_position(self, signal_data: Dict[str, Any]) -> bool:
        """
        Attempts to open a new position based on a signal and risk rules.

        Args:
            signal_data (Dict[str, Any]): Dictionary containing signal details:
                'ticker' (str): Ticker symbol.
                'date' (pd.Timestamp): Date of the signal/entry.
                'price' (float): Entry price.
                'direction' (int): 1 for long, -1 for short.
                'volatility' (Optional[float]): Asset volatility for sizing.

        Returns:
            bool: True if the position was successfully opened, False otherwise.
        """
        ticker = signal_data.get('ticker')
        entry_price = signal_data.get('price')
        entry_date = signal_data.get('date')
        direction = signal_data.get('direction', 1)
        volatility = signal_data.get('volatility')

        # --- Pre-Trade Checks ---
        if not all([ticker, entry_price, entry_date, direction]):
            logger.error(f"Missing required data in open_position signal: {signal_data}")
            return False
        if entry_price <= 0:
             logger.warning(f"Attempted to open position for {ticker} at invalid price ${entry_price:.2f}. Ignoring.")
             return False
        if ticker in self.positions:
            logger.info(f"Position for {ticker} already exists. Ignoring new open signal on {entry_date}.")
            return False
        if not self.risk_manager.can_open_new_position(len(self.positions)):
            logger.info(f"Max open positions limit ({self.risk_manager.max_open_positions}) reached. Cannot open {ticker}.")
            return False

        # --- Calculate Position Size ---
        current_total_value = self.get_current_portfolio_value({ticker: entry_price}) # Estimate current value
        shares_to_trade = self.risk_manager.calculate_position_size(
            current_portfolio_value=current_total_value,
            available_cash=self.cash,
            price=entry_price,
            volatility=volatility
        )

        if shares_to_trade <= 0:
            logger.info(f"Calculated position size for {ticker} is {shares_to_trade}. Cannot open position.")
            return False

        # --- Calculate Cost and Check Cash ---
        cost = shares_to_trade * entry_price
        # Add estimated commission if applicable
        # cost += self.calculate_commission(shares_to_trade, entry_price)

        if cost > self.cash:
            logger.warning(f"Insufficient cash to open {ticker}. Required: ${cost:.2f}, Available: ${self.cash:.2f}. Cannot open.")
            # Alternative: Reduce shares to fit cash (might violate min size)
            # shares_to_trade = int(np.floor(self.cash / entry_price))
            # cost = shares_to_trade * entry_price
            # if shares_to_trade <= 0: return False # Still cannot open
            return False


        # --- Calculate Stops ---
        stop_loss_price, take_profit_price = self.risk_manager.calculate_stops(
            entry_price=entry_price,
            direction=direction
        )

        # --- Create and Store Position ---
        new_position = Position(
            ticker=ticker,
            entry_date=entry_date,
            entry_price=entry_price,
            shares=shares_to_trade,
            direction=direction,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            initial_stop_price=stop_loss_price, # Store initial stop
            use_trailing=self.risk_manager.use_trailing_stop # Store if trailing is enabled
        )
        self.positions[ticker] = new_position

        # --- Update Cash ---
        self.cash -= cost
        # self.cash -= self.calculate_commission(shares_to_trade, entry_price) # Deduct commission

        logger.info(f"Opened {'LONG' if direction > 0 else 'SHORT'} position: {shares_to_trade} {ticker} @ ${entry_price:.2f} on {entry_date.date()}. "
                    f"Cost: ${cost:.2f}, Cash Left: ${self.cash:.2f}, SL: ${stop_loss_price:.2f}, TP: ${take_profit_price:.2f}")
        return True


    def close_position(self, ticker: str, exit_price: float, exit_date: pd.Timestamp, reason: str = "unknown") -> bool:
        """
        Closes an existing position and records the trade.

        Args:
            ticker (str): The ticker symbol of the position to close.
            exit_price (float): The price at which the position is closed.
            exit_date (pd.Timestamp): The date of the closure.
            reason (str): The reason for closing (e.g., 'signal', 'stop_loss', 'take_profit').

        Returns:
            bool: True if the position was successfully closed, False otherwise.
        """
        if ticker not in self.positions:
            logger.warning(f"Attempted to close non-existent position: {ticker}")
            return False
        if pd.isna(exit_price) or exit_price <= 0:
             logger.error(f"Invalid exit price ({exit_price}) for closing {ticker}. Cannot close.")
             return False


        position = self.positions[ticker]

        # --- Calculate Proceeds and P&L ---
        proceeds = position.shares * exit_price
        # Deduct commission if applicable
        # proceeds -= self.calculate_commission(position.shares, exit_price)

        cost_basis = position.shares * position.entry_price
        # Add entry commission if tracked separately
        # cost_basis += entry_commission

        gross_pnl = (exit_price - position.entry_price) * position.shares * position.direction
        # net_pnl = proceeds - cost_basis # Alternative P&L calculation including commissions

        pnl_pct = (gross_pnl / cost_basis) * 100 if cost_basis != 0 else 0.0

        # --- Record Trade ---
        trade_record = {
            'ticker': position.ticker,
            'entry_date': position.entry_date,
            'exit_date': exit_date,
            'entry_price': position.entry_price,
            'exit_price': exit_price,
            'shares': position.shares,
            'direction': position.direction, # Store as int
            'pnl': gross_pnl, # Store gross PnL
            'pnl_pct': pnl_pct,
            'exit_reason': reason,
            'holding_period_days': (exit_date - position.entry_date).days,
            # Add other fields if needed (commission, slippage, initial stop etc.)
            'initial_stop_price': position.initial_stop_price,
            'final_stop_price': position.stop_loss_price # Store the SL price at exit
        }
        self.closed_trades.append(trade_record)

        # --- Update Portfolio State ---
        self.cash += proceeds
        del self.positions[ticker]

        logger.info(f"Closed position: {position.shares} {ticker} @ ${exit_price:.2f} on {exit_date.date()} (Reason: {reason}). "
                    f"PnL: ${gross_pnl:,.2f} ({pnl_pct:.2f}%). Cash: ${self.cash:,.2f}")
        return True


    def close_all_positions(self, current_prices: Dict[str, float], current_date: pd.Timestamp, reason: str = "liquidation"):
        """Closes all currently open positions."""
        logger.warning(f"Closing all {len(self.positions)} open positions on {current_date.date()} due to: {reason}")
        # Iterate over a copy of keys because dictionary size changes during iteration
        tickers_to_close = list(self.positions.keys())
        closed_count = 0
        for ticker in tickers_to_close:
            if ticker in self.positions: # Check again in case already closed by stop logic etc.
                exit_price = current_prices.get(ticker)
                if exit_price is not None and pd.notna(exit_price):
                    if self.close_position(ticker, exit_price, current_date, reason=reason):
                        closed_count += 1
                else:
                    logger.error(f"Cannot close position {ticker}: No valid exit price provided for date {current_date}.")
        logger.info(f"Closed {closed_count} positions.")


    def update_positions_and_stops(self, current_prices: Dict[str, float], current_date: pd.Timestamp):
        """
        Iterates through open positions, checks for stop-loss/take-profit triggers,
        and updates trailing stops.

        Args:
            current_prices (Dict[str, float]): Current market prices for relevant tickers.
            current_date (pd.Timestamp): The current date of the simulation.
        """
        positions_to_close = [] # Store positions to close after iteration

        for ticker, position in self.positions.items():
            current_price = current_prices.get(ticker)
            if current_price is None or pd.isna(current_price):
                # logger.warning(f"No current price for open position {ticker} on {current_date}. Cannot update stops or check exits.")
                continue # Skip this position if no current price

            # Update peak prices for trailing stop calculation
            position.update_peak_prices(current_price)

            # --- Check Exits ---
            exit_reason = None
            exit_price = current_price # Assume exit at current price if triggered

            # 1. Check Stop Loss
            if position.direction > 0 and current_price <= position.stop_loss_price:
                exit_reason = "stop_loss"
                exit_price = position.stop_loss_price # Exit at stop price
                logger.debug(f"Stop Loss triggered for LONG {ticker}: Price ${current_price:.2f} <= SL ${position.stop_loss_price:.2f}")
            elif position.direction < 0 and current_price >= position.stop_loss_price:
                exit_reason = "stop_loss"
                exit_price = position.stop_loss_price # Exit at stop price
                logger.debug(f"Stop Loss triggered for SHORT {ticker}: Price ${current_price:.2f} >= SL ${position.stop_loss_price:.2f}")

            # 2. Check Take Profit (only if not stopped out)
            if exit_reason is None:
                if position.direction > 0 and current_price >= position.take_profit_price:
                    exit_reason = "take_profit"
                    exit_price = position.take_profit_price # Exit at take profit price
                    logger.debug(f"Take Profit triggered for LONG {ticker}: Price ${current_price:.2f} >= TP ${position.take_profit_price:.2f}")
                elif position.direction < 0 and current_price <= position.take_profit_price:
                    exit_reason = "take_profit"
                    exit_price = position.take_profit_price # Exit at take profit price
                    logger.debug(f"Take Profit triggered for SHORT {ticker}: Price ${current_price:.2f} <= TP ${position.take_profit_price:.2f}")

            # If an exit was triggered, schedule position for closure
            if exit_reason:
                positions_to_close.append((ticker, exit_price, exit_reason))
                continue # Don't update trailing stop if exiting

            # --- Update Trailing Stop (if enabled for position and no exit triggered) ---
            if position.use_trailing:
                new_stop_loss = self.risk_manager.update_trailing_stop(
                    entry_price=position.entry_price,
                    highest_price_since_entry=position.highest_price_since_entry,
                    lowest_price_since_entry=position.lowest_price_since_entry,
                    current_stop=position.stop_loss_price,
                    direction=position.direction
                )
                # Update the position's stop loss if it changed
                if new_stop_loss != position.stop_loss_price:
                     # logger.debug(f"Trailing stop for {ticker} moved to ${new_stop_loss:.2f}")
                     position.stop_loss_price = new_stop_loss

        # --- Close Positions Scheduled for Exit ---
        for ticker, price, reason in positions_to_close:
            self.close_position(ticker, price, current_date, reason=reason)


    # Optional: Add methods for calculating commissions, handling dividends, etc.
    # def calculate_commission(self, shares: int, price: float) -> float:
    #     commission_rate = 0.001 # Example rate
    #     min_commission = 1.0   # Example minimum
    #     commission = abs(shares) * price * commission_rate
    #     return max(min_commission, commission)