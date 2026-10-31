"""Regime = din ki range (high/low volatility). Dono regime me edge chahiye."""
from metrics import expectancy

MIN_TRADES = 5


def decide(groups):
    if sum(len(g) for g in groups.values()) < MIN_TRADES or any(len(g) < 2 for g in groups.values()):
        return "UNAVAILABLE", "TOO_FEW_TRADES_PER_REGIME"
    return ("PASS" if all(expectancy.expectancy(g) > 0 for g in groups.values()) else "FAIL"), ""


def run(dataset, result):
    rng = {}
    for b in dataset.bars:
        r = rng.setdefault(b.ts[:10], [b.high, b.low, b.open])
        r[0], r[1] = max(r[0], b.high), min(r[1], b.low)
    vol = {d: (h - l) / o for d, (h, l, o) in rng.items()}
    if not vol:
        return {"status": "UNAVAILABLE", "reason": "NO_DATA"}
    med = sorted(vol.values())[len(vol) // 2]
    groups = {"high_vol": [], "low_vol": []}
    for t in result.trades:
        groups["high_vol" if vol.get(t["entry_ts"][:10], 0) >= med else "low_vol"].append(t)
    status, reason = decide(groups)
    return {"status": status, "reason": reason,
            "regimes": {k: {"trades": len(g), "expectancy": expectancy.expectancy(g)} for k, g in groups.items()}}
