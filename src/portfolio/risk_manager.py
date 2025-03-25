import pandas as pd
import numpy as np

class RiskManager:
    def __init__(self, max_position_size: float = 0.2, stop_loss_pct: float = 0.02,
                 max_drawdown: float = 0.2, volatility_lookback: int = 20):
        self.max_position_size = max_position_size  # 20% of portfolio maximum
        self.stop_loss_pct = stop_loss_pct         # 2% stop loss
        self.max_drawdown = max_drawdown           # 20% maximum drawdown
        self.volatility_lookback = volatility_lookback

    def calculate_position_size(self, capital: float, price: float, volatility: float) -> float:
        """Calculate position size based on risk parameters"""
        risk_amount = capital * self.stop_loss_pct
        position_size = risk_amount / (price * volatility)
        max_size = capital * self.max_position_size / price
        return min(position_size, max_size)

    def calculate_stops(self, entry_price: float, signal: int) -> tuple:
        """Calculate stop-loss and take-profit levels"""
        direction = 1 if signal > 0 else -1
        stop_loss = entry_price * (1 - self.stop_loss_pct * direction)
        take_profit = entry_price * (1 + self.stop_loss_pct * 2 * direction)  # 2:1 reward-risk ratio
        return stop_loss, take_profit

    def check_risk_limits(self, portfolio_value: pd.Series) -> bool:
        """Check if portfolio drawdown exceeds limits"""
        if len(portfolio_value) < 2:
            return True
            
        drawdown = (portfolio_value - portfolio_value.cummax()) / portfolio_value.cummax()
        current_drawdown = abs(drawdown.iloc[-1])
        return current_drawdown <= self.max_drawdown
