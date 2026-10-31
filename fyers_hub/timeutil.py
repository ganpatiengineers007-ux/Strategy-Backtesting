"""IST, market sessions, expiry time."""
from __future__ import annotations

import re
from datetime import date, datetime, time as dtime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
_CD = re.compile(r"(USDINR|EURINR|GBPINR|JPYINR)")


def to_ist(ts: int | float) -> datetime:
    return datetime.fromtimestamp(ts, IST)


def ist_date(ts: int | float) -> date:
    return to_ist(ts).date()


def day_start_epoch(d: date) -> int:
    return int(datetime.combine(d, dtime(0, 0), IST).timestamp())


def session_for(symbol: str) -> tuple[int, int]:
    """(open, close) - raat 12 baje se minutes me, IST. Holiday calendar yahan nahi hai."""
    s = symbol.upper()
    if s.startswith("MCX:"):
        return 9 * 60, 23 * 60 + 30
    if s.startswith("NSE:") and _CD.search(s):
        return 9 * 60, 17 * 60
    return 9 * 60 + 15, 15 * 60 + 30


def is_market_open(symbol: str, now_ts: float) -> bool:
    dt = to_ist(now_ts)
    if dt.weekday() >= 5:
        return False
    o, c = session_for(symbol)
    m = dt.hour * 60 + dt.minute
    return o <= m < c


def expiry_close_epoch(expiry_epoch: int, symbol: str = "NSE:") -> int:
    """Fyers ka expiry epoch din batata hai; asli expiry us din ke market close par maani."""
    d = ist_date(expiry_epoch)
    _, close = session_for(symbol)
    return int(datetime.combine(d, dtime(close // 60, close % 60), IST).timestamp())


def parse_day(x) -> date:
    if isinstance(x, datetime):
        return x.astimezone(IST).date() if x.tzinfo else x.date()
    if isinstance(x, date):
        return x
    return date.fromisoformat(str(x)[:10])
