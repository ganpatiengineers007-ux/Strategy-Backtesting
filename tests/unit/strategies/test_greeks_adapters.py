"""Greeks adapters: four long-only strategies must emit signals; theta is blocked."""
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "all_strategies" / "greeks"))

import gamma_vwap_strategy as G  # noqa: E402

from strategies.context import Context  # noqa: E402


def _bars():
    return [{"ts": r["t"].isoformat(), "open": r["o"], "high": r["h"], "low": r["l"],
             "close": r["c"], "volume": r["v"], "max_gamma_strike": r["g"],
             "expiry_window": r["w"]} for r in G.synthetic()]


@pytest.mark.parametrize("module,cls_name", [
    ("strategies.G01_gamma_vwap.strategy", "GammaVwapAdapter"),
    ("strategies.G02_delta_vwap.strategy", "DeltaVwapAdapter"),
    ("strategies.G03_vega_iv.strategy", "VegaIvAdapter"),
    ("strategies.G05_greeks_confluence.strategy", "GreeksConfluenceAdapter"),
])
def test_adapter_emits_buys(module, cls_name):
    cls = getattr(importlib.import_module(module), cls_name)
    strategy, bars, pos, buys = cls(), _bars(), None, 0
    for i in range(len(bars)):
        sig = strategy.on_bar(Context(bars, i, pos))
        if sig is None:
            continue
        sig.validate()
        if sig.side == "BUY":
            buys += 1
            pos = True
        elif sig.side == "EXIT":
            pos = None
    assert buys > 0


def test_theta_adapter_is_explicitly_blocked():
    from strategies.G04_theta_straddle.strategy import ThetaStraddleAdapter
    with pytest.raises(RuntimeError, match="short option legs"):
        ThetaStraddleAdapter().on_bar(Context(_bars(), 0, None))
