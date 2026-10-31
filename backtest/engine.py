"""Backtest engine entry point.
Flow: event -> strategy -> signal validation -> sizing -> risk -> next-bar-open fill (no look-ahead)
      -> stops -> portfolio/accounting -> risk recheck."""
from backtest import position_sizing
from backtest.execution import ExecutionModel
from backtest.accounting import EquityCurve
from backtest.clock import SimClock
from backtest.event_queue import EventQueue
from backtest.portfolio import Portfolio
from backtest.results import BacktestResult
from risk.limits import RiskLimits
from risk.manager import RiskManager
from strategies.context import Context
from strategies.validation import check_data_requirements

ENGINE_VERSION = "0.1.0"
DEFAULT_CONFIG = {"initial_capital": 1_000_000.0, "slippage_bps": 2.0, "fee_pct": 0.0003,
                  "risk_per_trade_pct": 1.0, "ambiguous_candle_policy": "stop_first",
                  "max_position_pct": 100.0, "max_drawdown_pct": 30.0}


def run_backtest(dataset, strategy, config=None):
    cfg = dict(DEFAULT_CONFIG)
    cfg.update(config or {})
    meta = dict(dataset.meta())
    meta["engine_version"] = ENGINE_VERSION
    if dataset.quality_status == "BLOCKED":
        return BacktestResult("BLOCKED", "DATA_QUALITY_BLOCKED", config=cfg, meta=meta)
    ok, missing = check_data_requirements(strategy.required_data, dataset)
    if not ok:
        return BacktestResult("BLOCKED", "MISSING_DATA:" + ",".join(missing), config=cfg, meta=meta)

    pf, curve, clock = Portfolio(cfg["initial_capital"]), EquityCurve(), SimClock()
    risk = RiskManager(RiskLimits(cfg["max_position_pct"], cfg["max_drawdown_pct"]))
    bps, fee_pct, policy = cfg["slippage_bps"], cfg["fee_pct"], cfg["ambiguous_candle_policy"]
    bars, pending, rejections, status, reason = dataset.bars, None, [], "COMPLETED", ""

    model = ExecutionModel(bps, fee_pct, policy)

    def close(raw_price, bar, why):
        px, fee = model.fill_exit(raw_price, pf.position.qty)
        pf.close(px, bar.ts, fee, why)

    for i, bar in EventQueue(bars):
        clock.set(bar.ts)
        if pending and pf.position is None:
            px, fee = model.fill_entry(bar.open, pending["qty"])
            pf.open(pending["qty"], px, bar.ts, pending["stop"], pending["target"], fee)
        pending = None
        ex = model.check_exit(pf.position, bar)
        if ex:
            close(ex[0], bar, ex[1])
        eq = pf.equity(bar.close)
        curve.record(bar.ts, eq)
        if risk.after_bar(eq):
            if pf.position:
                close(bar.close, bar, "KILL_SWITCH")
            status, reason = "HALTED", risk.kill.reason
            break
        sig = strategy.on_bar(Context(bars, i, pf.position))
        if sig is None:
            continue
        try:
            sig.validate()
        except ValueError as e:
            rejections.append({"ts": bar.ts, "reason": f"INVALID_SIGNAL:{e}"})
            continue
        if sig.side == "BUY" and pf.position is None:
            qty = position_sizing.size(eq, bar.close, sig.stop_loss, cfg["risk_per_trade_pct"], cfg["max_position_pct"])
            allowed, why = risk.check_order(qty, bar.close, eq)
            if allowed:
                pending = {"qty": qty, "stop": sig.stop_loss, "target": sig.target}
            else:
                rejections.append({"ts": bar.ts, "reason": why})
        elif sig.side == "EXIT" and pf.position:
            close(bar.close, bar, "SIGNAL_EXIT")
    if pf.position and bars:
        close(bars[-1].close, bars[-1], "END_OF_DATA")
    return BacktestResult(status, reason, pf.trades, curve.points, rejections, cfg, meta)
