from registry.registry import Registry


def _readiness(manifest):
    reason = str(manifest.get("blocked_reason") or "").strip()
    status = "BLOCKED" if reason else "RUNNABLE"
    required = list(manifest.get("required_data") or [])
    hint = ""
    if status == "RUNNABLE" and required:
        hint = "requires " + ", ".join(required) + "; use a dataset containing those fields"
    return {"status": status, "runnable": status == "RUNNABLE", "reason": reason, "data_hint": hint}


def _view(manifest, source_hash):
    live = manifest.get("live_trading")
    enabled = bool(live.get("enabled")) if isinstance(live, dict) else bool(live)
    return {**manifest, **_readiness(manifest), "source_hash": source_hash,
            "live_trading_enabled": enabled}


def list_strategies():
    reg = Registry()
    return [_view(reg.manifest(s), reg.source_hash(s)) for s in reg.discover()]


def get_strategy(strategy_id):
    reg = Registry()
    m = reg.manifest(strategy_id)  # KeyError agar unknown
    return _view(m, reg.source_hash(strategy_id))
