"""Option data checks. Poora option backtest tab banega jab option-chain data + strategy ke niyam milenge."""
from dataclasses import dataclass
from datetime import date

REQUIRED = ("ts", "underlying", "expiry", "strike", "option_type", "lot_size")


@dataclass(frozen=True)
class OptionContract:
    underlying: str
    expiry: str
    strike: float
    kind: str
    lot_size: int


def days_to_expiry(ts, expiry):
    return (date.fromisoformat(expiry) - date.fromisoformat(ts[:10])).days


def validate_chain(rows):
    issues = []
    for i, r in enumerate(rows):
        missing = [k for k in REQUIRED if r.get(k) in (None, "")]
        if missing:
            issues.append({"row": i, "code": "MISSING_FIELDS", "msg": ",".join(missing)})
            continue
        try:
            if float(r["strike"]) <= 0:
                issues.append({"row": i, "code": "BAD_STRIKE", "msg": str(r["strike"])})
            if int(r["lot_size"]) <= 0:
                issues.append({"row": i, "code": "BAD_LOT_SIZE", "msg": str(r["lot_size"])})
            if str(r["option_type"]).upper() not in ("CE", "PE", "CALL", "PUT"):
                issues.append({"row": i, "code": "BAD_OPTION_TYPE", "msg": str(r["option_type"])})
            if days_to_expiry(r["ts"], r["expiry"]) < 0:
                issues.append({"row": i, "code": "EXPIRED_CONTRACT", "msg": r["expiry"]})
        except (ValueError, TypeError) as e:
            issues.append({"row": i, "code": "BAD_VALUE", "msg": str(e)})
            continue
        bid, ask = r.get("bid"), r.get("ask")
        if bid is not None and ask is not None and (float(bid) < 0 or float(bid) > float(ask)):
            issues.append({"row": i, "code": "BAD_BID_ASK", "msg": f"{bid}>{ask}"})
    return issues


def quality_status(issues):
    return "BLOCKED" if issues else "PASS"
