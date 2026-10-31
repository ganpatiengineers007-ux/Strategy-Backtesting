"""Backtest request/response models + strict validation (API ke andar aane wala data yahin parkha jaata hai)."""
from dataclasses import dataclass, field

ALLOWED_KEYS = {"strategy_id", "dataset", "params", "config", "symbol", "timeframe", "validation"}


@dataclass
class BacktestRequest:
    strategy_id: str
    dataset: str
    params: dict = field(default_factory=dict)
    config: dict = field(default_factory=dict)
    symbol: str = "UNKNOWN"
    timeframe: str = "UNKNOWN"
    validation: dict = field(default_factory=dict)  # optional: {"split": 0.7, "windows": 4}

    @classmethod
    def from_dict(cls, d):
        if not isinstance(d, dict):
            raise ValueError("JSON object chahiye")
        unknown = set(d) - ALLOWED_KEYS
        if unknown:
            raise ValueError("unknown keys: " + ", ".join(sorted(unknown)))
        for k in ("strategy_id", "dataset"):
            if not isinstance(d.get(k), str) or not d[k].strip():
                raise ValueError(f"{k} chahiye")
        for k in ("params", "config", "validation"):
            if d.get(k) is not None and not isinstance(d[k], dict):
                raise ValueError(f"{k} object hona chahiye")
        v = d.get("validation") or {}
        if set(v) - {"split", "windows"}:
            raise ValueError("validation me sirf split, windows allowed")
        if "split" in v and not (isinstance(v["split"], (int, float)) and 0.1 <= v["split"] <= 0.9):
            raise ValueError("split 0.1 se 0.9 ke beech")
        if "windows" in v and not (isinstance(v["windows"], int) and not isinstance(v["windows"], bool) and 2 <= v["windows"] <= 12):
            raise ValueError("windows 2 se 12 ke beech (int)")
        return cls(d["strategy_id"].strip(), d["dataset"].strip(), dict(d.get("params") or {}), dict(d.get("config") or {}),
                   str(d.get("symbol", "UNKNOWN")), str(d.get("timeframe", "UNKNOWN")), dict(v))


@dataclass
class BacktestResponse:
    job_id: str
    status: str
    result: dict = None
    error: str = None
