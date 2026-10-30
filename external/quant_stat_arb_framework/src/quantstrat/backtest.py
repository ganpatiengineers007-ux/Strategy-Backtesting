from dataclasses import dataclass
import pandas as pd
from .models import Side, Position, Signal
from .risk import RiskManager
from .execution import DryRunExecutor

@dataclass
class BacktestResult:
    trades: pd.DataFrame
    equity_curve: pd.Series
    final_equity: float

def run_backtest(data: pd.DataFrame, signals: list[Signal], risk_manager: RiskManager,
                 initial_equity: float = 1_000_000.0, fee_bps: float = 2.0,
                 slippage_bps: float = 1.0) -> BacktestResult:
    """One-position-at-a-time OHLC simulator; entries occur at next bar open."""
    if initial_equity <= 0:
        raise ValueError("initial_equity must be positive")
    if fee_bps < 0 or slippage_bps < 0:
        raise ValueError("cost assumptions cannot be negative")
    signal_by_time = {s.timestamp: s for s in signals}
    equity = float(initial_equity)
    position = None
    trades, curve = [], []
    for i in range(len(data)):
        ts, bar = data.index[i], data.iloc[i]
        # Manage existing position first. Conservative intrabar rule: stop wins if
        # both stop and target are touched within the same OHLC bar.
        if position is not None:
            exit_price, exit_reason = None, None
            if position.side == Side.BUY:
                if bar["low"] <= position.stop_price:
                    exit_price, exit_reason = position.stop_price, "STOP"
                elif bar["high"] >= position.target_price:
                    exit_price, exit_reason = position.target_price, "TARGET"
            else:
                if bar["high"] >= position.stop_price:
                    exit_price, exit_reason = position.stop_price, "STOP"
                elif bar["low"] <= position.target_price:
                    exit_price, exit_reason = position.target_price, "TARGET"
            if exit_price is not None:
                direction = 1 if position.side == Side.BUY else -1
                exit_price *= (1 - slippage_bps / 10000 * direction)
                gross = (exit_price - position.entry_price) * position.quantity * direction
                fees = (abs(exit_price * position.quantity) +
                        abs(position.entry_price * position.quantity)) * fee_bps / 10000
                pnl = gross - fees
                equity += pnl
                trades.append({"entry_time": position.entry_timestamp, "exit_time": ts,
                               "side": position.side.value, "quantity": position.quantity,
                               "entry_price": position.entry_price, "exit_price": exit_price,
                               "gross_pnl": gross, "fees": fees, "net_pnl": pnl,
                               "exit_reason": exit_reason, "equity": equity})
                position = None

        # Signal timestamp is the completed signal bar; execute at the next bar open.
        if position is None and i > 0:
            prior_ts = data.index[i - 1]
            sig = signal_by_time.get(prior_ts)
            if sig is not None:
                intent = risk_manager.create_order_intent(sig, equity)
                if intent is not None:
                    direction = 1 if intent.side == Side.BUY else -1
                    entry = float(bar["open"]) * (1 + slippage_bps / 10000 * direction)
                    # Shift ATR-derived barriers by the difference between signal close and
                    # actual next-open fill, preserving the original stop/target distances.
                    stop_dist = abs(intent.reference_price - intent.stop_price)
                    target_dist = abs(intent.target_price - intent.reference_price)
                    stop = entry - direction * stop_dist
                    target = entry + direction * target_dist
                    position = Position(intent.side, intent.quantity, entry, stop, target,
                                        ts, intent.risk_amount)

        curve.append({"timestamp": ts, "equity": equity})
    eq = pd.DataFrame(curve).set_index("timestamp")["equity"] if curve else pd.Series(dtype=float)
    return BacktestResult(pd.DataFrame(trades), eq, equity)
