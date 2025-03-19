def calculate_position_size(capital: float, risk_per_trade: float, stop_loss_distance: float) -> float:
    """
    Oblicza wielkość pozycji na podstawie ryzyka przypadającego na pojedynczą transakcję.
    
    capital: całkowity kapitał.
    risk_per_trade: procent kapitału ryzykowany w pojedynczej transakcji (np. 0.01 dla 1%).
    stop_loss_distance: odległość stop-loss w jednostkach ceny.
    """
    risk_amount = capital * risk_per_trade
    position_size = risk_amount / stop_loss_distance
    return position_size
