# Plik: src/portfolio/portfolio_manager.py (Poprawiony import)

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any # <<<--- POPRAWIONY IMPORT
import pandas as pd
import numpy as np
from datetime import datetime
import logging
# Upewnij się, że RiskManager jest importowany poprawnie
try:
    from .risk_manager import RiskManager
except ImportError:
    # Spróbuj importu z poziomu src
    from src.portfolio.risk_manager import RiskManager

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Represents an active trading position."""
    ticker: str
    entry_date: pd.Timestamp
    entry_price: float
    shares: int
    direction: int  # 1 for long, -1 for short
    stop_loss_price: float
    take_profit_price: float
    initial_stop_price: float # Store the initial SL
    use_trailing: bool = False
    highest_price_since_entry: float = field(init=False, default=0.0)
    lowest_price_since_entry: float = field(init=False, default=np.inf)

    def __post_init__(self):
        self.highest_price_since_entry = self.entry_price
        self.lowest_price_since_entry = self.entry_price

    def update_peak_prices(self, current_price: float):
        self.highest_price_since_entry = max(self.highest_price_since_entry, current_price)
        self.lowest_price_since_entry = min(self.lowest_price_since_entry, current_price)


class PortfolioManager:
    """Manages portfolio state, positions, cash, and trade execution."""

    def __init__(self, initial_capital: float = 10000.0, risk_manager: Optional[RiskManager] = None):
        if initial_capital <= 0: raise ValueError("Initial capital must be positive.")
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.closed_trades: List[Dict] = []
        self.portfolio_value_history: List[Tuple[pd.Timestamp, float]] = []
        self.risk_manager = risk_manager if risk_manager is not None else RiskManager()
        # Store risk feature flags for easy access
        self.use_stop_loss = False  # Will be set when RiskManager has stop_loss enabled
        self.use_take_profit = False  # Will be set when RiskManager has take_profit enabled
        self._update_risk_features()
        logger.info(f"PortfolioManager initialized with capital ${initial_capital:,.2f} and linked RiskManager.")
        
    def _update_risk_features(self):
        """Update internal flags based on risk manager settings"""
        if self.risk_manager:
            # Check if risk features are explicitly enabled
            # This is determined by the risk_params dict in BacktestManager.run_backtest()
            self.use_stop_loss = getattr(self.risk_manager, '_use_stop_loss', False)
            self.use_take_profit = getattr(self.risk_manager, '_use_take_profit', False)
            logger.info(f"Risk features: stop_loss={self.use_stop_loss}, take_profit={self.use_take_profit}")
        else:
            self.use_stop_loss = False
            self.use_take_profit = False

    def get_current_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculates the total current value of the portfolio."""
        position_value = 0.0
        for ticker, position in self.positions.items():
            current_price = current_prices.get(ticker, position.entry_price)
            if pd.notna(current_price): position_value += position.shares * current_price
            else: logger.warning(f"NaN price for {ticker}. Using entry price."); position_value += position.shares * position.entry_price
        return self.cash + position_value

    def update_portfolio_value(self, current_prices: Dict[str, float], current_date: Optional[pd.Timestamp] = None) -> float:
        """Calculates current portfolio value and optionally records it."""
        total_value = self.get_current_portfolio_value(current_prices)
        if current_date is not None: self.portfolio_value_history.append((current_date, total_value))
        return total_value

    # Poprawiony Type Hint tutaj:
    def open_position(self, signal_data: Dict[str, Any]) -> bool:
        """Attempts to open a new position based on a signal and risk rules."""
        ticker = signal_data.get('ticker'); entry_price = signal_data.get('price'); entry_date = signal_data.get('date'); direction = signal_data.get('direction', 1); volatility = signal_data.get('volatility')

        if not all([ticker, entry_price, entry_date, direction]): logger.error(f"Missing data in open signal: {signal_data}"); return False
        if entry_price <= 0: logger.warning(f"Invalid entry price ${entry_price:.2f} for {ticker}."); return False
        if ticker in self.positions: logger.info(f"Position {ticker} already exists."); return False
        if not self.risk_manager.can_open_new_position(len(self.positions)): logger.info(f"Max positions limit ({self.risk_manager.max_open_positions}) reached."); return False

        current_total_value = self.get_current_portfolio_value({ticker: entry_price})
        # Determine position size
        if getattr(self.risk_manager, '_use_position_sizing', True) is False:
            shares_to_trade = int(self.cash // entry_price)
        else:
            shares_to_trade = self.risk_manager.calculate_position_size(
                current_portfolio_value=current_total_value,
                available_cash=self.cash,
                price=entry_price,
                volatility=volatility
            )
        logger.debug(f"Sizing inputs: cash={self.cash:.2f}, portfolio_value={current_total_value:.2f}, price={entry_price:.2f}, volatility={volatility}; calculated shares={shares_to_trade}")
        # Fallback to 1 share if risk manager allocates zero
        if shares_to_trade <= 0:
            # Only default to 1 share if cash covers one share
            if entry_price <= self.cash:
                logger.info(f"No shares allocated by risk manager for {ticker}. Defaulting to 1 share.")
                shares_to_trade = 1
            else:
                return False
         
        cost = shares_to_trade * entry_price
        if cost > self.cash: logger.warning(f"Insufficient cash for {ticker}. Required: ${cost:.2f}, Available: ${self.cash:.2f}."); return False

        stop_loss_price, take_profit_price = self.risk_manager.calculate_stops(entry_price=entry_price, direction=direction)

        new_position = Position(ticker=ticker, entry_date=entry_date, entry_price=entry_price, shares=shares_to_trade, direction=direction, stop_loss_price=stop_loss_price, take_profit_price=take_profit_price, initial_stop_price=stop_loss_price, use_trailing=self.risk_manager.use_trailing_stop)
        self.positions[ticker] = new_position
        self.cash -= cost

        logger.debug(f"Opened {'LONG' if direction > 0 else 'SHORT'} position: {shares_to_trade} {ticker} @ ${entry_price:.2f} on {entry_date.date()}. Cost: ${cost:.2f}, Cash: ${self.cash:.2f}, SL: ${stop_loss_price:.2f}, TP: ${take_profit_price:.2f}")
        return True

    def close_position(self, ticker: str, exit_price: float, exit_date: pd.Timestamp, reason: str = "unknown") -> bool:
        """Closes an existing position and records the trade."""
        if ticker not in self.positions: logger.warning(f"Attempted to close non-existent position: {ticker}"); return False
        if pd.isna(exit_price) or exit_price <= 0: logger.error(f"Invalid exit price ({exit_price}) for closing {ticker}."); return False

        position = self.positions[ticker]; proceeds = position.shares * exit_price; cost_basis = position.shares * position.entry_price
        gross_pnl = (exit_price - position.entry_price) * position.shares * position.direction
        pnl_pct = (gross_pnl / cost_basis) * 100 if cost_basis != 0 else 0.0

        trade_record = {'ticker': position.ticker, 'entry_date': position.entry_date, 'exit_date': exit_date, 'entry_price': position.entry_price, 'exit_price': exit_price, 'shares': position.shares, 'direction': position.direction, 'pnl': gross_pnl, 'pnl_pct': pnl_pct, 'exit_reason': reason, 'holding_period_days': (exit_date - position.entry_date).days if pd.notna(position.entry_date) and pd.notna(exit_date) else None, 'initial_stop_price': position.initial_stop_price, 'final_stop_price': position.stop_loss_price}
        self.closed_trades.append(trade_record)
        self.cash += proceeds
        del self.positions[ticker]

        logger.debug(f"Closed position: {position.shares} {ticker} @ ${exit_price:.2f} on {exit_date.date()} (Reason: {reason}). PnL: ${gross_pnl:,.2f} ({pnl_pct:.2f}%). Cash: ${self.cash:,.2f}")
        return True

    def close_all_positions(self, current_prices: Dict[str, float], current_date: pd.Timestamp, reason: str = "liquidation"):
        """Closes all currently open positions."""
        logger.warning(f"Closing all {len(self.positions)} open positions on {current_date.date()} due to: {reason}")
        tickers_to_close = list(self.positions.keys()); closed_count = 0
        for ticker in tickers_to_close:
            if ticker in self.positions:
                exit_price = current_prices.get(ticker)
                if exit_price is not None and pd.notna(exit_price):
                    if self.close_position(ticker, exit_price, current_date, reason=reason): closed_count += 1
                else: logger.error(f"Cannot close {ticker}: No valid exit price on {current_date}.")
        logger.info(f"Closed {closed_count} positions during final closure.")

    def update_positions_and_stops(self, current_prices: Dict[str, float], current_date: pd.Timestamp):
        """Checks for stop-loss/take-profit triggers and updates trailing stops."""
        positions_to_close = []
        for ticker, position in self.positions.items():
            current_price = current_prices.get(ticker)
            if current_price is None or pd.isna(current_price): continue

            position.update_peak_prices(current_price)
            exit_reason, exit_price = None, current_price

            # Check Stops/Profits only if their respective features are enabled
            if position.direction > 0: # Long
                if self.use_stop_loss and current_price <= position.stop_loss_price: 
                    exit_reason, exit_price = "stop_loss", position.stop_loss_price
                elif self.use_take_profit and current_price >= position.take_profit_price: 
                    exit_reason, exit_price = "take_profit", position.take_profit_price
            else: # Short
                if self.use_stop_loss and current_price >= position.stop_loss_price: 
                    exit_reason, exit_price = "stop_loss", position.stop_loss_price
                elif self.use_take_profit and current_price <= position.take_profit_price: 
                    exit_reason, exit_price = "take_profit", position.take_profit_price

            if exit_reason:
                 logger.debug(f"{exit_reason.replace('_',' ').title()} triggered for {ticker}: Price ${current_price:.2f} vs Level ${exit_price:.2f}")
                 positions_to_close.append((ticker, exit_price, exit_reason))
                 continue

            # Update Trailing Stop only if trailing stop feature is enabled
            if position.use_trailing and self.use_stop_loss:
                new_stop_loss = self.risk_manager.update_trailing_stop(entry_price=position.entry_price, highest_price_since_entry=position.highest_price_since_entry, lowest_price_since_entry=position.lowest_price_since_entry, current_stop=position.stop_loss_price, direction=position.direction)
                if new_stop_loss != position.stop_loss_price:
                    position.stop_loss_price = new_stop_loss

        # Close positions scheduled for exit
        for ticker, price, reason in positions_to_close:
            self.close_position(ticker, price, current_date, reason=reason)