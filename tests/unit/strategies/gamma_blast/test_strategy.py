"""GammaBlast behaviour: option-chain signal and completing engine run."""
from backtest.engine import run_backtest
from data.models import Bar, Dataset
from strategies.gamma_blast.strategy import GammaBlastStrategy


def _chain(ce_gamma=10.0, pe_gamma=5.0):
    return [
        {"strike": 100, "opt_type": "CE", "gamma": ce_gamma, "oi": 100000, "iv": 0.15},
        {"strike": 100, "opt_type": "PE", "gamma": pe_gamma, "oi": 100000, "iv": 0.15},
    ]


def _bar(ts, close=100.0, chain=None):
    extras = {"oi": 5000.0}
    if chain is not None:
        extras["option_chain"] = chain
    return Bar(ts, close, close + 1, close - 1, close, 1000, extras)


def test_signal_requires_option_chain_and_reads_it():
    strategy = GammaBlastStrategy()
    entry = _bar("2026-01-01T09:30:00", chain=_chain())
    no_chain = _bar("2026-01-01T09:30:00")
    from strategies.context import Context
    assert strategy.on_bar(Context([no_chain], 0, None)) is None
    sig = strategy.on_bar(Context([entry], 0, None))
    assert sig is not None and sig.side == "BUY"
    assert "gamma_blast_call" in sig.reason


def test_backtest_completes_with_option_chain_dataset():
    bars = [
        _bar("2026-01-01T09:30:00", chain=_chain()),
        _bar("2026-01-01T09:35:00", close=101.0),
        _bar("2026-01-01T15:15:00", close=102.0),
    ]
    ds = Dataset("opt", "NIFTY", "5m", bars, fields={"option_chain", "oi"}, quality_status="OK")
    result = run_backtest(ds, GammaBlastStrategy())
    assert result.status == "COMPLETED", result.reason
