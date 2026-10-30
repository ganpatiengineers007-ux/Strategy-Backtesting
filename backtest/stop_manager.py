from backtest.fills import resolve_exit


def check(position, bar, policy="stop_first"):
    if position is None:
        return None
    return resolve_exit(bar, position.stop, position.target, policy)
