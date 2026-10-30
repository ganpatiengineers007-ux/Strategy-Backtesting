"""Data checks: duplicate / out-of-order / bad timestamp / non-positive / inconsistent OHLC."""
from data.timestamps import parse_ts


def _issue(level, code, msg):
    return {"level": level, "code": code, "msg": msg}


def validate(bars):
    issues, seen, prev = [], set(), None
    if not bars:
        return [_issue("ERROR", "EMPTY", "no bars")]
    for b in bars:
        if b.ts in seen:
            issues.append(_issue("ERROR", "DUPLICATE_TS", b.ts))
        seen.add(b.ts)
        try:
            t = parse_ts(b.ts)
        except ValueError:
            issues.append(_issue("ERROR", "BAD_TS", b.ts))
            continue
        if prev is not None and t < prev:
            issues.append(_issue("ERROR", "OUT_OF_ORDER", b.ts))
        prev = t
        if min(b.open, b.high, b.low, b.close) <= 0:
            issues.append(_issue("ERROR", "NON_POSITIVE_PRICE", b.ts))
        if b.high < max(b.open, b.close, b.low) or b.low > min(b.open, b.close, b.high):
            issues.append(_issue("ERROR", "OHLC_INCONSISTENT", b.ts))
    return issues
