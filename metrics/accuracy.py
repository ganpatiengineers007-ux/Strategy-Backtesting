def win_rate(trades):
    return 100.0 * sum(1 for t in trades if t["pnl"] > 0) / len(trades) if trades else 0.0
