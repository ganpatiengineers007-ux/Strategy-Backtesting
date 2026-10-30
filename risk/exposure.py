def position_value(position, price):
    return 0.0 if position is None else position.qty * price
