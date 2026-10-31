"""Survivorship-bias check: universe snapshots (date -> symbols) me churn dikhna chahiye."""


def check(snapshots):
    dates = sorted(snapshots)
    if len(dates) < 2:
        return {"status": "UNAVAILABLE", "reason": "NEED_MULTIPLE_UNIVERSE_SNAPSHOTS"}
    first, last = set(snapshots[dates[0]]), set(snapshots[dates[-1]])
    dropped, added = sorted(first - last), sorted(last - first)
    if not dropped and not added:
        return {"status": "WARN", "reason": "NO_CHURN: sirf aaj ke constituents hone ka khatra (survivorship bias)",
                "dropped": [], "added": []}
    return {"status": "PASS", "dropped": dropped, "added": added,
            "churn_pct": 100.0 * len(dropped) / len(first) if first else 0.0}
