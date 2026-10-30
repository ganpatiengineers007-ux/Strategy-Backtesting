"""Raw rows -> Bar list (common schema). Extra numeric columns (oi, option_chain...) extras me jaate hain."""
from data.models import Bar

BASE = ("ts", "timestamp", "datetime", "open", "high", "low", "close", "volume")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return v


def normalize(rows):
    bars = []
    for raw in rows:
        r = {str(k).strip().lower(): v for k, v in raw.items()}
        ts = r.get("ts") or r.get("timestamp") or r.get("datetime")
        if not ts:
            raise ValueError("timestamp column missing (ts/timestamp/datetime)")
        for col in ("open", "high", "low", "close"):
            if col not in r:
                raise ValueError(f"column missing: {col}")
        extras = {k: _num(v) for k, v in r.items() if k not in BASE and v not in ("", None)}
        bars.append(Bar(str(ts).strip(), float(r["open"]), float(r["high"]), float(r["low"]),
                        float(r["close"]), float(r.get("volume") or 0), extras))
    return bars
