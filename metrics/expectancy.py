def expectancy(trades):
    return sum(t["pnl"] for t in trades) / len(trades) if trades else 0.0
