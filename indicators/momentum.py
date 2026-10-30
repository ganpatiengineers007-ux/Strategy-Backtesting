def _rsi(ag, al):
    return 100.0 if al == 0 else 100.0 - 100.0 / (1 + ag / al)


def rsi(closes, n=14):
    out = [None] * len(closes)
    if len(closes) <= n:
        return out
    gains = losses = 0.0
    for i in range(1, n + 1):
        d = closes[i] - closes[i - 1]
        gains, losses = gains + max(d, 0), losses + max(-d, 0)
    ag, al = gains / n, losses / n
    out[n] = _rsi(ag, al)
    for i in range(n + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        ag, al = (ag * (n - 1) + max(d, 0)) / n, (al * (n - 1) + max(-d, 0)) / n
        out[i] = _rsi(ag, al)
    return out


def roc(values, n):
    return [None if i < n else (v / values[i - n] - 1) * 100.0 for i, v in enumerate(values)]
