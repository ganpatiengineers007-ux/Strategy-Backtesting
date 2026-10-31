"""Corporate actions: pichhli bars ko back-adjust (split, dividend). Naya Bar list lautata hai, original nahi badalta."""
from data.models import Bar


def _scale(bar, price_factor, volume_factor=1.0):
    return Bar(bar.ts, bar.open * price_factor, bar.high * price_factor, bar.low * price_factor,
               bar.close * price_factor, bar.volume * volume_factor, dict(bar.extras))


def apply_splits(bars, splits):
    """splits: [{"date": "YYYY-MM-DD", "ratio": 2.0}]  (2-for-1 => ratio 2.0). date se pehle ki bars adjust."""
    for s in splits:
        if s["ratio"] <= 0:
            raise ValueError("split ratio > 0 hona chahiye")
    out = []
    for b in bars:
        f = 1.0
        for s in splits:
            if b.ts[:10] < s["date"]:
                f *= s["ratio"]
        out.append(_scale(b, 1.0 / f, f))
    return out


def apply_dividends(bars, dividends):
    """dividends: [{"date": "YYYY-MM-DD", "amount": 5.0}]. Factor = 1 - amount / (ex-date se pehle ka last close)."""
    factors = []
    for d in dividends:
        prev = [b for b in bars if b.ts[:10] < d["date"]]
        if not prev:
            continue
        if d["amount"] < 0 or d["amount"] >= prev[-1].close:
            raise ValueError("dividend amount 0 se close ke beech hona chahiye")
        factors.append((d["date"], 1.0 - d["amount"] / prev[-1].close))
    out = []
    for b in bars:
        f = 1.0
        for date, k in factors:
            if b.ts[:10] < date:
                f *= k
        out.append(_scale(b, f))
    return out
