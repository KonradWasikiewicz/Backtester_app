import pytest
from src.portfolio.risk_manager import RiskManager


@pytest.fixture
def risk_manager():
    """Return a RiskManager with default configuration."""
    return RiskManager()


def test_calculate_stops_long_default(risk_manager):
    entry_price = 100.0
    stop, take = risk_manager.calculate_stops(entry_price=entry_price, direction=1)
    assert stop == pytest.approx(entry_price * 0.999)
    assert take == pytest.approx(entry_price * 1.001)


def test_calculate_stops_short_default(risk_manager):
    entry_price = 100.0
    stop, take = risk_manager.calculate_stops(entry_price=entry_price, direction=-1)
    assert stop == pytest.approx(entry_price * 1.001)
    assert take == pytest.approx(entry_price * 0.999)
