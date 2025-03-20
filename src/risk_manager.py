import pandas as pd
import numpy as np

class RiskManager:
    def __init__(self, max_position_size: float = 0.2, stop_loss_pct: float = 0.02,
                 max_drawdown: float = 0.2, volatility_lookback: int = 20):
        self.max_position_size = max_position_size
        self.stop_loss_pct = stop_loss_pct
        self.max_drawdown = max_drawdown
        self.volatility_lookback = volatility_lookback

    def calculate_position_size(self, capital: float, price: float, volatility: float) -> float:
        """Oblicza wielkość pozycji uwzględniając zmienność"""
        risk_amount = capital * self.stop_loss_pct
        position_size = risk_amount / (price * volatility)
        return min(position_size, capital * self.max_position_size / price)

    def calculate_stops(self, entry_price: float, signal: int) -> tuple:
        """Oblicza poziomy stop-loss i take-profit"""
        stop_loss = entry_price * (1 - self.stop_loss_pct * signal)
        take_profit = entry_price * (1 + self.stop_loss_pct * 2 * signal)
        return stop_loss, take_profit

    def check_risk_limits(self, portfolio_value: pd.Series) -> bool:
        """Sprawdza, czy nie przekroczono maksymalnego drawdownu"""
        drawdown = (portfolio_value - portfolio_value.cummax()) / portfolio_value.cummax()
        return drawdown.min() > -self.max_drawdown
