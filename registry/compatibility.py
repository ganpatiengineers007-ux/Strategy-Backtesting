"""Manifest compatibility: backtest mode, live-trading band, min engine version."""


def _ver(s):
    parts = [int(x) for x in str(s).split(".")[:3]]
    return tuple(parts + [0] * (3 - len(parts)))


def check(manifest, engine_version=None):
    if engine_version is None:
        from backtest.engine import ENGINE_VERSION as engine_version
    errs = []
    if "backtest" not in (manifest.get("execution_modes") or []):
        errs.append("EXECUTION_MODE_BACKTEST_MISSING")
    lt = manifest.get("live_trading")
    if lt is True or (isinstance(lt, dict) and lt.get("enabled") is True):
        errs.append("LIVE_TRADING_NOT_ALLOWED")
    mv = manifest.get("min_engine_version")
    if mv is not None:
        try:
            if _ver(mv) > _ver(engine_version):
                errs.append(f"ENGINE_TOO_OLD:needs {mv}")
        except ValueError:
            errs.append("BAD_MIN_ENGINE_VERSION")
    return errs
